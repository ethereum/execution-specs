"""
Address stubs model shared by the filler and execute plugins.

This model maps stub labels to on-chain addresses, optionally
carrying a private key for EOA stubs that need signing capability.
"""

import warnings
from pathlib import Path
from typing import Dict, Self

from pydantic import model_validator

from execution_testing.base_types import (
    Address,
    EthereumTestBaseModel,
    EthereumTestRootModel,
    Hash,
)
from execution_testing.test_types import EOA


class StubAddress(EthereumTestBaseModel):
    """A single stub entry with an address."""

    addr: Address


class StubEOA(EthereumTestBaseModel):
    """A single stub EOA entry with an address and a private key."""

    addr: Address
    pkey: Hash

    @model_validator(mode="after")
    def _validate_key_matches_address(self) -> Self:
        """Verify the private key derives the declared address."""
        derived = Address(EOA(key=self.pkey))
        if derived != self.addr:
            raise ValueError(
                f"pkey derives address {derived}, but addr is {self.addr}"
            )
        return self


class AddressStubs(EthereumTestRootModel[Dict[str, StubAddress | StubEOA]]):
    """
    Address stubs class.

    The key represents the label that is used in the test to tag the
    account, and the value is a StubAddress or StubEOA containing
    the on-chain address and an optional private key.
    """

    root: Dict[str, StubAddress | StubEOA]

    def __contains__(self, item: str) -> bool:
        """Check if an item is in the address stubs."""
        return item in self.root

    def __getitem__(self, item: str) -> Address:
        """Get the address for a stub label."""
        return self.root[item].addr

    def get_entry(self, item: str) -> StubAddress | StubEOA:
        """Get the full stub entry for a label."""
        return self.root[item]

    def is_eoa(self, item: str) -> bool:
        """Check if a stub entry is an EOA (has a private key)."""
        return item in self.root and isinstance(self.root[item], StubEOA)

    def extract_tokens(self, prefix: str) -> list[str]:
        """Return stub keys matching *prefix*."""
        return [k for k in self.root if k.startswith(prefix)]

    def parametrize_args(
        self, prefix: str, *, caller: str = ""
    ) -> tuple[list[str], list[str]]:
        """
        Return ``(values, ids)`` for ``metafunc.parametrize``.

        *values* are full stub keys matching *prefix*.
        *ids* are the keys with the prefix stripped for clean test output.
        Emit a warning when no stubs match.
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
    def model_validate_json_or_file(cls, json_data_or_path: str) -> Self:
        """
        Parse a JSON string or load from a JSON file.

        If the value ends with ``.json`` and the file exists, the file
        contents are loaded; otherwise the value is parsed as inline JSON.
        """
        if json_data_or_path.lower().endswith(".json"):
            path = Path(json_data_or_path)
            if path.is_file():
                return cls.model_validate_json(path.read_text())
            else:
                raise FileNotFoundError(
                    f"Address stubs file not found: {path}"
                )
        if json_data_or_path.strip() == "":
            return cls(root={})
        return cls.model_validate_json(json_data_or_path)
