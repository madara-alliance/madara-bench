import random
import typing
from typing import Any, AsyncGenerator, cast

from starknet_py.net.client_models import (
    DeclareTransactionV1,
    DeclareTransactionV2,
    DeclareTransactionV3,
    DeployAccountTransactionV1,
    DeployAccountTransactionV3,
    DeprecatedContractClass,
    InvokeTransactionV1,
    InvokeTransactionV3,
    L1HandlerTransaction,
    SierraContractClass,
    Transaction,
    TransactionExecutionStatus,
)
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.transaction import (
    DeclareV1,
    DeclareV2,
    DeclareV3,
    DeployAccountV1,
    DeployAccountV3,
    InvokeV1,
    InvokeV3,
)

from app import error, models, rpc

GENERATE_RANGE: int = 1_000


InputGenerator = AsyncGenerator[dict[str, Any], Any]


async def tx_conv(
    tx: Transaction, client: FullNodeClient
) -> (
    InvokeV1
    | InvokeV3
    | DeclareV1
    | DeclareV2
    | DeclareV3
    | DeployAccountV1
    | DeployAccountV3
):
    if isinstance(tx, InvokeTransactionV1):
        tx_conv = InvokeV1(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            max_fee=tx.max_fee,
            sender_address=tx.sender_address,
            calldata=tx.calldata,
        )
    elif isinstance(tx, InvokeTransactionV3):
        tx_conv = InvokeV3(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            resource_bounds=tx.resource_bounds,
            calldata=tx.calldata,
            sender_address=tx.sender_address,
            account_deployment_data=tx.account_deployment_data,
        )
    elif isinstance(tx, DeclareTransactionV1):
        contract_class = await client.get_class_by_hash(tx.class_hash)
        tx_conv = DeclareV1(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            max_fee=tx.max_fee,
            contract_class=cast(DeprecatedContractClass, contract_class),
            sender_address=tx.sender_address,
        )
    elif isinstance(tx, DeclareTransactionV2):
        contract_class = await client.get_class_by_hash(tx.class_hash)
        tx_conv = DeclareV2(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            max_fee=tx.max_fee,
            contract_class=cast(SierraContractClass, contract_class),
            compiled_class_hash=tx.compiled_class_hash,
            sender_address=tx.sender_address,
        )
    elif isinstance(tx, DeclareTransactionV3):
        contract_class = await client.get_class_by_hash(tx.class_hash)
        tx_conv = DeclareV3(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            resource_bounds=tx.resource_bounds,
            sender_address=tx.sender_address,
            compiled_class_hash=tx.compiled_class_hash,
            contract_class=cast(SierraContractClass, contract_class),
            account_deployment_data=tx.account_deployment_data,
        )
    elif isinstance(tx, DeployAccountTransactionV1):
        tx_conv = DeployAccountV1(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            max_fee=tx.max_fee,
            class_hash=tx.class_hash,
            contract_address_salt=tx.contract_address_salt,
            constructor_calldata=tx.constructor_calldata,
        )
    elif isinstance(tx, DeployAccountTransactionV3):
        tx_conv = DeployAccountV3(
            version=tx.version,
            signature=tx.signature,
            nonce=tx.nonce,
            resource_bounds=tx.resource_bounds,
            class_hash=tx.class_hash,
            contract_address_salt=tx.contract_address_salt,
            constructor_calldata=tx.constructor_calldata,
        )

    return tx_conv


async def latest_common_block_number(urls: dict[models.NodeName, str]) -> int:
    block_numbers: list[int] = [
        (await rpc.rpc_starknet_blockNumber(node, url)).output
        for node, url in urls.items()
    ]

    return min(block_numbers)


async def gen_param_empty(_: dict[models.NodeName, str]) -> InputGenerator:
    while True:
        yield {}


