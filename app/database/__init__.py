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


async def db_bench_routine():
    logger.info("Node info - INIT")
    node_info_madara = deps.deps_container(models_app.NodeName.MADARA)
    node_info_juno = deps.deps_container(models_app.NodeName.JUNO)
    node_info_pathfinder = deps.deps_container(models_app.NodeName.PATHFINDER)
    logger.info("Node info - DONE")

    logger.info("Node url - INIT")
    url_madara = rpc.rpc_url(node_info_madara.node, node_info_madara.info)
    url_juno = rpc.rpc_url(node_info_juno.node, node_info_juno.info)
    url_pathfinder = rpc.rpc_url(
        node_info_pathfinder.node, node_info_pathfinder.info
    )
    logger.info("Node url - DONE")

    logger.info("Session - ACQUIRING")
    s = next(session())
    logger.info("Session - DONE")

    while True:
        logger.info("Bench - START")
        bench = await benchmarks.benchmark_rpc(
            urls={models_app.NodeName.MADARA: url_madara},
            rpc_call=models_app.RpcCallBench.STARKNET_SPEC_VERSION,
            samples=10,
            interval=100,
        )
        logger.info("Bench - DONE")

        node_results = bench.nodes[0]

        logger.info("DB data - CREATING")
        block = models_db.BlockDB(
            method_idx=models_db.MethodDB.STARKNET_SPEC_VERSION
        )

        input = models_db.InputDB(input=json.dumps(bench.inputs))

        benchmark = models_db.BenchmarkDB(
            node_idx=models_db.NodeDB.MADARA,
            elapsed_avg=node_results.elapsed_avg,
            elapsed_low=node_results.elapsed_avg,
            elapsed_high=node_results.elapsed_avg,
            block=block,
            input=input,
        )
        logger.info("DB data - DONE")

        logger.info("Session - ADD")
        s.add(benchmark)
        logger.info("Session - COMMIT")
        s.commit()
        logger.info("Session - UPDATED")

        logger.info("Bench - WAIT")
        await asyncio.sleep(10)
        logger.info("Bench - NEXT")


def init_db_and_tables():
    sqlmodel.SQLModel.metadata.create_all(engine)


def session() -> Generator[sqlmodel.Session, Any, Any]:
    with sqlmodel.Session(engine) as session:
        yield session


Session = Annotated[sqlmodel.Session, fastapi.Depends(session)]
