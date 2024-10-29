from enum import Enum
from typing import Any

import docker
import fastapi
import requests
from docker import errors as docker_errors
from starknet_py.net.client_errors import ClientError
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
    TransactionReceipt,
    TransactionStatusResponse,
)

from app import benchmarks, deps, error, logging, models, rpc, system

MADARA: str = "madara_runner"
MADARA_DB: str = "madara_runner_db"

ERROR_CODES: dict[int, dict[str, Any]] = {
    fastapi.status.HTTP_400_BAD_REQUEST: {
        "description": "Invalid block id",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_404_NOT_FOUND: {
        "description": "The node could not be found",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_406_NOT_ACCEPTABLE: {
        "description": "Method was called with an invalid transaction type",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_412_PRECONDITION_FAILED: {
        "description": "Could not generate benchmarking input",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_417_EXPECTATION_FAILED: {
        "description": "Node exists but is not running",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Failed to deserialize JSON response from node",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_424_FAILED_DEPENDENCY: {
        "description": "Node exists but did not respond",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_425_TOO_EARLY: {
        "description": (
            "Method was called on a block with an incompatible starknet "
            "version"
        ),
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "RPC call failed on the node side",
        "model": error.ErrorMessage,
    },
}


class Tags(str, Enum):
    BENCH = "bench"
    SYSTEM = "system"
    READ = "read"
    TRACE = "trace"
    DEBUG = "debug"


logger = logging.get_logger()
app = fastapi.FastAPI()


@app.exception_handler(docker_errors.NotFound)
async def excepton_handler_docker_not_found(
    request: fastapi.Request, _: docker_errors.APIError
):
    raise error.ErrorNodeNotFound(request.path_params.get("node", "all"))


@app.exception_handler(docker_errors.APIError)
async def excepton_handler_docker_api_error(
    request: fastapi.Request, _: docker_errors.APIError
):
    raise error.ErrorNodeSilent(request.path_params.get("node", "all"))


@app.exception_handler(requests.exceptions.JSONDecodeError)
async def exception_handler_requests_json_decode_error(
    request: fastapi.Request, err: requests.exceptions.JSONDecodeError
):
    api_call = (
        str(request.url).removeprefix(str(request.base_url)).partition("?")[0]
    )
    raise error.ErrorJsonDecode(request.path_params["node"], api_call, err)


@app.exception_handler(ClientError)
async def exception_handler_client_error(
    request: fastapi.Request, err: ClientError
):
    api_call = (
        str(request.url).removeprefix(str(request.base_url)).partition("?")[0]
    )
    raise error.ErrorRpcCall(
        request.path_params.get("node", "all"), models.RpcCall(api_call), err
    )


# =========================================================================== #
#                                  BENCHMARKS                                 #
# =========================================================================== #


@app.get("/bench/system/", responses={**ERROR_CODES}, tags=[Tags.BENCH])
async def benchmark_system(
    metric: models.SystemMetric,
    samples: models.query.TestSamples = 10,
    interval: models.query.TestInterval = 100,
) -> list[models.ResponseModelSystem]:
    containers = {node: system.container_get(node) for node in models.NodeName}

    return await benchmarks.benchmark_system(
        containers, metric, samples, interval
    )


@app.get(
    "/bench/rpc/",
    responses={**ERROR_CODES},
    tags=[Tags.BENCH],
)
async def benchmark_rpc(
    rpc_call: models.RpcCallBench,
    samples: models.query.TestSamples = 10,
    interval: models.query.TestInterval = 100,
    # diff: models.query.DiffEnable = False,
    # diff_source: models.query.DiffSource = models.models.NodeName.MADARA,
) -> models.ResponseModelBenchRpc:
    containers = [
        (node, system.container_get(node)) for node in models.NodeName
    ]
    urls = {
        node: rpc.rpc_url(node, container) for (node, container) in containers
    }

    return await benchmarks.benchmark_rpc(
        urls,
        rpc_call,
        samples,
        interval,
    )


# =========================================================================== #
#                                SYSTEM METRICS                               #
# =========================================================================== #


@app.get("/system/cpu/{node}", responses={**ERROR_CODES}, tags=[Tags.SYSTEM])
async def node_get_cpu(
    container: deps.Container,
    format: models.CpuResultFormat = models.CpuResultFormat.CPU,
) -> models.ResponseModelSystem[float]:
    """## Get node CPU usage.

    Return format depends on the value of `system`, but will default to a
    percent value normalized to the number of CPU cores. So, for example, 800%
    usage would represent 800% of the capabilites of a single core, and not the
    entire system.
    """

    match format:
        case models.CpuResultFormat.CPU:
            return await system.system_cpu_normalized(
                container.node, container.info
            )
        case models.CpuResultFormat.SYSTEM:
            return await system.system_cpu_system(
                container.node, container.info
            )


@app.get("/system/memory/{node}", responses={**ERROR_CODES}, tags=[Tags.SYSTEM])
async def node_get_memory(
    container: deps.Container,
) -> models.ResponseModelSystem[int]:
    """## Get node memory usage.

    Fetches the amount of ram used by the node. Result will be in _bytes_.
    """

    return await system.system_memory(container.node, container.info)


@app.get(
    "/system/storage/{node}", responses={**ERROR_CODES}, tags=[Tags.SYSTEM]
)
async def node_get_storage(
    container: deps.Container,
) -> models.ResponseModelSystem[int]:
    """## Returns node storage usage

    Fetches the amount of space the node database is currently taking up. This
    is currently set up to be the size of `/data` where the node db should be
    set up. Result will be in _bytes_.
    """

    return await system.system_storage(container.node, container.info)


# =========================================================================== #
#                                   READ API                                  #
# =========================================================================== #


@app.get(
    "/info/rpc/starknet_blockHashAndNumber/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_blockHashAndNumber(
    url: deps.Url,
) -> models.ResponseModelJSON[BlockHashAndNumber]:
    return await rpc.rpc_starknet_blockHashAndNumber(url.node, url.info)


@app.get(
    "/info/rpc/starknet_blockNumber/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_blockNumber(
    url: deps.Url,
) -> models.ResponseModelJSON[int]:
    return await rpc.rpc_starknet_blockNumber(url.node, url.info)


@app.post(
    "/info/rpc/starknet_call/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_call(
    url: deps.Url,
    call: models.body.Call,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[int]]:
    return await rpc.rpc_starknet_call(
        url.node,
        url.info,
        call,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_chainId/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_chainId(
    url: deps.Url,
) -> models.ResponseModelJSON[str]:
    return await rpc.rpc_starknet_chainId(url.node, url.info)


@app.post(
    "/info/rpc/starknet_estimateFee/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_estimateFee(
    url: deps.Url,
    body: models.body.TxIn | list[models.body.TxIn],
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[EstimatedFee | list[EstimatedFee]]:
    return await rpc.rpc_starknet_estimateFee(
        url.node,
        url.info,
        body,
        block_hash,
        block_number,
        block_tag,
    )


@app.post(
    "/info/rpc/starknet_estimateMessageFee/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_estimateMessageFee(
    url: deps.Url,
    body: models.body.EstimateMessageFee,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[EstimatedFee]:
    return await rpc.rpc_starknet_estimateMessageFee(
        url.node,
        url.info,
        body,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockTransactionCount/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getBlockTransactionCount(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    return await rpc.rpc_starknet_getBlockTransactionCount(
        url.node, url.info, block_hash, block_number, block_tag
    )


@app.get(
    "/info/rpc/starknet_getBlockWithReceipts/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getBlockWithReceipts(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[
    PendingStarknetBlockWithReceipts | StarknetBlockWithReceipts
]:
    return await rpc.rpc_starknet_getBlockWithReceipts(
        url.node,
        url.info,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockWithTxHashes/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getBlockWithTxHashes(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[
    PendingStarknetBlockWithTxHashes | StarknetBlockWithTxHashes
]:
    return await rpc.rpc_starknet_getBlockWithTxHashes(
        url.node,
        url.info,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockWithTxs/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getBlockWithTxs(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[PendingStarknetBlock | StarknetBlock]:
    return await rpc.rpc_starknet_getBlockWithTxs(
        url.node,
        url.info,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getClass/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getClass(
    url: deps.Url,
    class_hash: models.query.ClassHash,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[SierraContractClass | DeprecatedContractClass]:
    return await rpc.rpc_starknet_getClass(
        url.node,
        url.info,
        class_hash,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getClassAt/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getClassAt(
    url: deps.Url,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[SierraContractClass | DeprecatedContractClass]:
    return await rpc.rpc_starknet_getClassAt(
        url.node,
        url.info,
        contract_address,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getClassHashAt/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getClassHashAt(
    url: deps.Url,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    return await rpc.rpc_starknet_getClassHashAt(
        url.node,
        url.info,
        contract_address,
        block_hash,
        block_number,
        block_tag,
    )


@app.post(
    "/info/rpc/starknet_getEvents/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getEvents(
    url: deps.Url,
    body: models.body.GetEvents,
) -> models.ResponseModelJSON[EventsChunk]:
    return await rpc.rpc_starknet_getEvents(url.node, url.info, body)


@app.get(
    "/info/rpc/starknet_getNonce/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getNonce(
    url: deps.Url,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    return await rpc.rpc_starknet_getNonce(
        url.node,
        url.info,
        contract_address,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getStateUpdate/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getStateUpdate(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[PendingBlockStateUpdate | BlockStateUpdate]:
    return await rpc.rpc_starknet_getStateUpdate(
        url.node,
        url.info,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getStorageAt/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getStorageAt(
    url: deps.Url,
    contract_address: models.query.ContractAddress,
    contract_key: models.query.ContractKey,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    return await rpc.rpc_starknet_getStorageAt(
        url.node,
        url.info,
        contract_address,
        contract_key,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getTransactionByBlockIdAndIndex/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionByBlockIdAndIndex(
    url: deps.Url,
    index: models.query.TxIndex,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[models.body.TxOut]:
    return await rpc.rpc_starknet_getTransactionByBlockIdAndIndex(
        url.node,
        url.info,
        index,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getTransactionByHash/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionByHash(
    url: deps.Url,
    transaction_hash: models.query.TxHash,
) -> models.ResponseModelJSON[models.body.TxOut]:
    return await rpc.rpc_starknet_getTransactionByHash(
        url.node, url.info, transaction_hash
    )


@app.get(
    "/info/rpc/starknet_getTransactionReceipt/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionReceipt(
    url: deps.Url,
    tx_hash: models.query.TxHash,
) -> models.ResponseModelJSON[TransactionReceipt]:
    return await rpc.rpc_starknet_getTransactionReceipt(
        url.node, url.info, tx_hash
    )


@app.get(
    "/info/rpc/starknet_getTransactionStatus/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionStatus(
    url: deps.Url,
    transaction_hash: models.query.TxHash,
) -> models.ResponseModelJSON[TransactionStatusResponse]:
    return await rpc.rpc_starknet_getTransactionStatus(
        url.node, url.info, transaction_hash
    )


@app.get(
    "/info/rpc/starknet_specVersion/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_specVersion(
    url: deps.Url,
) -> models.ResponseModelJSON[str]:
    return await rpc.rpc_starknet_specVersion(url.node, url.info)


@app.get(
    "/info/rpc/starknet_syncing/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_syncing(
    url: deps.Url,
) -> models.ResponseModelJSON[bool | SyncStatus]:
    return await rpc.rpc_starknet_syncing(url.node, url.info)


# =========================================================================== #
#                                  TRACE API                                  #
# =========================================================================== #


@app.post(
    "/info/rpc/starknet_simulateTransactions/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.TRACE],
)
async def starknet_simulateTransactions(
    url: deps.Url,
    body: models.body.SimulateTransactions,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[SimulatedTransaction]]:
    return await rpc.rpc_starknet_simulateTransactions(
        url.node, url.info, body, block_hash, block_number, block_tag
    )


@app.post(
    "/info/rpc/starknet_traceBlockTransactions/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.TRACE],
)
async def starknet_traceBlockTransactions(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[BlockTransactionTrace]]:
    return await rpc.rpc_starknet_traceBlockTransactions(
        url.node, url.info, block_hash, block_number, block_tag
    )


@app.post(
    "/info/rpc/starknet_traceTransaction/{node}/",
    responses={**ERROR_CODES},
    tags=[Tags.TRACE],
)
async def starknet_traceTransaction(
    url: deps.Url,
    tx_hash: models.query.TxHash,
) -> models.ResponseModelJSON[Any]:
    return await rpc.rpc_starknet_traceTransaction(url.node, url.info, tx_hash)


# =========================================================================== #
#                                    DEBUG                                    #
# =========================================================================== #


@app.get("/info/docker/running", responses={**ERROR_CODES}, tags=[Tags.DEBUG])
async def docker_get_running() -> list[str]:
    """List all running container instances"""
    client = docker.client.from_env()
    return [container.name for container in client.containers.list()]


@app.get(
    "/info/docker/ports/{node}",
    responses={**ERROR_CODES},
    tags=[Tags.DEBUG],
)
async def docker_get_ports(node: models.NodeName):
    """List all the ports exposed by a node's container"""

    container = system.container_get(node)
    return container.ports
