from typing import Annotated

import fastapi

from .models import *

System = Annotated[
    bool,
    fastapi.Query(
        description=(
            "If true, cpu usage will be returned as a percent value of total "
            "system usage as opposed to being normalized to the number of CPU"
            "cores. This means 75% usage would represent 75% of system usage."
        )
    ),
]

BlockHash = Annotated[
    str | None,
    fastapi.Query(
        pattern=REGEX_HEX,
        description="A block hash, represented as a field element",
    ),
]


BlockNumber = Annotated[
    int | None, fastapi.Query(ge=0, description="A block number")
]

QueryBlockTag = Annotated[
    BlockTag | None,
    fastapi.Query(
        description="A block tag, ca be either 'latest' to reference the last synchronized block, or 'pending' to reference the last unverified block to yet be added to the chain",
    ),
]

ContractAddress = Annotated[
    str,
    fastapi.Query(
        pattern=REGEX_HEX,
        description="Address of a contract on-chain",
    ),
]

ContractKey = Annotated[
    str,
    fastapi.Query(
        pattern=REGEX_HEX, description="Key to a storage element in a contract"
    ),
]

TxHash = Annotated[
    str,
    fastapi.Query(
        pattern=REGEX_HEX, description="Address of a Transaction on-chain"
    ),
]

TxIndex = Annotated[
    int,
    fastapi.Query(
        ge=0,
        description="Index of a transaction in a given block, in order of occurrence",
    ),
]

ClassHash = Annotated[
    str,
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
        le=100,
        description=("Interval between subsequent tests, in milliseconds"),
    ),
]


BlockId = BlockHash | BlockNumber | BlockTag
