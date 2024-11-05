import asyncio
import functools
import io
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

import docker
import fastapi
import matplotlib.pyplot
import requests
import sqlmodel
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

from app import database, deps, error, graph, models, rpc, system
from app.models.models import NodeResponseBenchRpc

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
        "description": ("Method was called on a block with an incompatible starknet " "version"),
        "model": error.ErrorMessage,
    },
    fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "RPC call failed on the node side",
        "model": error.ErrorMessage,
    },
}


class Tags(str, Enum):
    BENCH = "bench"
    READ = "read"
    TRACE = "trace"
    DEBUG = "debug"


# =========================================================================== #
#                                   LIFESPAN                                  #
# =========================================================================== #


@asynccontextmanager
async def lifespan(_: fastapi.FastAPI):
    database.init_db_and_tables()

    task = asyncio.create_task(database.db_bench_routine())

    yield

    try:
        ex = task.exception()
        if ex:
            raise ex
    except asyncio.CancelledError:
        pass
    except asyncio.InvalidStateError:
        pass

    task.cancel()


# =========================================================================== #
#                                ERROR HANDLERS                               #
# =========================================================================== #

app = fastapi.FastAPI(lifespan=lifespan)


@app.exception_handler(docker_errors.NotFound)
async def excepton_handler_docker_not_found(request: fastapi.Request, _: docker_errors.APIError):
    raise error.ErrorNodeNotFound(request.path_params.get("node", "all"))


@app.exception_handler(docker_errors.APIError)
async def excepton_handler_docker_api_error(request: fastapi.Request, _: docker_errors.APIError):
    raise error.ErrorNodeSilent(request.path_params.get("node", "all"))


@app.exception_handler(requests.exceptions.JSONDecodeError)
async def exception_handler_requests_json_decode_error(
    request: fastapi.Request, err: requests.exceptions.JSONDecodeError
):
    api_call = str(request.url).removeprefix(str(request.base_url)).partition("?")[0]
    raise error.ErrorJsonDecode(request.path_params["node"], api_call, err)


@app.exception_handler(ClientError)
async def exception_handler_client_error(request: fastapi.Request, err: ClientError):
    api_call = str(request.url).removeprefix(str(request.base_url)).partition("?")[0]
    raise error.ErrorRpcCall(request.path_params.get("node", "all"), models.RpcCall(api_call), err)


# =========================================================================== #
#                                  BENCHMARKS                                 #
# =========================================================================== #


def latest(session: sqlmodel.Session) -> int:
    latest = session.exec(
        sqlmodel.select(database.models.BlockDB)
        .order_by(sqlmodel.desc(database.models.BlockDB.id))
        .limit(1)
    ).first()

    if latest:
        return latest.id
    else:
        return 0


def or_latest(n: int | models.query.Latest, latest: int) -> int:
    if n == "latest":
        return latest
    else:
        return n


def deduplicate_merge_rpc(
    acc: list[models.models.NodeResponseBenchRpc], resp: NodeResponseBenchRpc
) -> list[models.models.NodeResponseBenchRpc]:
    if acc and acc[-1].block_number == resp.block_number:
        # This only works because benchmarks for a same method have the same sample count
        acc[-1].elapsed_avg = (acc[-1].elapsed_avg + resp.elapsed_avg) // 2
        acc[-1].elapsed_low = min(acc[-1].elapsed_low, resp.elapsed_low)
        acc[-1].elapsed_high = max(acc[-1].elapsed_high, resp.elapsed_high)
    else:
        acc.append(resp)
    return acc


def deduplicate_merge_sys(
    acc: list[models.models.ResponseModelSystem], resp: models.models.ResponseModelSystem
) -> list[models.models.ResponseModelSystem]:
    if acc and acc[-1].block_number == resp.block_number:
        # This only works because benchmarks for a same metric have the same sample count
        acc[-1].value = (acc[-1].value + resp.value) // 2
    else:
        acc.append(resp)
    return acc


