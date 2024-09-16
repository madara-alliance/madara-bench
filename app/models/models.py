import datetime
from enum import Enum
from typing import Annotated, Any, Generic, TypeVar

import pydantic
from pydantic.generics import GenericModel

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


class ResponseModelStats(GenericModel, Generic[T]):
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


class ResponseModelBench(pydantic.BaseModel):
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


class ResponseModelJSON(pydantic.BaseModel):
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
    output: Annotated[Any, pydantic.Field(description="JSON RPC node response")]


class BlockTag(str, Enum):
    latest = "latest"
    pending = "pending"


class TxType(str, Enum):
    INVOKE = "INVOKE"
    DECLARE = "DECLARE"
    DEPLOY_ACCOUNT = "DEPLOY_ACCOUNT"


class TxVersion(int, Enum):
    V0 = 0
    V1 = 1
    V2 = 2
    V3 = 3


class TxInvokeV0(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to INVOKE for "
                "invoke transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.INVOKE
    max_fee: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The maximal fee that can be charged for including "
                "the transaction"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V0. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V0
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    contract_address: Annotated[
        FieldHex,
        pydantic.Field(description="The contract used to invoke the function"),
    ]
    entry_point_selector: Annotated[
        FieldHex,
        pydantic.Field(description="Entry point used to call the function"),
    ]
    calldata: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "The data expected by the account's `execute` function (in "
                "most usecases, this includes the called contract address and "
                "a function selector)"
            )
        ),
    ]

    model_config = {
        "json_schema_extra": {
            "description": (
                "describes what parts of the transaction should be executed"
            ),
            "deprecated": True,
        }
    }


class TxInvokeV1(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to INVOKE for "
                "invoke transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.INVOKE
    sender_address: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The address of the account contract sending the invoke "
                "transaction"
            )
        ),
    ]
    calldata: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "The data expected by the account's `execute` function (in "
                "most usecases, this includes the called contract address and "
                "a function selector)"
            )
        ),
    ]
    max_fee: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The maximal fee that can be charged for including "
                "the transaction"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V1. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V1
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]


class ResourceBoundsGas(pydantic.BaseModel):
    max_amount: FieldHex
    max_price_per_unit: FieldHex


class ResourceBounds(pydantic.BaseModel):
    l1_gas: ResourceBoundsGas
    l2_gas: ResourceBoundsGas


class DaMode(str, Enum):
    L1 = "L1"
    L2 = "L2"


class TxInvokeV3(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to INVOKE for "
                "invoke transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.INVOKE
    sender_address: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The address of the account contract sending the invoke "
                "transaction"
            )
        ),
    ]
    calldata: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "The data expected by the account's `execute` function (in "
                "most usecases, this includes the called contract address and "
                "a function selector)"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V3. You "
                "should not pass any other value than this."
            ),
        ),
    ] = TxVersion.V3
    signature: Annotated[
        list[FieldHex], pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]
    resource_bounds: Annotated[
        ResourceBounds,
        pydantic.Field(
            description=(
                "Resource bounds for the transaction execution, allow you to "
                "specify a max gas price for l1 and l2"
            )
        ),
    ]
    tip: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The tip for the transaction. A higher tip means your "
                "transaction should be processed faster."
            )
        ),
    ]
    paymaster_data: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "Data needed to allow the paymaster to pay for the "
                "transaction in native tokens"
            )
        ),
    ]
    acount_deployment_data: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "data needed to deploy the account contract from "
                "which this tx will be initiated"
            )
        ),
    ]
    nonce_data_availability_mode: Annotated[
        DaMode,
        pydantic.Field(
            description=(
                "The storage domain of the account's nonce (an account has a "
                "nonce per DA mode)"
            )
        ),
    ]
    fee_data_availability_mode: Annotated[
        DaMode,
        pydantic.Field(
            description=(
                "The storage domain of the account's balance from "
                "which fee will be charged"
            )
        ),
    ]


