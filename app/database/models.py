from enum import Enum

import sqlalchemy
import sqlmodel


class MethodDB(int, Enum):
    # Read API
    STARKNET_BLOCK_HASH_AND_NUMBER = 0
    STARKNET_BLOCK_NUMBER = 1
    STARKNET_CALL = 2
    STARKNET_CHAIN_ID = 3
    STARKNET_ESTIMATE_FEE = 4
    STARKNET_ESTIMATE_MESSAGE_FEE = 5
    STARKNET_GET_BLOCK_TRANSACTION_COUNT = 6
    STARKNET_GET_BLOCK_WITH_RECEIPTS = 7
    STARKNET_GET_BLOCK_WITH_TX_HASHES = 8
    STARKNET_GET_BLOCK_WITH_TXS = 9
    STARKNET_GET_CLASS = 10
    STARKNET_GET_CLASS_AT = 11
    STARKNET_GET_CLASS_HASH_AT = 12
    STARKNET_GET_EVENTS = 13
    STARKNET_GET_NONCE = 14
    STARKNET_GET_STATE_UPDATE = 15
    STARKNET_GET_STORAGE_AT = 16
    STARKNET_GET_TRANSACTION_BY_BLOCK_ID_AND_INDEX = 17
    STARKNET_GET_TRANSACTION_BY_HASH = 18
    STARKNET_GET_TRANSACTION_RECEIPT = 19
    STARKNET_GET_TRANSACTION_STATUS = 20
    STARKNET_SPEC_VERSION = 21
    STARKNET_SYNCING = 22

    # Trace API
    STARKNET_SIMULATE_TRANSACTIONS = 23
    STARKNET_TRACE_BLOCK_TRANSACTIONS = 24
    STARKNET_TRACE_TRANSACTION = 25


class NodeDB(int, Enum):
    MADARA = 0
    JUNO = 1
    PATHFINDER = 2


class BlockDB(sqlmodel.SQLModel, table=True):
    __table_args__ = (sqlalchemy.PrimaryKeyConstraint("id", "method_idx"),)

    id: int | None = sqlmodel.Field(
        default=None, primary_key=True, sa_column_kwargs={"autoincrement": True}
    )
    method_idx: int = sqlmodel.Field(primary_key=True)
    benchmark_id: int | None = sqlmodel.Field(
        default=None, foreign_key="benchmarkdb.id", ondelete="RESTRICT"
    )

    benchmarks: list["BenchmarkDB"] = sqlmodel.Relationship(
        back_populates="block", passive_deletes="all"
    )


class BenchmarkDB(sqlmodel.SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    node_idx: int = sqlmodel.Field(index=True)
    elapsed_avg: int
    elapsed_low: int
    elapsed_high: int
    input_id: int | None = sqlmodel.Field(
        default=None, foreign_key="inputdb.id", ondelete="CASCADE"
    )

    block: BlockDB = sqlmodel.Relationship(
        back_populates="benchmarks", passive_deletes="all"
    )
    input: "InputDB" = sqlmodel.Relationship(
        back_populates="benchmark", passive_deletes="all"
    )


class InputDB(sqlmodel.SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    input: str

    benchmark: BenchmarkDB = sqlmodel.Relationship(
        back_populates="input", passive_deletes="all"
    )
