"""Tests for AddressStubs prefix extraction and parametrization."""

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.cli.pytest_commands.plugins.shared.address_stubs import (  # noqa: E501
    AddressStubs,
    StubAddress,
    StubEOA,
)

ADDR = Address("0x398324972FcE0e89E048c2104f1298031d1931fc")
# TestPrivateKey and its derived TestAddress
TEST_PKEY = Hash(
    0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
)
TEST_ADDR = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")


def _stubs(mapping: dict[str, StubAddress | StubEOA]) -> AddressStubs:
    """Create an AddressStubs instance from a plain dict."""
    return AddressStubs(root=mapping)


def _entry(addr: Address = ADDR) -> StubAddress:
    """Create an address-only StubAddress."""
    return StubAddress(addr=addr)


def test_extract_tokens_returns_full_keys() -> None:
    """Return full keys matching the prefix."""
    stubs = _stubs(
        {
            "test_sload_empty_erc20_balanceof_XEN": _entry(),
            "test_sload_empty_erc20_balanceof_USDC": _entry(),
            "unrelated_key": _entry(),
        }
    )
    result = stubs.extract_tokens("test_sload_empty_erc20_balanceof_")
    assert result == [
        "test_sload_empty_erc20_balanceof_XEN",
        "test_sload_empty_erc20_balanceof_USDC",
    ]


def test_extract_tokens_no_match() -> None:
    """Return empty list when no keys match the prefix."""
    stubs = _stubs({"test_sstore_erc20_approve_XEN": _entry()})
    assert stubs.extract_tokens("test_sload_empty_erc20_balanceof_") == []


def test_extract_tokens_empty_stubs() -> None:
    """Return empty list for empty stubs."""
    stubs = _stubs({})
    assert stubs.extract_tokens("any_prefix_") == []


@pytest.mark.parametrize(
    "prefix",
    [
        "test_sload_empty_erc20_balanceof_",
        "test_sstore_erc20_approve_",
        "test_sstore_erc20_mint_",
        "test_mixed_sload_sstore_",
        "bloatnet_factory_",
    ],
)
def test_extract_tokens_various_prefixes(prefix: str) -> None:
    """Extract matching keys for each prefix."""
    stubs = _stubs(
        {
            f"{prefix}A": _entry(),
            f"{prefix}B": _entry(),
            "unrelated_key": _entry(),
        }
    )
    assert stubs.extract_tokens(prefix) == [
        f"{prefix}A",
        f"{prefix}B",
    ]


def test_parametrize_args_values_and_ids() -> None:
    """Return full keys as values and stripped names as ids."""
    stubs = _stubs(
        {
            "test_sload_empty_erc20_balanceof_XEN": _entry(),
            "test_sload_empty_erc20_balanceof_USDC": _entry(),
        }
    )
    values, ids = stubs.parametrize_args("test_sload_empty_erc20_balanceof_")
    assert values == [
        "test_sload_empty_erc20_balanceof_XEN",
        "test_sload_empty_erc20_balanceof_USDC",
    ]
    assert ids == ["XEN", "USDC"]


def test_parametrize_args_empty_warns() -> None:
    """Emit a warning when no stubs match the prefix."""
    stubs = _stubs({})
    with pytest.warns(UserWarning, match="no stubs matched prefix"):
        values, ids = stubs.parametrize_args(
            "missing_prefix_", caller="test_foo"
        )
    assert values == []
    assert ids == []


def test_stub_eoa_pkey_mismatch_raises() -> None:
    """Raise when private key derives a different address."""
    with pytest.raises(ValueError, match="pkey derives address"):
        StubEOA(addr=ADDR, pkey=TEST_PKEY)
