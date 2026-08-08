"""Test the projection of fixture data onto JSON-RPC response objects."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
    HexNumber,
)
from execution_testing.fixtures.blockchain import (
    FixtureBlock,
    FixtureHeader,
    FixtureTransaction,
)
from execution_testing.fixtures.common import (
    FixtureTransactionLog,
    FixtureTransactionReceipt,
)
from execution_testing.rpc.serialization import (
    block_response,
    contract_address,
    effective_gas_price,
    receipt_responses,
)

SENDER = Address(0xA1)
RECIPIENT = Address(0xB2)


def make_header(**overrides: Any) -> FixtureHeader:
    """Return a header with every mandatory field populated."""
    fields: Dict[str, Any] = {
        "parent_hash": Hash(1),
        "ommers_hash": Hash(2),
        "fee_recipient": Address(3),
        "state_root": Hash(4),
        "transactions_trie": Hash(5),
        "receipts_root": Hash(6),
        "logs_bloom": Bloom(7),
        "difficulty": 0,
        "number": 1,
        "gas_limit": 100_000,
        "gas_used": 21_000,
        "timestamp": 12,
        "extra_data": Bytes(b""),
        "prev_randao": Hash(8),
        "nonce": HeaderNonce(0),
    }
    fields.update(overrides)
    return FixtureHeader(**fields)


def make_transaction(**overrides: Any) -> FixtureTransaction:
    """Return a legacy transaction from SENDER to RECIPIENT."""
    fields: Dict[str, Any] = {
        "ty": 0,
        "nonce": 0,
        "gas_price": 10,
        "gas_limit": 21_000,
        "to": RECIPIENT,
        "value": 0,
        "data": Bytes(b""),
        "sender": SENDER,
    }
    fields.update(overrides)
    return FixtureTransaction(**fields)


def make_receipt(
    cumulative_gas_used: int,
    logs: List[FixtureTransactionLog] | None = None,
    **overrides: Any,
) -> FixtureTransactionReceipt:
    """Return a successful receipt carrying the given logs."""
    fields: Dict[str, Any] = {
        "transaction_hash": Hash(0xDEAD),
        "ty": 0,
        "cumulative_gas_used": cumulative_gas_used,
        "bloom": Bloom(0),
        "logs": logs or [],
        "status": True,
    }
    fields.update(overrides)
    return FixtureTransactionReceipt(**fields)


def make_log(topic: int) -> FixtureTransactionLog:
    """Return a log with a single distinguishable topic."""
    return FixtureTransactionLog(
        address=RECIPIENT, topics=[Hash(topic)], data=Bytes(b"")
    )


def make_block(
    transactions: List[FixtureTransaction],
    receipts: List[FixtureTransactionReceipt],
    **header_overrides: Any,
) -> FixtureBlock:
    """Return a block pairing the given transactions and receipts."""
    return FixtureBlock(
        header=make_header(**header_overrides),
        txs=transactions,
        ommers=[],
        receipts=receipts,
        rlp=Bytes(b"\xc0" * 42),
    )


def test_quantities_use_minimal_hex() -> None:
    """
    Quantities serialize without zero padding.

    The schema's `uint` pattern rejects `0x01`, but fixtures store
    quantities as `ZeroPaddedHexNumber`, so the projection must convert.
    """
    block = make_block(
        [make_transaction()], [make_receipt(21_000)], number=1, timestamp=12
    )
    response = block_response(block).to_rpc()

    assert response["number"] == "0x1"
    assert response["timestamp"] == "0xc"
    assert response["difficulty"] == "0x0"


def test_log_index_counts_across_the_block() -> None:
    """
    `logIndex` is block-scoped, not transaction-scoped.

    A per-transaction counter is the tempting mistake and only shows up
    once a block holds more than one log-emitting transaction.
    """
    transactions = [make_transaction(nonce=0), make_transaction(nonce=1)]
    receipts = [
        make_receipt(
            21_000,
            logs=[make_log(1), make_log(2)],
            transaction_hash=Hash(0xAA),
        ),
        make_receipt(42_000, logs=[make_log(3)], transaction_hash=Hash(0xBB)),
    ]

    responses = receipt_responses(make_block(transactions, receipts))

    assert [log.log_index for log in responses[0].logs] == [0, 1]
    assert [log.log_index for log in responses[1].logs] == [2]


def test_gas_used_is_the_cumulative_difference() -> None:
    """Per-transaction `gasUsed` differences consecutive cumulative sums."""
    transactions = [make_transaction(nonce=0), make_transaction(nonce=1)]
    receipts = [
        make_receipt(21_000, transaction_hash=Hash(0xAA)),
        make_receipt(53_000, transaction_hash=Hash(0xBB)),
    ]

    responses = receipt_responses(make_block(transactions, receipts))

    assert responses[0].gas_used == 21_000
    assert responses[1].gas_used == 32_000
    assert responses[1].cumulative_gas_used == 53_000


def test_contract_address_only_for_creations() -> None:
    """`contractAddress` is derived for creations and null otherwise."""
    assert contract_address(make_transaction(to=RECIPIENT)) is None

    created = contract_address(make_transaction(to=None, nonce=0))
    assert created is not None
    assert len(created) == 20


def test_contract_address_varies_with_nonce() -> None:
    """A creation address depends on the sender's nonce."""
    first = contract_address(make_transaction(to=None, nonce=0))
    second = contract_address(make_transaction(to=None, nonce=1))

    assert first != second


