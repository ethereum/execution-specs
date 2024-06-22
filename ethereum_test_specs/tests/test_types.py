"""
Test types from ethereum_test_specs.
"""

import pytest

from ethereum_test_base_types import Address, Bloom, Bytes, Hash, HeaderNonce
from ethereum_test_fixtures.blockchain import FixtureHeader

from ..blockchain import Header

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
            Header(state_root="0x100"),
            fixture_header_ones.copy(state_root="0x100"),
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
            Header(withdrawals_root=Header.REMOVE_FIELD),  # state_root is not removable
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
            Header(logs_bloom="0x100"),
            fixture_header_ones.copy(logs_bloom="0x100"),
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
            Header(logs_bloom=Hash(100)),
            fixture_header_ones.copy(logs_bloom=100),
            id="bloom_as_hash",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root="0x100", logs_bloom=Hash(200), difficulty=300),
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
    fixture_header: FixtureHeader, modifier: Header, fixture_header_expected: FixtureHeader
):
    """
    Test that the join method works as expected.
    """
    assert modifier.apply(fixture_header) == fixture_header_expected
