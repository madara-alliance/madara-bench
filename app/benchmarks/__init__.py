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
don't do that. Please also note that generators are responsible for sleeping
the interval between test samples: this is to allow for the use of list
comprehension over traditional for loops. Again, you are responsible for adding
this functionality!

## Rationale

This structure allows for easy automation of tests and extensibility. It also
removes the hassle of having the caller provide valid rpc arguments, allowing
them to focus on the benchmark.

Lastly, assuming all generators are generating up-to-date inputs, this allows
for very future-proof tests which keep testing nodes as the chain grows.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from app import models, rpc

from . import generators


@dataclass
class BenchmarkTools:
    input_generator: Callable[[list[str], float], generators.InputGenerator]
    runner: Callable[..., Coroutine[Any, Any, Any]]


# Mapping from rpc method name to its associated runner and input generator
MAPPINGS: dict[rpc.RpcCall, BenchmarkTools] = {
    rpc.RpcCall.STARKNET_GET_BLOCK_WITH_TXS: BenchmarkTools(
        generators.gen_starknet_getBlockWithTxs,
        rpc.rpc_starknet_getBlockWithTxs,
    ),
    rpc.RpcCall.STARKNET_GET_STORAGE_AT: BenchmarkTools(
        generators.gen_starknet_getStorageAt, rpc.rpc_starknet_getStorageAt
    ),
    rpc.RpcCall.STARKNET_ESTIMATE_FEE: BenchmarkTools(
        generators.gen_starknet_estimateFee, rpc.rpc_starknet_estimateFee
    ),
    rpc.RpcCall.STARKNET_TRACE_BLOCK_TRANSACTIONS: BenchmarkTools(
        generators.gen_starknet_traceBlockTransactions,
        rpc.rpc_starknet_traceBlockTransactions,
    ),
    rpc.RpcCall.STARKNET_GET_BLOCK_WITH_RECEIPTS: BenchmarkTools(
        generators.gen_starknet_getBlockWithReceipts,
        rpc.rpc_starknet_getBlockWithReceipts,
    ),
}


TO_MILLIS: float = 0.001


async def benchmark(
    urls: list[str],
    rpc_call: rpc.RpcCall,
    samples: int,
    interval: int,
) -> models.ResponseModelBench:
    """Runs the actual rpc benchmark

    Args:
        urls: list of node urls to query
        rpc_call: rpc call to benchmark
        samples: number of test samples
        interval: wait interval between test

    Returns:
        List of benchmarking results
    """
    tool = MAPPINGS[rpc_call]

    sleep = interval * TO_MILLIS
    generator = tool.input_generator(urls, sleep)

    # python loops are slow so we use list comprehension instead
    inputs = [await anext(generator) for _ in range(samples)]

    futures_layered = [
        [tool.runner(url, **input) for input in inputs] for url in urls
    ]
    results = [await asyncio.gather(*futures) for futures in futures_layered]

    node = [resp[0].node for resp in results]
    when = [min([resp.when for resp in resps]) for resps in results]
    elapsed = [[resp.elapsed for resp in resps] for resps in results]
    elapsed_avg = [sum(all) // len(all) for all in elapsed]

    nodes = [
        models.NodeResponseBench(
            node=node,
            method=rpc_call,
            when=when,
            elapsed_avg=elapsed_avg,
        )
        for (node, when, elapsed_avg) in zip(node, when, elapsed_avg)
    ]

    return models.ResponseModelBench(nodes=nodes, inputs=inputs)
