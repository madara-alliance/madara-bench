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
from starknet_py.net.client_models import SyncStatus

from app import models, rpc, system

from . import generators


@dataclass
class BenchmarkToolsRpc:
    input_generator: Callable[
        [dict[models.NodeName, str]], generators.InputGenerator
    ]
    runner: Callable[..., Coroutine[Any, Any, models.ResponseModelJSON]]


# Mapping from rpc method name to its associated runner and input generator
MAPPINGS_RPC: dict[models.RpcCallBench, BenchmarkToolsRpc] = {
    models.RpcCallBench.STARKNET_BLOCK_HASH_AND_NUMBER: BenchmarkToolsRpc(
        generators.gen_param_empty,
        rpc.rpc_starknet_blockHashAndNumber,
    ),
    models.RpcCallBench.STARKNET_BLOCK_NUMBER: BenchmarkToolsRpc(
        generators.gen_param_empty,
        rpc.rpc_starknet_blockNumber,
    ),
    models.RpcCallBench.STARKNET_CHAIN_ID: BenchmarkToolsRpc(
        generators.gen_param_empty,
        rpc.rpc_starknet_chainId,
    ),
    models.RpcCallBench.STARKNET_ESTIMATE_FEE: BenchmarkToolsRpc(
        generators.gen_starknet_estimateFee, rpc.rpc_starknet_estimateFee
    ),
    models.RpcCallBench.STARKNET_ESTIMATE_MESSAGE_FEE: BenchmarkToolsRpc(
        generators.gen_starknet_estimate_message_fee,
        rpc.rpc_starknet_estimateMessageFee,
    ),
    models.RpcCallBench.STARKNET_GET_BLOCK_TRANSACTION_COUNT: BenchmarkToolsRpc(
        generators.gen_param_block_number,
        rpc.rpc_starknet_getBlockTransactionCount,
    ),
    models.RpcCallBench.STARKNET_GET_BLOCK_WITH_RECEIPTS: BenchmarkToolsRpc(
        generators.gen_param_block_number,
        rpc.rpc_starknet_getBlockWithReceipts,
    ),
    models.RpcCallBench.STARKNET_GET_BLOCK_WITH_TX_HASHES: BenchmarkToolsRpc(
        generators.gen_param_block_number,
        rpc.rpc_starknet_getBlockWithTxHashes,
    ),
    models.RpcCallBench.STARKNET_GET_BLOCK_WITH_TXS: BenchmarkToolsRpc(
        generators.gen_param_block_number,
        rpc.rpc_starknet_getBlockWithTxs,
    ),
    models.RpcCallBench.STARKNET_GET_CLASS: BenchmarkToolsRpc(
        generators.gen_param_class_hash,
        rpc.rpc_starknet_getClass,
    ),
    models.RpcCallBench.STARKNET_GET_CLASS_AT: BenchmarkToolsRpc(
        generators.gen_param_class_contract_address,
        rpc.rpc_starknet_getClassAt,
    ),
    models.RpcCallBench.STARKNET_GET_CLASS_HASH_AT: BenchmarkToolsRpc(
        generators.gen_param_class_contract_address,
        rpc.rpc_starknet_getClassHashAt,
    ),
    models.RpcCallBench.STARKNET_GET_NONCE: BenchmarkToolsRpc(
        generators.gen_param_class_contract_address,
        rpc.rpc_starknet_getNonce,
    ),
    models.RpcCallBench.STARKNET_GET_STATE_UPDATE: BenchmarkToolsRpc(
        generators.gen_param_block_number,
        rpc.rpc_starknet_getStateUpdate,
    ),
    models.RpcCallBench.STARKNET_GET_STORAGE_AT: BenchmarkToolsRpc(
        generators.gen_starknet_getStorageAt, rpc.rpc_starknet_getStorageAt
    ),
    models.RpcCallBench.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX: BenchmarkToolsRpc(
        generators.gen_starknet_getTransactionByBlockIdAndIndex,
        rpc.rpc_starknet_getTransactionByBlockIdAndIndex,
    ),
    models.RpcCallBench.STARKNET_GET_TRANSACTION_BY_HASH: BenchmarkToolsRpc(
        generators.gen_param_tx_hash,
        rpc.rpc_starknet_getTransactionByHash,
    ),
    models.RpcCallBench.STARKNET_GET_TRANSACTION_RECEIPT: BenchmarkToolsRpc(
        generators.gen_param_tx_hash,
        rpc.rpc_starknet_getTransactionReceipt,
    ),
    models.RpcCallBench.STARKNET_GET_TRANSACTION_STATUS: BenchmarkToolsRpc(
        generators.gen_param_tx_hash,
        rpc.rpc_starknet_getTransactionStatus,
    ),
    models.RpcCallBench.STARKNET_SPEC_VERSION: BenchmarkToolsRpc(
        generators.gen_param_empty,
        rpc.rpc_starknet_specVersion,
    ),
    models.RpcCallBench.STARKNET_SYNCING: BenchmarkToolsRpc(
        generators.gen_param_empty, rpc.rpc_starknet_syncing
    ),
    models.RpcCallBench.STARKNET_SIMULATE_TRANSACTIONS: BenchmarkToolsRpc(
        generators.gen_starknet_simulateTransactions,
        rpc.rpc_starknet_simulateTransactions,
    ),
    models.RpcCallBench.STARKNET_TRACE_BLOCK_TRANSACTIONS: BenchmarkToolsRpc(
        generators.gen_param_block_number,
        rpc.rpc_starknet_traceBlockTransactions,
    ),
    models.RpcCallBench.STARKNET_TRACE_TRANSACTION: BenchmarkToolsRpc(
        generators.gen_param_tx_hash, rpc.rpc_starknet_traceTransaction
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
    # diff: models.query.DiffEnable,
    # diff_source: models.query.DiffSource,
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

    # Aggregates futures for them to be launched together
    futures_bench = [
        [
            with_sleep(tool.runner(node, url, **input), i * sleep)
            for i, input in enumerate(inputs)
        ]
        for node, url in urls.items()
    ]
    futures_block_no = [
        rpc.rpc_starknet_blockNumber(node, url) for node, url in urls.items()
    ]
    futures_syncing = [
        rpc.rpc_starknet_syncing(node, url) for node, url in urls.items()
    ]

    # Block number and sync status is retrieved BEFORE rpc tests results, which
    # WILL lead to imprecisions, however we deem those to be negligeable (in
    # the order of magnitude of a few blocks at most)
    block_nos = [
        resp.output for resp in await asyncio.gather(*futures_block_no)
    ]
    sync_status = [
        isinstance(resp.output, SyncStatus)
        for resp in await asyncio.gather(*futures_syncing)
    ]
    results = [await asyncio.gather(*futures) for futures in futures_bench]

    # Accumulates each future's results
    node = [resps[0].node for resps in results]
    when = [min([resp.when for resp in resps]) for resps in results]
    elapsed = [[resp.elapsed for resp in resps] for resps in results]
    elapsed_avg = [sum(all) // len(all) for all in elapsed]

    # if diff == True:
    #     source = next(
    #         [
    #             json.dumps(
    #                 vars(resp.output), sort_keys=True, indent=2, default=str
    #             ).splitlines()
    #             for resp in item
    #         ]
    #         for item in results
    #         if item[0].node == diff_source
    #     )
    #     targets = {
    #         item[0].node: [
    #             json.dumps(
    #                 vars(resp.output), sort_keys=True, indent=2, default=str
    #             ).splitlines()
    #             for resp in item
    #         ]
    #         for item in results
    #         if item[0].node != diff_source
    #     }
    #     diffs = {
    #         node: [
    #             list(
    #                 difflib.unified_diff(resp_source, resp_target, lineterm="")
    #             )
    #             for resp_source, resp_target in zip(source, target)
    #         ]
    #         for node, target in targets.items()
    #     }
    # else:
    #     diffs: dict[models.models.NodeName, list[list[str]]] = {}

    nodes = [
        models.NodeResponseBenchRpc(
            node=node,
            method=rpc_call,
            when=when,
            block_number=block_number,
            syncing=syncing,
            elapsed_avg=elapsed_avg,
        )
        for node, when, block_number, syncing, elapsed_avg in zip(
            node, when, block_nos, sync_status, elapsed_avg
        )
    ]

    return models.ResponseModelBenchRpc(nodes=nodes, inputs=inputs)


async def benchmark_system(
    containers: dict[models.NodeName, DockerContainer],
    metric: models.SystemMetric,
    samples: models.query.TestSamples,
    interval: models.query.TestInterval,
) -> list[models.ResponseModelSystem]:
    f = MAPPINGS_SYSTEM[metric]
    sleep = interval * TO_MILLIS

    urls = [
        (node, rpc.rpc_url(node, container))
        for node, container in containers.items()
    ]

    # Aggregates futures for them to be launched together
    futures_bench = [
        [with_sleep(f(node, container), i * sleep) for i in range(samples)]
        for node, container in containers.items()
    ]
    futures_block_no = [
        rpc.rpc_starknet_blockNumber(node, url) for node, url in urls
    ]
    futures_syncing = [
        rpc.rpc_starknet_syncing(node, url) for node, url in urls
    ]

    # Block number and sync status is retrieved BEFORE rpc tests results, which
    # WILL lead to imprecisions, however we deem those to be negligeable (in
    # the order of magnitude of a few blocks at most)
    block_nos = [
        resp.output for resp in await asyncio.gather(*futures_block_no)
    ]
    sync_status = [
        isinstance(resp.output, SyncStatus)
        for resp in await asyncio.gather(*futures_syncing)
    ]
    results = [await asyncio.gather(*futures) for futures in futures_bench]

    # Accumulates each future's results
    node = [resp[0].node for resp in results]
    when = [min([resp.when for resp in resps]) for resps in results]
    value = [[resp.value for resp in resps] for resps in results]

    if value[0][0] is int:
        value_avg = [sum(all) // len(all) for all in value]
    else:
        value_avg = [sum(all) / len(all) for all in value]

    return [
        models.ResponseModelSystem(
            node=node,
            metric=metric,
            when=when,
            block_number=block_number,
            syncing=syncing,
            value=value,
        )
        for node, when, block_number, syncing, value in zip(
            node, when, block_nos, sync_status, value_avg
        )
    ]
