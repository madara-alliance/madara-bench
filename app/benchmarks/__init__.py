"""
# Benchmarking

## Structure

Tests are benchmarked programatically, with inputs generated on-the-fly.

A test is structured as follows:

    - a method from the `rpc` module is responsible for pinging the node
    - a generator is used to generate valid inputs for the test

## Contracts

As a general rule, this is done so generators can generate up-to-date inputs
for the tests based on the latest state of the node. Nothing is stopping you
from creating a generator which always returns the same value however, so just
don't do that.

## Rationale

This structure allows for easy automation of tests and extensibility. It also
removes the hassle of having the caller provide valid rpc arguments, allowing
them to focus on the benchmark.

Lastly, assuming all generators are generating up-to-date inputs, this allows
for very future-proof tests which keep testing nodes as the chain grows.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, TypeVar

from docker.models.containers import Container as DockerContainer

from app import models, rpc, system

from . import generators


@dataclass
class BenchmarkToolsRpc:
    input_generator: Callable[
        [dict[models.NodeName, str]], generators.InputGenerator
    ]
    runner: Callable[..., Coroutine[Any, Any, Any]]


# Mapping from rpc method name to its associated runner and input generator
MAPPINGS_RPC: dict[models.RpcCallBench, BenchmarkToolsRpc] = {
    models.RpcCallBench.STARKNET_GET_BLOCK_WITH_TXS: BenchmarkToolsRpc(
        generators.gen_starknet_getBlockWithTxs,
        rpc.rpc_starknet_getBlockWithTxs,
    ),
    models.RpcCallBench.STARKNET_GET_STORAGE_AT: BenchmarkToolsRpc(
        generators.gen_starknet_getStorageAt, rpc.rpc_starknet_getStorageAt
    ),
    models.RpcCallBench.STARKNET_ESTIMATE_FEE: BenchmarkToolsRpc(
        generators.gen_starknet_estimateFee, rpc.rpc_starknet_estimateFee
    ),
    models.RpcCallBench.STARKNET_TRACE_BLOCK_TRANSACTIONS: BenchmarkToolsRpc(
        generators.gen_starknet_traceBlockTransactions,
        rpc.rpc_starknet_traceBlockTransactions,
    ),
    models.RpcCallBench.STARKNET_GET_BLOCK_WITH_RECEIPTS: BenchmarkToolsRpc(
        generators.gen_starknet_getBlockWithReceipts,
        rpc.rpc_starknet_getBlockWithReceipts,
    ),
}

SystemRunner = Callable[
    [models.NodeName, DockerContainer],
    Coroutine[Any, Any, models.ResponseModelSystem],
]

MAPPINGS_SYSTEM: dict[models.SystemMetric, SystemRunner] = {
    models.SystemMetric.CPU: system.system_cpu_normalized,
    models.SystemMetric.CPU_SYSTEM: system.system_cpu_system,
    models.SystemMetric.MEMORY: system.system_memory,
    models.SystemMetric.STORAGE: system.system_storage,
}


TO_MILLIS: float = 0.001

T = TypeVar("T")


async def with_sleep(f: Coroutine[Any, Any, T], duration: float) -> T:
    await asyncio.sleep(duration)
    return await f


async def benchmark_rpc(
    urls: dict[models.NodeName, str],
    rpc_call: models.RpcCallBench,
    samples: models.query.TestSamples,
    interval: models.query.TestInterval,
) -> models.ResponseModelBenchRpc:
    """Runs the actual rpc benchmark

    Args:
        urls: list of node urls to query
        rpc_call: rpc call to benchmark
        samples: number of test samples
        interval: wait interval between test

    Returns:
        List of benchmarking results
    """
    tool = MAPPINGS_RPC[rpc_call]

    sleep = interval * TO_MILLIS
    generator = tool.input_generator(urls)

    # python loops are slow so we use list comprehension instead
    inputs = [await anext(generator) for _ in range(samples)]

    futures_layered = [
        [
            with_sleep(tool.runner(node, url, **input), i * sleep)
            for i, input in enumerate(inputs)
        ]
        for node, url in urls.items()
    ]
    results = [await asyncio.gather(*futures) for futures in futures_layered]

    node = [resps[0].node for resps in results]
    when = [min([resp.when for resp in resps]) for resps in results]
    elapsed = [[resp.elapsed for resp in resps] for resps in results]
    elapsed_avg = [sum(all) // len(all) for all in elapsed]

    nodes = [
        models.NodeResponseBenchRpc(
            node=node,
            method=rpc_call,
            when=when,
            elapsed_avg=elapsed_avg,
        )
        for node, when, elapsed_avg in zip(node, when, elapsed_avg)
    ]

    return models.ResponseModelBenchRpc(nodes=nodes, inputs=inputs)


async def benchmark_system(
    containers: dict[models.NodeName, DockerContainer],
    metrics: models.SystemMetric,
    samples: models.query.TestSamples,
    interval: models.query.TestInterval,
) -> list[models.ResponseModelSystem]:
    f = MAPPINGS_SYSTEM[metrics]
    sleep = interval * TO_MILLIS

    futures_layered = [
        [with_sleep(f(node, container), i * sleep) for i in range(samples)]
        for node, container in containers.items()
    ]
    results = [await asyncio.gather(*futures) for futures in futures_layered]

    node = [resp[0].node for resp in results]
    when = [min([resp.when for resp in resps]) for resps in results]
    value = [[resp.value for resp in resps] for resps in results]

    if value[0][0] is int:
        value_avg = [sum(all) // len(all) for all in value]
    else:
        value_avg = [sum(all) / len(all) for all in value]

    return [
        models.ResponseModelSystem(node=node, when=when, value=value)
        for node, when, value in zip(node, when, value_avg)
    ]