apply_key = lambda x: x.block_number
apply_sort = lambda l: sorted(l, key=apply_key)
apply_merge_rpc = lambda l: functools.reduce(deduplicate_merge_rpc, l, [])
apply_merge_sys = lambda l: functools.reduce(deduplicate_merge_sys, l, [])


@app.get(
    "/bench/rpc",
    responses={**ERROR_CODES},
    tags=[Tags.BENCH],
)
async def benchmark_rpc(
    method: models.models.RpcCallBench,
    node: models.models.NodeName,
    block_start: models.query.BlockRange,
    block_end: models.query.BlockRange,
    session: database.Session,
    limit: models.query.RangeLimit = None,
) -> list[models.models.NodeResponseBenchRpc]:
    """## Retrieve node benchmark results

    Benchmarks take place in a continuous background thread and are stored in a
    local database. This endpoint allows you to query this database to retrieve
    benchmarks results from a specific node, on a specific function, in a given
    interval of blocks.

    The range of blocks is start and end inclusive. Use `latest` as placeholder
    for the highest current block number.
    """
    l = latest(session)
    block_start = or_latest(block_start, l)
    block_end = or_latest(block_end, l)

    method_idx = database.models.RpcCallDB.from_model_bench(method)
    node_idx = database.models.NodeDB.from_model_bench(node)
    blocks = session.exec(
        sqlmodel.select(database.models.BlockDB, database.models.BenchmarkRpcDB)
        .join(database.models.BenchmarkRpcDB)
        .where(database.models.BlockDB.id >= block_start)
        .where(database.models.BlockDB.id <= block_end)
        .where(database.models.BenchmarkRpcDB.node_idx == node_idx)
        .where(database.models.BenchmarkRpcDB.method_idx == method_idx)
        .limit(limit)
    ).all()

    resps = [bench.node_response(block.id) for block, bench in blocks]
    return apply_merge_rpc(apply_sort(resps))


@app.get("/bench/sys", responses={**ERROR_CODES}, tags=[Tags.BENCH])
async def benchmark_sys(
    metrics: models.SystemMetric,
    node: models.models.NodeName,
    block_start: models.query.BlockRange,
    block_end: models.query.BlockRange,
    session: database.Session,
    limit: models.query.RangeLimit = None,
) -> list[models.ResponseModelSystem]:
    l = latest(session)
    block_start = or_latest(block_start, l)
    block_end = or_latest(block_end, l)

    metrics_idx = database.models.SystemMetricDB.from_model_bench(metrics)
    node_idx = database.models.NodeDB.from_model_bench(node)
    blocks = session.exec(
        sqlmodel.select(database.models.BlockDB, database.models.BenchmarkSystemDB)
        .join(database.models.BenchmarkSystemDB)
        .where(database.models.BlockDB.id >= block_start)
        .where(database.models.BlockDB.id <= block_end)
        .where(database.models.BenchmarkSystemDB.node_idx == node_idx)
        .where(database.models.BenchmarkSystemDB.metrics_idx == metrics_idx)
        .limit(limit)
    ).all()

    return [bench.node_response(block.id) for block, bench in blocks]


