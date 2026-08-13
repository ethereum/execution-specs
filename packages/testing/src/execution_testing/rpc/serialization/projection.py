"""
Project filled fixture data onto JSON-RPC response objects.

The expected value of an RPC call is derived from the Python spec's own
output rather than recorded from a client. By the time a fixture is
written, `t8n` has already produced the receipts, logs and post-state, and
the header has been assembled; everything here is a pure function of that
data. No client is consulted and no execution is repeated.

The fields that do not exist in consensus data are derived as follows:

| field                | derivation                                    |
| -------------------- | --------------------------------------------- |
| `blockHash`          | header                                        |
| `blockTimestamp`     | header                                        |
| `transactionIndex`   | position in the block                         |
| `logIndex`           | position within the block, across receipts    |
| `from`               | transaction sender, known to the filler       |
| `contractAddress`    | sender and nonce, for creations               |
| `gasUsed` (per tx)   | difference of consecutive `cumulativeGasUsed` |
| `effectiveGasPrice`  | transaction gas fields and the base fee       |
| `size`               | length of the RLP-encoded block               |
"""

from typing import List

import ethereum_rlp as eth_rlp

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HexNumber,
)
from execution_testing.fixtures.blockchain import (
    FixtureBlock,
    FixtureTransaction,
)
from execution_testing.fixtures.common import FixtureTransactionReceipt
from execution_testing.test_types.utils import int_to_bytes

from .types import (
    RPCAccessListEntry,
    RPCAccountAccess,
    RPCAuthorization,
    RPCBlock,
    RPCCodeChange,
    RPCLog,
    RPCReceipt,
    RPCSlotChanges,
    RPCStorageChange,
    RPCTransaction,
    RPCValueChange,
    RPCWithdrawal,
)


def effective_gas_price(
    transaction: FixtureTransaction,
    base_fee_per_gas: HexNumber | None,
) -> HexNumber:
    """
    Return the gas price actually charged to the sender.

    Before EIP-1559 this is the transaction's `gasPrice`. After it, the
    sender pays the base fee plus whatever priority fee fits under the
    cap they set.
    """
    if transaction.gas_price is not None:
        return HexNumber(transaction.gas_price)

    assert transaction.max_fee_per_gas is not None, (
        "transaction has neither gas_price nor max_fee_per_gas"
    )
    if base_fee_per_gas is None:
        return HexNumber(transaction.max_fee_per_gas)

    priority_fee = min(
        HexNumber(transaction.max_priority_fee_per_gas or 0),
        HexNumber(transaction.max_fee_per_gas) - base_fee_per_gas,
    )
    return HexNumber(base_fee_per_gas + priority_fee)


def contract_address(transaction: FixtureTransaction) -> Address | None:
    """
    Return the address created by the transaction, if it is a creation.

    `Transaction.created_contract` is not available here: a fixture
    transaction is a `TransactionGeneric`, which carries the signed fields
    but none of the derived properties.
    """
    if transaction.to is not None:
        return None
    sender = _sender_of(transaction)
    encoded = Bytes(
        eth_rlp.encode([sender, int_to_bytes(int(transaction.nonce))])
    )
    return Address(encoded.keccak256()[-20:])


def receipt_responses(block: FixtureBlock) -> List[RPCReceipt]:
    """
    Project a block's consensus receipts onto RPC receipt objects.

    `logIndex` counts across the whole block rather than restarting per
    transaction, so the receipts must be projected together.
    """
    block_hash = block.header.block_hash
    block_number = HexNumber(block.header.number)
    timestamp = HexNumber(block.header.timestamp)
    base_fee = (
        HexNumber(block.header.base_fee_per_gas)
        if block.header.base_fee_per_gas is not None
        else None
    )

    responses: List[RPCReceipt] = []
    previous_cumulative_gas_used = 0
    log_index = 0

    for index, receipt in enumerate(block.receipts or []):
        transaction = block.txs[index]
        cumulative_gas_used = int(receipt.cumulative_gas_used)

        logs: List[RPCLog] = []
        for log in receipt.logs:
            assert log.address is not None, "log is missing an address"
            assert log.topics is not None, "log is missing topics"
            assert log.data is not None, "log is missing data"
            logs.append(
                RPCLog(
                    address=log.address,
                    topics=log.topics,
                    data=log.data,
                    block_hash=block_hash,
                    block_number=block_number,
                    block_timestamp=timestamp,
                    transaction_hash=receipt.transaction_hash,
                    transaction_index=HexNumber(index),
                    log_index=HexNumber(log_index),
                )
            )
            log_index += 1

        responses.append(
            RPCReceipt(
                transaction_hash=receipt.transaction_hash,
                transaction_index=HexNumber(index),
                block_hash=block_hash,
                block_number=block_number,
                sender=_sender_of(transaction),
                to=transaction.to,
                cumulative_gas_used=HexNumber(cumulative_gas_used),
                gas_used=HexNumber(
                    cumulative_gas_used - previous_cumulative_gas_used
                ),
                contract_address=contract_address(transaction),
                logs=logs,
                logs_bloom=Bloom(receipt.bloom),
                ty=HexNumber(receipt.ty),
                effective_gas_price=effective_gas_price(transaction, base_fee),
                status=_status_of(receipt),
                root=receipt.post_state,
            )
        )
        previous_cumulative_gas_used = cumulative_gas_used

    return responses


