"""
SSZ support for ``base_types``: declare a container once, get SSZ for free.

A container is written as a normal pydantic model (subclass :class:`SszModel`)
using the ordinary base types (``Hash``/``Address``/``Bytes`` ...) plus the
width-carrying integer types (``Uint64`` ...) defined here. Each field's SSZ
schema is then *derived*:

* every ``FixedSizeBytes`` subtype self-describes by its ``byte_length``
  (``Hash`` -> ``ByteVector[32]``, ``Address`` -> ``ByteVector[20]`` ...),
* integers carry their width (``Uint64`` -> ``uint64``),
* ``bool`` -> ``boolean``, nested :class:`SszModel` -> ``Container``,
* the only genuinely SSZ-only facts -- list/bytelist/bitvector caps -- ride as
  ``Annotated`` markers on the single declaration.

The engine reads that schema, builds a ``remerkleable`` container dynamically,
and delegates the actual wire encoding + ``hash_tree_root`` to it. This module
is the one place ``remerkleable`` is imported; nothing re-implements SSZ.
"""

from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    ClassVar,
    List,
    Type,
    TypeVar,
    get_args,
    get_origin,
)

from remerkleable.basic import boolean, uint8, uint64, uint256
from remerkleable.bitfields import Bitvector as RmkBitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList
from remerkleable.core import View

from .base_types import Bytes, FixedSizeBytes, HexNumber
from .pydantic import CamelModel


# --------------------------------------------------------------------------- #
# SSZ schema descriptors (pure data)
# --------------------------------------------------------------------------- #
class SszSpec:
    """How a field maps to SSZ. Pure data; no remerkleable dependency."""


@dataclass(frozen=True)
class SszUint(SszSpec):
    """An unsigned integer of ``bits`` width."""

    bits: int


@dataclass(frozen=True)
class SszByteVector(SszSpec):
    """A fixed-length byte vector of ``length`` bytes."""

    length: int


@dataclass(frozen=True)
class SszByteList(SszSpec):
    """A variable byte list capped at ``limit`` bytes."""

    limit: int


@dataclass(frozen=True)
class SszList(SszSpec):
    """A list of ``element`` capped at ``limit`` items."""

    element: SszSpec
    limit: int


@dataclass(frozen=True)
class SszBitvector(SszSpec):
    """A fixed-length bit vector of ``length`` bits."""

    length: int


@dataclass(frozen=True)
class SszContainer(SszSpec):
    """A nested container backed by pydantic ``model``."""

    model: Type["SszModel"]


SSZ_BOOL = SszSpec()  # marker singleton for boolean fields

_M = TypeVar("_M", bound="SszModel")


# --------------------------------------------------------------------------- #
# Width-carrying integer types (base_types.HexNumber underneath)
# --------------------------------------------------------------------------- #
class Uint8(HexNumber):
    """An 8-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(8)


class Uint64(HexNumber):
    """A 64-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(64)


class Uint256(HexNumber):
    """A 256-bit unsigned integer."""

    __ssz__: ClassVar[SszSpec] = SszUint(256)


class SszModel(CamelModel):
    """A pydantic model whose fields carry SSZ specs; encoded by the engine."""


# --------------------------------------------------------------------------- #
# reading the SSZ spec off a model field
# --------------------------------------------------------------------------- #
def _spec_for_type(annotation: Any) -> SszSpec:
    """Derive the SSZ spec implied by a field's *type* (no annotation)."""
    ssz = getattr(annotation, "__ssz__", None)
    if isinstance(ssz, SszSpec):
        return ssz
    if isinstance(annotation, type):
        if issubclass(annotation, FixedSizeBytes):
            return SszByteVector(annotation.byte_length)
        if issubclass(annotation, SszModel):
            return SszContainer(annotation)
        if annotation is bool:
            return SSZ_BOOL
    raise TypeError(f"no SSZ spec for type {annotation!r}")