async def gen_param_block_number(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        yield {"block_number": block_number}


async def gen_param_class_hash(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    """Generates a ramdom contract storage key

    Key is taken from the state diffs over the last 1000 common blocks. It is
    possible for a key to be generated that falls before that range in some
    rare cases where the random block to have been chose had no storage diffs
    """
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        state_update = await client.get_state_update(block_number=block_number)

        while (
            len(state_update.state_diff.declared_classes) == 0
            and len(state_update.state_diff.deprecated_declared_classes) == 0
        ):
            # This is safe since block 0 has declared classes
            block_number -= 1
            state_update = await client.get_state_update(
                block_number=block_number
            )

        if len(state_update.state_diff.declared_classes) != 0:
            class_hash = state_update.state_diff.declared_classes[0].class_hash
        else:
            class_hash = state_update.state_diff.deprecated_declared_classes[0]

        yield {
            "class_hash": class_hash,
            "block_number": block_number,
        }


async def gen_param_class_contract_address(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    """Generates a ramdom contract storage key

    Key is taken from the state diffs over the last 1000 common blocks. It is
    possible for a key to be generated that falls before that range in some
    rare cases where the random block to have been chose had no storage diffs
    """
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        state_update = await client.get_state_update(block_number=block_number)

        while len(state_update.state_diff.deployed_contracts) == 0:
            # This is safe since block 0 has declared classes
            block_number -= 1
            state_update = await client.get_state_update(
                block_number=block_number
            )

        contract_address = state_update.state_diff.deployed_contracts[0].address

        yield {
            "contract_address": contract_address,
            "block_number": block_number,
        }


async def gen_param_tx_hash(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        block = await client.get_block(block_number=block_number)

        while len(block.transactions) == 0:
            # This is safe since block 0 has transactions
            block_number -= 1
            block = await client.get_block(block_number=block_number)

        yield {"tx_hash": block.transactions[0].hash}


async def gen_starknet_estimateFee(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        block = await client.get_block(block_number=block_number)
        txs = block.transactions

        if len(txs) > 0:
            tx_status = await client.get_transaction_status(
                typing.cast(int, txs[0].hash)
            )
            tx_status = tx_status.execution_status
        else:
            tx_status = TransactionExecutionStatus.SUCCEEDED

        while (
            len(txs) == 0
            or txs[0].version == 0
            or tx_status == TransactionExecutionStatus.REVERTED
        ):
            block_number -= 1

            if block_number < 0:
                raise error.ErrorNoInputFound(
                    models.RpcCallBench.STARKNET_ESTIMATE_FEE
                )

            block = await client.get_block(block_number=block_number)
            txs = block.transactions
            tx_status = await client.get_transaction_status(
                typing.cast(int, txs[0].hash)
            )
            tx_status = tx_status.execution_status

        tx = await tx_conv(txs[0], client)

        yield {"tx": tx, "block_number": block_number - 1}


async def gen_starknet_estimate_message_fee(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        block = await client.get_block(block_number=block_number)
        txs = block.transactions

        if len(txs) > 0:
            tx_status = await client.get_transaction_status(
                typing.cast(int, txs[0].hash)
            )
            tx_status = tx_status.execution_status
        else:
            tx_status = TransactionExecutionStatus.SUCCEEDED

        while (
            len(txs) == 0
            or not isinstance(txs[0], L1HandlerTransaction)
            or tx_status == TransactionExecutionStatus.REVERTED
        ):
            block_number -= 1

            if block_number < 0:
                raise error.ErrorNoInputFound(
                    models.RpcCallBench.STARKNET_ESTIMATE_FEE
                )

            block = await client.get_block(block_number=block_number)
            txs = block.transactions
            tx_status = await client.get_transaction_status(
                typing.cast(int, txs[0].hash)
            )
            tx_status = tx_status.execution_status

        tx = txs[0]

        yield {
            "body": models.body._BodyEstimateMessageFee(
                from_address="0x0",
                to_address=tx.contract_address,
                entry_point_selector=tx.entry_point_selector,
                payload=tx.calldata,
            ),
            "block_number": block_number,
        }


async def gen_starknet_getEvents(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )

        block_with_receits = await client.get_block_with_receipts(
            block_number=block_number
        )

        while (
            len(block_with_receits.transactions) == 0
            and len(block_with_receits.transactions[0].receipt.events) == 0
        ):
            block_number -= 1

            if block_number < 0:
                raise error.ErrorNoInputFound(
                    models.RpcCallBench.STARKNET_ESTIMATE_FEE
                )

            block_with_receits = await client.get_block_with_receipts(
                block_number=block_number
            )

        events = block_with_receits.transactions[0].receipt.events

        yield {
            "body": models.body._BodyGetEvents(
                address=events[0].from_address,
                keys=[events[0].keys],
                from_block_number=max(0, block_number - GENERATE_RANGE),
            )
        }


async def gen_starknet_getStorageAt(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    """Generates a ramdom contract storage key

    Key is taken from the state diffs over the last 1000 common blocks. It is
    possible for a key to be generated that falls before that range in some
    rare cases where the random block to have been chose had no storage diffs
    """
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        state_update = await client.get_state_update(block_number=block_number)

        while len(state_update.state_diff.storage_diffs) < 2:
            # This is safe since block 0 has storage diffs
            block_number -= 1
            state_update = await client.get_state_update(
                block_number=block_number
            )

        storage_diff = state_update.state_diff.storage_diffs[1]
        storage_entry = storage_diff.storage_entries[0]
        yield {
            "contract_address": storage_diff.address,
            "key": storage_entry.key,
            "block_number": block_number,
        }


async def gen_starknet_getTransactionByBlockIdAndIndex(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        block = await client.get_block(block_number=block_number)

        while len(block.transactions) == 0:
            # This is safe since block 0 has transactions
            block_number -= 1
            block = await client.get_block(block_number=block_number)

        yield {
            "index": random.randrange(0, len(block.transactions)),
            "block_number": block_number,
        }


async def gen_starknet_simulateTransactions(
    urls: dict[models.NodeName, str],
) -> InputGenerator:
    client = FullNodeClient(node_url=next(iter(urls.values())))

    while True:
        block_number = await latest_common_block_number(urls)
        block_number = random.randrange(
            max(block_number - GENERATE_RANGE, 0), block_number
        )
        block = await client.get_block(block_number=block_number)
        txs = block.transactions

        if len(txs) > 0:
            tx_status = await client.get_transaction_status(
                typing.cast(int, txs[0].hash)
            )
            tx_status = tx_status.execution_status
        else:
            tx_status = TransactionExecutionStatus.SUCCEEDED

        # Allows reverted transactions to be simulated
        while len(txs) == 0 or txs[0].version == 0:
            block_number -= 1

            if block_number < 0:
                raise error.ErrorNoInputFound(
                    models.RpcCallBench.STARKNET_ESTIMATE_FEE
                )

            block = await client.get_block(block_number=block_number)
            txs = block.transactions
            tx_status = await client.get_transaction_status(
                typing.cast(int, txs[0].hash)
            )
            tx_status = tx_status.execution_status

        txs = [
            await tx_conv(tx, client)
            for tx in block.transactions
            if not isinstance(tx, L1HandlerTransaction)
        ]

        yield {
            "body": models.body._BodySimulateTransactions(transactions=txs),
            "block_number": block_number,
        }
