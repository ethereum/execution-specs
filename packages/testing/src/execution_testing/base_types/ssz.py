"""
Native SSZ serialization for base_types models.

Declare a container once as a pydantic SszModel, in the ordinary base types,
and get SSZ encoding, hash_tree_root, and defaults for them.

Each field's SSZ type is derived from its Python type, so the model stays the
single source of truth:

* fixed byte types self-describe by byte_length
  (Hash -> ByteVector[32], Address -> ByteVector[20]);
* the width ints defined here carry it (Uint64 -> uint64);
* bool -> boolean; a nested SszModel -> Container;
* the only facts a Python type cannot express -- list / vector / bytelist / bit
  caps -- ride as Annotated markers (ssz_list(N), ssz_vector(N), byte_list(N),
  bitvector(N), bitlist(N)). Element types are derived from the annotation, so
  a marker carries only the cap/length, never a duplicated element spec.

Each field's SSZ type is described by an SszType value (SszUint, SszByteList,
SszList, SszContainer, ...). The engine turns that into a remerkleable type
on demand (build_ssz_type) and delegates the actual encoding, merkleization,
and default (zero) values to it.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import (
    Any,
    ClassVar,
    List,
    Sequence,
    Type,
    TypeVar,
    get_args,
    get_origin,
)

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


class SszType:
    """A description of a field's SSZ type."""


@dataclass(frozen=True)
class SszUint(SszType):
    """An unsigned integer of bits width (8/16/32/64/128/256)."""

    bits: int


@dataclass(frozen=True)
class SszByteVector(SszType):
    """A fixed-length byte vector of length bytes."""

    length: int


@dataclass(frozen=True)
class SszByteList(SszType):
    """A variable byte list capped at limit bytes."""

    limit: int


@dataclass(frozen=True)
class SszList(SszType):
    """A list of element capped at limit items."""

    element: SszType
    limit: int


@dataclass(frozen=True)
class SszVector(SszType):
    """A fixed-length vector of exactly length element items."""

    element: SszType
    length: int


@dataclass(frozen=True)
class SszBitvector(SszType):
    """A fixed-length bit vector of length bits."""

    length: int


@dataclass(frozen=True)
class SszBitlist(SszType):
    """A variable bit list capped at limit bits."""

    limit: int


@dataclass(frozen=True)
class SszBool(SszType):
    """The SSZ boolean type."""


@dataclass(frozen=True)
class SszContainer(SszType):
    """A nested container backed by pydantic model."""

    model: Type["SszModel"]


@dataclass(frozen=True)
class SszProgressiveList(SszType):
    """An uncapped progressive list of element (EIP-7916)."""

    element: SszType


@dataclass(frozen=True)
class SszProgressiveBitlist(SszType):
    """An uncapped progressive bit list."""


@dataclass(frozen=True)
class SszProgressiveContainer(SszType):
    """A forward-compatible progressive container backed by model."""

    model: Type["SszModel"]


_M = TypeVar("_M", bound="SszModel")


# Annotated markers: carry ONLY the cap/length; the element is derived from the
# field's Python annotation by spec_of, so nothing is declared twice.
class _Marker:
    """Base for cap-only Annotated markers resolved by spec_of."""


@dataclass(frozen=True)
class _ListCap(_Marker):
    limit: int


@dataclass(frozen=True)
class _VectorLen(_Marker):
    length: int


@dataclass(frozen=True)
class _ProgressiveListMark(_Marker):
    pass


def byte_list(limit: int) -> SszByteList:
    """Annotate a Bytes field as a capped SSZ byte list."""
    return SszByteList(limit)


def ssz_list(limit: int) -> _ListCap:
    """Annotate a list[...] field as a capped SSZ list (element derived)."""
    return _ListCap(limit)


def ssz_vector(length: int) -> _VectorLen:
    """Annotate a list[...] field as a fixed SSZ vector (element derived)."""
    return _VectorLen(length)


def bitvector(length: int) -> SszBitvector:
    """Annotate a list[bool] field as a fixed SSZ bit vector."""
    return SszBitvector(length)


