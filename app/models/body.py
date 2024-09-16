import fastapi
from starknet_py.net.client_models import Call, Hash
from starknet_py.net.models.transaction import (
    DeclareV1,
    DeclareV2,
    DeclareV3,
    DeployAccountV1,
    DeployAccountV3,
    InvokeV1,
    InvokeV3,
)

from app.models.query import BlockHash, BlockNumber

from .models import *

TxInvoke = Annotated[InvokeV1 | InvokeV3, fastapi.Body()]

TxDeclare = Annotated[DeclareV1 | DeclareV2 | DeclareV3, fastapi.Body()]

TxDeploy = Annotated[DeployAccountV1 | DeployAccountV3, fastapi.Body()]

Tx = Annotated[TxInvoke | TxDeclare | TxDeploy, fastapi.Body()]


Call = Annotated[Call, fastapi.Body(include_in_schema=False)]


class _BodyEstimateMessageFee(pydantic.BaseModel):
    from_address: Annotated[
        FieldHex,
        pydantic.Field(
            title="Ethereum address",
            description="The address of the L1 contract sending the message",
        ),
    ]
    to_address: Annotated[
        Hash,
        pydantic.Field(
            title="Starknet address",
            description="The target L2 address the message is sent to",
        ),
    ]
    entry_point_selector: Annotated[
        Hash,
        pydantic.Field(
            description=(
                "Entry point in the L1 contract used to send the message"
            )
        ),
    ]
    payload: Annotated[
        list[Hash],
        pydantic.Field(
            description=(
                "The message payload being sent to an address on Starknet"
            )
        ),
    ]


EstimateMessageFee = Annotated[
    _BodyEstimateMessageFee, fastapi.Body(include_in_schema=False)
]


class _BodyGetEvents(pydantic.BaseModel):
    address: Annotated[
        Hash,
        pydantic.Field(
            description="On-chain address of the contract emitting the events"
        ),
    ]
    keys: Annotated[
        list[list[Hash]],
        pydantic.Field(
            description=(
                "Value used to filter events. Each key designate the possible "
                "values to be matched for events to be returned. Empty array "
                "designates 'any' value"
            )
        ),
    ]
    from_block_number: Annotated[
        BlockNumber | None,
        pydantic.Field(description="Filter events from this block (inclusive)"),
    ] = None
    from_block_hash: Annotated[
        BlockHash | None,
        pydantic.Field(description="Filter events from this block (inclusive)"),
    ] = None
    to_block_number: Annotated[
        BlockNumber | None,
        pydantic.Field(
            description="Filter events up to this block (exclusive)"
        ),
    ] = None
    to_block_hash: Annotated[
        BlockHash | None,
        pydantic.Field(
            description="Filter events up to this block (exclusive)"
        ),
    ] = None
    continuation_token: Annotated[
        str | None,
        pydantic.Field(
            description=(
                "The token returned from the previous query. If no token is "
                "provided the first page is returned. In cases where "
                "`chunk_size` is provided, this allows to keep looking for "
                "events at the end of that chunk in the next query"
            )
        ),
    ] = None
    chunk_size: Annotated[
        int,
        pydantic.Field(ge=0, description="Maximum number of events to return"),
    ] = 1


GetEvents = Annotated[_BodyGetEvents, fastapi.Body(include_in_schema=False)]


class _BodySimulateTransactions(pydantic.BaseModel):
    transactions: Annotated[
        list[Tx],
        pydantic.Field(
            description="The transactions to simulate",
        ),
    ]
    skip_validate: Annotated[bool, pydantic.Field()] = False
    skip_fee_charge: Annotated[bool, pydantic.Field()] = False


SimulateTransactions = Annotated[
    _BodySimulateTransactions, fastapi.Body(include_in_schema=False)
]