class CairoV1EntryPoint(pydantic.BaseModel):
    offset: Annotated[
        FieldHex,
        pydantic.Field(
            description="The offset of the entry point in the program",
            deprecated=True,
        ),
    ]
    selector: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "A unique identifier of the entry point (function) in "
                "the program"
            ),
            deprecated=True,
        ),
    ]


class CairoV2EntryPoint(pydantic.BaseModel):
    selector: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "A unique identifier of the entry point (function) in the "
                "program"
            )
        ),
    ]
    function_idx: Annotated[
        int,
        pydantic.Field(description="The index of the function in the program"),
    ]


class CairoV1EntryPointsByType(pydantic.BaseModel):
    CONSTRUCTOR: Annotated[
        list[CairoV1EntryPoint],
        pydantic.Field(description="Deprecated constructor", deprecated=True),
    ]
    EXTERNAL: Annotated[
        list[CairoV1EntryPoint],
        pydantic.Field(description="Deprecated external", deprecated=True),
    ]
    L1_HANDLER: Annotated[
        list[CairoV1EntryPoint],
        pydantic.Field(
            description="Deprecated Cairo entry point", deprecated=True
        ),
    ]


class CairoV1ABIFunctionType(str, Enum):
    function = "function"
    l1_handler = "l1_handler"
    constructor = "constructor"


class CairoV1TypedParameter(pydantic.BaseModel):
    name: Annotated[str, pydantic.Field(description="Parameter name")]
    type: Annotated[str, pydantic.Field(description="Parameter type")]


class CairoV1StateMutability(str, Enum):
    view = "view"


class CairoV1ABIEntryFunction(pydantic.BaseModel):
    type: Annotated[
        CairoV1ABIFunctionType, pydantic.Field(description="Function ABI type")
    ]
    name: Annotated[str, pydantic.Field(description="Function name")]
    inputs: Annotated[
        list[CairoV1TypedParameter],
        pydantic.Field(description="Function input typed parameters"),
    ]
    output: Annotated[
        list[CairoV1TypedParameter],
        pydantic.Field(description="Function output typed parameters"),
    ]
    stateMutability: Annotated[
        CairoV1StateMutability,
        pydantic.Field(
            description=(
                "Defines if a function is allowed to mutate state or "
                "if it must be pure"
            )
        ),
    ]


class CairoV1ABIEventType(str, Enum):
    event = "event"


class CairoV1ABIEntryEvent(pydantic.BaseModel):
    type: Annotated[
        CairoV1ABIEventType,
        pydantic.Field(
            description=(
                "Event ABI type. This defaults to 'event' and is only used to "
                "differentiate from the other ABI entry types"
            )
        ),
    ] = CairoV1ABIEventType.event
    name: Annotated[str, pydantic.Field(description="Event name")]
    keys: Annotated[
        list[CairoV1TypedParameter],
        pydantic.Field(description="Event keys used to query this event"),
    ]
    data: Annotated[
        list[CairoV1TypedParameter],
        pydantic.Field(description="Data held by the event as typed parameter"),
    ]


class CairoV1ABIStructType(str, Enum):
    struct = "struct"


class CairoV1StructEntryOffset(pydantic.BaseModel):
    offset: Annotated[
        int, pydantic.Field(description="Offset of a property within a struct")
    ]


class CairoV1ABIEntryStruct(pydantic.BaseModel):
    type: Annotated[
        CairoV1ABIStructType,
        pydantic.Field(
            description=(
                "Struct ABI type. This defaults to 'struct' and is only used "
                "to differentiate from the other ABI entry types"
            )
        ),
    ] = CairoV1ABIStructType.struct
    name: Annotated[str, pydantic.Field(description="Struct name")]
    size: Annotated[int, pydantic.Field(description="Struct size")]
    members: Annotated[
        list[CairoV1TypedParameter | CairoV1StructEntryOffset],
        pydantic.Field(
            description=(
                "Struct members. This includes struct properties, as typed "
                "parameters, and the offset to each of these properties."
            )
        ),
    ]


