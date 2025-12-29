"""Helpers for the benchmark tests."""

from enum import Enum, auto


class ParameterEnum(Enum):
    """Enum for parameters."""

    def __str__(self) -> str:
        """Return the name of the enum as a lowercase string."""
        return self.name.lower()


class StateAccess(ParameterEnum):
    """Enum for state access types."""

    WARM = True
    COLD = False


class StorageSize(ParameterEnum):
    """Enum for state sizes (contract code size)."""

    EMPTY = 0  # Just Created
    SMALL = 1024  # 1024 Bytes
    MEDIUM = 1024 * 12  # 12 KiB
    XEN = 1024 * 24  # 24 KiB


class StateSize(ParameterEnum):
    """Enum for storage sizes."""

    MAINNET = auto()
    BLOANET = auto()


class MemorySize(ParameterEnum):
    """Enum for memory sizes (args size for CALL operations)."""

    ZERO = 0
    SMALL = 32
    MEDIUM = 256
    LARGE = 1024
