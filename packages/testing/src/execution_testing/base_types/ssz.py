"""
Native SSZ serialization for base_types models.

Declare a container once as a pydantic class:SszModel, in the ordinary
base types, and get SSZ encoding,hash_tree_root, and defaults.

Each field's SSZ type is derived from its Python type, so the model stays the
single source of truth:

* fixed byte types self-describe by byte_length
  (Hash -> ByteVector[32],Address -> ByteVector[20]);
* the width ints defined here carry it (Uint64-> uint64);
* bool -> boolean;
* the only facts a Python type cannot express -- list / vector / bytelist / bit
  caps -- ride as Annotated markers (ssz_list, bitvector).
"""

from dataclasses import dataclass
from typing import Annotated, Any, ClassVar, List, Sequence, Type, TypeVar

from remerkleable.basic import (
    boolean,
    uint8,
    uint16,
    uint32,
    uint64,
    uint128,
    uint256,
)
from remerkleable.bitfields import Bitlist as RmkBitlist
from remerkleable.bitfields import Bitvector as RmkBitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList
from remerkleable.complex import Vector as RmkVector
from remerkleable.core import View
from remerkleable.progressive import (
    ProgressiveBitlist as RmkProgressiveBitlist,
)
from remerkleable.progressive import ProgressiveContainer
from remerkleable.progressive import ProgressiveList as RmkProgressiveList

from .base_types import Bytes, FixedSizeBytes, HexNumber
from .pydantic import CamelModel

_UINTS = {
    8: uint8,
    16: uint16,
    32: uint32,
    64: uint64,
    128: uint128,
    256: uint256,
}


class SszSpec:
    """How a field maps to SSZ. Pure data; no remerkleable dependency."""


@dataclass(frozen=True)
class SszUint(SszSpec):
    """An unsigned integer of bits width (8/16/32/64/128/256)."""

    bits: int


@dataclass(frozen=True)
class SszByteVector(SszSpec):
    """A fixed-length byte vector of length bytes."""

    length: int


@dataclass(frozen=True)
class SszByteList(SszSpec):
    """A variable byte list capped at limit bytes."""

    limit: int


@dataclass(frozen=True)
class SszList(SszSpec):
    """A list of element capped at limit items."""

    element: SszSpec
    limit: int


@dataclass(frozen=True)
class SszVector(SszSpec):
    """A fixed-length vector of exactly length element items."""

    element: SszSpec
    length: int


@dataclass(frozen=True)
class SszBitvector(SszSpec):
    """A fixed-length bit vector of length bits."""

    length: int


@dataclass(frozen=True)
class SszBitlist(SszSpec):
    """A variable bit list capped at limit bits."""

    limit: int


@dataclass(frozen=True)
class SszContainer(SszSpec):
    """A nested container backed by pydantic model."""

    model: Type["SszModel"]


@dataclass(frozen=True)
class SszProgressiveList(SszSpec):
    """An uncapped progressive list of element (EIP-7916)."""

    element: SszSpec


@dataclass(frozen=True)
class SszProgressiveBitlist(SszSpec):
    """An uncapped progressive bit list."""


@dataclass(frozen=True)
class SszProgressiveContainer(SszSpec):
    """A forward-compatible progressive container backed by model."""

    model: Type["SszModel"]


SSZ_BOOL = SszSpec()  # marker singleton for boolean fields

_M = TypeVar("_M", bound="SszModel")


class Uint8(HexNumber):
    """An 8-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(8)


class Uint16(HexNumber):
    """A 16-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(16)


class Uint32(HexNumber):
    """A 32-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(32)


class Uint64(HexNumber):
    """A 64-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(64)


class Uint128(HexNumber):
    """A 128-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(128)


class Uint256(HexNumber):
    """A 256-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(256)


