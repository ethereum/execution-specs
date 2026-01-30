"""
Define the PayloadStatus type for Engine API responses.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ethereum.crypto.hash import Hash32


@dataclass
class PayloadStatus:
    """
    Represents the response format for Engine API payload validation.

    This follows the Engine API specification from execution-apis:
    https://github.com/ethereum/execution-apis
    """

    status: str
    latest_valid_hash: Optional[Hash32]
    validation_error: Optional[str]

    def to_json(self) -> Dict[str, Any]:
        """Encode the payload status to Engine API JSON format."""
        data: Dict[str, Any] = {
            "status": self.status,
            "latestValidHash": (
                "0x" + self.latest_valid_hash.hex()
                if self.latest_valid_hash is not None
                else None
            ),
            "validationError": self.validation_error,
        }
        return data

    @classmethod
    def valid(cls, block_hash: Hash32) -> "PayloadStatus":
        """Create a VALID payload status."""
        return cls(
            status="VALID",
            latest_valid_hash=block_hash,
            validation_error=None,
        )

    @classmethod
    def invalid(
        cls,
        error: str,
        latest_valid_hash: Optional[Hash32] = None,
    ) -> "PayloadStatus":
        """Create an INVALID payload status."""
        return cls(
            status="INVALID",
            latest_valid_hash=latest_valid_hash,
            validation_error=error,
        )