def bitlist(limit: int) -> SszBitlist:
    """Annotate a list[bool] field as a capped SSZ bit list."""
    return SszBitlist(limit)


def progressive_list() -> _ProgressiveListMark:
    """Annotate a list[...] field as an uncapped progressive list."""
    return _ProgressiveListMark()


def progressive_bitlist() -> SszProgressiveBitlist:
    """Annotate a list[bool] field as an uncapped progressive bit list."""
    return SszProgressiveBitlist()


class SszModel(CamelModel):
    """
    A pydantic model whose fields carry SSZ types.

    Every field must resolve to an SszType, and each Annotated marker must be
    consistent with the field's Python type; both are checked when the subclass
    is defined, so a mis-typed container fails at import, not at first encode.
    """

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Validate every field resolves to a consistent SSZ type."""
        super().__pydantic_init_subclass__(**kwargs)
        for name in cls.model_fields:
            spec_of(cls, name)  # raises TypeError on unmapped/inconsistent


class ProgressiveModel(SszModel):
    """
    A forward-compatible progressive container (a remerkleable
    ProgressiveContainer).

    __active_fields__ is the active-field bitvector; it defaults to all fields
    active. A 0 marks a reserved gap with no declared field, so new fields can
    be slotted in later without shifting existing roots -- the declared fields
    fill the 1 positions in order. The number of 1s, when set, must equal the
    declared field count.
    """

    __active_fields__: ClassVar[Sequence[int]] = ()

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Check the active-field bitvector agrees with the field count."""
        super().__pydantic_init_subclass__(**kwargs)
        active = cls.__active_fields__
        if active and sum(active) != len(cls.model_fields):
            raise TypeError(
                f"{cls.__name__}.__active_fields__ has {sum(active)} active "
                f"entries but the container declares "
                f"{len(cls.model_fields)} fields"
            )


def _marker_in(metadata: Any) -> Any:
    """The first SSZ marker (SszType or cap-only _Marker) in metadata."""
    return next(
        (m for m in metadata if isinstance(m, (SszType, _Marker))), None
    )


def _spec_for_type_bare(annotation: Any) -> SszType:
    """Derive the SSZ type of a plain Python type."""
    ssz = getattr(annotation, "__ssz__", None)
    if isinstance(ssz, SszType):
        return ssz
    if isinstance(annotation, type):
        if issubclass(annotation, FixedSizeBytes):
            return SszByteVector(annotation.byte_length)
        if issubclass(annotation, ProgressiveModel):
            return SszProgressiveContainer(annotation)
        if issubclass(annotation, SszModel):
            return SszContainer(annotation)
        if annotation is bool:
            return SszBool()
    raise TypeError(f"no SSZ type for {annotation!r}")


def _spec_for_type(annotation: Any) -> SszType:
    """Resolve an SSZ type, honoring an inner Annotated marker if present."""
    meta = getattr(annotation, "__metadata__", None)
    if meta is not None:
        return _resolve(_marker_in(meta), annotation.__origin__)
    return _spec_for_type_bare(annotation)


def _element_of(annotation: Any, ctx: str) -> SszType:
    """Resolve the element SSZ type of a list[...] annotation."""
    if get_origin(annotation) not in (list, List):
        raise TypeError(f"{ctx} requires a list[...] field: {annotation!r}")
    args = get_args(annotation)
    if len(args) != 1:
        raise TypeError(f"{ctx} needs a single list element type")
    return _spec_for_type(args[0])


def _resolve(marker: Any, annotation: Any) -> SszType:
    """
    Resolve a field/element into an SSZ type.

    Cap-only markers (ssz_list/ssz_vector/progressive_list) derive their
    element from the annotation; complete markers (byte_list/bitvector/...)
    are checked for consistency with it. Byte-list elements are expressed as
    Annotated[Bytes, byte_list(N)] so the inner cap lives on the element.
    """
    if marker is None:
        return _spec_for_type(annotation)
    if isinstance(marker, _ListCap):
        return SszList(_element_of(annotation, "ssz_list"), marker.limit)
    if isinstance(marker, _VectorLen):
        return SszVector(_element_of(annotation, "ssz_vector"), marker.length)
    if isinstance(marker, _ProgressiveListMark):
        return SszProgressiveList(_element_of(annotation, "progressive_list"))
    if isinstance(marker, SszByteList):
        is_bytes = isinstance(annotation, type) and issubclass(
            annotation, Bytes
        )
        if not is_bytes:
            raise TypeError(
                f"byte_list requires a Bytes field/element: {annotation!r}"
            )
        return marker
    if isinstance(marker, (SszBitvector, SszBitlist, SszProgressiveBitlist)):
        if not isinstance(_element_of(annotation, "bit markers"), SszBool):
            raise TypeError(
                f"bit markers require a list[bool] field: {annotation!r}"
            )
        return marker
    return marker  # any other complete SszType marker


