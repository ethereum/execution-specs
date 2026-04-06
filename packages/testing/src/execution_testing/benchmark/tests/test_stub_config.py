"""Tests for the StubConfig model."""

import json
from pathlib import Path

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.benchmark import StubConfig, StubEntry

ADDR = Address("0x398324972FcE0e89E048c2104f1298031d1931fc")
# TestPrivateKey and its derived TestAddress
TEST_PKEY = Hash(
    0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
)
TEST_ADDR = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")


def _entry(addr: Address = ADDR) -> StubEntry:
    """Create an address-only StubEntry."""
    return StubEntry(addr=addr)


def _eoa_entry() -> StubEntry:
    """Create a StubEntry with a private key."""
    return StubEntry(addr=TEST_ADDR, pkey=TEST_PKEY)


def test_extract_tokens_returns_full_keys() -> None:
    """Return full keys matching the prefix."""
    stub_config = StubConfig(
        stubs={
            "test_sload_empty_erc20_balanceof_XEN": _entry(),
            "test_sload_empty_erc20_balanceof_USDC": _entry(),
            "unrelated_key": _entry(),
        }
    )
    result = stub_config.extract_tokens("test_sload_empty_erc20_balanceof_")
    assert result == [
        "test_sload_empty_erc20_balanceof_XEN",
        "test_sload_empty_erc20_balanceof_USDC",
    ]


def test_extract_tokens_no_match() -> None:
    """Return empty list when no keys match the prefix."""
    stub_config = StubConfig(stubs={"test_sstore_erc20_approve_XEN": _entry()})
    assert (
        stub_config.extract_tokens("test_sload_empty_erc20_balanceof_") == []
    )


def test_extract_tokens_empty_stubs() -> None:
    """Return empty list for empty stubs."""
    stub_config = StubConfig(stubs={})
    assert stub_config.extract_tokens("any_prefix_") == []


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
    stub_config = StubConfig(
        stubs={
            f"{prefix}A": _entry(),
            f"{prefix}B": _entry(),
            "unrelated_key": _entry(),
        }
    )
    assert stub_config.extract_tokens(prefix) == [
        f"{prefix}A",
        f"{prefix}B",
    ]


def test_parametrize_args_values_and_ids() -> None:
    """Return full keys as values and stripped names as ids."""
    stub_config = StubConfig(
        stubs={
            "test_sload_empty_erc20_balanceof_XEN": _entry(),
            "test_sload_empty_erc20_balanceof_USDC": _entry(),
        }
    )
    values, ids = stub_config.parametrize_args(
        "test_sload_empty_erc20_balanceof_"
    )
    assert values == [
        "test_sload_empty_erc20_balanceof_XEN",
        "test_sload_empty_erc20_balanceof_USDC",
    ]
    assert ids == ["XEN", "USDC"]


def test_parametrize_args_empty_warns() -> None:
    """Emit a warning when no stubs match the prefix."""
    stub_config = StubConfig(stubs={})
    with pytest.warns(UserWarning, match="no stubs matched prefix"):
        values, ids = stub_config.parametrize_args(
            "missing_prefix_", caller="test_foo"
        )
    assert values == []
    assert ids == []


def test_from_file(tmp_path: Path) -> None:
    """Load stubs from a JSON file."""
    data = {
        "test_sload_empty_erc20_balanceof_XEN": {"addr": str(ADDR)},
        "bloatnet_factory_1kb": {"addr": str(ADDR)},
    }
    stub_file = tmp_path / "stubs.json"
    stub_file.write_text(json.dumps(data))

    stub_config = StubConfig.from_file(stub_file)
    assert stub_config.extract_tokens("test_sload_empty_erc20_balanceof_") == [
        "test_sload_empty_erc20_balanceof_XEN"
    ]
    assert stub_config.extract_tokens("bloatnet_factory_") == [
        "bloatnet_factory_1kb"
    ]


def test_from_file_not_found(tmp_path: Path) -> None:
    """Raise FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        StubConfig.from_file(tmp_path / "nonexistent.json")


def test_stub_entry_addr_only() -> None:
    """Create a StubEntry with only an address."""
    entry = StubEntry(addr=ADDR)
    assert entry.addr == ADDR
    assert entry.pkey is None


def test_stub_entry_with_pkey() -> None:
    """Create a StubEntry with a matching address and private key."""
    entry = StubEntry(addr=TEST_ADDR, pkey=TEST_PKEY)
    assert entry.addr == TEST_ADDR
    assert entry.pkey == TEST_PKEY


def test_stub_entry_pkey_mismatch_raises() -> None:
    """Raise when private key derives a different address."""
    with pytest.raises(ValueError, match="pkey derives address"):
        StubEntry(addr=ADDR, pkey=TEST_PKEY)


def test_is_eoa() -> None:
    """Return True only for stubs that have a pkey."""
    stub_config = StubConfig(
        stubs={
            "contract": _entry(),
            "eoa": _eoa_entry(),
        }
    )
    assert not stub_config.is_eoa("contract")
    assert stub_config.is_eoa("eoa")
    assert not stub_config.is_eoa("nonexistent")


def test_from_file_with_pkey(tmp_path: Path) -> None:
    """Load stubs from a JSON file with private key entries."""
    data = {
        "contract": {"addr": str(ADDR)},
        "eoa": {"addr": str(TEST_ADDR), "pkey": str(TEST_PKEY)},
    }
    stub_file = tmp_path / "stubs.json"
    stub_file.write_text(json.dumps(data))

    stub_config = StubConfig.from_file(stub_file)
    assert not stub_config.is_eoa("contract")
    assert stub_config.is_eoa("eoa")