class CairoV1ContractClass(pydantic.BaseModel):
    program: Annotated[
        FieldBase64,
        pydantic.Field(
            description="A base64 representation of the compressed program code"
        ),
    ]
    entry_points_by_type: Annotated[
        CairoV1EntryPointsByType,
        pydantic.Field(
            description="Deprecated entry point by type", deprecated=True
        ),
    ]
    abit: Annotated[
        list[
            CairoV1ABIEntryFunction
            | CairoV1ABIEntryEvent
            | CairoV1ABIEntryStruct
        ],
        pydantic.Field(
            description="Intermediary program sierra representation"
        ),
    ]


class TxDeclareV1(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to DECLARE for "
                "declare transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.DECLARE
    sender_address: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The address of the account contract sending the declaration "
                "transaction"
            )
        ),
    ]
    max_fee: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The maximal fee that can be charged for including "
                "the transaction"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V1. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V1
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]
    contract_class: Annotated[
        CairoV1ContractClass,
        pydantic.Field(description="The class to be declared"),
    ]

    model_config = {"json_schema_extra": {"deprecated": True}}


class CairoV2EntryPointsByType(pydantic.BaseModel):
    CONTRUCTOR: Annotated[
        list[CairoV2EntryPoint],
        pydantic.Field(description="Contract class contructor"),
    ]
    EXTERNAL: Annotated[
        list[CairoV2EntryPoint], pydantic.Field(description="External")
    ]
    L1_HANDLER: Annotated[
        list[CairoV2EntryPoint], pydantic.Field(description="L1 Handler")
    ]


class CairoV2ContractClass(pydantic.BaseModel):
    sierra_program: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "The list of Sierra instructions of which the program "
                "consists, encoded as field elements"
            )
        ),
    ]
    contract_class_version: Annotated[
        str,
        pydantic.Field(
            description=(
                "The version of the contract class object. Currently, the "
                "Starknet OS supports version 0.1.0"
            ),
            default="0.1.0",
        ),
    ]
    entry_points_by_type: Annotated[
        CairoV2EntryPointsByType,
        pydantic.Field(
            description=(
                "Entry points by type. These are 'CONSTRUCTOR', 'EXTERNAL' "
                "and 'L1_HANDLER'"
            )
        ),
    ]
    abi: Annotated[
        str,
        pydantic.Field(
            description=(
                "The class ABI, as supplied by the user declaring the class"
            )
        ),
    ]


class TxDeclareV2(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to DECLARE for "
                "declare transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.DECLARE
    sender_address: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The address of the account contract sending the declaration "
                "transaction"
            )
        ),
    ]
    compiled_class_hash: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The hash of the Cairo assembly resulting from the Sierra"
            )
        ),
    ]
    max_hash: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The maximal fee that can be charged for including the "
                "transaction"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V2. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V2
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]
    contract_class: Annotated[
        CairoV2ContractClass,
        pydantic.Field(description="The class to be declared"),
    ]


class TxDeclareV3(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to DECLARE for "
                "declare transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.DECLARE
    sender_address: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The address of the account contract sending the declaration "
                "transaction"
            )
        ),
    ]
    compiled_class_hash: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The hash of the Cairo assembly resulting from the Sierra"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V3. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V3
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]
    contract_class: Annotated[
        CairoV2ContractClass,
        pydantic.Field(description="The class to be declared"),
    ]
    resource_bounds: Annotated[
        ResourceBounds,
        pydantic.Field(
            description=(
                "Resource bounds for the transaction execution, allow you to "
                "specify a max gas price for l1 and l2"
            )
        ),
    ]
    tip: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The tip for the transaction. A higher tip means your "
                "transaction should be processed faster."
            )
        ),
    ]
    paymaster_data: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "Data needed to allow the paymaster to pay for the "
                "transaction in native tokens"
            )
        ),
    ]
    acount_deployment_data: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "data needed to deploy the account contract from "
                "which this tx will be initiated"
            )
        ),
    ]
    nonce_data_availability_mode: Annotated[
        DaMode,
        pydantic.Field(
            description=(
                "The storage domain of the account's nonce (an account has a "
                "nonce per DA mode)"
            )
        ),
    ]
    fee_data_availability_mode: Annotated[
        DaMode,
        pydantic.Field(
            description=(
                "The storage domain of the account's balance from "
                "which fee will be charged"
            )
        ),
    ]


