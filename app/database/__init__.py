import asyncio
from typing import Annotated, Any, Generator

import fastapi
import marshmallow
import sqlmodel
from docker.models.containers import Container as DockerContainer

from app import benchmarks, deps, error, logging, rpc
from app import models as models_app

from . import models


def read_secret(path: str) -> str:
    try:
        with open(path) as file:
            secret = file.read().strip()
        return secret
    except FileNotFoundError:
        raise FileNotFoundError(f"Missing: {path}")
    except PermissionError:
        raise PermissionError(f"Missing permission to read: {path}")
    except Exception as e:
        raise Exception(f"Error reading {path}: {str(e)}")


def db_url() -> str:
    secret = read_secret("./secrets/db_password.secret")
    return f"postgresql://postgres:{secret}@localhost:5432/postgres"


engine = sqlmodel.create_engine(db_url())
logger = logging.get_logger()


async def db_bench_routine():
    node_info_madara = deps.deps_container(models_app.NodeName.MADARA)
    node_info_juno = deps.deps_container(models_app.NodeName.JUNO)
    node_info_pathfinder = deps.deps_container(models_app.NodeName.PATHFINDER)

    url_madara = rpc.rpc_url(node_info_madara.node, node_info_madara.info)
    url_juno = rpc.rpc_url(node_info_juno.node, node_info_juno.info)
    url_pathfinder = rpc.rpc_url(node_info_pathfinder.node, node_info_pathfinder.info)

    methods = [
        # Read API
        (
            models_app.RpcCallBench.STARKNET_BLOCK_HASH_AND_NUMBER,
            models.RpcCallDB.STARKNET_BLOCK_HASH_AND_NUMBER,
            10,  # samples
            100,  # interval
        ),
        (
            models_app.RpcCallBench.STARKNET_BLOCK_NUMBER,
            models.RpcCallDB.STARKNET_BLOCK_NUMBER,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_CHAIN_ID,
            models.RpcCallDB.STARKNET_CHAIN_ID,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_ESTIMATE_FEE,
            models.RpcCallDB.STARKNET_ESTIMATE_FEE,
            10,
            250,
        ),
        (
            models_app.RpcCallBench.STARKNET_ESTIMATE_MESSAGE_FEE,
            models.RpcCallDB.STARKNET_ESTIMATE_MESSAGE_FEE,
            10,
            250,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_BLOCK_TRANSACTION_COUNT,
            models.RpcCallDB.STARKNET_GET_BLOCK_TRANSACTION_COUNT,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_BLOCK_WITH_RECEIPTS,
            models.RpcCallDB.STARKNET_GET_BLOCK_WITH_RECEIPTS,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_BLOCK_WITH_TX_HASHES,
            models.RpcCallDB.STARKNET_GET_BLOCK_WITH_TX_HASHES,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_BLOCK_WITH_TXS,
            models.RpcCallDB.STARKNET_GET_BLOCK_WITH_TXS,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_CLASS,
            models.RpcCallDB.STARKNET_GET_CLASS,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_CLASS_AT,
            models.RpcCallDB.STARKNET_GET_CLASS_AT,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_CLASS_HASH_AT,
            models.RpcCallDB.STARKNET_GET_CLASS_HASH_AT,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_EVENTS,
            models.RpcCallDB.STARKNET_GET_EVENTS,
            10,
            500,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_NONCE,
            models.RpcCallDB.STARKNET_GET_NONCE,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_STATE_UPDATE,
            models.RpcCallDB.STARKNET_GET_STATE_UPDATE,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_STORAGE_AT,
            models.RpcCallDB.STARKNET_GET_STORAGE_AT,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX,
            models.RpcCallDB.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_TRANSACTION_BY_HASH,
            models.RpcCallDB.STARKNET_GET_TRANSACTION_BY_HASH,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_TRANSACTION_RECEIPT,
            models.RpcCallDB.STARKNET_GET_TRANSACTION_RECEIPT,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_GET_TRANSACTION_STATUS,
            models.RpcCallDB.STARKNET_GET_TRANSACTION_STATUS,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_SPEC_VERSION,
            models.RpcCallDB.STARKNET_SPEC_VERSION,
            10,
            100,
        ),
        (
            models_app.RpcCallBench.STARKNET_SYNCING,
            models.RpcCallDB.STARKNET_SYNCING,
            10,
            100,
        ),
        # Trace API
        (
            models_app.RpcCallBench.STARKNET_SIMULATE_TRANSACTIONS,
            models.RpcCallDB.STARKNET_SIMULATE_TRANSACTIONS,
            10,
            250,
        ),
        (
            models_app.RpcCallBench.STARKNET_TRACE_BLOCK_TRANSACTIONS,
            models.RpcCallDB.STARKNET_TRACE_BLOCK_TRANSACTIONS,
            10,
            250,
        ),
        # (
        #     models_app.RpcCallBench.STARKNET_TRACE_TRANSACTION,
        #     models.RpcCallDB.STARKNET_TRACE_TRANSACTION,
        #     10,
        #     250,
        # ),
    ]

    metrics = [
        (
            models_app.models.SystemMetric.CPU_SYSTEM,
            models.SystemMetricDB.CPU_SYSTEM,
            10,  # samples
            1000,  # interval
        ),
        (
            models_app.models.SystemMetric.MEMORY,
            models.SystemMetricDB.MEMORY,
            10,
            1000,
        ),
        (
            models_app.models.SystemMetric.STORAGE,
            models.SystemMetricDB.STORAGE,
            1,
            1000,
        ),
    ]

    while True:
        logger.info(">> RPC BENCH SESSION - START")
        for method_rpc, method_db, samples, interval in methods:
            await asyncio.gather(
                db_bench_method(
                    s=next(session()),
                    node_rpc=models_app.NodeName.MADARA,
                    node_db=models.NodeDB.MADARA,
                    node_url=url_madara,
                    method_rpc=method_rpc,
                    method_db=method_db,
                    samples=samples,
                    interval=interval,
                ),
                db_bench_method(
                    s=next(session()),
                    node_rpc=models_app.NodeName.JUNO,
                    node_db=models.NodeDB.JUNO,
                    node_url=url_juno,
                    method_rpc=method_rpc,
                    method_db=method_db,
                    samples=samples,
                    interval=interval,
                ),
                db_bench_method(
                    s=next(session()),
                    node_rpc=models_app.NodeName.PATHFINDER,
                    node_db=models.NodeDB.PATHFINDER,
                    node_url=url_pathfinder,
                    method_rpc=method_rpc,
                    method_db=method_db,
                    samples=samples,
                    interval=interval,
                ),
            )

        logger.info(">> SYS BENCH SESSION - START")
        for metrics_app, metrics_db, samples, interval in metrics:
            await db_bench_system(
                next(session()),
                node_info_madara.info,
                node_info_juno.info,
                node_info_pathfinder.info,
                metrics_app,
                metrics_db,
                samples,
                interval,
            )