def _is_typed(transaction: FixtureTransaction) -> bool:
    """Return whether the transaction is typed rather than legacy."""
    return int(transaction.ty) > 0


def transaction_responses(block: FixtureBlock) -> List[RPCTransaction]:
    """
    Project a block's transactions onto RPC transaction objects.

    Type determines which fields appear. Legacy transactions report `v`
    and typed ones `yParity`; `gasPrice` is present throughout, holding
    the effective price from EIP-1559 onwards rather than a value the
    sender chose.
    """
    header = block.header
    base_fee = (
        HexNumber(header.base_fee_per_gas)
        if header.base_fee_per_gas is not None
        else None
    )
    receipts = block.receipts or []
    assert len(receipts) == len(block.txs), (
        "every transaction needs its receipt to supply the hash"
    )

    responses: List[RPCTransaction] = []
    for index, transaction in enumerate(block.txs):
        receipt = receipts[index]
        responses.append(
            RPCTransaction(
                block_hash=header.block_hash,
                block_number=HexNumber(header.number),
                block_timestamp=HexNumber(header.timestamp),
                transaction_index=HexNumber(index),
                transaction_hash=receipt.transaction_hash,
                sender=_sender_of(transaction),
                to=transaction.to,
                value=HexNumber(transaction.value),
                gas=HexNumber(transaction.gas_limit),
                input=transaction.data,
                nonce=HexNumber(transaction.nonce),
                ty=HexNumber(transaction.ty),
                r=HexNumber(transaction.r),
                s=HexNumber(transaction.s),
                v=None if _is_typed(transaction) else HexNumber(transaction.v),
                y_parity=(
                    HexNumber(transaction.v)
                    if _is_typed(transaction)
                    else None
                ),
                chain_id=(
                    HexNumber(transaction.chain_id)
                    if _is_typed(transaction)
                    else None
                ),
                access_list=(
                    [
                        RPCAccessListEntry(
                            address=entry.address,
                            storage_keys=list(entry.storage_keys),
                        )
                        for entry in (transaction.access_list or [])
                    ]
                    if _is_typed(transaction)
                    else None
                ),
                gas_price=effective_gas_price(transaction, base_fee),
                max_fee_per_gas=_optional_number(transaction.max_fee_per_gas),
                max_priority_fee_per_gas=_optional_number(
                    transaction.max_priority_fee_per_gas
                ),
                max_fee_per_blob_gas=_optional_number(
                    transaction.max_fee_per_blob_gas
                ),
                blob_versioned_hashes=(
                    list(transaction.blob_versioned_hashes)
                    if transaction.blob_versioned_hashes is not None
                    else None
                ),
                authorization_list=(
                    [
                        RPCAuthorization(
                            chain_id=HexNumber(authorization.chain_id),
                            address=authorization.address,
                            nonce=HexNumber(authorization.nonce),
                            y_parity=HexNumber(authorization.v),
                            r=HexNumber(authorization.r),
                            s=HexNumber(authorization.s),
                        )
                        for authorization in transaction.authorization_list
                    ]
                    if transaction.authorization_list is not None
                    else None
                ),
            )
        )
    return responses


def withdrawal_responses(
    block: FixtureBlock,
) -> List[RPCWithdrawal] | None:
    """
    Project a block's withdrawals, or None before Shanghai.

    The empty list and absence mean different things: from Shanghai
    onwards a block reports an empty list when it has no withdrawals,
    while an earlier block has no such field at all.
    """
    if block.withdrawals is None:
        return None
    return [
        RPCWithdrawal(
            index=HexNumber(withdrawal.index),
            validator_index=HexNumber(withdrawal.validator_index),
            address=withdrawal.address,
            amount=HexNumber(withdrawal.amount),
        )
        for withdrawal in block.withdrawals
    ]


