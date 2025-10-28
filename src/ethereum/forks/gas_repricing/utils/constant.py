"""
Gas Cost Constants for Gas Repricing Fork.

This module provides a unified dataclass for accessing gas costs
loaded from the gas_cost.yaml configuration file.

Reference: https://github.com/ethereum/execution-specs/issues/1599
"""

from pathlib import Path
from typing import Dict

import yaml
from ethereum_types.numeric import Uint


class GasCosts:
    """
    Unified gas cost constants with direct opcode access.
    """

    def __init__(self, yaml_path: Path | None = None):
        """
        Initialize GasCosts by loading from gas_cost.yaml file.
        """
        if yaml_path is None:
            yaml_path = Path(__file__).parent / "gas_cost.yaml"

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        static_costs = data["static_costs"]
        opcode_costs = data["opcode_costs"]

        self._static_costs = static_costs
        self._opcode_costs = opcode_costs
        self._opcode_values_cache: Dict[str, int] = {}

        for opcode, cost_name in opcode_costs.items():
            self._opcode_values_cache[opcode] = static_costs[cost_name]

    def __getattr__(self, name: str) -> Uint:
        """
        Get gas cost by attribute access.
        """
        # Avoid infinite recursion for internal attributes
        if name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        # Try static constants first
        if name in self._static_costs:
            return Uint(self._static_costs[name])

        # Try opcode costs
        if name in self._opcode_values_cache:
            return Uint(self._opcode_values_cache[name])

        # Not found
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, opcode: str) -> int:
        """
        Dictionary-style access to opcode gas costs.
        """
        if opcode in self._opcode_values_cache:
            return self._opcode_values_cache[opcode]
        raise KeyError(f"Opcode '{opcode}' not found")

    def __contains__(self, opcode: str) -> bool:
        """
        Check if an opcode has a gas cost mapping.
        """
        return opcode in self._opcode_values_cache

    def get(self, opcode: str, default: int | None = None) -> int | None:
        """
        Get gas cost with a default value.
        """
        return self._opcode_values_cache.get(opcode, default)

    def items(self):
        """
        Iterate over (opcode, gas_cost) pairs.
        """
        return self._opcode_values_cache.items()

    def keys(self):
        """
        Get all opcode names.
        """
        return self._opcode_values_cache.keys()

    def values(self):
        """
        Get all gas cost values.
        """
        return self._opcode_values_cache.values()

    def get_opcode_cost_name(self, opcode: str) -> str:
        """
        Get the gas cost constant name for an opcode.
        """
        if opcode not in self._opcode_costs:
            raise KeyError(f"Opcode '{opcode}' not found")
        return self._opcode_costs[opcode]

    def get_all_opcodes(self) -> list[str]:
        """
        Get list of all opcodes.
        """
        return list(self._opcode_costs.keys())

    def get_opcodes_by_gas_cost(self, cost_name: str) -> list[str]:
        """
        Get all opcodes using a specific gas cost constant.
        """
        return [
            opcode
            for opcode, cost in self._opcode_costs.items()
            if cost == cost_name
        ]

    def get_summary(self) -> Dict[str, list[str]]:
        """
        Get summary of all gas costs and their opcodes.
        """
        summary: Dict[str, list[str]] = {}
        for opcode, cost_name in self._opcode_costs.items():
            if cost_name not in summary:
                summary[cost_name] = []
            summary[cost_name].append(opcode)
        return summary

    def __repr__(self) -> str:
        """Return string representation."""
        num_opcodes = len(self._opcode_costs)
        num_constants = len(self._static_costs)
        return f"GasCosts({num_constants} constants, {num_opcodes} opcodes)"


G = GasCosts()
