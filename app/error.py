from enum import Enum

import fastapi
import pydantic
import requests
from docker.models.containers import Container
from starknet_py.net.client_errors import ClientError

from app import models


class StarknetVersion(str, Enum):
    V0_13_0 = "0.13.0"
    V0_13_1 = "0.13.1"
    V0_13_1_1 = "0.13.1.1"


class ErrorMessage(pydantic.BaseModel):
    detail: str


class ErrorBlockIdMissing(fastapi.HTTPException):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=(
                "invalid block id, method requires either a valid block hash, "
                "block number or block tag"
            ),
        )


class ErrorNodeNotFound(fastapi.HTTPException):
    def __init__(self, node: models.NodeName) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=(
                f"{node.capitalize()} node container not found, it might not "
                "have been started yet or have a different name"
            ),
        )


class ErrorUnsupportedDeploy(fastapi.HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_406_NOT_ACCEPTABLE,
            detail=("Deploy transactions are not supported"),
        )


class ErrorNodeNotRunning(fastapi.HTTPException):
    def __init__(self, node: models.NodeName) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_417_EXPECTATION_FAILED,
            detail=(
                f"{node.name.capitalize()} node container is no longer running",
            ),
        )


class ErrorJsonDecode(fastapi.HTTPException):
    def __init__(
        self,
        node: models.NodeName,
        api_call: str,
        json_error: requests.exceptions.JSONDecodeError,
    ) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Failed to deserialize JSON response from "
                f"{node.capitalize()} node after '{api_call}' api call"
                f"{json_error}"
            ),
        )


class ErrorNodeSilent(fastapi.HTTPException):
    def __init__(self, node: models.NodeName) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_424_FAILED_DEPENDENCY,
            detail=(
                f"Failed to query {node.name.capitalize()} node docker, "
                "something is seriously wrong"
            ),
        )


class ErrorStarknetVersion(fastapi.HTTPException):
    def __init__(
        self,
        method: models.RpcCall,
        starknet_version: str,
        starknet_version_min: StarknetVersion,
    ) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_425_TOO_EARLY,
            detail=(
                f"Failed to call {method.value}, requires a minimum block "
                f"version of {starknet_version_min.value}, got "
                f"{starknet_version}"
            ),
        )


class ErrorRpcCall(fastapi.HTTPException):
    def __init__(
        self, node: models.NodeName, method: models.RpcCall, e: ClientError
    ) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"{node.name.capitalize()} failed to call {method.value}, generated "
                f"error: {e}"
            ),
        )


class ErrorNoInputFound(fastapi.HTTPException):
    def __init__(self, method: models.RpcCallBench) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_412_PRECONDITION_FAILED,
            detail=f"Found no valid input to benchmark {method.value} with",
        )


def ensure_container_is_running(node: models.NodeName, container: Container):
    if container.status != "running":
        raise ErrorNodeNotRunning(node)


def ensure_meet_version_requirements(
    method: models.RpcCall, v: str, v_min: StarknetVersion
):
    if v < v_min:
        raise ErrorStarknetVersion(method, v, v_min)
