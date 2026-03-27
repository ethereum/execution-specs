"""Tests for the StubConfig model and token extraction."""

import json
from pathlib import Path

import pytest

from execution_testing.benchmark.stub_config import StubConfig, _extract_tokens

ADDR = "0x398324972FcE0e89E048c2104f1298031d1931fc"


def test_extract_tokens_matching_prefix() -> None:
    """Return stripped token names for keys matching the prefix."""
    stubs = {
        "test_sload_empty_erc20_balanceof_XEN": ADDR,
        "test_sload_empty_erc20_balanceof_USDC": ADDR,
    }
    result = _extract_tokens(stubs, "test_sload_empty_erc20_balanceof_")
    assert result == ["XEN", "USDC"]


def test_extract_tokens_no_match() -> None:
    """Return empty list when no keys match the prefix."""
    stubs = {"test_sstore_erc20_approve_XEN": ADDR}
    assert _extract_tokens(stubs, "test_sload_empty_erc20_balanceof_") == []


def test_extract_tokens_empty() -> None:
    """Return empty list for empty input."""
    assert _extract_tokens({}, "any_prefix_") == []


def test_stub_config_empty() -> None:
    """Derive empty token lists from empty stubs."""
    stub_config = StubConfig(stubs={})
    assert stub_config.sload_tokens == []
    assert stub_config.sstore_tokens == []
    assert stub_config.sstore_mint_tokens == []
    assert stub_config.mixed_tokens == []
    assert stub_config.factory_stubs == []


@pytest.mark.parametrize(
    "prefix,attr",
    [
        ("test_sload_empty_erc20_balanceof_", "sload_tokens"),
        ("test_sstore_erc20_approve_", "sstore_tokens"),
        ("test_sstore_erc20_mint_", "sstore_mint_tokens"),
        ("test_mixed_sload_sstore_", "mixed_tokens"),
    ],
)
def test_stub_config_token_extraction(prefix: str, attr: str) -> None:
    """Extract the correct token list for each prefix."""
    stub_config = StubConfig(
        stubs={
            f"{prefix}XEN": ADDR,
            f"{prefix}USDC": ADDR,
            "unrelated_key": ADDR,
        }
    )
    assert getattr(stub_config, attr) == ["XEN", "USDC"]


def test_stub_config_factory_stubs_sorted() -> None:
    """Sort factory stubs by bytecode size."""
    stub_config = StubConfig(
        stubs={
            "bloatnet_factory_24kb": ADDR,
            "bloatnet_factory_0_5kb": ADDR,
            "bloatnet_factory_5kb": ADDR,
            "bloatnet_factory_1kb": ADDR,
        }
    )
    assert stub_config.factory_stubs == [
        "bloatnet_factory_0_5kb",
        "bloatnet_factory_1kb",
        "bloatnet_factory_5kb",
        "bloatnet_factory_24kb",
    ]


def test_stub_config_unrelated_keys_ignored() -> None:
    """Ignore keys that don't match any known prefix."""
    stub_config = StubConfig(stubs={"some_other_key": ADDR})
    assert stub_config.sload_tokens == []
    assert stub_config.factory_stubs == []


def test_stub_config_from_file(tmp_path: Path) -> None:
    """Load stubs from a JSON file."""
    data = {
        "test_sload_empty_erc20_balanceof_XEN": ADDR,
        "bloatnet_factory_1kb": ADDR,
    }
    stub_file = tmp_path / "stubs.json"
    stub_file.write_text(json.dumps(data))

    stub_config = StubConfig.from_file(stub_file)
    assert stub_config.sload_tokens == ["XEN"]
    assert stub_config.factory_stubs == ["bloatnet_factory_1kb"]


def test_stub_config_from_file_not_found(tmp_path: Path) -> None:
    """Raise FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        StubConfig.from_file(tmp_path / "nonexistent.json")