class SszModel(CamelModel):
    """
    A pydantic model whose fields carry SSZ specs; encoded by this engine.

    Every field must resolve to an SszSpec; this is checked when the
    subclass is defined, so a mis-typed container fails at import, not at first
    encode.
    """

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Validate every field resolves to an SSZ spec at declaration time."""
        super().__pydantic_init_subclass__(**kwargs)
        for name in cls.model_fields:
            _spec_of(cls, name)  # raises TypeError if unmapped


class ProgressiveModel(SszModel):
    """
    A forward-compatible progressive container (built as a
    remerkleable.ProgressiveContainer).

    __active_fields__ is the active-field bitvector; it defaults to all
    fields active. Reserve inactive slots (0) to keep roots stable as new
    fields are appended later.
    """

    __active_fields__: ClassVar[Sequence[int]] = ()


def _spec_for_type(annotation: Any) -> SszSpec:
    """Derive the SSZ spec implied by a field's *type* (no annotation)."""
    ssz = getattr(annotation, "__ssz__", None)
    if isinstance(ssz, SszSpec):
        return ssz
    if isinstance(annotation, type):
        if issubclass(annotation, FixedSizeBytes):
            return SszByteVector(annotation.byte_length)
        if issubclass(annotation, ProgressiveModel):
            return SszProgressiveContainer(annotation)
        if issubclass(annotation, SszModel):
            return SszContainer(annotation)
        if annotation is bool:
            return SSZ_BOOL
    raise TypeError(f"no SSZ spec for type {annotation!r}")


def _spec_of(model_cls: Type["SszModel"], name: str) -> SszSpec:
    """The SSZ spec for a field: an Annotated marker, else its type."""
    field = model_cls.model_fields[name]
    for (
        meta
    ) in field.metadata:  # SszList / SszVector / SszBitlist / ... marker
        if isinstance(meta, SszSpec):
            return meta
    return _spec_for_type(field.annotation)


def _rmk_type(spec: SszSpec) -> Type[View]:
    if isinstance(spec, SszUint):
        return _UINTS[spec.bits]
    if isinstance(spec, SszByteVector):
        return ByteVector[spec.length]
    if isinstance(spec, SszByteList):
        return ByteList[spec.limit]
    if isinstance(spec, SszList):
        return RmkList[_rmk_type(spec.element), spec.limit]
    if isinstance(spec, SszVector):
        return RmkVector[_rmk_type(spec.element), spec.length]
    if isinstance(spec, SszBitvector):
        return RmkBitvector[spec.length]
    if isinstance(spec, SszBitlist):
        return RmkBitlist[spec.limit]
    if isinstance(spec, SszProgressiveList):
        return RmkProgressiveList[_rmk_type(spec.element)]
    if isinstance(spec, SszProgressiveBitlist):
        return RmkProgressiveBitlist
    if isinstance(spec, SszContainer):
        return ssz_container_for(spec.model)
    if isinstance(spec, SszProgressiveContainer):
        return ssz_container_for(spec.model)
    if spec is SSZ_BOOL:
        return boolean
    raise TypeError(f"unhandled spec {spec!r}")


def _active_fields(model_cls: Type["SszModel"]) -> Sequence[int]:
    declared = getattr(model_cls, "__active_fields__", ())
    return declared if declared else [1] * len(model_cls.model_fields)


def ssz_container_for(model_cls: Type["SszModel"]) -> Type[Container]:
    """Build a remerkleable container mirroring model_cls's fields."""
    anns = {
        name: _rmk_type(_spec_of(model_cls, name))
        for name in model_cls.model_fields
    }
    if issubclass(model_cls, ProgressiveModel):
        base: Any = ProgressiveContainer(
            active_fields=list(_active_fields(model_cls))
        )
    else:
        base = Container
    return type(model_cls.__name__, (base,), {"__annotations__": anns})


def _to_rmk(spec: SszSpec, value: Any) -> Any:
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return _rmk_instance(value)
    if isinstance(spec, (SszList, SszVector, SszProgressiveList)):
        return [_to_rmk(spec.element, v) for v in value]
    if isinstance(spec, (SszBitvector, SszBitlist, SszProgressiveBitlist)):
        return list(value)
    return value  # scalar / byte-vector / byte-list: remerkleable coerces


def _rmk_instance(model: "SszModel") -> Container:
    model_cls: Type[SszModel] = type(model)
    container = ssz_container_for(model_cls)
    values = {
        name: _to_rmk(_spec_of(model_cls, name), getattr(model, name))
        for name in model_cls.model_fields
    }
    return container(**values)


