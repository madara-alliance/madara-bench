import datetime

import docker
from docker.models.containers import Container
from starknet_py.net.client_models import SyncStatus

from app import error, models, rpc


def container_get(
    node: models.NodeName,
) -> Container:
    client = docker.client.from_env()
    return client.containers.get(node + "_runner")


# As explained in https://github.com/moby/moby/issues/26711
async def system_cpu_normalized(
    node: models.NodeName, container: Container
) -> models.ResponseModelSystem[float]:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    time_start = datetime.datetime.now()
    stats = container.stats(stream=False)

    cpu_delta: int = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )
    cpu_count: int = stats["cpu_stats"]["online_cpus"]
    system_delta: int = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )

    cpu_usage = (
        (float(cpu_delta) / float(system_delta)) * float(cpu_count) * 100.0
        if system_delta > 0
        else 0.0
    )

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output
    sync_status = await rpc.rpc_starknet_syncing(node, url)
    sync_status = isinstance(sync_status.output, SyncStatus)

    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.CPU,
        when=time_start,
        block_number=block_number,
        syncing=sync_status,
        value=cpu_usage,
    )


async def system_cpu_system(
    node: models.NodeName, container: Container
) -> models.ResponseModelSystem[float]:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    time_start = datetime.datetime.now()
    stats = container.stats(stream=False)

    cpu_delta: int = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )
    system_delta: int = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )

    cpu_usage = (
        (float(cpu_delta) / float(system_delta)) * 100.0
        if system_delta > 0
        else 0.0
    )

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output
    sync_status = await rpc.rpc_starknet_syncing(node, url)
    sync_status = isinstance(sync_status.output, SyncStatus)

    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.CPU_SYSTEM,
        when=time_start,
        block_number=block_number,
        syncing=sync_status,
        value=cpu_usage,
    )


async def system_memory(
    node: models.NodeName, container: Container
) -> models.ResponseModelSystem[int]:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    time_start = datetime.datetime.now()
    stats = container.stats(stream=False)

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output
    sync_status = await rpc.rpc_starknet_syncing(node, url)
    sync_status = isinstance(sync_status.output, SyncStatus)

    memory_usage = stats["memory_stats"]["usage"]
    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.MEMORY,
        when=time_start,
        block_number=block_number,
        syncing=sync_status,
        value=memory_usage,
    )


async def system_storage(
    node: models.NodeName, container: Container
) -> models.ResponseModelSystem[int]:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    time_start = datetime.datetime.now()
    result = container.exec_run(["du", "-sb", "/data"])

    stdin: str = result.output.decode("utf8")
    test = stdin.removesuffix("\t/data\n")
    storage_usage = int(test)

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output
    sync_status = await rpc.rpc_starknet_syncing(node, url)
    sync_status = isinstance(sync_status.output, SyncStatus)

    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.STORAGE,
        when=time_start,
        block_number=block_number,
        syncing=sync_status,
        value=storage_usage,
    )
