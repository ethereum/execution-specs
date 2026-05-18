"""Test types from execution_testing.specs."""

import pytest

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
)
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayloadModifier,
    FixtureHeader,
)
from execution_testing.test_types.block_access_list import BlockAccessList

from ..blockchain import BuiltBlock, Header

fixture_header_ones = FixtureHeader(
    parent_hash=Hash(1),
    ommers_hash=Hash(1),
    fee_recipient=Address(1),
    state_root=Hash(1),
    transactions_trie=Hash(1),
    receipts_root=Hash(1),
    logs_bloom=Bloom(1),
    difficulty=1,
    number=1,
    gas_limit=1,
    gas_used=1,
    timestamp=1,
    extra_data=Bytes([1]),
    prev_randao=Hash(1),
    nonce=HeaderNonce(1),
    base_fee_per_gas=1,
    withdrawals_root=Hash(1),
    blob_gas_used=1,
    excess_blob_gas=1,
    # hash=Hash(1),
)


@pytest.mark.parametrize(
    "fixture_header,modifier,fixture_header_expected",
    [
        pytest.param(
            fixture_header_ones,
            Header(),
            fixture_header_ones,
            id="default_header",
        ),
        pytest.param(
            fixture_header_ones,
            Header(
                state_root="0x0000000000000000000000000000000000000000000000000000000000000100"
            ),
            fixture_header_ones.copy(
                state_root="0x0000000000000000000000000000000000000000000000000000000000000100"
            ),
            id="state_root_as_str",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root=100),
            fixture_header_ones.copy(state_root=100),
            id="state_root_as_int",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root=Hash(100)),
            fixture_header_ones.copy(state_root=100),
            id="state_root_as_hash",
        ),
        pytest.param(
            fixture_header_ones,
            Header(
                withdrawals_root=Header.REMOVE_FIELD
            ),  # state_root is not removable
            fixture_header_ones.copy(withdrawals_root=None),
            id="state_root_as_header_remove_field",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root=None),
            fixture_header_ones,
            id="state_root_as_none",
        ),
        pytest.param(
            fixture_header_ones,
            Header(
                logs_bloom="0x00000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000100"
            ),
            fixture_header_ones.copy(
                logs_bloom="0x00000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000100"
            ),
            id="bloom_as_str",
        ),
        pytest.param(
            fixture_header_ones,
            Header(logs_bloom=100),
            fixture_header_ones.copy(logs_bloom=100),
            id="bloom_as_int",
        ),
        pytest.param(
            fixture_header_ones,
            Header(logs_bloom=Bloom(100)),
            fixture_header_ones.copy(logs_bloom=100),
            id="bloom_as_hash",
        ),
        pytest.param(
            fixture_header_ones,
            Header(
                state_root="0x0000000000000000000000000000000000000000000000000000000000000100",
                logs_bloom=Bloom(200),
                difficulty=300,
            ),
            fixture_header_ones.copy(
                state_root=0x100,
                logs_bloom=200,
                difficulty=300,
            ),
            id="multiple_fields",
        ),
    ],
)
def test_fixture_header_join(
    fixture_header: FixtureHeader,
    modifier: Header,
    fixture_header_expected: FixtureHeader,
) -> None:
    """Test that the join method works as expected."""
    assert modifier.apply(fixture_header) == fixture_header_expected


class TestDeriveEnginePayloadModifier:
    """
    Verify the auto-propagation from ``rlp_modifier``'s header-only changes
    to the engine payload body. Test authors set ``rlp_modifier`` once on a
    ``Block``; the framework must reflect that change on both the RLP block
    and the ``engine_newPayload`` fixture.
    """

    def test_no_rlp_modifier_returns_none(self) -> None:
        """No modifier → no engine payload override."""
        assert (
            BuiltBlock.derive_engine_payload_modifier(
                rlp_modifier=None,
                block_access_list=None,
            )
            is None
        )

    def test_rlp_modifier_unrelated_field_returns_none(self) -> None:
        """A modifier that doesn't touch BAL hash leaves the payload alone."""
        assert (
            BuiltBlock.derive_engine_payload_modifier(
                rlp_modifier=Header(state_root=Hash(100)),
                block_access_list=None,
            )
            is None
        )

    def test_remove_bal_hash_removes_body_from_payload(self) -> None:
        """Removing the header's BAL hash also removes the payload body."""
        modifier = BuiltBlock.derive_engine_payload_modifier(
            rlp_modifier=Header(block_access_list_hash=Header.REMOVE_FIELD),
            block_access_list=BlockAccessList(),
        )
        assert isinstance(modifier, FixtureExecutionPayloadModifier)
        assert modifier.block_access_list is (
            FixtureExecutionPayloadModifier.REMOVE_FIELD
        )

    def test_inject_bal_hash_on_pre_fork_adds_body(self) -> None:
        """
        Injecting a header BAL hash on a block that has no body (pre-fork)
        triggers a body to be added to the engine payload, so a payload-
        version mismatch is detectable.
        """
        modifier = BuiltBlock.derive_engine_payload_modifier(
            rlp_modifier=Header(block_access_list_hash=Hash(0)),
            block_access_list=None,
        )
        assert isinstance(modifier, FixtureExecutionPayloadModifier)
        assert modifier.block_access_list == Bytes(b"")

    def test_inject_bal_hash_on_post_fork_leaves_body_alone(self) -> None:
        """
        Setting a BAL hash on a block that already has a body (post-fork)
        does not override the body — the resulting block-hash mismatch is
        what triggers the client rejection in that scenario.
        """
        assert (
            BuiltBlock.derive_engine_payload_modifier(
                rlp_modifier=Header(block_access_list_hash=Hash(0)),
                block_access_list=BlockAccessList(),
            )
            is None
        )
