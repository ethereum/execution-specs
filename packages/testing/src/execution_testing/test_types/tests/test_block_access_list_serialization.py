"""
Tests for BlockAccessList serialization format.

These tests verify that BAL models serialize to JSON with the correct
format, particularly zero-padded hex strings.
"""

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
    Test that BAL serializes with zero-padded hex format and round-trips correctly.

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