class TxDeployV1(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to DEPLOY_ACCOUNT for "
                "deploy transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.DEPLOY_ACCOUNT
    max_fee: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The maximal fee that can be charged for including "
                "the transaction"
            )
        ),
    ]
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V1. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V1
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]
    contract_address_salt: Annotated[
        FieldHex,
        pydantic.Field(
            description="The salt for the address of the deployed contract"
        ),
    ]
    constructor_calldata: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "The parameters passed to the constructor, represented as "
                "field elements"
            )
        ),
    ]
    class_hash: Annotated[
        FieldHex,
        pydantic.Field(
            description=("The hash of the deployed contract's class")
        ),
    ]

    model_config = {
        "json_schema_extra": {
            "description": (
                "Deploys an account contract, charges fee from the pre-funded "
                "account addresses"
            )
        }
    }


class TxDeployV3(pydantic.BaseModel):
    type: Annotated[
        TxType,
        pydantic.Field(
            description=(
                "The transaction type, will default to DEPLOY_ACCOUNT for "
                "deploy transactions. You should not pass any other value "
                "than this"
            )
        ),
    ] = TxType.DEPLOY_ACCOUNT
    version: Annotated[
        TxVersion,
        pydantic.Field(
            description=(
                "The transaction version, will default to V3. You "
                "should not pass any other value than this."
            )
        ),
    ] = TxVersion.V3
    signature: Annotated[
        FieldHex, pydantic.Field(description="A transaction signature")
    ]
    nonce: Annotated[
        FieldHex,
        pydantic.Field(description="Transaction nonce, avoids replay attacks"),
    ]
    contract_address_salt: Annotated[
        FieldHex,
        pydantic.Field(
            description="The salt for the address of the deployed contract"
        ),
    ]
    constructor_calldata: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "The parameters passed to the constructor, represented as "
                "field elements"
            )
        ),
    ]
    class_hash: Annotated[
        FieldHex,
        pydantic.Field(
            description=("The hash of the deployed contract's class")
        ),
    ]
    resource_bounds: Annotated[
        ResourceBounds,
        pydantic.Field(
            description=(
                "Resource bounds for the transaction execution, allow you to "
                "specify a max gas price for l1 and l2"
            )
        ),
    ]
    tip: Annotated[
        FieldHex,
        pydantic.Field(
            description=(
                "The tip for the transaction. A higher tip means your "
                "transaction should be processed faster."
            )
        ),
    ]
    paymaster_data: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "Data needed to allow the paymaster to pay for the "
                "transaction in native tokens"
            )
        ),
    ]
    acount_deployment_data: Annotated[
        list[FieldHex],
        pydantic.Field(
            description=(
                "data needed to deploy the account contract from "
                "which this tx will be initiated"
            )
        ),
    ]
    nonce_data_availability_mode: Annotated[
        DaMode,
        pydantic.Field(
            description=(
                "The storage domain of the account's nonce (an account has a "
                "nonce per DA mode)"
            )
        ),
    ]
    fee_data_availability_mode: Annotated[
        DaMode,
        pydantic.Field(
            description=(
                "The storage domain of the account's balance from "
                "which fee will be charged"
            )
        ),
    ]

    model_config = {
        "json_schema_extra": {
            "description": (
                "Deploys an account contract, charges fee from the pre-funded "
                "account addresses"
            )
        }
    }


class SimulationFlags(str, Enum):
    SKIP_VALIDATE = "SKIP_VALIDATE"
    SKIP_FEE_CHARGE = "SKIP_FEE_CHARGE"

    model_config = {
        "json_schema_extra": {
            "description": (
                "Flags that indicate how to simulate a given transaction. By "
                "default, the sequencer behavior is replicated locally "
                "(enough funds are expected to be in the account, and fee "
                "will be deducted from the balance before the simulation of "
                "the next transaction). To skip the fee charge, use the "
                "SKIP_FEE_CHARGE flag."
            )
        }
    }