async def db_bench_method(
    s: sqlmodel.Session,
    node_rpc: models_app.NodeName,
    node_db: models.NodeDB,
    node_url: str,
    method_rpc: models_app.models.RpcCallBench,
    method_db: models.RpcCallDB,
    samples: int,
    interval: int,
):
    logger_common = f"Benchmarking RPC - {node_rpc.value}: {method_rpc.value}"
    logger.info(logger_common)
    try:
        bench = await benchmarks.benchmark_rpc(
            urls={node_rpc: node_url},
            rpc_call=method_rpc,
            samples=samples,
            interval=interval,
        )
    except error.ErrorNoInputFound:
        logger.info(f"{logger_common} - NO INPUT FOUND")
        return
    except error.ErrorStarknetVersion:
        logger.info(f"{logger_common} - INVALID STARKNET VERSION")
        return
    except error.ErrorRpcCall as e:
        logger.info(f"{logger_common} - RPC CALL FAILURE - {e}")
        return
    except marshmallow.ValidationError as e:
        logger.info(f"{logger_common} - VALIDATION ERROR - {e}")
        return
    except Exception as e:
        latest = s.exec(
            sqlmodel.select(models.BlockDB)
            .join(models.BenchmarkRpcDB)
            .where(models.BenchmarkRpcDB.node_idx == node_db)
            .order_by(sqlmodel.desc(models.BlockDB.id))
            .limit(1)
        ).first()

        if latest:
            latest = latest.id
        else:
            latest = 0

        logger.info(
            f"{logger_common} - UNEXPECTED ERROR: {node_rpc.value} {method_rpc.value} {latest} - {e}"
        )
        return

    # This is safe as we are only benchmarking a single node
    node_results = bench.nodes[0]
    block_db = s.get(models.BlockDB, node_results.block_number)

    if block_db:
        logger.info(f"{logger_common} - STORING - {block_db.id}")
    else:
        logger.info(f"{logger_common} - STORING - {node_results.block_number}")

    block = block_db or models.BlockDB(id=node_results.block_number)

    benchmark = models.BenchmarkRpcDB(
        node_idx=node_db,
        method_idx=method_db,
        elapsed_avg=node_results.elapsed_avg,
        elapsed_low=node_results.elapsed_low,
        elapsed_high=node_results.elapsed_high,
        block=block,
    )

    s.add(benchmark)
    s.commit()
    logger.info(f"{logger_common} - DONE - {block}")


