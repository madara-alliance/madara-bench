from enum import Enum

import sqlalchemy
import sqlmodel

from app import models


class RpcCallDB(int, Enum):
    # Read API
    STARKNET_BLOCK_HASH_AND_NUMBER = 0
    STARKNET_BLOCK_NUMBER = 1
    STARKNET_CHAIN_ID = 2
    STARKNET_ESTIMATE_FEE = 3
    STARKNET_ESTIMATE_MESSAGE_FEE = 4
    STARKNET_GET_BLOCK_TRANSACTION_COUNT = 5
    STARKNET_GET_BLOCK_WITH_RECEIPTS = 6
    STARKNET_GET_BLOCK_WITH_TX_HASHES = 7
    STARKNET_GET_BLOCK_WITH_TXS = 8
    STARKNET_GET_CLASS = 9
    STARKNET_GET_CLASS_AT = 10
    STARKNET_GET_CLASS_HASH_AT = 11
    STARKNET_GET_EVENTS = 12
    STARKNET_GET_NONCE = 13
    STARKNET_GET_STATE_UPDATE = 14
    STARKNET_GET_STORAGE_AT = 15
    STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX = 16
    STARKNET_GET_TRANSACTION_BY_HASH = 17
    STARKNET_GET_TRANSACTION_RECEIPT = 18
    STARKNET_GET_TRANSACTION_STATUS = 19
    STARKNET_SPEC_VERSION = 20
    STARKNET_SYNCING = 21

    # Trace API
    STARKNET_SIMULATE_TRANSACTIONS = 22
    STARKNET_TRACE_BLOCK_TRANSACTIONS = 23
    STARKNET_TRACE_TRANSACTION = 24

    @classmethod
    def from_model_bench(cls, model: models.models.RpcCallBench) -> "RpcCallDB":
        match model:
            case models.models.RpcCallBench.STARKNET_BLOCK_HASH_AND_NUMBER:
                return RpcCallDB.STARKNET_BLOCK_HASH_AND_NUMBER
            case models.models.RpcCallBench.STARKNET_BLOCK_NUMBER:
                return RpcCallDB.STARKNET_BLOCK_NUMBER
            case models.models.RpcCallBench.STARKNET_CHAIN_ID:
                return RpcCallDB.STARKNET_CHAIN_ID
            case models.models.RpcCallBench.STARKNET_ESTIMATE_FEE:
                return RpcCallDB.STARKNET_ESTIMATE_FEE
            case models.models.RpcCallBench.STARKNET_ESTIMATE_MESSAGE_FEE:
                return RpcCallDB.STARKNET_ESTIMATE_MESSAGE_FEE
            case models.models.RpcCallBench.STARKNET_GET_BLOCK_TRANSACTION_COUNT:
                return RpcCallDB.STARKNET_GET_BLOCK_TRANSACTION_COUNT
            case models.models.RpcCallBench.STARKNET_GET_BLOCK_WITH_RECEIPTS:
                return RpcCallDB.STARKNET_GET_BLOCK_WITH_RECEIPTS
            case models.models.RpcCallBench.STARKNET_GET_BLOCK_WITH_TX_HASHES:
                return RpcCallDB.STARKNET_GET_BLOCK_WITH_TX_HASHES
            case models.models.RpcCallBench.STARKNET_GET_BLOCK_WITH_TXS:
                return RpcCallDB.STARKNET_GET_BLOCK_WITH_TXS
            case models.models.RpcCallBench.STARKNET_GET_CLASS:
                return RpcCallDB.STARKNET_GET_CLASS
            case models.models.RpcCallBench.STARKNET_GET_CLASS_AT:
                return RpcCallDB.STARKNET_GET_CLASS_AT
            case models.models.RpcCallBench.STARKNET_GET_CLASS_HASH_AT:
                return RpcCallDB.STARKNET_GET_CLASS_HASH_AT
            case models.models.RpcCallBench.STARKNET_GET_EVENTS:
                return RpcCallDB.STARKNET_GET_EVENTS
            case models.models.RpcCallBench.STARKNET_GET_NONCE:
                return RpcCallDB.STARKNET_GET_NONCE
            case models.models.RpcCallBench.STARKNET_GET_STATE_UPDATE:
                return RpcCallDB.STARKNET_GET_STATE_UPDATE
            case models.models.RpcCallBench.STARKNET_GET_STORAGE_AT:
                return RpcCallDB.STARKNET_GET_STORAGE_AT
            case models.models.RpcCallBench.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX:
                return RpcCallDB.STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX
            case models.models.RpcCallBench.STARKNET_GET_TRANSACTION_BY_HASH:
                return RpcCallDB.STARKNET_GET_TRANSACTION_BY_HASH
            case models.models.RpcCallBench.STARKNET_GET_TRANSACTION_RECEIPT:
                return RpcCallDB.STARKNET_GET_TRANSACTION_RECEIPT
            case models.models.RpcCallBench.STARKNET_GET_TRANSACTION_STATUS:
                return RpcCallDB.STARKNET_GET_TRANSACTION_STATUS
            case models.models.RpcCallBench.STARKNET_SPEC_VERSION:
                return RpcCallDB.STARKNET_SPEC_VERSION
            case models.models.RpcCallBench.STARKNET_SYNCING:
                return RpcCallDB.STARKNET_SYNCING
            case models.models.RpcCallBench.STARKNET_SIMULATE_TRANSACTIONS:
                return RpcCallDB.STARKNET_SIMULATE_TRANSACTIONS
            case models.models.RpcCallBench.STARKNET_TRACE_BLOCK_TRANSACTIONS:
                return RpcCallDB.STARKNET_TRACE_BLOCK_TRANSACTIONS
            case models.models.RpcCallBench.STARKNET_TRACE_TRANSACTION:
                return RpcCallDB.STARKNET_TRACE_TRANSACTION


