"""
Test the blockchain test types.
"""
from dataclasses import replace

import pytest

from ..common.types import Address, Bloom, Bytes, Hash, HeaderNonce
from ..spec.blockchain.types import FixtureHeader, Header

fixture_header_ones = FixtureHeader(
    parent_hash=Hash(1),
    ommers_hash=Hash(1),
    coinbase=Address(1),
    state_root=Hash(1),
    transactions_root=Hash(1),
    receipt_root=Hash(1),
    bloom=Bloom(1),
    difficulty=1,
    number=1,
    gas_limit=1,
    gas_used=1,
    timestamp=1,
    extra_data=Bytes([1]),
    mix_digest=Hash(1),
    nonce=HeaderNonce(1),
    base_fee=1,
    withdrawals_root=Hash(1),
    blob_gas_used=1,
    excess_blob_gas=1,
    hash=Hash(1),
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
            replace(fixture_header_ones, state_root=Hash("0x100")),
            id="state_root_as_str",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root=100),
            replace(fixture_header_ones, state_root=Hash(100)),
            id="state_root_as_int",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root=Hash(100)),
            replace(fixture_header_ones, state_root=Hash(100)),
            id="state_root_as_hash",
        ),
        pytest.param(
            fixture_header_ones,
            Header(withdrawals_root=Header.REMOVE_FIELD),  # state_root is not removable
            replace(fixture_header_ones, withdrawals_root=None),
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
            Header(bloom="0x100"),
            replace(fixture_header_ones, bloom=Bloom("0x100")),
            id="bloom_as_str",
        ),
        pytest.param(
            fixture_header_ones,
            Header(bloom=100),
            replace(fixture_header_ones, bloom=Bloom(100)),
            id="bloom_as_int",
        ),
        pytest.param(
            fixture_header_ones,
            Header(bloom=Hash(100)),
            replace(fixture_header_ones, bloom=Bloom(100)),
            id="bloom_as_hash",
        ),
        pytest.param(
            fixture_header_ones,
            Header(state_root="0x100", bloom=Hash(200), difficulty=300),
            replace(fixture_header_ones, state_root=Hash(0x100), bloom=Bloom(200), difficulty=300),
            id="multiple_fields",
        ),
    ],
)
def test_fixture_header_join(
    fixture_header: FixtureHeader, modifier: Header, fixture_header_expected: FixtureHeader
):
    assert fixture_header.join(modifier) == fixture_header_expected
