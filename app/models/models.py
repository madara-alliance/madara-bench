from enum import Enum
from typing import Annotated, Any, Generic, TypeVar, Union

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
FieldBase64 = Annotated[str, pydantic.Field(pattern=REGEX_BASE_64, examples=["0x0"])]


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
    STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX = "starknet_getTransactionByBlockIdAndIndex"
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
    STARKNET_BLOCK_HASH_AND_NUMBER = "starknet_blockHashAndNumber"
    STARKNET_BLOCK_NUMBER = "starknet_blockNumber"
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
    STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX = "starknet_getTransactionByBlockIdAndIndex"
    STARKNET_GET_TRANSACTION_BY_HASH = "starknet_getTransactionByHash"
    STARKNET_GET_TRANSACTION_RECEIPT = "starknet_getTransactionReceipt"
    STARKNET_GET_TRANSACTION_STATUS = "starknet_getTransactionStatus"
    STARKNET_SPEC_VERSION = "starknet_specVersion"
    STARKNET_SYNCING = "starknet_syncing"

    # Trace API
    STARKNET_SIMULATE_TRANSACTIONS = "starknet_simulateTransactions"
    STARKNET_TRACE_BLOCK_TRANSACTIONS = "starknet_traceBlockTransactions"
    STARKNET_TRACE_TRANSACTION = "starknet_traceTransaction"

    @staticmethod
    def from_scalar_idx(idx: int) -> Union["RpcCallBench", None]:
        match idx:
            case 0:
                return RpcCallBench.STARKNET_BLOCK_HASH_AND_NUMBER
            case 1:
                return RpcCallBench.STARKNET_BLOCK_NUMBER
            case 2:
                return RpcCallBench.STARKNET_CHAIN_ID
            case 3:
                return RpcCallBench.STARKNET_ESTIMATE_FEE
            case 4:
                return RpcCallBench.STARKNET_ESTIMATE_MESSAGE_FEE
            case 5:
                return RpcCallBench.STARKNET_GET_BLOCK_TRANSACTION_COUNT
            case 6:
                return RpcCallBench.STARKNET_GET_BLOCK_WITH_RECEIPTS
            case 7:
                return RpcCallBench.STARKNET_GET_BLOCK_WITH_TX_HASHES
            case 8:
                return RpcCallBench.STARKNET_GET_BLOCK_WITH_TXS
            case 9:
                return RpcCallBench.STARKNET_GET_CLASS
            case 10:
                return RpcCallBench.STARKNET_GET_CLASS_AT
            case 11:
                return RpcCallBench.STARKNET_GET_CLASS_HASH_AT
            case 12:
                return RpcCallBench.STARKNET_GET_EVENTS
            case 13:
                return RpcCallBench.STARKNET_GET_NONCE
            case 14:
                return RpcCallBench.STARKNET_GET_STATE_UPDATE
            case 15:
                return RpcCallBench.STARKNET_GET_STORAGE_AT
            case 16:
                return RpcCallBench.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX
            case 17:
                return RpcCallBench.STARKNET_GET_TRANSACTION_BY_HASH
            case 18:
                return RpcCallBench.STARKNET_GET_TRANSACTION_RECEIPT
            case 19:
                return RpcCallBench.STARKNET_GET_TRANSACTION_STATUS
            case 20:
                return RpcCallBench.STARKNET_SPEC_VERSION
            case 21:
                return RpcCallBench.STARKNET_SYNCING
            case 22:
                return RpcCallBench.STARKNET_SIMULATE_TRANSACTIONS
            case 23:
                return RpcCallBench.STARKNET_TRACE_BLOCK_TRANSACTIONS
            case 24:
                return RpcCallBench.STARKNET_TRACE_TRANSACTION


class SystemMetric(str, Enum):
    CPU_SYSTEM = "cpu_system"
    MEMORY = "memory"
    STORAGE = "storage"

    @staticmethod
    def from_scalar_idx(idx: int) -> Union["SystemMetric", None]:
        match idx:
            case 0:
                return SystemMetric.CPU_SYSTEM
            case 1:
                return SystemMetric.MEMORY
            case 2:
                return SystemMetric.STORAGE


class NodeName(str, Enum):
    """The node used to run benchmarks."""

    MADARA = "madara"
    JUNO = "juno"
    PATHFINDER = "pathfinder"

    @staticmethod
    def from_scalar_idx(idx: int) -> Union["NodeName", None]:
        match idx:
            case 0:
                return NodeName.MADARA
            case 1:
                return NodeName.JUNO
            case 2:
                return NodeName.PATHFINDER


class ResponseModelSystem(pydantic.BaseModel):
    """Holds system measurement (cpu, ram, storage) identifying data. This is
    used to store data resulting from a system measurement for use in
    benchmarking.
    """

    node: Annotated[str, pydantic.Field(description="Node on which the test was run")]
    metric: Annotated[str, pydantic.Field(description="System metric being tested")]
    block_number: Annotated[
        int,
        pydantic.Field(description="Block number at the start of the tests"),
    ]
    value: Annotated[int, pydantic.Field(description="System measurement result")]


class NodeResponseBenchRpc(pydantic.BaseModel):
    """Holds benchmarking indetifying data and average response time. This is
    used to store the results of several tests, averaged over multiple samples
    """

    node: Annotated[str, pydantic.Field(description="Node on which the test was run")]
    method: Annotated[str, pydantic.Field(description="JSON RPC method being tested")]
    block_number: Annotated[
        int,
        pydantic.Field(description="Block number at the start of the tests"),
    ]
    elapsed_avg: Annotated[
        int,
        pydantic.Field(description=("Average method latency over all samples, in nanoseconds")),
    ]
    elapsed_low: Annotated[
        int,
        pydantic.Field(description=("Lowest method latency over all samples, in nanoseconds")),
    ]
    elapsed_high: Annotated[
        int,
        pydantic.Field(description=("Highest method latency over all samples, in nanoseconds")),
    ]


class ResponseModelBenchRpc(pydantic.BaseModel):
    """Holds benchmarking results and the inputs used in the benchmarks"""

    nodes: Annotated[
        list[NodeResponseBenchRpc],
        pydantic.Field(description="Benchmarking results for each node"),
    ]
    inputs: Annotated[
        list[dict[str, Any]],
        pydantic.Field(description=("Procedurally generated inputs used as part of the benchmark")),
    ]


class ResponseModelJSON(pydantic.BaseModel, Generic[T]):
    """Holds JSON RPC call identifying data and execution time. This is used to
    store data resulting from a JSON RPC call for use in benchmarking
    """

    node: NodeName
    method: Annotated[str, pydantic.Field(description="JSON RPC method being called")]
    elapsed: Annotated[int, pydantic.Field(description="Call response delay, in nanoseconds")]
    output: Annotated[T, pydantic.Field(description="JSON RPC node response")]
