"""Benchmark stub configuration model."""

import json
from pathlib import Path
from typing import Any, Dict

from execution_testing import Address
from execution_testing.base_types import EthereumTestBaseModel


def _extract_tokens(stubs: dict, prefix: str) -> list[str]:
    """Extract token names by stripping *prefix* from matching keys."""
    return [k.removeprefix(prefix) for k in stubs if k.startswith(prefix)]


class StubConfig(EthereumTestBaseModel):
    """
    Benchmark stub configuration with derived token lists.

    Build from an ``AddressStubs`` mapping (via ``--address-stubs``)
    or from a JSON file.  Token lists and factory stub names are
    derived automatically in ``model_post_init``.
    """

    stubs: Dict[str, Address]

    sload_tokens: list[str] = []
    sstore_tokens: list[str] = []
    sstore_mint_tokens: list[str] = []
    mixed_tokens: list[str] = []
    factory_stubs: list[str] = []

    def model_post_init(self, __context: Any) -> None:
        """Derive token lists from stub keys."""
        self.sload_tokens = _extract_tokens(
            self.stubs, "test_sload_empty_erc20_balanceof_"
        )
        self.sstore_tokens = _extract_tokens(
            self.stubs, "test_sstore_erc20_approve_"
        )
        self.sstore_mint_tokens = _extract_tokens(
            self.stubs, "test_sstore_erc20_mint_"
        )
        self.mixed_tokens = _extract_tokens(
            self.stubs, "test_mixed_sload_sstore_"
        )
        self.factory_stubs = sorted(
            [k for k in self.stubs if k.startswith("bloatnet_factory_")],
            key=lambda name: float(
                name.replace("bloatnet_factory_", "")
                .replace("kb", "")
                .replace("_", ".")
            ),
        )

    @classmethod
    def from_file(cls, path: Path) -> "StubConfig":
        """Load stubs from a JSON file."""
        with open(path) as f:
            return cls(stubs=json.load(f))
