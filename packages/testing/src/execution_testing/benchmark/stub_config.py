"""Benchmark stub configuration model."""

import json
import warnings
from pathlib import Path

from execution_testing.base_types import (
    EthereumTestBaseModel,
)
from execution_testing.cli.pytest_commands.plugins.shared.address_stubs import (  # noqa: E501
    StubEntry,
)


class StubConfig(EthereumTestBaseModel):
    """
    Benchmark stub configuration with prefix-based token extraction.

    Build from an ``AddressStubs`` mapping (via ``--address-stubs``)
    or from a JSON file.  Use ``extract_tokens`` to derive parameter
    lists for any prefix — no hardcoded categories required.
    """

    stubs: dict[str, StubEntry]

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

    def is_eoa(self, label: str) -> bool:
        """Return whether the stub is an EOA (has a private key)."""
        return label in self.stubs and self.stubs[label].pkey is not None

    @classmethod
    def from_file(cls, path: Path) -> "StubConfig":
        """Load stubs from a JSON file."""
        raw = json.loads(path.read_text())
        stubs: dict[str, StubEntry] = {}
        for label, value in raw.items():
            if isinstance(value, dict):
                stubs[label] = StubEntry(**value)
            else:
                raise ValueError(
                    f"Invalid stub entry '{label}': "
                    f"expected object with 'addr' field"
                )
        return cls(stubs=stubs)
