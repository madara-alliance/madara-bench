import datetime
import time
import typing
from enum import Enum
from typing import Any, Coroutine, TypeVar

import requests
from docker.models.containers import Container
from starknet_py.net.client_models import (
    BlockHashAndNumber,
    BlockStateUpdate,
    BlockTransactionTrace,
    DeprecatedContractClass,
    EstimatedFee,
    EventsChunk,
    PendingBlockStateUpdate,
    PendingStarknetBlock,
    PendingStarknetBlockWithReceipts,
    PendingStarknetBlockWithTxHashes,
    SierraContractClass,
    SimulatedTransaction,
    StarknetBlock,
    StarknetBlockWithReceipts,
    StarknetBlockWithTxHashes,
    SyncStatus,
    Tag,
    Transaction,
    TransactionReceipt,
    TransactionStatusResponse,
)
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.transaction import AccountTransaction

from app import error, models

MADARA_RPC_PORT: str = "9944/tcp"
DOCKER_HOST_PORT: str = "HostPort"

T = TypeVar("T")


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


def json_rpc(
    url: str, method: str, params: dict[str, Any] | list[Any] = {}
) -> models.ResponseModelJSON[Any]:
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


async def json_rpc_starknet_py(
    method: str,
    caller: Coroutine[Any, Any, T],
) -> models.ResponseModelJSON:
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


