"""
Address stubs model shared by the filler and execute plugins.
This model maps stub labels to on-chain contract addresses.
"""

from pathlib import Path
from typing import Dict, Self

from execution_testing.base_types import Address, EthereumTestRootModel


class AddressStubs(EthereumTestRootModel[Dict[str, Address]]):
    """
    Address stubs class.

    The key represents the label that is used in the test to tag the contract,
    and the value is the address where the contract is already located at in
    the current network.
    """

    root: Dict[str, Address]

    def __contains__(self, item: str) -> bool:
        """Check if an item is in the address stubs."""
        return item in self.root

    def __getitem__(self, item: str) -> Address:
        """Get an item from the address stubs."""
        return self.root[item]

    @classmethod
    def model_validate_json_or_file(cls, json_data_or_path: str) -> Self:
        """
        Parse a JSON string or load from a JSON file.

        If the value ends with `.json` and the file exists, the file
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
