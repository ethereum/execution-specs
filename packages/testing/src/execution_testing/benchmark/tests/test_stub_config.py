"""Tests for the StubConfig model."""

import json
from pathlib import Path

import pytest

from execution_testing.benchmark.stub_config import StubConfig

ADDR = "0x398324972FcE0e89E048c2104f1298031d1931fc"


def test_extract_tokens_returns_full_keys() -> None:
    """Return full keys matching the prefix."""
    stub_config = StubConfig(
        stubs={
            "test_sload_empty_erc20_balanceof_XEN": ADDR,
            "test_sload_empty_erc20_balanceof_USDC": ADDR,
            "unrelated_key": ADDR,
        }
    )
    result = stub_config.extract_tokens("test_sload_empty_erc20_balanceof_")
    assert result == [
        "test_sload_empty_erc20_balanceof_XEN",
        "test_sload_empty_erc20_balanceof_USDC",
    ]


def test_extract_tokens_no_match() -> None:
    """Return empty list when no keys match the prefix."""
    stub_config = StubConfig(stubs={"test_sstore_erc20_approve_XEN": ADDR})
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
            f"{prefix}A": ADDR,
            f"{prefix}B": ADDR,
            "unrelated_key": ADDR,
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
            "test_sload_empty_erc20_balanceof_XEN": ADDR,
            "test_sload_empty_erc20_balanceof_USDC": ADDR,
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
        "test_sload_empty_erc20_balanceof_XEN": ADDR,
        "bloatnet_factory_1kb": ADDR,
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