class NodeDB(int, Enum):
    MADARA = 0
    JUNO = 1
    PATHFINDER = 2

    @classmethod
    def from_model_bench(cls, model: models.models.NodeName) -> "NodeDB":
        match model:
            case models.models.NodeName.MADARA:
                return NodeDB.MADARA
            case models.models.NodeName.JUNO:
                return NodeDB.JUNO
            case models.models.NodeName.PATHFINDER:
                return NodeDB.PATHFINDER


class SystemMetricDB(int, Enum):
    CPU_SYSTEM = 0
    MEMORY = 1
    STORAGE = 2

    @classmethod
    def from_model_bench(cls, model: models.models.SystemMetric) -> "SystemMetricDB":
        match model:
            case models.models.SystemMetric.CPU_SYSTEM:
                return SystemMetricDB.CPU_SYSTEM
            case models.models.SystemMetric.MEMORY:
                return SystemMetricDB.MEMORY
            case models.models.SystemMetric.STORAGE:
                return SystemMetricDB.STORAGE


class BlockDB(sqlmodel.SQLModel, table=True):
    # columns
    id: int = sqlmodel.Field(primary_key=True)

    # relationships
    benchmarks_rpc: list["BenchmarkRpcDB"] = sqlmodel.Relationship(
        back_populates="block", passive_deletes="all"
    )
    benchmarks_sys: list["BenchmarkSystemDB"] = sqlmodel.Relationship(
        back_populates="block", passive_deletes="all"
    )

    def node_response_rpc(self, method_idx: int) -> list[models.models.NodeResponseBenchRpc]:
        return [
            models.models.NodeResponseBenchRpc(
                node=models.models.NodeName.from_scalar_idx(bench.node_idx) or "invalid",
                method=models.models.RpcCallBench.from_scalar_idx(bench.method_idx) or "invalid",
                block_number=self.id,
                elapsed_avg=bench.elapsed_avg,
                elapsed_low=bench.elapsed_low,
                elapsed_high=bench.elapsed_high,
            )
            for bench in self.benchmarks_rpc
            if bench.method_idx == method_idx
        ]

    def node_response_sys(self, metrics_idx: int) -> list[models.models.ResponseModelSystem]:
        return [
            models.models.ResponseModelSystem(
                node=models.models.NodeName.from_scalar_idx(bench.node_idx) or "invalid",
                metric=models.models.SystemMetric.from_scalar_idx(bench.metrics_idx) or "invalid",
                block_number=self.id,
                value=bench.value,
            )
            for bench in self.benchmarks_sys
            if bench.metrics_idx == metrics_idx
        ]


class BenchmarkRpcDB(sqlmodel.SQLModel, table=True):
    # columns
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    node_idx: int = sqlmodel.Field(index=True)
    method_idx: int = sqlmodel.Field(index=True)
    elapsed_avg: int = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.BigInteger))
    elapsed_low: int = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.BigInteger))
    elapsed_high: int = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.BigInteger))

    # foreign keys
    block_id: int | None = sqlmodel.Field(
        default=None, foreign_key="blockdb.id", ondelete="RESTRICT"
    )
    input_id: int | None = sqlmodel.Field(
        default=None, foreign_key="inputdb.id", ondelete="CASCADE"
    )

    # relationships
    block: BlockDB = sqlmodel.Relationship(back_populates="benchmarks_rpc", passive_deletes="all")
    input: "InputDB" = sqlmodel.Relationship(back_populates="benchmark", passive_deletes="all")


class InputDB(sqlmodel.SQLModel, table=True):
    # columns
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    input: str

    # relationships
    benchmark: BenchmarkRpcDB = sqlmodel.Relationship(back_populates="input", passive_deletes="all")


class BenchmarkSystemDB(sqlmodel.SQLModel, table=True):
    # columns
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    node_idx: int = sqlmodel.Field(index=True)
    metrics_idx: int = sqlmodel.Field(index=True)
    value: int = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.BigInteger))

    # foreign keys
    block_id: int | None = sqlmodel.Field(
        default=None, foreign_key="blockdb.id", ondelete="RESTRICT"
    )

    # relationships
    block: BlockDB = sqlmodel.Relationship(back_populates="benchmarks_sys", passive_deletes="all")