@pytest.mark.parametrize(
    "transaction_fields,base_fee,expected",
    [
        pytest.param({"gas_price": 10}, None, 10, id="legacy"),
        pytest.param(
            {"gas_price": 10},
            HexNumber(7),
            10,
            id="legacy_ignores_base_fee",
        ),
        pytest.param(
            {
                "gas_price": None,
                "max_fee_per_gas": 100,
                "max_priority_fee_per_gas": 2,
            },
            HexNumber(7),
            9,
            id="eip1559_priority_fee_fits",
        ),
        pytest.param(
            {
                "gas_price": None,
                "max_fee_per_gas": 10,
                "max_priority_fee_per_gas": 50,
            },
            HexNumber(7),
            10,
            id="eip1559_priority_fee_capped",
        ),
    ],
)
def test_effective_gas_price(
    transaction_fields: Dict[str, Any],
    base_fee: HexNumber | None,
    expected: int,
) -> None:
    """The sender pays the base fee plus whatever priority fee fits."""
    transaction = make_transaction(ty=2, **transaction_fields)

    assert effective_gas_price(transaction, base_fee) == expected


def test_nullable_fields_are_present_as_null() -> None:
    """
    `to` and `contractAddress` are always present, possibly null.

    The schema describes them as nullable rather than optional, so
    dropping them would be wrong even though both can be `None`.
    """
    block = make_block([make_transaction()], [make_receipt(21_000)])
    response = receipt_responses(block)[0].to_rpc()

    assert "contractAddress" in response
    assert response["contractAddress"] is None
    assert response["to"] is not None


def test_conditional_fields_are_omitted() -> None:
    """
    Inapplicable fields are dropped rather than serialized as null.

    `blobGasUsed` is meaningless for a non-blob transaction, and `root`
    was replaced by `status` at Byzantium.
    """
    block = make_block([make_transaction()], [make_receipt(21_000)])
    response = receipt_responses(block)[0].to_rpc()

    assert "blobGasUsed" not in response
    assert "root" not in response
    assert response["status"] == "0x1"


def test_pre_byzantium_receipt_carries_root_not_status() -> None:
    """Before Byzantium a receipt reports a post-state root."""
    receipt = make_receipt(21_000, status=None, post_state=Hash(0xC0FFEE))
    block = make_block([make_transaction()], [receipt])

    response = receipt_responses(block)[0].to_rpc()

    assert "status" not in response
    assert response["root"] is not None


def test_fork_optional_header_fields_are_omitted() -> None:
    """A pre-London block omits `baseFeePerGas` rather than nulling it."""
    block = make_block([], [])
    response = block_response(block).to_rpc()

    assert "baseFeePerGas" not in response
    assert "withdrawalsRoot" not in response
    assert "blobGasUsed" not in response


def test_fork_optional_header_fields_appear_when_set() -> None:
    """A post-Cancun block carries its fork-specific header fields."""
    block = make_block(
        [], [], base_fee_per_gas=7, blob_gas_used=131_072, excess_blob_gas=0
    )
    response = block_response(block).to_rpc()

    assert response["baseFeePerGas"] == "0x7"
    assert response["blobGasUsed"] == "0x20000"
    assert response["excessBlobGas"] == "0x0"


def test_block_size_is_the_rlp_length() -> None:
    """`size` measures the encoded block, which the header does not carry."""
    block = make_block([], [])

    assert block_response(block).to_rpc()["size"] == hex(42)


def test_block_lists_transaction_hashes() -> None:
    """The hash form of a block lists its transactions in order."""
    transactions = [make_transaction(nonce=0), make_transaction(nonce=1)]
    receipts = [
        make_receipt(21_000, transaction_hash=Hash(0xAA)),
        make_receipt(42_000, transaction_hash=Hash(0xBB)),
    ]

    response = block_response(make_block(transactions, receipts)).to_rpc()

    assert response["transactions"] == [str(Hash(0xAA)), str(Hash(0xBB))]
