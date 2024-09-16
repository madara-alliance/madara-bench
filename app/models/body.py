from typing import Any

import fastapi

from app.models.query import BlockId

from .models import *


def ex_tx_invoke() -> dict[str, Any]:
    tx = TxInvokeV1(
        sender_address="0x0",
        calldata=["0x0"],
        max_fee="0x0",
        signature="0x0",
        nonce="0x0",
    )

    return tx.model_dump()


def ex_tx_declare() -> dict[str, Any]:
    tx = TxDeclareV2(
        sender_address="0x0",
        compiled_class_hash="0x0",
        max_hash="0x0",
        signature="0x0",
        nonce="0x0",
        contract_class=CairoV2ContractClass(
            sierra_program=["0x0"],
            contract_class_version="0.1.0",
            entry_points_by_type=CairoV2EntryPointsByType(
                CONTRUCTOR=[], EXTERNAL=[], L1_HANDLER=[]
            ),
            abi="",
        ),
    )

    return tx.model_dump()


TxInvoke = Annotated[
    TxInvokeV0 | TxInvokeV1 | TxInvokeV3,
    fastapi.Body(examples=[ex_tx_invoke()]),
]


TxDeclare = Annotated[
    TxDeclareV1 | TxDeclareV2 | TxDeclareV3,
    fastapi.Body(examples=[ex_tx_declare()]),
]

TxDeploy = TxDeployV1 | TxDeclareV3

Tx = Annotated[
    TxInvoke | TxDeclare | TxDeploy,
    fastapi.Body(examples=[ex_tx_invoke()]),
]


class _BodyCall(pydantic.BaseModel):
    contract_address: FieldHex
    entry_point_selector: FieldHex
    calldata: list[FieldHex] = []


Call = Annotated[_BodyCall, fastapi.Body(include_in_schema=False)]


class _BodyEstimateFee(pydantic.BaseModel):
    request: Annotated[
        Tx,
        fastapi.Body(
            description=(
                "a sequence of transactions to estimate, running each "
                "transaction on the state resulting from applying all the "
                "previous ones"
            ),
        ),
    ]
    simulation_flags: Annotated[
        list[SimulationFlags],
        fastapi.Body(
            description=(
                "describes what parts of the transaction should be executed"
            )
        ),
    ]


EstimateFee = Annotated[_BodyEstimateFee, fastapi.Body(include_in_schema=False)]


class _BodyEstimateMessageFee(pydantic.BaseModel):
    from_address: Annotated[
        FieldHex,
        pydantic.Field(
            title="Ethereum address",
            description="The address of the L1 contract sending the message",
        ),
    ]
    to_address: Annotated[
        FieldHex,
        pydantic.Field(
            title="Starknet address",
            description="The target L2 address the message is sent to",
        ),
    ]
    entry_point_selector: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "Entry point in the L1 contract used to send the message"
            )
        ),
    ]
    payload: Annotated[
        list[FieldHex],
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
    from_block: Annotated[
        BlockId,
        pydantic.Field(description="Filter events from this block (inclusive)"),
    ]
    to_block: Annotated[
        BlockId,
        pydantic.Field(
            description="Filter events up to this block (exclusive)"
        ),
    ]
    address: Annotated[
        FieldHex,
        pydantic.Field(
            description="On-chain address of the contract emitting the events"
        ),
    ]
    keys: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "Value used to filter events. Each key designate the possible "
                "values to be matched for events to be returned. Empty array "
                "designates 'any' value"
            )
        ),
    ]
    continuation_token: Annotated[
        str,
        pydantic.Field(
            description=(
                "The token returned from the previous query. If no token is "
                "provided the first page is returned. In cases where "
                "`chunk_size` is provided, this allows to keep looking for "
                "events at the end of that chunk in the next query"
            )
        ),
    ]
    chunk_size: Annotated[
        int,
        pydantic.Field(ge=0, description="Maximum number of events to return"),
    ]


GetEvents = Annotated[_BodyGetEvents, fastapi.Body(include_in_schema=False)]


class _BodySimulateTransactions(pydantic.BaseModel):
    transactions: Annotated[
        list[Tx],
        pydantic.Field(
            description="The transactions to simulate",
            examples=[[ex_tx_invoke(), ex_tx_invoke()]],
        ),
    ]
    simulation_flags: Annotated[
        SimulationFlags,
        pydantic.Field(
            description="Describes what parts of the transaction should be executed"
        ),
    ]


SimulateTransactions = Annotated[
    _BodySimulateTransactions, fastapi.Body(include_in_schema=False)
]
