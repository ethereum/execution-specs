"""Benchmark stub configuration model."""

import json
import warnings
from pathlib import Path

from execution_testing.base_types import (
    Address,
    EthereumTestBaseModel,
)


class StubConfig(EthereumTestBaseModel):
    """
    Benchmark stub configuration with prefix-based token extraction.

    Build from an ``AddressStubs`` mapping (via ``--address-stubs``)
    or from a JSON file.  Use ``extract_tokens`` to derive parameter
    lists for any prefix — no hardcoded categories required.
    """

    stubs: dict[str, Address]

    def extract_tokens(self, prefix: str) -> list[str]:
        """Return stub keys matching *prefix*."""
        return [k for k in self.stubs if k.startswith(prefix)]

    def parametrize_args(
        self, prefix: str, *, caller: str = ""
    ) -> tuple[list[str], list[str]]:
        """
        Return ``(values, ids)`` for ``metafunc.parametrize``.

        *values* are full stub keys matching *prefix*.
        *ids* are the keys with the prefix stripped for clean test output.
        Emits a warning when no stubs match.
        """
        values = self.extract_tokens(prefix)
        ids = [v.removeprefix(prefix) for v in values]
        if not values:
            label = f" for {caller}" if caller else ""
            warnings.warn(
                f"stub_parametrize: no stubs matched prefix "
                f"'{prefix}'{label}; test will be skipped",
                stacklevel=2,
            )
        return values, ids

    @classmethod
    def from_file(cls, path: Path) -> "StubConfig":
        """Load stubs from a JSON file."""
        return cls(stubs=json.loads(path.read_text()))
