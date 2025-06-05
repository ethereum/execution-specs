"""
Defines the serialization and deserialization format used throughout Ethereum.
"""

from .rlp import (  # noqa: F401
    RLP,
    Extended,
    Simple,
    With,
    decode,
    decode_to,
    encode,
)

__version__ = "0.1.3"