@lru_cache(maxsize=None)
def spec_of(model_cls: Type["SszModel"], name: str) -> SszType:
    """
    The resolved SSZ type of a field.

    An Annotated marker takes precedence over the bare type; cap-only markers
    derive their element from the annotation, and every marker is checked for
    consistency with it. Cached per (model_cls, name).
    """
    field = model_cls.model_fields[name]
    return _resolve(_marker_in(field.metadata), field.annotation)


def _rmk_type(spec: SszType) -> Type[View]:
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
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return build_ssz_type(spec.model)
    if isinstance(spec, SszBool):
        return boolean
    raise TypeError(f"unhandled SSZ type {spec!r}")


def _active_fields(model_cls: Type["SszModel"]) -> Sequence[int]:
    declared = getattr(model_cls, "__active_fields__", ())
    return declared if declared else [1] * len(model_cls.model_fields)


@lru_cache(maxsize=None)
def build_ssz_type(model_cls: Type["SszModel"]) -> Type[Container]:
    """
    Build (and cache) the remerkleable container type mirroring model_cls.

    Cached per class object -- distinct same-named models get distinct types.
    """
    anns = {
        name: _rmk_type(spec_of(model_cls, name))
        for name in model_cls.model_fields
    }
    if issubclass(model_cls, ProgressiveModel):
        base: Any = ProgressiveContainer(
            active_fields=list(_active_fields(model_cls))
        )
    else:
        base = Container
    return type(model_cls.__name__, (base,), {"__annotations__": anns})


def _to_rmk(spec: SszType, value: Any) -> Any:
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return _rmk_instance(value)
    if isinstance(spec, (SszList, SszVector, SszProgressiveList)):
        return [_to_rmk(spec.element, v) for v in value]
    if isinstance(spec, (SszBitvector, SszBitlist, SszProgressiveBitlist)):
        return list(value)
    return value  # scalar / byte-vector / byte-list: remerkleable coerces


def _rmk_instance(model: "SszModel") -> Container:
    model_cls: Type[SszModel] = type(model)
    container = build_ssz_type(model_cls)
    values = {
        name: _to_rmk(spec_of(model_cls, name), getattr(model, name))
        for name in model_cls.model_fields
    }
    return container(**values)


def _to_py(spec: SszType, value: Any) -> Any:
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
    if isinstance(spec, SszBool):
        return bool(value)
    raise TypeError(f"unhandled SSZ type {spec!r}")


def _view_to_model(model_cls: Type[_M], view: Container) -> _M:
    return model_cls(
        **{
            name: _to_py(spec_of(model_cls, name), getattr(view, name))
            for name in model_cls.model_fields
        }
    )


def default_value(spec: SszType) -> Any:
    """Return the SSZ default (zero) value for spec as a pydantic value."""
    if isinstance(spec, SszUint):
        return 0
    if isinstance(spec, SszByteVector):
        return b"\x00" * spec.length
    if isinstance(
        spec,
        (SszByteList, SszList, SszBitlist, SszProgressiveList),
    ):
        return []
    if isinstance(spec, SszProgressiveBitlist):
        return []
    if isinstance(spec, SszVector):
        # A fresh value per slot: container defaults are mutable, so a shared
        # [x] * n would alias one instance across every position.
        return [default_value(spec.element) for _ in range(spec.length)]
    if isinstance(spec, SszBitvector):
        return [False] * spec.length
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return ssz_default(spec.model)
    if isinstance(spec, SszBool):
        return False
    raise TypeError(f"no default for SSZ type {spec!r}")


