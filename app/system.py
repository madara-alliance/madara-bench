import docker
from docker.models.containers import Container

from app import error, models, rpc


def container_get(
    node: models.NodeName,
) -> Container:
    client = docker.client.from_env()
    return client.containers.get(node + "_runner")


async def system_cpu_system(
    node: models.NodeName, container: Container
) -> models.ResponseModelSystem:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    stats = container.stats(stream=False)

    cpu_delta: int = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )
    system_delta: int = (
        stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
    )

    cpu_usage = (float(cpu_delta) / float(system_delta)) * 10_000 if system_delta > 0 else 0.0

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output

    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.CPU_SYSTEM,
        block_number=block_number,
        value=int(cpu_usage),
    )


async def system_memory(node: models.NodeName, container: Container) -> models.ResponseModelSystem:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    stats = container.stats(stream=False, one_shot=True)

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output

    memory_usage = stats["memory_stats"]["usage"]
    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.MEMORY,
        block_number=block_number,
        value=memory_usage,
    )


async def system_storage(node: models.NodeName, container: Container) -> models.ResponseModelSystem:
    error.ensure_container_is_running(node, container)

    url = rpc.rpc_url(node, container)

    # log files are ignored as juno seems to be doing some funky stuff there
    # which is causing `du` to crash
    result = container.exec_run(["du", "-sb", "--exclude=*.log", "/data"])

    stdin: str = result.output.decode("utf8")
    test = stdin.removesuffix("\t/data\n")
    storage_usage = int(test)

    block_number = await rpc.rpc_starknet_blockNumber(node, url)
    block_number = block_number.output

    return models.ResponseModelSystem(
        node=node,
        metric=models.models.SystemMetric.STORAGE,
        block_number=block_number,
        value=storage_usage,
    )