@app.post(
    "/bench/graph/rpc",
    responses={**ERROR_CODES, 200: {"content": {"image/png": {}}}},
    response_class=fastapi.responses.Response,
    tags=[Tags.BENCH],
)
async def benchmark_graph_rpc(
    method: models.models.RpcCallBench,
    nodes: list[models.models.NodeName],
    block_start: models.query.BlockRange,
    block_end: models.query.BlockRange,
    session: database.Session,
    with_error: bool = False,
    threshold: models.query.Threshold = 100,
):
    l = latest(session)
    block_start = or_latest(block_start, l)
    block_end = or_latest(block_end, l)

    method_idx = database.models.RpcCallDB.from_model_bench(method)
    blocks = [
        session.exec(
            sqlmodel.select(database.models.BlockDB, database.models.BenchmarkRpcDB)
            .join(database.models.BenchmarkRpcDB)
            .where(database.models.BlockDB.id >= block_start)
            .where(database.models.BlockDB.id <= block_end)
            .where(
                database.models.BenchmarkRpcDB.node_idx
                == database.models.NodeDB.from_model_bench(node)
            )
            .where(database.models.BenchmarkRpcDB.method_idx == method_idx)
        ).all()
        for node in nodes
    ]

    data = [
        merge
        for blks in blocks
        for merge in apply_merge_rpc(apply_sort([bnch.node_response(blk.id) for blk, bnch in blks]))
    ]

    if len(data) == 0:
        raise error.ErrorNoInputFound(method.value)

    # WARNING: THERE BE DRAGONS, THE FOLLOWING CODE IS AI GENERATED 🐉

    # Generate the plot
    fig = graph.generate_line_graph_rpc(data, method.value, with_error, threshold)

    # Create a bytes buffer for the image
    buf = io.BytesIO()

    # Save the plot to the buffer in PNG format
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)

    # Close the figure to free memory
    matplotlib.pyplot.close(fig)

    # Seek to the start of the buffer
    buf.seek(0)

    # Return the image as a downloadable file
    return fastapi.responses.StreamingResponse(
        buf,
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename={method.value}_{block_start}_{block_end}.png"
        },
    )


@app.post(
    "/bench/graph/sys",
    responses={**ERROR_CODES, 200: {"content": {"image/png": {}}}},
    response_class=fastapi.responses.Response,
    tags=[Tags.BENCH],
)
async def benchmark_graph_sys(
    metrics: models.SystemMetric,
    nodes: list[models.models.NodeName],
    block_start: models.query.BlockRange,
    block_end: models.query.BlockRange,
    session: database.Session,
    threshold: models.query.Threshold = 100,
):
    l = latest(session)
    block_start = or_latest(block_start, l)
    block_end = or_latest(block_end, l)

    metrics_idx = database.models.SystemMetricDB.from_model_bench(metrics)
    blocks = [
        session.exec(
            sqlmodel.select(database.models.BlockDB, database.models.BenchmarkSystemDB)
            .join(database.models.BenchmarkSystemDB)
            .where(database.models.BlockDB.id >= block_start)
            .where(database.models.BlockDB.id <= block_end)
            .where(
                database.models.BenchmarkSystemDB.node_idx
                == database.models.NodeDB.from_model_bench(node)
            )
            .where(database.models.BenchmarkSystemDB.metrics_idx == metrics_idx)
        ).all()
        for node in nodes
    ]

    data = [
        merge
        for blks in blocks
        for merge in apply_merge_sys(apply_sort([bnch.node_response(blk.id) for blk, bnch in blks]))
    ]

    if len(data) == 0:
        raise error.ErrorNoInputFound(metrics.value)

    # WARNING: THERE BE DRAGONS, THE FOLLOWING CODE IS AI GENERATED 🐉

    # Generate the plot
    fig = graph.generate_line_graph_sys(data, metrics, metrics.value, threshold=threshold)

    # Create a bytes buffer for the image
    buf = io.BytesIO()

    # Save the plot to the buffer in PNG format
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)

    # Close the figure to free memory
    matplotlib.pyplot.close(fig)

    # Seek to the start of the buffer
    buf.seek(0)

    # Return the image as a downloadable file
    return fastapi.responses.StreamingResponse(
        buf,
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename={metrics.value}_{block_start}_{block_end}.png"
        },
    )


# =========================================================================== #
#                                   READ API                                  #
# =========================================================================== #


