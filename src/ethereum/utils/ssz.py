"""
Serialize specification dataclasses with SSZ while retaining Python types.
"""

from dataclasses import dataclass, fields
from typing import (
    Annotated,
    Any,
    Dict,
    Tuple,
    Type,
    TypeVar,
    final,
    get_args,
    get_origin,
    get_type_hints,
)

from ethereum_types.bytes import FixedBytes
from ethereum_types.numeric import FixedUnsigned, Unsigned
from remerkleable import basic as rmk_basic
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList
from remerkleable.progressive import (
    ProgressiveByteList,
    ProgressiveContainer,
    ProgressiveList,
)


class _SszType:
    pass


@final
@dataclass(frozen=True)
class _Uint(_SszType):
    bits: int


@final
@dataclass(frozen=True)
class _ByteVector(_SszType):
    length: int


@final
@dataclass(frozen=True)
class _ByteList(_SszType):
    limit: int


@final
@dataclass(frozen=True)
class _List(_SszType):
    element: _SszType
    limit: int


@final
@dataclass(frozen=True)
class _ProgressiveList(_SszType):
    element: _SszType


@final
@dataclass(frozen=True)
class _Container(_SszType):
    model: Any


class _Bool(_SszType):
    pass


class _ProgressiveByteList(_SszType):
    pass


@final
@dataclass(frozen=True)
class _ListLimit:
    limit: int


class _ProgressiveListMarker:
    pass


def uint(bits: int) -> _Uint:
    """Mark an unsigned integer field with its SSZ bit width."""
    if bits not in (8, 16, 32, 64, 128, 256):
        raise ValueError(f"Unsupported SSZ integer width: {bits}")
    return _Uint(bits)


def byte_vector(length: int) -> _ByteVector:
    """Mark a byte field as a fixed-length SSZ byte vector."""
    return _ByteVector(length)


def byte_list(limit: int) -> _ByteList:
    """Mark a byte field as a bounded SSZ byte list."""
    return _ByteList(limit)


def ssz_list(limit: int) -> _ListLimit:
    """Mark a collection field as a bounded SSZ list."""
    return _ListLimit(limit)


def progressive_list() -> _ProgressiveListMarker:
    """Mark a collection field as an SSZ progressive list."""
    return _ProgressiveListMarker()


def progressive_byte_list() -> _ProgressiveByteList:
    """Mark a byte field as an SSZ progressive byte list."""
    return _ProgressiveByteList()


_C = TypeVar("_C", bound="SszContainer")


class SszContainer:
    """Provide SSZ operations for a specification dataclass."""

    def encode_bytes(self) -> bytes:
        """Encode this dataclass as SSZ bytes."""
        return _to_view(self).encode_bytes()

    def hash_tree_root(self) -> bytes:
        """Return the SSZ hash-tree root of this dataclass."""
        return bytes(_to_view(self).hash_tree_root())

    @classmethod
    def decode_bytes(cls: Type[_C], data: bytes) -> _C:
        """Decode SSZ bytes into this dataclass type."""
        view = _container_type(cls).decode_bytes(data)
        return _from_view(cls, view)


class ProgressiveSszContainer(SszContainer):
    """Identify a dataclass encoded as an SSZ progressive container."""


def _annotated(annotation: Any) -> Tuple[Any, Any]:
    if get_origin(annotation) is not Annotated:
        return annotation, None
    base, *metadata = get_args(annotation)
    markers = [
        item
        for item in metadata
        if isinstance(item, (_SszType, _ListLimit, _ProgressiveListMarker))
    ]
    if len(markers) != 1:
        raise TypeError(
            f"Annotated SSZ field requires exactly one marker: {annotation!r}"
        )
    return base, markers[0]


def _collection_element(annotation: Any) -> Any:
    base, _ = _annotated(annotation)
    args = get_args(base)
    if get_origin(base) is not tuple or (
        len(args) != 2 or args[1] is not Ellipsis
    ):
        raise TypeError(f"SSZ tuple must have one repeated type: {base!r}")
    return args[0]


def _infer(annotation: Any) -> _SszType:
    base, marker = _annotated(annotation)
    if isinstance(marker, _ListLimit):
        return _List(_infer(_collection_element(base)), marker.limit)
    if isinstance(marker, _ProgressiveListMarker):
        return _ProgressiveList(_infer(_collection_element(base)))
    if isinstance(marker, _SszType):
        if isinstance(marker, _Uint):
            if not isinstance(base, type) or not issubclass(base, Unsigned):
                raise TypeError(f"SSZ uint requires Unsigned: {base!r}")
        elif isinstance(
            marker, (_ByteVector, _ByteList, _ProgressiveByteList)
        ):
            if not isinstance(base, type) or not issubclass(base, bytes):
                raise TypeError(f"SSZ byte type requires bytes: {base!r}")
        return marker

    if base is bool:
        return _Bool()
    if isinstance(base, type):
        if issubclass(base, FixedBytes):
            return _ByteVector(base.LENGTH)
        if issubclass(base, FixedUnsigned):
            return _Uint(int(base.MAX_VALUE).bit_length())
        if issubclass(base, SszContainer):
            return _Container(base)
    raise TypeError(f"Cannot infer an SSZ type for {base!r}")


