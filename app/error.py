import fastapi
import pydantic
import requests
from docker.models.containers import Container
from starknet_py.net.client_errors import ClientError

from app import models


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


class ErrorNodeNotRunning(fastapi.HTTPException):
    def __init__(self, node: models.NodeName) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_417_EXPECTATION_FAILED,
            detail=(
                f"{node.name.capitalize()} node container is no longer running",
            ),
        )


class ErrorCodePlumbing(fastapi.HTTPException):
    def __init__(self, err: ClientError) -> None:
        super().__init__(
            status_code=fastapi.status.HTTP_418_IM_A_TEAPOT,
            detail=(
                "Sorry! This section of the code is under works, I'm aware of "
                "it and working on a fix, please contact me. "
                f"{err}"
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


def container_check_running(node: models.NodeName, container: Container):
    if container.status != "running":
        raise ErrorNodeNotRunning(node)
