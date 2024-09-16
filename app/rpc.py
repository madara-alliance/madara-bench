import datetime
import time
from enum import Enum
from typing import Any, Coroutine

import requests
from docker.models.containers import Container
from starknet_py.net.client_models import Hash, Tag
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.transaction import AccountTransaction

from app import error, models

MADARA_RPC_PORT: str = "9944/tcp"
DOCKER_HOST_PORT: str = "HostPort"


class RpcCall(str, Enum):
    # Read API
    STARKNET_BLOCK_HASH_AND_NUMBER = "starknet_blockHashAndNumber"
    STARKNET_BLOCK_NUMBER = "starknet_blockNumber"
    STARKNET_CALL = "starknet_call"
    STARKNET_CHAIN_ID = "starknet_chainId"
    STARKNET_ESTIMATE_FEE = "starknet_estimateFee"
    STARKNET_ESTIMATE_MESSAGE_FEE = "starknet_estimateMessageFee"
    STARKNET_GET_BLOCK_TRANSACTION_COUNT = "starknet_getBlockTransactionCount"
    STARKNET_GET_BLOCK_WITH_RECEIPTS = "starknet_getBlockWithReceipts"
    STARKNET_GET_BLOCK_WITH_TX_HASHES = "starknet_getBlockWithTxHashes"
    STARKNET_GET_BLOCK_WITH_TXS = "starknet_getBlockWithTxs"
    STARKNET_GET_CLASS = "starknet_getClass"
    STARKNET_GET_CLASS_AT = "starknet_getClassAt"
    STARKNET_GET_CLASS_HASH_AT = "starknet_getClassHashAt"
    STARKNET_GET_EVENTS = "starknet_getEvents"
    STARKNET_GET_NONCE = "starknet_getNonce"
    STARKNET_GET_STATE_UPDATE = "starknet_getStateUpdate"
    STARKNET_GET_STORAGE_AT = "starknet_getStorageAt"
    STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX = (
        "starknet_getTransactionByBlockIdAndIndex"
    )
    STARKNET_GET_TRANSACTION_BY_HASH = "starknet_getTransactionByHash"
    STARKNET_GET_TRANSACTION_RECEIPT = "starknet_getTransactionReceipt"
    STARKNET_GET_TRANSACTION_STATUS = "starknet_getTransactionStatus"
    STARKNET_SPEC_VERSION = "starknet_specVersion"
    STARKNET_SYNCING = "starknet_syncing"

    # Trace API
    STARKNET_SIMULATE_TRANSACTIONS = "starknet_simulateTransactions"
    STARKNET_TRACE_BLOCK_TRANSACTIONS = "starknet_traceBlockTransactions"
    STARKNET_TRACE_TRANSACTION = "starknet_traceTransaction"

    # ADD API
    STARKNET_ADD_DECLARE_TRANSACTION = "starknet_addDeclareTransaction"
    STARKNET_ADD_DEPLOY_ACCOUNT_TRANSACTION = (
        "starknet_addDeployAccountTransaction"
    )
    STARKNET_ADD_INVOKE_TRANSACTION = "starknet_addInvokeTransaction"


def json_rpc(
    url: str, method: str, params: dict[str, Any] | list[Any] = {}
) -> models.ResponseModelJSON:
    headers = {"content-type": "application/json"}
    data = {"id": 1, "jsonrpc": "2.0", "method": method, "params": params}

    time_start = datetime.datetime.now()
    perf_start = time.perf_counter_ns()
    response = requests.post(url=url, json=data, headers=headers)
    perf_stop = time.perf_counter_ns()
    perf_delta = perf_stop - perf_start

    output = response.json()

    return models.ResponseModelJSON(
        node=models.NodeName.MADARA,
        method=method,
        when=time_start,
        elapsed=perf_delta,
        output=output,
    )


async def json_rpc_duct_tape(
    method: str,
    caller: Coroutine[Any, Any, Any],
) -> models.ResponseModelJSON:
    # Temporary tape until starknet py has been integrated into the codebase
    time_start = datetime.datetime.now()
    perf_start = time.perf_counter_ns()
    output = await caller
    perf_stop = time.perf_counter_ns()
    perf_delta = perf_stop - perf_start

    return models.ResponseModelJSON(
        node=models.NodeName.MADARA,
        method=method,
        when=time_start,
        elapsed=perf_delta,
        output=output,
    )