def to_block_number_or_tag(
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> Tag | int | None:
    if block_number is None:
        return block_tag
    else:
        return block_number


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


async def rpc_starknet_blockHashAndNumber(
    url: str,
) -> models.ResponseModelJSON[BlockHashAndNumber]:
    client = FullNodeClient(node_url=url)
    block_hash_and_number = client.get_block_hash_and_number()
    return await json_rpc_starknet_py(
        RpcCall.STARKNET_BLOCK_HASH_AND_NUMBER, block_hash_and_number
    )


async def rpc_starknet_blockNumber(url: str) -> models.ResponseModelJSON[int]:
    client = FullNodeClient(node_url=url)
    block_number = client.get_block_number()
    return await json_rpc_starknet_py(
        RpcCall.STARKNET_BLOCK_NUMBER, block_number
    )


async def rpc_starknet_call(
    url: str,
    call: models.body.Call,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[list[int]]:
    client = FullNodeClient(node_url=url)
    call = client.call_contract(
        call, block_hash, to_block_number_or_tag(block_number, block_tag)
    )
    return await json_rpc_starknet_py(RpcCall.STARKNET_CALL, call)


async def rpc_starknet_chainId(url: str) -> models.ResponseModelJSON[str]:
    client = FullNodeClient(node_url=url)
    chain_id = client.get_chain_id()
    return await json_rpc_starknet_py(RpcCall.STARKNET_CHAIN_ID, chain_id)


async def rpc_starknet_estimateFee(
    url: str,
    tx: models.body.Tx | list[models.body.Tx],
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[EstimatedFee | list[EstimatedFee]]:
    client = FullNodeClient(node_url=url)
    estimate_fee = client.estimate_fee(
        typing.cast(AccountTransaction, tx),
        # TODO: make this an option
        True,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_ESTIMATE_FEE, estimate_fee
    )


async def rpc_starknet_estimateMessageFee(
    url: str,
    body: models.body.EstimateMessageFee,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[EstimatedFee]:
    client = FullNodeClient(node_url=url)
    estimage_message_fee = client.estimate_message_fee(
        body.from_address,
        body.to_address,
        body.entry_point_selector,
        body.payload,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_ESTIMATE_MESSAGE_FEE, estimage_message_fee
    )


async def rpc_starknet_getBlockTransactionCount(
    url: str,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[int]:
    client = FullNodeClient(node_url=url)
    get_block_tx_count = client.get_block_transaction_count(
        block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_BLOCK_TRANSACTION_COUNT, get_block_tx_count
    )


async def rpc_starknet_getBlockWithReceipts(
    url: str,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[
    PendingStarknetBlockWithReceipts | StarknetBlockWithReceipts
]:
    client = FullNodeClient(node_url=url)
    block_with_receipts = client.get_block_with_receipts(
        block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_BLOCK_WITH_RECEIPTS, block_with_receipts
    )


async def rpc_starknet_getBlockWithTxHashes(
    url: str,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[
    PendingStarknetBlockWithTxHashes | StarknetBlockWithTxHashes
]:
    client = FullNodeClient(node_url=url)
    block_with_tx_hashes = client.get_block_with_tx_hashes(
        block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_BLOCK_WITH_TX_HASHES, block_with_tx_hashes
    )


async def rpc_starknet_getBlockWithTxs(
    url: str,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[PendingStarknetBlock | StarknetBlock]:
    client = FullNodeClient(node_url=url)
    block_with_txs = client.get_block_with_txs(
        block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_BLOCK_WITH_TXS, block_with_txs
    )


async def rpc_starnet_getClass(
    url: str,
    class_hash: models.query.ClassHash,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[SierraContractClass | DeprecatedContractClass]:
    client = FullNodeClient(node_url=url)
    class_by_hash = client.get_class_by_hash(
        class_hash, block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(RpcCall.STARKNET_GET_CLASS, class_by_hash)


async def rpc_starknet_getClassAt(
    url: str,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[SierraContractClass | DeprecatedContractClass]:
    client = FullNodeClient(node_url=url)
    class_at = client.get_class_at(
        contract_address,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(RpcCall.STARKNET_GET_CLASS_AT, class_at)


async def rpc_starknet_getClassHashAt(
    url: str,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[int]:
    client = FullNodeClient(node_url=url)
    class_hash = client.get_class_hash_at(
        contract_address,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_CLASS_HASH_AT, class_hash
    )


async def rcp_starknet_getEvents(
    url: str, body: models.body.GetEvents
) -> models.ResponseModelJSON[EventsChunk]:
    client = FullNodeClient(node_url=url)
    get_events = client.get_events(
        address=body.address,
        keys=body.keys,
        from_block_number=body.from_block_number,
        from_block_hash=body.from_block_hash,
        to_block_number=body.to_block_number,
        to_block_hash=body.to_block_hash,
        follow_continuation_token=body.continuation_token is None,
        continuation_token=body.continuation_token,
        chunk_size=body.chunk_size,
    )

    return await json_rpc_starknet_py(RpcCall.STARKNET_GET_EVENTS, get_events)


async def rpc_starknet_getNonce(
    url: str,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[int]:
    client = FullNodeClient(node_url=url)
    nonce = client.get_contract_nonce(
        contract_address,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(RpcCall.STARKNET_GET_NONCE, nonce)


async def rpc_starknet_getStateUpdate(
    url: str,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[PendingBlockStateUpdate | BlockStateUpdate]:
    client = FullNodeClient(node_url=url)
    state_update = client.get_state_update(
        block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_STATE_UPDATE, state_update
    )


async def rpc_starknet_getStorageAt(
    url: str,
    contract_address: models.query.ContractAddress,
    key: models.query.ContractKey,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[int]:
    if isinstance(key, str):
        key = int(key, 0)

    client = FullNodeClient(node_url=url)
    storage = client.get_storage_at(
        contract_address,
        key,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(RpcCall.STARKNET_GET_STORAGE_AT, storage)


async def rpc_starknet_getTransactionByBlockIdAndIndex(
    url: str,
    index: int,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[Transaction]:
    client = FullNodeClient(node_url=url)
    tx = client.get_transaction_by_block_id(
        index, block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX, tx
    )


async def rpc_starknet_getTransactionByHash(
    url: str, tx_hash: models.query.TxHash
) -> models.ResponseModelJSON[Transaction]:
    client = FullNodeClient(node_url=url)
    tx = client.get_transaction(tx_hash)

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_TRANSACTION_BY_HASH, tx
    )


async def rpc_starknet_getTransactionReceipt(
    url: str, tx_hash: models.query.TxHash
) -> models.ResponseModelJSON[TransactionReceipt]:
    client = FullNodeClient(node_url=url)
    tx_receipt = client.get_transaction_receipt(tx_hash)

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_TRANSACTION_RECEIPT, tx_receipt
    )


async def rpc_starknet_getTransactionStatus(
    url: str, tx_hash: models.query.TxHash
) -> models.ResponseModelJSON[TransactionStatusResponse]:
    client = FullNodeClient(node_url=url)
    tx_status = client.get_transaction_status(tx_hash)

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_GET_TRANSACTION_STATUS, tx_status
    )


async def rpc_starknet_specVersion(url: str) -> models.ResponseModelJSON[str]:
    client = FullNodeClient(node_url=url)
    spec_version = client.spec_version()

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_SPEC_VERSION, spec_version
    )


async def rpc_starknet_syncing(
    url: str,
) -> models.ResponseModelJSON[bool | SyncStatus]:
    client = FullNodeClient(node_url=url)
    syncing = client.get_syncing_status()

    return await json_rpc_starknet_py(RpcCall.STARKNET_SYNCING, syncing)


# =========================================================================== #
#                                  TRACE API                                  #
# =========================================================================== #


async def rpc_starknet_simulateTransactions(
    url: str,
    body: models.body.SimulateTransactions,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = None,
) -> models.ResponseModelJSON[list[SimulatedTransaction]]:
    client = FullNodeClient(node_url=url)
    simulation = client.simulate_transactions(
        typing.cast(list[AccountTransaction], body.transactions),
        body.skip_validate,
        body.skip_fee_charge,
        block_hash,
        to_block_number_or_tag(block_number, block_tag),
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_SIMULATE_TRANSACTIONS, simulation
    )


async def rpc_starknet_traceBlockTransactions(
    url: str,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[BlockTransactionTrace]]:
    client = FullNodeClient(node_url=url)
    trace_block_transactions = client.trace_block_transactions(
        block_hash, to_block_number_or_tag(block_number, block_tag)
    )

    return await json_rpc_starknet_py(
        RpcCall.STARKNET_TRACE_BLOCK_TRANSACTIONS, trace_block_transactions
    )


async def rpc_starknet_traceTransaction(
    url: str, tx_hash: models.query.TxHash
) -> models.ResponseModelJSON[Any]:
    # TODO: fix starknet-py `trace_transaction`
    return json_rpc(
        url,
        RpcCall.STARKNET_TRACE_TRANSACTION,
        {"transaction_hash": tx_hash},
    )