def ssz_default(model_cls: Type[_M]) -> _M:
    """Build the SSZ default (all-zero) instance of model_cls."""
    return model_cls(
        **{
            name: default_value(spec_of(model_cls, name))
            for name in model_cls.model_fields
        }
    )


def describe_type(spec: SszType) -> str:
    """Render an SSZ type as consensus-style text (uint64, List[T, N], ...)."""
    if isinstance(spec, SszUint):
        return f"uint{spec.bits}"
    if isinstance(spec, SszByteVector):
        return f"ByteVector[{spec.length}]"
    if isinstance(spec, SszByteList):
        return f"ByteList[{spec.limit}]"
    if isinstance(spec, SszList):
        return f"List[{describe_type(spec.element)}, {spec.limit}]"
    if isinstance(spec, SszVector):
        return f"Vector[{describe_type(spec.element)}, {spec.length}]"
    if isinstance(spec, SszBitvector):
        return f"Bitvector[{spec.length}]"
    if isinstance(spec, SszBitlist):
        return f"Bitlist[{spec.limit}]"
    if isinstance(spec, SszProgressiveList):
        return f"ProgressiveList[{describe_type(spec.element)}]"
    if isinstance(spec, SszProgressiveBitlist):
        return "ProgressiveBitlist"
    if isinstance(spec, SszContainer):
        return spec.model.__name__
    if isinstance(spec, SszProgressiveContainer):
        return f"Progressive[{spec.model.__name__}]"
    if isinstance(spec, SszBool):
        return "boolean"
    raise TypeError(f"unhandled SSZ type {spec!r}")


def describe_schema(model_cls: Type["SszModel"]) -> str:
    """Render model_cls's resolved SSZ schema, one 'field: type' per line."""
    lines = [f"{model_cls.__name__}:"]
    for name in model_cls.model_fields:
        lines.append(f"    {name}: {describe_type(spec_of(model_cls, name))}")
    return "\n".join(lines)


def encode(model: "SszModel") -> bytes:
    """Return the SSZ wire bytes of model."""
    return _rmk_instance(model).encode_bytes()


def hash_tree_root(model: "SszModel") -> bytes:
    """Return the 32-byte SSZ hash_tree_root of model."""
    return bytes(_rmk_instance(model).hash_tree_root())


def decode(model_cls: Type[_M], data: bytes) -> _M:
    """Decode SSZ data into an instance of model_cls."""
    view = build_ssz_type(model_cls).decode_bytes(data)
    return _view_to_model(model_cls, view)


__all__ = [
    "ProgressiveModel",
    "SszBitlist",
    "SszBitvector",
    "SszBool",
    "SszByteList",
    "SszByteVector",
    "SszContainer",
    "SszList",
    "SszModel",
    "SszProgressiveBitlist",
    "SszProgressiveContainer",
    "SszProgressiveList",
    "SszType",
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
    "build_ssz_type",
    "decode",
    "default_value",
    "describe_schema",
    "describe_type",
    "encode",
    "hash_tree_root",
    "progressive_bitlist",
    "progressive_list",
    "spec_of",
    "ssz_default",
    "ssz_list",
    "ssz_vector",
]


# width-carrying integer types (base_types.HexNumber underneath)
class Uint8(HexNumber):
    """An 8-bit unsigned integer."""

    __ssz__: ClassVar[SszType] = SszUint(8)


class Uint16(HexNumber):
    """A 16-bit unsigned integer."""

    __ssz__: ClassVar[SszType] = SszUint(16)


class Uint32(HexNumber):
    """A 32-bit unsigned integer."""

    __ssz__: ClassVar[SszType] = SszUint(32)


class Uint64(HexNumber):
    """A 64-bit unsigned integer."""

    __ssz__: ClassVar[SszType] = SszUint(64)


class Uint128(HexNumber):
    """A 128-bit unsigned integer."""

    __ssz__: ClassVar[SszType] = SszUint(128)


class Uint256(HexNumber):
    """A 256-bit unsigned integer."""

    __ssz__: ClassVar[SszType] = SszUint(256)
