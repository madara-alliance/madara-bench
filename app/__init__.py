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
    Transaction,
    TransactionReceipt,
    TransactionStatusResponse,
)

from app import benchmarks, error, logging, models, rpc, stats

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
    fastapi.status.HTTP_417_EXPECTATION_FAILED: {
        "description": "Node exists but is not running",
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_418_IM_A_TEAPOT: {
        "description": (
            "Beware there be dragons, this section of the code is still under "
            "development"
        ),
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
}


TAG_READ: str = "read"
TAG_TRACE: str = "trace"
TAG_WRITE: str = "write"
TAG_BENCH: str = "bench"
TAG_DEBUG: str = "debug"

logger = logging.get_logger()
app = fastapi.FastAPI()


@app.exception_handler(docker_errors.NotFound)
async def excepton_handler_docker_not_found(
    request: fastapi.Request, _: docker_errors.APIError
):
    raise error.ErrorNodeNotFound(request.path_params["node"])


@app.exception_handler(docker_errors.APIError)
async def excepton_handler_docker_api_error(
    request: fastapi.Request, _: docker_errors.APIError
):
    raise error.ErrorNodeSilent(request.path_params["node"])


@app.exception_handler(requests.exceptions.JSONDecodeError)
async def exception_handler_requests_json_decode_error(
    request: fastapi.Request, err: requests.exceptions.JSONDecodeError
):
    api_call = (
        str(request.url).removeprefix(str(request.base_url)).partition("?")[0]
    )
    raise error.ErrorJsonDecode(request.path_params["node"], api_call, err)


@app.exception_handler(ClientError)
async def exception_handler_starknet_py_client_error(
    _: fastapi.Request, err: ClientError
):
    raise error.ErrorCodePlumbing(err)


# =========================================================================== #
#                                  BENCHMARKS                                 #
# =========================================================================== #


@app.get("/bench/cpu/{node}", responses={**ERROR_CODES}, tags=[TAG_BENCH])
async def node_get_cpu(
    node: models.NodeName,
    system: models.query.System = False,
) -> models.ResponseModelStats[float]:
    """## Get node CPU usage.

    Return format depends on the value of `system`, but will default to a
    percent value normalized to the number of CPU cores. So, for example, 800%
    usage would represent 800% of the capabilites of a single core, and not the
    entire system.
    """

    container = stats.container_get(node)
    if system:
        return stats.stats_cpu_system(node, container)
    else:
        return stats.stats_cpu_normalized(node, container)


@app.get("/bench/memory/{node}", responses={**ERROR_CODES}, tags=[TAG_BENCH])
async def node_get_memory(
    node: models.NodeName,
) -> models.ResponseModelStats[int]:
    """## Get node memory usage.

    Fetches the amount of ram used by the node. Result will be in _bytes_.
    """

    container = stats.container_get(node)
    return stats.stats_memory(node, container)


@app.get("/bench/storage/{node}", responses={**ERROR_CODES}, tags=[TAG_BENCH])
async def node_get_storage(
    node: models.NodeName,
) -> models.ResponseModelStats[int]:
    """## Returns node storage usage

    Fetches the amount of space the node database is currently taking up. This
    is currently set up to be the size of `/data` where the node db should be
    set up. Result will be in _bytes_.
    """

    container = stats.container_get(node)
    return stats.stats_storage(node, container)


@app.get("/bench/rpc/{node}", responses={**ERROR_CODES}, tags=[TAG_BENCH])
async def benchmark_rpc(
    rpc_call: rpc.RpcCall,
    samples: models.query.TestSamples = 10,
    interval: models.query.TestInterval = 100,
) -> models.ResponseModelBench:
    # containers = [(node, stats.container_get(node)) for node in models.NodeName]
    # urls = [rpc.rpc_url(node, container) for (node, container) in containers]

    containers = [
        (node, stats.container_get(node))
        for node in [models.NodeName.MADARA, models.NodeName.MADARA]
    ]
    urls = [rpc.rpc_url(node, container) for (node, container) in containers]

    return await benchmarks.benchmark(urls, rpc_call, samples, interval)


# =========================================================================== #
#                                   READ API                                  #
# =========================================================================== #


@app.get(
    "/info/rpc/starknet_blockHashAndNumber/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_blockHashAndNumber(
    node: models.NodeName,
) -> models.ResponseModelJSON[BlockHashAndNumber]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_blockHashAndNumber(url)


@app.get(
    "/info/rpc/starknet_blockNumber/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_blockNumber(
    node: models.NodeName,
) -> models.ResponseModelJSON[int]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_blockNumber(url)


@app.post(
    "/info/rpc/starknet_call/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_call(
    node: models.NodeName,
    call: models.body.Call,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[int]]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_call(
        url,
        call,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_chainId/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_chainId(
    node: models.NodeName,
) -> models.ResponseModelJSON[str]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_chainId(url)


@app.post(
    "/info/rpc/starknet_estimateFee/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_estimateFee(
    node: models.NodeName,
    body: models.body.Tx | list[models.body.Tx],
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[EstimatedFee | list[EstimatedFee]]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_estimateFee(
        url,
        body,
        block_hash,
        block_number,
        block_tag,
    )


@app.post(
    "/info/rpc/starknet_estimateMessageFee/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_estimateMessageFee(
    node: models.NodeName,
    body: models.body.EstimateMessageFee,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[EstimatedFee]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_estimateMessageFee(
        url,
        body,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockTransactionCount/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getBlockTransactionCount(
    node: models.NodeName,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getBlockTransactionCount(
        url, block_hash, block_number, block_tag
    )


@app.get(
    "/info/rpc/starknet_getBlockWithReceipts/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getBlockWithReceipts(
    node: models.NodeName,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[
    PendingStarknetBlockWithReceipts | StarknetBlockWithReceipts
]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getBlockWithReceipts(
        url,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockWithTxHashes/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getBlockWithTxHashes(
    node: models.NodeName,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[
    PendingStarknetBlockWithTxHashes | StarknetBlockWithTxHashes
]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getBlockWithTxHashes(
        url,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockWithTxs/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getBlockWithTxs(
    node: models.NodeName,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[PendingStarknetBlock | StarknetBlock]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getBlockWithTxs(
        url,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getClass/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getClass(
    node: models.NodeName,
    class_hash: models.query.ClassHash,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[SierraContractClass | DeprecatedContractClass]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starnet_getClass(
        url,
        class_hash,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getClassAt/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getClassAt(
    node: models.NodeName,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[SierraContractClass | DeprecatedContractClass]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getClassAt(
        url,
        contract_address,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getClassHashAt/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getClassHashAt(
    node: models.NodeName,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getClassHashAt(
        url,
        contract_address,
        block_hash,
        block_number,
        block_tag,
    )


@app.post(
    "/info/rpc/starknet_getEvents/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getEvents(
    node: models.NodeName,
    body: models.body.GetEvents,
) -> models.ResponseModelJSON[EventsChunk]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rcp_starknet_getEvents(url, body)


@app.get(
    "/info/rpc/starknet_getNonce/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getNonce(
    node: models.NodeName,
    contract_address: models.query.ContractAddress,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getNonce(
        url,
        contract_address,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getStateUpdate/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getStateUpdate(
    node: models.NodeName,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[PendingBlockStateUpdate | BlockStateUpdate]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getStateUpdate(
        url,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getStorageAt/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getStorageAt(
    node: models.NodeName,
    contract_address: models.query.ContractAddress,
    contract_key: models.query.ContractKey,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[int]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getStorageAt(
        url,
        contract_address,
        contract_key,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getTransactionByBlockIdAndIndex/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getTransactionByBlockIdAndIndex(
    node: models.NodeName,
    index: models.query.TxIndex,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[Transaction]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getTransactionByBlockIdAndIndex(
        url,
        index,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getTransactionByHash/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getTransactionByHash(
    node: models.NodeName,
    transaction_hash: models.query.TxHash,
) -> models.ResponseModelJSON[Transaction]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getTransactionByHash(url, transaction_hash)


@app.get(
    "/info/rpc/starknet_getTransactionReceipt/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getTransactionReceipt(
    node: models.NodeName,
    tx_hash: models.query.TxHash,
) -> models.ResponseModelJSON[TransactionReceipt]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getTransactionReceipt(url, tx_hash)


@app.get(
    "/info/rpc/starknet_getTransactionStatus/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_getTransactionStatus(
    node: models.NodeName,
    transaction_hash: models.query.TxHash,
) -> models.ResponseModelJSON[TransactionStatusResponse]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_getTransactionStatus(url, transaction_hash)


@app.get(
    "/info/rpc/starknet_specVersion/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_specVersion(
    node: models.NodeName,
) -> models.ResponseModelJSON[str]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_specVersion(url)


@app.get(
    "/info/rpc/starknet_syncing/{node}",
    responses={**ERROR_CODES},
    tags=[TAG_READ],
)
async def starknet_syncing(
    node: models.NodeName,
) -> models.ResponseModelJSON[bool | SyncStatus]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_syncing(url)


# =========================================================================== #
#                                  TRACE API                                  #
# =========================================================================== #


@app.post(
    "/info/rpc/starknet_simulateTransactions/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_TRACE],
)
async def starknet_simulateTransactions(
    node: models.NodeName,
    body: models.body.SimulateTransactions,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[SimulatedTransaction]]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_simulateTransactions(
        url, body, block_hash, block_number, block_tag
    )


@app.post(
    "/info/rpc/starknet_traceBlockTransactions/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_TRACE],
)
async def starknet_traceBlockTransactions(
    node: models.NodeName,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[list[BlockTransactionTrace]]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_traceBlockTransactions(
        url, block_hash, block_number, block_tag
    )


@app.post(
    "/info/rpc/starknet_traceTransaction/{node}/",
    responses={**ERROR_CODES},
    tags=[TAG_TRACE],
)
async def starknet_traceTransaction(
    node: models.NodeName,
    tx_hash: models.query.TxHash,
) -> models.ResponseModelJSON[Any]:
    container = stats.container_get(node)
    url = rpc.rpc_url(node, container)
    return await rpc.rpc_starknet_traceTransaction(url, tx_hash)


# =========================================================================== #
#                                    DEBUG                                    #
# =========================================================================== #


@app.get("/info/docker/running", responses={**ERROR_CODES}, tags=[TAG_DEBUG])
async def docker_get_running():
    """List all running container instances"""
    client = docker.client.from_env()
    client.containers.list()


@app.get(
    "/info/docker/ports/{node}", responses={**ERROR_CODES}, tags=[TAG_DEBUG]
)
async def docker_get_ports(node: models.NodeName):
    """List all the ports exposed by a node's container"""

    container = stats.container_get(node)
    return container.ports
