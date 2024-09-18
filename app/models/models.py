import datetime
from enum import Enum
from typing import Annotated, Any, Generic, TypeVar

import pydantic

T = TypeVar("T")

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


class RpcCall(str, Enum):
    # Read API
    STARKNET_BLOCK_HASH_AND_NUMBER = "starknet_blockHashAndNumber"
    STARKNET_BLOCK_NUMBER = "starknet_blockNumber"
    STARKNET_CALL = "starknet_call"
    STARKNET_CHAIN_ID = "starknet_chainId"
    STARKNET_ESTIMATE_FEE = "starknet_estimateFee"
    STARKNET_ESTIMATE_MESSAGE_FEE = "starknet_estimateMessageFee"
    STARKNET_GET_BLOCK_TRANSACTION_COUNT = "starknet_getBlockTransactionCount"
    STARKNET_GET_BLOCK_WITH_RECEIPTS = "starknet_getBlockWithReceipts"
    STARKNET_GET_BLOCK_WITH_TX_HASHES = "starknet_getBlockWithTxHashes"
    STARKNET_GET_BLOCK_WITH_TXS = "starknet_getBlockWithTxs"
    STARKNET_GET_CLASS = "starknet_getClass"
    STARKNET_GET_CLASS_AT = "starknet_getClassAt"
    STARKNET_GET_CLASS_HASH_AT = "starknet_getClassHashAt"
    STARKNET_GET_EVENTS = "starknet_getEvents"
    STARKNET_GET_NONCE = "starknet_getNonce"
    STARKNET_GET_STATE_UPDATE = "starknet_getStateUpdate"
    STARKNET_GET_STORAGE_AT = "starknet_getStorageAt"
    STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX = (
        "starknet_getTransactionByBlockIdAndIndex"
    )
    STARKNET_GET_TRANSACTION_BY_HASH = "starknet_getTransactionByHash"
    STARKNET_GET_TRANSACTION_RECEIPT = "starknet_getTransactionReceipt"
    STARKNET_GET_TRANSACTION_STATUS = "starknet_getTransactionStatus"
    STARKNET_SPEC_VERSION = "starknet_specVersion"
    STARKNET_SYNCING = "starknet_syncing"

    # Trace API
    STARKNET_SIMULATE_TRANSACTIONS = "starknet_simulateTransactions"
    STARKNET_TRACE_BLOCK_TRANSACTIONS = "starknet_traceBlockTransactions"
    STARKNET_TRACE_TRANSACTION = "starknet_traceTransaction"


class RpcCallBench(str, Enum):
    """A lits of RPC calls that can be currently benchmarked. This list does
    not _currently_ include all RPC call but will grow as more benchmarks are
    added
    """

    # Read API
    STARKNET_ESTIMATE_FEE = "starknet_estimateFee"
    STARKNET_GET_BLOCK_WITH_RECEIPTS = "starknet_getBlockWithReceipts"
    STARKNET_GET_BLOCK_WITH_TXS = "starknet_getBlockWithTxs"
    STARKNET_GET_STORAGE_AT = "starknet_getStorageAt"

    # Trace API
    STARKNET_TRACE_BLOCK_TRANSACTIONS = "starknet_traceBlockTransactions"


class SystemMetric(str, Enum):
    CPU = "cpu"
    CPU_SYSTEM = "cpu_system"
    MEMORY = "memory"
    STORAGE = "storage"


class NodeName(str, Enum):
    """The node used to run benchmarks."""

    MADARA = "madara"
    JUNO = "juno"
    PATHFINDER = "pathfinder"


class CpuResultFormat(str, Enum):
    """
    ### CPU

    CPU usage will be returned as a percent value normalized to the number of
    CPU cores. This means 800% usage would represent 800% of the capabilities
    of a single core

    ### SYSTEM

    CPU usage will be returned as a percent value of total system
    usage as opposed to being normalized to the number of CPU cores. This means
    75% usage would represent 75% of system usage
    """

    CPU = "cpu"
    SYSTEM = "system"


class ResponseModelSystem(pydantic.BaseModel, Generic[T]):
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


class NodeResponseBenchRpc(pydantic.BaseModel):
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


class ResponseModelBenchRpc(pydantic.BaseModel):
    """Holds benchmarking results and the inputs used in the benchmarks"""

    nodes: Annotated[
        list[NodeResponseBenchRpc],
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