def _to_py(spec: SszSpec, value: Any) -> Any:
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return _view_to_model(spec.model, value)
    if isinstance(spec, (SszList, SszVector, SszProgressiveList)):
        return [_to_py(spec.element, v) for v in value]
    if isinstance(spec, (SszBitvector, SszBitlist, SszProgressiveBitlist)):
        return [bool(b) for b in value]
    if isinstance(spec, (SszByteVector, SszByteList)):
        return bytes(value)
    if isinstance(spec, SszUint):
        return int(value)
    if spec is SSZ_BOOL:
        return bool(value)
    raise TypeError(f"unhandled spec {spec!r}")


def _view_to_model(model_cls: Type[_M], view: Container) -> _M:
    return model_cls(
        **{
            name: _to_py(_spec_of(model_cls, name), getattr(view, name))
            for name in model_cls.model_fields
        }
    )


def default_value(spec: SszSpec) -> Any:
    """Return the SSZ default (zero) value for spec as a pydantic value."""
    if isinstance(spec, SszUint):
        return 0
    if isinstance(spec, SszByteVector):
        return b"\x00" * spec.length
    if isinstance(
        spec, (SszByteList, SszList, SszBitlist, SszProgressiveList)
    ):
        return []
    if isinstance(spec, SszProgressiveBitlist):
        return []
    if isinstance(spec, SszVector):
        return [default_value(spec.element)] * spec.length
    if isinstance(spec, SszBitvector):
        return [False] * spec.length
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return ssz_default(spec.model)
    if spec is SSZ_BOOL:
        return False
    raise TypeError(f"no default for spec {spec!r}")


def ssz_default(model_cls: Type[_M]) -> _M:
    """Build the SSZ default (all-zero) instance of model_cls."""
    return model_cls(
        **{
            name: default_value(_spec_of(model_cls, name))
            for name in model_cls.model_fields
        }
    )


def encode(model: "SszModel") -> bytes:
    """Return the SSZ wire bytes of model."""
    return _rmk_instance(model).encode_bytes()


def hash_tree_root(model: "SszModel") -> bytes:
    """Return the 32-byte SSZ hash_tree_root of model."""
    return bytes(_rmk_instance(model).hash_tree_root())


def decode(model_cls: Type[_M], data: bytes) -> _M:
    """Decode SSZ data into an instance of model_cls."""
    view = ssz_container_for(model_cls).decode_bytes(data)
    return _view_to_model(model_cls, view)


def byte_list(limit: int) -> SszByteList:
    """Annotate a Bytes field as a capped SSZ byte list."""
    return SszByteList(limit)


def ssz_list(element: SszSpec, limit: int) -> SszList:
    """Annotate a list[...] field as a capped SSZ list."""
    return SszList(element, limit)


def ssz_vector(element: SszSpec, length: int) -> SszVector:
    """Annotate a list[...] field as a fixed-length SSZ vector."""
    return SszVector(element, length)


def bitvector(length: int) -> SszBitvector:
    """Annotate a list[bool] field as a fixed SSZ bit vector."""
    return SszBitvector(length)


def bitlist(limit: int) -> SszBitlist:
    """Annotate a list[bool] field as a capped SSZ bit list."""
    return SszBitlist(limit)


def progressive_list(element: SszSpec) -> SszProgressiveList:
    """Annotate a list[...] field as an uncapped progressive list."""
    return SszProgressiveList(element)


def progressive_bitlist() -> SszProgressiveBitlist:
    """Annotate a list[bool] field as an uncapped progressive bit list."""
    return SszProgressiveBitlist()


# referenced only via annotations / re-export
_ = (Annotated, List, Bytes)

__all__ = [
    "ProgressiveModel",
    "SszBitlist",
    "SszBitvector",
    "SszByteList",
    "SszByteVector",
    "SszContainer",
    "SszList",
    "SszModel",
    "SszProgressiveBitlist",
    "SszProgressiveContainer",
    "SszProgressiveList",
    "SszSpec",
    "SszUint",
    "SszVector",
    "Uint128",
    "Uint16",
    "Uint256",
    "Uint32",
    "Uint64",
    "Uint8",
    "bitlist",
    "bitvector",
    "byte_list",
    "decode",
    "default_value",
    "encode",
    "hash_tree_root",
    "progressive_bitlist",
    "progressive_list",
    "ssz_container_for",
    "ssz_default",
    "ssz_list",
    "ssz_vector",
]
