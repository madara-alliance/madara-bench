from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

import fastapi
from docker.models.containers import Container as DockerContainer

from app import models, rpc, system

T = TypeVar("T")


@dataclass
class NodeInfo(Generic[T]):
    def __init__(self, node: models.NodeName, info: T):
        self.node = node
        self.info = info


def deps_container(node: models.NodeName) -> NodeInfo[DockerContainer]:
    return NodeInfo(node, system.container_get(node))


Container = Annotated[
    NodeInfo[DockerContainer], fastapi.Depends(deps_container)
]


def deps_url(
    container: Container,
) -> NodeInfo[str]:
    return NodeInfo(container.node, rpc.rpc_url(container.node, container.info))


Url = Annotated[NodeInfo[str], fastapi.Depends(deps_url)]