def to_block_id(
    block_hash: str | None = None,
    block_number: int | None = None,
    block_tag: models.BlockTag | None = None,
) -> str | dict[str, str] | dict[str, int]:
    if isinstance(block_hash, str):
        return {"block_hash": block_hash}
    elif isinstance(block_number, int):
        return {"block_number": block_number}
    elif isinstance(block_tag, models.BlockTag):
        return block_tag.name
    else:
        raise error.ErrorBlockIdMissing()


def rpc_url(node: models.NodeName, container: Container):
    error.container_check_running(node, container)

    ports = container.ports

    match node:
        case models.NodeName.MADARA:
            port = ports[MADARA_RPC_PORT][0][DOCKER_HOST_PORT]
            return f"http://0.0.0.0:{port}"


# =========================================================================== #
#                                   READ API                                  #
# =========================================================================== #


def rpc_starknet_blockHashAndNumber(url: str) -> models.ResponseModelJSON:
    return json_rpc(url, RpcCall.STARKNET_BLOCK_HASH_AND_NUMBER)


def rpc_starknet_blockNumber(url: str) -> models.ResponseModelJSON:
    return json_rpc(url, RpcCall.STARKNET_BLOCK_NUMBER)


def rpc_starknet_call(
    url: str,
    request: models.body.Call,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_CALL,
        {"request": vars(request), "block_id": block_id},
    )


def rpc_starknet_chainId(url: str) -> models.ResponseModelJSON:
    return json_rpc(url, RpcCall.STARKNET_CHAIN_ID)


async def rpc_starknet_estimateFee(
    url: str,
    tx: AccountTransaction | list[AccountTransaction],
    block_hash: Hash | None = None,
    block_number: Tag | int | None = None,
) -> models.ResponseModelJSON:
    client = FullNodeClient(node_url=url)
    estimate_fee = client.estimate_fee(
        tx=tx, block_hash=block_hash, block_number=block_number
    )

    return await json_rpc_duct_tape(RpcCall.STARKNET_ESTIMATE_FEE, estimate_fee)


def rpc_starknet_estimateMessageFee(
    url: str,
    body: models.body.EstimateMessageFee,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_ESTIMATE_MESSAGE_FEE,
        {
            "from_address": body.from_address,
            "to_address": body.to_address,
            "entry_point_selector": body.entry_point_selector,
            "payload": body.payload,
            "block_id": block_id,
        },
    )


def rpc_starknet_getBlockTransactionCount(
    url: str, block_id: str | dict[str, str] | dict[str, int]
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_BLOCK_TRANSACTION_COUNT,
        {"block_id": block_id},
    )


async def rpc_starknet_getBlockWithReceipts(
    url: str, block_id: str | dict[str, str] | dict[str, int]
) -> models.ResponseModelJSON:
    return json_rpc(
        url, RpcCall.STARKNET_GET_BLOCK_WITH_RECEIPTS, {"block_id": block_id}
    )


def rpc_starknet_getBlockWithTxHashes(
    url: str, block_id: str | dict[str, str] | dict[str, int]
) -> models.ResponseModelJSON:
    return json_rpc(
        url, RpcCall.STARKNET_GET_BLOCK_WITH_TX_HASHES, {"block_id": block_id}
    )


async def rpc_starknet_getBlockWithTxs(
    url: str, block_id: str | dict[str, str] | dict[str, int]
) -> models.ResponseModelJSON:
    return json_rpc(
        url, RpcCall.STARKNET_GET_BLOCK_WITH_TXS, {"block_id": block_id}
    )


def rpc_starnet_getClass(
    url: str, class_hash: str, block_id: str | dict[str, str] | dict[str, int]
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_CLASS,
        {"block_id": block_id, "class_hash": class_hash},
    )


def rpc_starknet_getClassAt(
    url: str,
    contract_address: str,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_CLASS_AT,
        {"block_id": block_id, "contract_address": contract_address},
    )