async def db_bench_system(
    s: sqlmodel.Session,
    container_madara: DockerContainer,
    container_juno: DockerContainer,
    container_pathfinder: DockerContainer,
    metrics_app: models_app.models.SystemMetric,
    metrics_db: models.SystemMetricDB,
    samples: int,
    interval: int,
):
    logger_common = f"Benchmarking SYS - {metrics_app.value}"
    logger.info(logger_common)

    try:
        system_results = await benchmarks.benchmark_system(
            containers={
                models_app.models.NodeName.MADARA: container_madara,
                models_app.models.NodeName.JUNO: container_juno,
                models_app.models.NodeName.PATHFINDER: container_pathfinder,
            },
            metric=metrics_app,
            samples=samples,
            interval=interval,
        )
    except Exception as e:
        latest_madara = s.exec(
            sqlmodel.select(models.BlockDB)
            .join(models.BenchmarkRpcDB)
            .where(models.BenchmarkRpcDB.node_idx == models.NodeDB.MADARA)
            .order_by(sqlmodel.desc(models.BlockDB.id))
            .limit(1)
        ).first()

        if latest_madara:
            latest_madara = latest_madara.id
        else:
            latest_madara = 0

        latest_juno = s.exec(
            sqlmodel.select(models.BlockDB)
            .join(models.BenchmarkRpcDB)
            .where(models.BenchmarkRpcDB.node_idx == models.NodeDB.JUNO)
            .order_by(sqlmodel.desc(models.BlockDB.id))
            .limit(1)
        ).first()

        if latest_juno:
            latest_juno = latest_juno.id
        else:
            latest_juno = 0

        latest_pathfinder = s.exec(
            sqlmodel.select(models.BlockDB)
            .join(models.BenchmarkRpcDB)
            .where(models.BenchmarkRpcDB.node_idx == models.NodeDB.MADARA)
            .order_by(sqlmodel.desc(models.BlockDB.id))
            .limit(1)
        ).first()

        if latest_pathfinder:
            latest_pathfinder = latest_pathfinder.id
        else:
            latest_pathfinder = 0

        logger.info(
            f"{logger_common} - UNEXPECTED ERROR: {metrics_app.value} {latest_madara} {latest_juno} {latest_pathfinder} - {e}"
        )
        return

    for result in system_results:
        block_db = s.get(models.BlockDB, result.block_number)

        if block_db:
            logger.info(f"{logger_common} - {result.node} - STORING - {block_db.id}")
        else:
            logger.info(f"{logger_common} - {result.node} - STORING - {result.block_number}")

        block = block_db or models.BlockDB(id=result.block_number)

        benchmark = models.BenchmarkSystemDB(
            node_idx=models.NodeDB.from_model_bench(result.node),
            metrics_idx=metrics_db,
            value=result.value,
            block=block,
        )

        s.add(benchmark)

    s.commit()
    logger.info(f"{logger_common} - DONE")


def init_db_and_tables():
    sqlmodel.SQLModel.metadata.create_all(engine)


def session() -> Generator[sqlmodel.Session, Any, Any]:
    with sqlmodel.Session(engine) as session:
        yield session


Session = Annotated[sqlmodel.Session, fastapi.Depends(session)]