def block_access_list_response(
    block: FixtureBlock,
) -> List[RPCAccountAccess] | None:
    """
    Project a block's access list, or None where the fork produces none.

    This is the one projection that reformats and nothing more: the access
    list is a consensus object the transition tool already returned, and the
    fixture carries it whole. The RPC view differs only in spelling — the
    consensus field names are positional (`post_balance`, `new_code`), the
    response names them `value` and `code`, and quantities become minimal
    hex while storage keys and values stay padded to 32 bytes.

    A fork that does not produce an access list has nothing to say here, and
    neither does the genesis block, which a fixture stores as a header
    rather than as a built block.
    """
    if block.block_access_list is None:
        return None
    return [
        RPCAccountAccess(
            address=account.address,
            balance_changes=[
                RPCValueChange(
                    index=HexNumber(change.block_access_index),
                    value=HexNumber(change.post_balance),
                )
                for change in account.balance_changes
            ],
            code_changes=[
                RPCCodeChange(
                    index=HexNumber(change.block_access_index),
                    code=change.new_code,
                )
                for change in account.code_changes
            ],
            nonce_changes=[
                RPCValueChange(
                    index=HexNumber(change.block_access_index),
                    value=HexNumber(change.post_nonce),
                )
                for change in account.nonce_changes
            ],
            storage_changes=[
                RPCSlotChanges(
                    key=Hash(slot.slot),
                    changes=[
                        RPCStorageChange(
                            index=HexNumber(change.block_access_index),
                            value=Hash(change.post_value),
                        )
                        for change in slot.slot_changes
                    ],
                )
                for slot in account.storage_changes
            ],
            storage_reads=[Hash(slot) for slot in account.storage_reads],
        )
        for account in block.block_access_list.root
    ]


def block_response(
    block: FixtureBlock, *, full_transactions: bool = False
) -> RPCBlock:
    """
    Project a fixture block onto an RPC block object.

    `full_transactions` selects the form the request asked for: the hash
    list, or the transaction objects a client returns when the second
    parameter is true.
    """
    header = block.header
    assert block.rlp is not None, "block is missing its RLP encoding"

    return RPCBlock(
        block_hash=header.block_hash,
        parent_hash=header.parent_hash,
        ommers_hash=header.ommers_hash,
        fee_recipient=header.fee_recipient,
        state_root=header.state_root,
        transactions_root=header.transactions_trie,
        receipts_root=header.receipts_root,
        logs_bloom=header.logs_bloom,
        difficulty=HexNumber(header.difficulty),
        number=HexNumber(header.number),
        gas_limit=HexNumber(header.gas_limit),
        gas_used=HexNumber(header.gas_used),
        timestamp=HexNumber(header.timestamp),
        extra_data=header.extra_data,
        prev_randao=header.prev_randao,
        nonce=Bytes(header.nonce),
        size=HexNumber(len(block.rlp)),
        transactions=(
            [tx.to_rpc() for tx in transaction_responses(block)]
            if full_transactions
            else [
                # Stringified because `transactions` is untyped: with `Any`
                # pydantic has no `Hash` serializer and would try to decode
                # the raw bytes as utf-8.
                str(receipt.transaction_hash)
                for receipt in (block.receipts or [])
            ]
        ),
        base_fee_per_gas=_optional_number(header.base_fee_per_gas),
        withdrawals_root=header.withdrawals_root,
        blob_gas_used=_optional_number(header.blob_gas_used),
        excess_blob_gas=_optional_number(header.excess_blob_gas),
        parent_beacon_block_root=header.parent_beacon_block_root,
        requests_hash=header.requests_hash,
        withdrawals=withdrawal_responses(block),
    )


def _sender_of(transaction: FixtureTransaction) -> Address:
    """Return the transaction's sender, which the filler always knows."""
    assert transaction.sender is not None, "transaction has no sender"
    return Address(transaction.sender)


def _status_of(receipt: FixtureTransactionReceipt) -> HexNumber | None:
    """
    Return the receipt status, or None before Byzantium.

    Pre-Byzantium receipts carry a post-state root instead, and the two are
    mutually exclusive in the response.
    """
    if receipt.status is None:
        return None
    return HexNumber(1 if receipt.status else 0)


def _optional_number(value: int | None) -> HexNumber | None:
    """Convert an optional header quantity to minimal-hex form."""
    return None if value is None else HexNumber(value)


__all__ = [
    "block_access_list_response",
    "block_response",
    "contract_address",
    "effective_gas_price",
    "receipt_responses",
    "transaction_responses",
    "withdrawal_responses",
]