def rpc_starknet_getClassHashAt(
    url: str,
    contract_address: str,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_CLASS_HASH_AT,
        {"block_id": block_id, "contract_address": contract_address},
    )


def rcp_starknet_getEvents(
    url: str, body: models.body.GetEvents
) -> models.ResponseModelJSON:
    return json_rpc(url, RpcCall.STARKNET_GET_EVENTS, {"filter": body})


def rpc_starknet_getNonce(
    url: str,
    contract_address: models.query.ContractAddress,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_NONCE,
        {"block_id": block_id, "contract_address": contract_address},
    )


def rpc_starknet_getStateUpdate(
    url: str, block_id: str | dict[str, str] | dict[str, int]
) -> models.ResponseModelJSON:
    return json_rpc(
        url, RpcCall.STARKNET_GET_STATE_UPDATE, {"block_id": block_id}
    )


async def rpc_starknet_getStorageAt(
    url: str,
    contract_address: str,
    contract_key: str,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_STORAGE_AT,
        {
            "contract_address": contract_address,
            "key": contract_key,
            "block_id": block_id,
        },
    )


def rpc_starknet_getTransactionByBlockIdAndIndex(
    url: str,
    transaction_index: int,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX,
        {"block_id": block_id, "index": transaction_index},
    )


def rpc_starknet_getTransactionByHash(
    url: str, transaction_hash: str
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_TRANSACTION_BY_HASH,
        {"transaction_hash": transaction_hash},
    )


def rpc_starknet_getTransactionReceipt(
    url: str, transaction_hash: str
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_TRANSACTION_RECEIPT,
        {"transaction_hash": transaction_hash},
    )


def rpc_starknet_getTransactionStatus(
    url: str, transaction_hash: str
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_GET_TRANSACTION_STATUS,
        {"transaction_hash": transaction_hash},
    )


def rpc_starknet_specVersion(url: str) -> models.ResponseModelJSON:
    return json_rpc(url, RpcCall.STARKNET_SPEC_VERSION)


def rpc_starknet_syncing(url: str) -> models.ResponseModelJSON:
    return json_rpc(url, RpcCall.STARKNET_SYNCING)


# =========================================================================== #
#                                  TRACE API                                  #
# =========================================================================== #


def rpc_starknet_simulateTransactions(
    url: str,
    body: models.body.SimulateTransactions,
    block_id: str | dict[str, str] | dict[str, int],
):
    return json_rpc(
        url,
        RpcCall.STARKNET_SIMULATE_TRANSACTIONS,
        {
            "block_id": block_id,
            "transactions": body.transactions,
            "simulation_flags": body.simulation_flags,
        },
    )


async def rpc_starknet_traceBlockTransactions(
    url: str,
    block_id: str | dict[str, str] | dict[str, int],
) -> models.ResponseModelJSON:
    return json_rpc(
        url, RpcCall.STARKNET_TRACE_BLOCK_TRANSACTIONS, {"block_id": block_id}
    )


def rpc_starknet_traceTransaction(
    url: str, transaction_hash: models.query.TxHash
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_TRACE_TRANSACTION,
        {"transaction_hash": transaction_hash},
    )


# =========================================================================== #
#                                  WRITE API                                  #
# =========================================================================== #


def rpc_starknet_addDeclareTransaction(
    url: str, declare_transaction: models.body.TxDeclare
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_ADD_DECLARE_TRANSACTION,
        {"declare_transaction": declare_transaction},
    )


def rpc_starknet_addDeployAccountTransaction(
    url: str, deploy_account_transaction: models.body.TxDeploy
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_ADD_DEPLOY_ACCOUNT_TRANSACTION,
        {"deploy_account_transaction": deploy_account_transaction},
    )


def rpc_starknetAddInvokeTransaction(
    url: str, invoke_transaction: models.body.TxInvoke
) -> models.ResponseModelJSON:
    return json_rpc(
        url,
        RpcCall.STARKNET_ADD_INVOKE_TRANSACTION,
        {"invoke_transaction": invoke_transaction},
    )
