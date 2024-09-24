"""
Common definitions and types.
"""

from .base_types import (
    Address,
    Bloom,
    BLSPublicKey,
    BLSSignature,
    Bytes,
    FixedSizeBytes,
    Hash,
    HashInt,
    HeaderNonce,
    HexNumber,
    Number,
    NumberBoundTypeVar,
    Wei,
    ZeroPaddedHexNumber,
)
from .composite_types import Account, Alloc, Storage, StorageRootType
from .constants import (
    AddrAA,
    AddrBB,
    EmptyOmmersRoot,
    EmptyTrieRoot,
    TestAddress,
    TestAddress2,
    TestPrivateKey,
    TestPrivateKey2,
)
from .conversions import to_bytes, to_hex
from .json import to_json
from .pydantic import CamelModel
from .reference_spec import ReferenceSpec

__all__ = (
    "Account",
    "AddrAA",
    "AddrBB",
    "Address",
    "Alloc",
    "Bloom",
    "BLSPublicKey",
    "BLSSignature",
    "Bytes",
    "CamelModel",
    "EmptyOmmersRoot",
    "EmptyTrieRoot",
    "FixedSizeBytes",
    "Hash",
    "HashInt",
    "HeaderNonce",
    "HexNumber",
    "Number",
    "NumberBoundTypeVar",
    "ReferenceSpec",
    "Storage",
    "StorageRootType",
    "TestAddress",
    "TestAddress2",
    "TestPrivateKey",
    "TestPrivateKey2",
    "Wei",
    "ZeroPaddedHexNumber",
    "to_bytes",
    "to_hex",
    "to_json",
)