def _spec_of(model_cls: Type["SszModel"], name: str) -> SszSpec:
    """The SSZ spec for a field: an ``Annotated`` marker, else its type."""
    field = model_cls.model_fields[name]
    for meta in field.metadata:  # SszList / SszByteList / SszBitvector markers
        if isinstance(meta, SszSpec):
            return meta
    return _spec_for_type(field.annotation)


# --------------------------------------------------------------------------- #
# spec -> remerkleable type
# --------------------------------------------------------------------------- #
def _rmk_type(spec: SszSpec) -> Type[View]:
    if isinstance(spec, SszUint):
        return {8: uint8, 64: uint64, 256: uint256}[spec.bits]
    if isinstance(spec, SszByteVector):
        return ByteVector[spec.length]
    if isinstance(spec, SszByteList):
        return ByteList[spec.limit]
    if isinstance(spec, SszList):
        return RmkList[_rmk_type(spec.element), spec.limit]
    if isinstance(spec, SszBitvector):
        return RmkBitvector[spec.length]
    if isinstance(spec, SszContainer):
        return ssz_container_for(spec.model)
    if spec is SSZ_BOOL:
        return boolean
    raise TypeError(f"unhandled spec {spec!r}")


def ssz_container_for(model_cls: Type["SszModel"]) -> Type[Container]:
    """Build a remerkleable ``Container`` mirroring ``model_cls``'s fields."""
    anns = {
        name: _rmk_type(_spec_of(model_cls, name))
        for name in model_cls.model_fields
    }
    return type(model_cls.__name__, (Container,), {"__annotations__": anns})


# --------------------------------------------------------------------------- #
# value conversion (pydantic <-> remerkleable)
# --------------------------------------------------------------------------- #
def _to_rmk(spec: SszSpec, value: Any) -> Any:
    if isinstance(spec, SszContainer):
        return _rmk_instance(value)
    if isinstance(spec, SszList):
        return [_to_rmk(spec.element, v) for v in value]
    if isinstance(spec, SszBitvector):
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
    if isinstance(spec, SszContainer):
        return _view_to_model(spec.model, value)
    if isinstance(spec, SszList):
        return [_to_py(spec.element, v) for v in value]
    if isinstance(spec, SszBitvector):
        return [bool(value[i]) for i in range(spec.length)]
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


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
def encode(model: "SszModel") -> bytes:
    """Return the SSZ wire bytes of ``model``."""
    return _rmk_instance(model).encode_bytes()


def hash_tree_root(model: "SszModel") -> bytes:
    """Return the 32-byte SSZ ``hash_tree_root`` of ``model``."""
    return bytes(_rmk_instance(model).hash_tree_root())


def decode(model_cls: Type[_M], data: bytes) -> _M:
    """Decode SSZ ``data`` into an instance of ``model_cls``."""
    view = ssz_container_for(model_cls).decode_bytes(data)
    return _view_to_model(model_cls, view)


# --------------------------------------------------------------------------- #
# annotation helpers (for the SSZ-only facts: caps)
# --------------------------------------------------------------------------- #
def byte_list(limit: int) -> SszByteList:
    """Annotate a ``Bytes`` field as a capped SSZ byte list."""
    return SszByteList(limit)


def ssz_list(element: SszSpec, limit: int) -> SszList:
    """Annotate a ``list[...]`` field as a capped SSZ list."""
    return SszList(element, limit)


def bitvector(length: int) -> SszBitvector:
    """Annotate a ``list[bool]`` field as a fixed SSZ bit vector."""
    return SszBitvector(length)


# used only via annotations / re-export; keep the linters informed
_ = (Annotated, List, Bytes, get_args, get_origin)

__all__ = [
    "SszBitvector",
    "SszByteList",
    "SszByteVector",
    "SszContainer",
    "SszList",
    "SszModel",
    "SszSpec",
    "SszUint",
    "Uint256",
    "Uint64",
    "Uint8",
    "bitvector",
    "byte_list",
    "decode",
    "encode",
    "hash_tree_root",
    "ssz_container_for",
    "ssz_list",
]
