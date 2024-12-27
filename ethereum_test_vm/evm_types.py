"""EVM types definitions."""

from enum import Enum


class EVMCodeType(str, Enum):
    """Enum representing the type of EVM code that is supported in a given fork."""

    LEGACY = "legacy"
    EOF_V1 = "eof_v1"

    def __str__(self) -> str:
        """Return the name of the EVM code type."""
        return self.name