def _rmk_type(ssz_type: _SszType) -> Any:
    if isinstance(ssz_type, _Uint):
        return getattr(rmk_basic, f"uint{ssz_type.bits}")
    if isinstance(ssz_type, _ByteVector):
        return ByteVector[ssz_type.length]
    if isinstance(ssz_type, _ByteList):
        return ByteList[ssz_type.limit]
    if isinstance(ssz_type, _List):
        return RmkList[_rmk_type(ssz_type.element), ssz_type.limit]
    if isinstance(ssz_type, _ProgressiveList):
        return ProgressiveList[_rmk_type(ssz_type.element)]
    if isinstance(ssz_type, _ProgressiveByteList):
        return ProgressiveByteList
    if isinstance(ssz_type, _Container):
        return _container_type(ssz_type.model)
    if isinstance(ssz_type, _Bool):
        return rmk_basic.boolean
    raise TypeError(f"Unsupported SSZ type: {ssz_type!r}")


_FIELD_TYPES: Dict[Any, Tuple[Tuple[str, Any], ...]] = {}


def _field_types(model: Any) -> Tuple[Tuple[str, Any], ...]:
    if model in _FIELD_TYPES:
        return _FIELD_TYPES[model]
    hints = get_type_hints(model, include_extras=True)
    result = tuple((field.name, hints[field.name]) for field in fields(model))
    _FIELD_TYPES[model] = result
    return result


_CONTAINER_TYPES: Dict[Any, Type[Container]] = {}


def _container_type(model: Any) -> Type[Container]:
    if model in _CONTAINER_TYPES:
        return _CONTAINER_TYPES[model]
    annotations = {
        name: _rmk_type(_infer(annotation))
        for name, annotation in _field_types(model)
    }
    if issubclass(model, ProgressiveSszContainer):
        base: Any = ProgressiveContainer(active_fields=[1] * len(annotations))
    else:
        base = Container
    result = type(
        f"_{model.__name__}Ssz",
        (base,),
        {"__annotations__": annotations},
    )
    _CONTAINER_TYPES[model] = result
    return result


def _to_ssz_value(annotation: Any, ssz_type: _SszType, value: Any) -> Any:
    if isinstance(ssz_type, _Container):
        return _to_view(value)
    if isinstance(ssz_type, (_List, _ProgressiveList)):
        element = _collection_element(annotation)
        return [
            _to_ssz_value(element, ssz_type.element, item) for item in value
        ]
    if isinstance(ssz_type, _Uint):
        return int(value)
    if isinstance(ssz_type, (_ByteVector, _ByteList, _ProgressiveByteList)):
        encoded = bytes(value)
        if (
            isinstance(ssz_type, _ByteVector)
            and len(encoded) != ssz_type.length
        ):
            raise ValueError(
                f"Expected {ssz_type.length} bytes, got {len(encoded)}"
            )
        return encoded
    if isinstance(ssz_type, _Bool):
        return bool(value)
    raise TypeError(f"Unsupported SSZ type: {ssz_type!r}")


def _to_view(value: SszContainer) -> Container:
    model = type(value)
    values = {
        name: _to_ssz_value(
            annotation, _infer(annotation), getattr(value, name)
        )
        for name, annotation in _field_types(model)
    }
    return _container_type(model)(**values)


def _from_ssz_value(annotation: Any, ssz_type: _SszType, value: Any) -> Any:
    base, _ = _annotated(annotation)
    if isinstance(ssz_type, _Container):
        return _from_view(ssz_type.model, value)
    if isinstance(ssz_type, (_List, _ProgressiveList)):
        element = _collection_element(annotation)
        decoded = [
            _from_ssz_value(element, ssz_type.element, item) for item in value
        ]
        return tuple(decoded)
    if isinstance(ssz_type, _Uint):
        return base(int(value))
    if isinstance(ssz_type, (_ByteVector, _ByteList, _ProgressiveByteList)):
        return base(bytes(value))
    if isinstance(ssz_type, _Bool):
        return bool(value)
    raise TypeError(f"Unsupported SSZ type: {ssz_type!r}")


def _from_view(model: Type[_C], view: Container) -> _C:
    values = {
        name: _from_ssz_value(
            annotation, _infer(annotation), getattr(view, name)
        )
        for name, annotation in _field_types(model)
    }
    return model(**values)
