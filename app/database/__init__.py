import asyncio
import json
from typing import Annotated, Any, Generator

import fastapi
import sqlmodel

from app import benchmarks, deps, logging, rpc
from app import models as models_app

from . import models as models_db

postgres_url = "postgresql://postgres:password@localhost:5432/postgres"
engine = sqlmodel.create_engine(postgres_url, echo=True)
logger = logging.get_logger()


async def db_bench_method(
    s: sqlmodel.Session,
    node_rpc: models_app.NodeName,
    node_db: models_db.NodeDB,
    node_url: str,
    method_rpc: models_app.models.RpcCallBench,
    method_db: models_db.RpcCallDB,
    samples: int,
    interval: int,
):
    logger.info(f"Bench - {node_rpc.value}: {method_rpc.value}")
    bench = await benchmarks.benchmark_rpc(
        urls={node_rpc: node_url},
        rpc_call=method_rpc,
        samples=samples,
        interval=interval,
    )
    logger.info("Bench - DONE")

    # This is safe as we are only benchmarking a single node
    node_results = bench.nodes[0]

    logger.info("DB data - CREATING")
    block = models_db.BlockDB(
        block_id=node_results.block_number,
        method_idx=method_db,
    )

    input = models_db.InputDB(input=json.dumps(bench.inputs))

    benchmark = models_db.BenchmarkDB(
        node_idx=node_db,
        elapsed_avg=node_results.elapsed_avg,
        elapsed_low=node_results.elapsed_low,
        elapsed_high=node_results.elapsed_high,
        block=block,
        input=input,
    )
    logger.info("DB data - DONE")

    logger.info("Session - ADD")
    s.add(benchmark)
    logger.info("Session - COMMIT")
    s.commit()
    logger.info("Session - UPDATED")


async def db_bench_routine():
    node_info_madara = deps.deps_container(models_app.NodeName.MADARA)
    node_info_juno = deps.deps_container(models_app.NodeName.JUNO)
    node_info_pathfinder = deps.deps_container(models_app.NodeName.PATHFINDER)

    url_madara = rpc.rpc_url(node_info_madara.node, node_info_madara.info)
    url_juno = rpc.rpc_url(node_info_juno.node, node_info_juno.info)
    url_pathfinder = rpc.rpc_url(
        node_info_pathfinder.node, node_info_pathfinder.info
    )

    methods = [
        (
            models_app.RpcCallBench.STARKNET_SPEC_VERSION,
            models_db.RpcCallDB.STARKNET_SPEC_VERSION,
            10,  # samples
            100,  # interval
        )
    ]

    while True:
        for method_rpc, method_db, samples, interval in methods:
            await asyncio.gather(
                db_bench_method(
                    s=next(session()),
                    node_rpc=models_app.NodeName.MADARA,
                    node_db=models_db.NodeDB.MADARA,
                    node_url=url_madara,
                    method_rpc=method_rpc,
                    method_db=method_db,
                    samples=samples,
                    interval=interval,
                ),
                db_bench_method(
                    s=next(session()),
                    node_rpc=models_app.NodeName.JUNO,
                    node_db=models_db.NodeDB.JUNO,
                    node_url=url_juno,
                    method_rpc=method_rpc,
                    method_db=method_db,
                    samples=samples,
                    interval=interval,
                ),
                db_bench_method(
                    s=next(session()),
                    node_rpc=models_app.NodeName.PATHFINDER,
                    node_db=models_db.NodeDB.PATHFINDER,
                    node_url=url_pathfinder,
                    method_rpc=method_rpc,
                    method_db=method_db,
                    samples=samples,
                    interval=interval,
                ),
            )

        logger.info("Bench - WAIT")
        await asyncio.sleep(10)
        logger.info("Bench - NEXT")


def init_db_and_tables():
    sqlmodel.SQLModel.metadata.create_all(engine)


def session() -> Generator[sqlmodel.Session, Any, Any]:
    with sqlmodel.Session(engine) as session:
        yield session


Session = Annotated[sqlmodel.Session, fastapi.Depends(session)]
