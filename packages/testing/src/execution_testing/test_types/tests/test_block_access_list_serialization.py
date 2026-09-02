"""
Tests for BlockAccessList serialization format.

These tests verify that BAL models serialize to JSON with the correct
format, particularly zero-padded hex strings.
"""

from typing import Any

import pytest

from execution_testing.base_types import Address, Bytes
from execution_testing.test_types.block_access_list import (
    BalAccountChange,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessList,
)


def test_bal_serialization_roundtrip_zero_padded_hex() -> None:
    """
    Test BAL serializes with zero-padded hex format and round-trips correctly.

    This verifies that values like 12 serialize as "0x0c" (not "0xc"), which is
    required for consistency with other test vector fields.
    """
    addr = Address(0xA)

    original = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=12),
                    BalNonceChange(block_access_index=2, post_nonce=255),
                ],
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=15),
                ],
                code_changes=[
                    BalCodeChange(
                        block_access_index=3, new_code=Bytes(b"\xde\xad")
                    ),
                ],
                storage_changes=[
                    BalStorageSlot(
                        slot=12,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=255
                            ),
                            BalStorageChange(
                                block_access_index=2, post_value=4096
                            ),
                        ],
                    ),
                ],
                storage_reads=[1, 15, 256],
            )
        ]
    )

    # Serialize to JSON
    json_data = original.model_dump(mode="json")
    account_data = json_data[0]

    # Verify zero-padded hex format (0x0c not 0xc, 0x01 not 0x1)
    assert account_data["nonce_changes"][0]["block_access_index"] == "0x01"
    assert account_data["nonce_changes"][0]["post_nonce"] == "0x0c"
    assert account_data["nonce_changes"][1]["post_nonce"] == "0xff"
    assert account_data["balance_changes"][0]["post_balance"] == "0x0f"
    assert account_data["code_changes"][0]["block_access_index"] == "0x03"
    assert account_data["storage_changes"][0]["slot"] == "0x0c"
    assert (
        account_data["storage_changes"][0]["slot_changes"][0]["post_value"]
        == "0xff"
    )
    assert (
        account_data["storage_changes"][0]["slot_changes"][1]["post_value"]
        == "0x1000"
    )
    assert account_data["storage_reads"] == ["0x01", "0x0f", "0x0100"]

    # Round-trip: deserialize and verify equality
    restored = BlockAccessList.model_validate(json_data)
    assert restored == original


def test_bal_rlp_override_replaces_serialization_only() -> None:
    """`with_rlp_override` swaps the bytes but keeps the contents."""
    original = BlockAccessList(
        [
            BalAccountChange(
                address=Address(0xA),
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            )
        ]
    )
    canonical = original.rlp
    overridden = original.with_rlp_override(Bytes(b"\xc0"))

    assert overridden.has_rlp_override
    assert not original.has_rlp_override
    assert overridden.rlp == b"\xc0"
    assert overridden.rlp_hash == Bytes(b"\xc0").keccak256()
    assert overridden.to_list() == original.to_list()
    assert original.rlp == canonical


@pytest.mark.parametrize(
    "rlp",
    [
        pytest.param(None, id="none"),
        pytest.param(BlockAccessList([]), id="list"),
        pytest.param(0xC0, id="int"),
    ],
)
def test_bal_rlp_override_refuses_non_bytes(rlp: Any) -> None:
    """The override bypasses validation, so its type is checked here."""
    with pytest.raises(TypeError, match="expects the serialization as bytes"):
        BlockAccessList([]).with_rlp_override(rlp)


@pytest.mark.parametrize(
    "rlp",
    [pytest.param(b"\xc0", id="bytes"), pytest.param("0xc0", id="hex_str")],
)
def test_bal_rlp_override_coerces_to_bytes(rlp: Any) -> None:
    """Plain bytes and hex strings are coerced so ``rlp_hash`` works."""
    overridden = BlockAccessList([]).with_rlp_override(rlp)

    assert overridden.rlp == Bytes(b"\xc0")
    assert overridden.rlp_hash == Bytes(b"\xc0").keccak256()
