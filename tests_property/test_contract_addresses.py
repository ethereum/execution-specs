"""
The address a contract creation deploys to, against the framework.

The framework derives both addresses on its own, from the creator and its
nonce and, for `CREATE2`, from the creator, a salt and the init code.
"""

from types import ModuleType

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import Uint
from execution_testing import (
    compute_create2_address,
    compute_create_address,
)
from hypothesis import given
from hypothesis import strategies as st

from ethereum.state import Address
from ethereum_spec_tools.forks import Hardfork

from .forks import targets
from .strategies import MAX_U64, addresses, bytes_data, ints


@pytest.fixture(scope="session")
def address_utils(spec: Hardfork) -> ModuleType:
    """Return the address module of the fork under test."""
    return spec.module("utils.address")


# The nonce is RLP-encoded, so the address depends on its byte length.
@targets("utils.address.compute_contract_address")
@given(creator=addresses(), nonce=ints(MAX_U64))
def test_create_address_matches_the_framework(
    address_utils: ModuleType, creator: Address, nonce: int
) -> None:
    """A creator at a nonce deploys to the address the framework derives."""
    expected = compute_create_address(address=creator, nonce=nonce)
    actual = address_utils.compute_contract_address(creator, Uint(nonce))
    assert actual == expected


@targets("utils.address.compute_create2_contract_address")
@given(
    creator=addresses(),
    salt=st.binary(min_size=32, max_size=32),
    init_code=bytes_data(),
)
def test_create2_address_matches_the_framework(
    address_utils: ModuleType, creator: Address, salt: bytes, init_code: Bytes
) -> None:
    """`CREATE2` deploys to the address the framework derives."""
    expected = compute_create2_address(creator, salt, init_code)
    actual = address_utils.compute_create2_contract_address(
        creator, Bytes32(salt), init_code
    )
    assert actual == expected
