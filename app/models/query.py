from typing import Annotated, Literal

import fastapi
from starknet_py.net.client_models import Hash, Tag

from .models import *

BlockHash = Annotated[
    Hash | None,
    fastapi.Query(
        pattern=REGEX_HEX,
        description="A block hash, represented as a field element",
    ),
]


BlockNumber = Annotated[
    int | None,
    fastapi.Query(ge=0, description="A block number or block tag"),
]

BlockTag = Annotated[
    Tag | None,
    fastapi.Query(
        description="A block tag, ca be either 'latest' to reference the last synchronized block, or 'pending' to reference the last unverified block to yet be added to the chain",
    ),
]

ContractAddress = Annotated[
    Hash,
    fastapi.Query(
        pattern=REGEX_HEX,
        description="Address of a contract on-chain",
    ),
]

ContractKey = Annotated[
    Hash,
    fastapi.Query(pattern=REGEX_HEX, description="Key to a storage element in a contract"),
]

TxHash = Annotated[
    Hash,
    fastapi.Query(pattern=REGEX_HEX, description="Address of a Transaction on-chain"),
]

TxIndex = Annotated[
    int,
    fastapi.Query(
        ge=0,
        description="Index of a transaction in a given block, in order of occurrence",
    ),
]

ClassHash = Annotated[
    Hash,
    fastapi.Query(pattern=REGEX_HEX, description="Address of a class on-chain"),
]

TestSamples = Annotated[
    int,
    fastapi.Query(
        ge=1,
        le=100,
        description=(
            "Number of sample to take, more samples means a higher "
            "benchmarking precision at the cost of speed"
        ),
    ),
]

TestInterval = Annotated[
    int,
    fastapi.Query(
        ge=0,
        le=1000,
        description="Interval between subsequent tests, in milliseconds",
    ),
]

Latest = Literal["latest"]

BlockRange = Annotated[
    int | Latest,
    fastapi.Query(description="Block number in a range of blocks, or 'latest'"),
]

RangeLimit = Annotated[
    int | None,
    fastapi.Query(description="Maximum number of benchmarks to return"),
]

Threshold = Annotated[
    int,
    fastapi.Query(
        ge=0,
        le=100,
        description=(
            "Take only the first percent data points by order of magnitude. "
            "Use this to filter out outliers"
        ),
    ),
]
