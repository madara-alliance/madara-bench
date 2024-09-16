import datetime
from enum import Enum
from typing import Annotated, Any, Generic, TypeVar

import pydantic

REGEX_HEX: str = "^0x[a-fA-F0-9]+$"
REGEX_BASE_64: str = "^0x[a-zA-Z0-9]+$"

FieldHex = Annotated[
    str,
    pydantic.Field(
        pattern=REGEX_HEX,
        examples=["0x0"],
    ),
]
FieldBase64 = Annotated[
    str, pydantic.Field(pattern=REGEX_BASE_64, examples=["0x0"])
]

T = TypeVar("T")


class NodeName(str, Enum):
    """The node used to run benchmarks."""

    MADARA = "madara"


class ResponseModelStats(pydantic.BaseModel, Generic[T]):
    """Holds system measurement (cpu, ram, storage) identifying data. This is
    used to store data resulting from a system measurement for use in
    benchmarking.

    `time_start` is kept as a way to sort measurements if needed.
    """

    node: NodeName
    when: Annotated[
        datetime.datetime,
        pydantic.Field(description="Measurement issuing time"),
    ]
    value: Annotated[T, pydantic.Field(description="System measurement result")]


class NodeResponseBench(pydantic.BaseModel):
    """Holds benchmarking indetifying data and average response time. This is
    used to store the results of several tests, averaged over multiple samples

    `time_start` is kept as a way to sort measurements or discriminate test if
    the starting time between tests is too large. This could be the case in the
    event of high load
    """

    node: NodeName
    method: Annotated[
        str, pydantic.Field(description="JSON RPC method being tested")
    ]
    when: Annotated[
        datetime.datetime,
        pydantic.Field(description="Test start time"),
    ]
    elapsed_avg: Annotated[
        int,
        pydantic.Field(
            description=(
                "Average method latency over all samples, in nanoseconds"
            )
        ),
    ]


class ResponseModelBench(pydantic.BaseModel):
    """Holds benchmarking results and the inputs used in the benchmarks"""

    nodes: Annotated[
        list[NodeResponseBench],
        pydantic.Field(description="Benchmarking results for each node"),
    ]
    inputs: Annotated[
        list[dict[str, Any]],
        pydantic.Field(
            description=(
                "Procedurally generated inputs used as part of the benchmark"
            )
        ),
    ]


class ResponseModelJSON(pydantic.BaseModel, Generic[T]):
    """Holds JSON RPC call identifying data and execution time. This is used to
    store data resulting from a JSON RPC call for use in benchmarking
    """

    node: NodeName
    method: Annotated[
        str, pydantic.Field(description="JSON RPC method being called")
    ]
    when: Annotated[
        datetime.datetime,
        pydantic.Field(description="Call issuing time"),
    ]
    elapsed: Annotated[
        int, pydantic.Field(description="Call response delay, in nanoseconds")
    ]
    output: Annotated[T, pydantic.Field(description="JSON RPC node response")]