@app.get(
    "/info/rpc/starknet_blockHashAndNumber",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_blockHashAndNumber(
    url: deps.Url,
) -> models.ResponseModelJSON[BlockHashAndNumber]:
    return await rpc.rpc_starknet_blockHashAndNumber(url.node, url.info)


@app.get(
    "/info/rpc/starknet_blockNumber",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_blockNumber(
    url: deps.Url,
) -> models.ResponseModelJSON[int]:
    return await rpc.rpc_starknet_blockNumber(url.node, url.info)


@app.post(
    "/info/rpc/starknet_call",
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
    "/info/rpc/starknet_chainId",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_chainId(
    url: deps.Url,
) -> models.ResponseModelJSON[str]:
    return await rpc.rpc_starknet_chainId(url.node, url.info)


@app.post(
    "/info/rpc/starknet_estimateFee",
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
    "/info/rpc/starknet_estimateMessageFee",
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
    "/info/rpc/starknet_getBlockTransactionCount",
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
    "/info/rpc/starknet_getBlockWithReceipts",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getBlockWithReceipts(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[PendingStarknetBlockWithReceipts | StarknetBlockWithReceipts]:
    return await rpc.rpc_starknet_getBlockWithReceipts(
        url.node,
        url.info,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockWithTxHashes",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getBlockWithTxHashes(
    url: deps.Url,
    block_hash: models.query.BlockHash = None,
    block_number: models.query.BlockNumber = None,
    block_tag: models.query.BlockTag = "latest",
) -> models.ResponseModelJSON[PendingStarknetBlockWithTxHashes | StarknetBlockWithTxHashes]:
    return await rpc.rpc_starknet_getBlockWithTxHashes(
        url.node,
        url.info,
        block_hash,
        block_number,
        block_tag,
    )


@app.get(
    "/info/rpc/starknet_getBlockWithTxs",
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
    "/info/rpc/starknet_getClass",
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
    "/info/rpc/starknet_getClassAt",
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
    "/info/rpc/starknet_getClassHashAt",
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
    "/info/rpc/starknet_getEvents",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getEvents(
    url: deps.Url,
    body: models.body.GetEvents,
) -> models.ResponseModelJSON[EventsChunk]:
    return await rpc.rpc_starknet_getEvents(url.node, url.info, body)


@app.get(
    "/info/rpc/starknet_getNonce",
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
    "/info/rpc/starknet_getStateUpdate",
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
    "/info/rpc/starknet_getStorageAt",
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
    "/info/rpc/starknet_getTransactionByBlockIdAndIndex",
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
    "/info/rpc/starknet_getTransactionByHash",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionByHash(
    url: deps.Url,
    transaction_hash: models.query.TxHash,
) -> models.ResponseModelJSON[models.body.TxOut]:
    return await rpc.rpc_starknet_getTransactionByHash(url.node, url.info, transaction_hash)


@app.get(
    "/info/rpc/starknet_getTransactionReceipt",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionReceipt(
    url: deps.Url,
    tx_hash: models.query.TxHash,
) -> models.ResponseModelJSON[TransactionReceipt]:
    return await rpc.rpc_starknet_getTransactionReceipt(url.node, url.info, tx_hash)


@app.get(
    "/info/rpc/starknet_getTransactionStatus",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_getTransactionStatus(
    url: deps.Url,
    transaction_hash: models.query.TxHash,
) -> models.ResponseModelJSON[TransactionStatusResponse]:
    return await rpc.rpc_starknet_getTransactionStatus(url.node, url.info, transaction_hash)


@app.get(
    "/info/rpc/starknet_specVersion",
    responses={**ERROR_CODES},
    tags=[Tags.READ],
)
async def starknet_specVersion(
    url: deps.Url,
) -> models.ResponseModelJSON[str]:
    return await rpc.rpc_starknet_specVersion(url.node, url.info)


@app.get(
    "/info/rpc/starknet_syncing",
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
    "/info/rpc/starknet_simulateTransactions",
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
    "/info/rpc/starknet_traceBlockTransactions",
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
    "/info/rpc/starknet_traceTransaction",
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
    "/info/docker/ports",
    responses={**ERROR_CODES},
    tags=[Tags.DEBUG],
)
async def docker_get_ports(node: models.NodeName):
    """List all the ports exposed by a node's container"""

    container = system.container_get(node)
    return container.ports
