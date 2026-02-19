"""Base classes for the EVM."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol


class OpcodeBase:
    """Base class for the opcode type."""

    metadata: Dict[str, Any]
    _name_: str = ""

    def __bytes__(self) -> bytes:
        """Return the opcode byte representation."""
        raise NotImplementedError("OpcodeBase does not implement __bytes__")


class OpcodeGasCalculator(Protocol):
    """
    A protocol to calculate the cost or refund of a single opcode.
    """

    def __call__(self, opcode: OpcodeBase) -> int:
        """Return the gas cost or refund for executing the given opcode."""
        pass


class ForkOpcodeInterface(ABC):
    """
    Interface for a fork that is used to calculate opcode gas costs
    and refunds.
    """

    @classmethod
    @abstractmethod
    def opcode_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas cost of a single opcode.
        """
        pass

    @classmethod
    @abstractmethod
    def opcode_refund_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas refund of a single opcode.
        """
        pass
