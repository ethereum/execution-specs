"""
Native SSZ serialization for base_types models.

Declare a container once as a pydantic SSZModel, in the ordinary base types,
and get SSZ encoding, hash_tree_root, and defaults for them.

Each field's SSZ type is derived from its Python type, so the model stays the
single source of truth:

* fixed byte types self-describe by byte_length
  (Hash -> ByteVector[32], Address -> ByteVector[20]);
* the width ints defined here carry it (Uint64 -> uint64);
* bool -> boolean; a nested SSZModel -> Container;
* the only facts a Python type cannot express -- list / vector / bytelist / bit
  caps -- ride as Annotated markers (ssz_list(N), ssz_vector(N), byte_list(N),
  bitvector(N), bitlist(N)). Element types are derived from the annotation, so
  a marker carries only the cap/length, never a duplicated element spec.

Each field's SSZ type is described by an SSZType value (SSZUint, SSZByteList,
SSZList, SSZContainer, ...). The engine turns that into a remerkleable type
on demand (build_ssz_type) and delegates the actual encoding, merkleization,
and default (zero) values to it.

Fork-scoped models: one model can serve every fork. Future-fork fields are
declared T | None (None == absent in older forks, omitted from JSON), and a
__ssz_schema__ = SSZForkSchema(...) table beside the fields says which fork
introduces what, in canonical SSZ order (the class body's order stays free
for JSON). Such models require fork= on encode / hash_tree_root / decode /
ssz_default / describe_schema / build_ssz_type
"""

from dataclasses import dataclass
from functools import lru_cache
from types import UnionType
from typing import (
    Any,
    ClassVar,
    Hashable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
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

ForkKey = Hashable
"""An opaque fork-schema key; base_types knows nothing about forks."""

_UINTS = {
    8: uint8,
    16: uint16,
    32: uint32,
    64: uint64,
    128: uint128,
    256: uint256,
}


class SSZType:
    """A description of a field's SSZ type."""


@dataclass(frozen=True)
class SSZUint(SSZType):
    """An unsigned integer of bits width (8/16/32/64/128/256)."""

    bits: int


@dataclass(frozen=True)
class SSZByteVector(SSZType):
    """A fixed-length byte vector of length bytes."""

    length: int


@dataclass(frozen=True)
class SSZByteList(SSZType):
    """A variable byte list capped at limit bytes."""

    limit: int


@dataclass(frozen=True)
class SSZList(SSZType):
    """A list of element capped at limit items."""

    element: SSZType
    limit: int


@dataclass(frozen=True)
class SSZVector(SSZType):
    """A fixed-length vector of exactly length element items."""

    element: SSZType
    length: int


@dataclass(frozen=True)
class SSZBitvector(SSZType):
    """A fixed-length bit vector of length bits."""

    length: int


@dataclass(frozen=True)
class SSZBitlist(SSZType):
    """A variable bit list capped at limit bits."""

    limit: int


@dataclass(frozen=True)
class SSZBool(SSZType):
    """The SSZ boolean type."""


@dataclass(frozen=True)
class SSZContainer(SSZType):
    """A nested container backed by pydantic model."""

    model: Type["SSZModel"]


@dataclass(frozen=True)
class SSZProgressiveList(SSZType):
    """An uncapped progressive list of element (EIP-7916)."""

    element: SSZType


@dataclass(frozen=True)
class SSZProgressiveBitlist(SSZType):
    """An uncapped progressive bit list."""


@dataclass(frozen=True)
class SSZProgressiveContainer(SSZType):
    """A forward-compatible progressive container backed by model."""

    model: Type["SSZModel"]


_M = TypeVar("_M", bound="SSZModel")


@dataclass(frozen=True, eq=False)
class SSZForkSchema:
    """
    Fork-scoped field sets for a fork-evolving container.

    One model declares every fork's fields; this table says which fields
    exist at which fork and in which SSZ order. base holds the fields of
    base_fork; appended maps each later fork (in order) to the fields it
    adds, which must be declared Optional (T | None) on the model.

    Fork keys are opaque hashable values (e.g. fork classes): base_types
    knows nothing about forks;
    """

    base_fork: ForkKey
    base: Tuple[str, ...]
    appended: Mapping[ForkKey, Tuple[str, ...]]

    def forks(self) -> Tuple[ForkKey, ...]:
        """Every known fork key, oldest first."""
        return (self.base_fork, *self.appended)

    def fields_at(self, fork: ForkKey) -> Tuple[str, ...]:
        """The SSZ field names of fork, in canonical order."""
        if fork == self.base_fork:
            return self.base
        if fork not in self.appended:
            raise TypeError(
                f"unknown fork {fork!r}; known forks: {self.forks()}"
            )
        names = list(self.base)
        for key, fields in self.appended.items():
            names.extend(fields)
            if key == fork:
                break
        return tuple(names)

    def all_fields(self) -> Tuple[str, ...]:
        """Every field of the newest fork, in canonical order."""
        keys = self.forks()
        return self.fields_at(keys[-1])


def _unwrap_optional(annotation: Any) -> Tuple[Any, bool]:
    """Strip a T | None union; return."""
    if get_origin(annotation) in (Union, UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) != 1:
            raise TypeError(
                f"only T | None unions are supported: {annotation!r}"
            )
        return args[0], True
    return annotation, False


def _is_fork_optional(model_cls: Type["SSZModel"], name: str) -> bool:
    ann = model_cls.model_fields[name].annotation
    return _unwrap_optional(ann)[1]


def _is_ssz_excluded(model_cls: Type["SSZModel"], name: str) -> bool:
    """Whether name carries the ssz_exclude() marker (JSON-only)."""
    metadata = model_cls.model_fields[name].metadata
    return any(isinstance(m, _SSZExclude) for m in metadata)


def _included_fields(model_cls: Type["SSZModel"]) -> Tuple[str, ...]:
    """Every SSZ-participating field, in declaration order."""
    return tuple(
        name
        for name in model_cls.model_fields
        if not _is_ssz_excluded(model_cls, name)
    )


def _check_fork_schema(model_cls: Type["SSZModel"]) -> None:
    """
    Validate a model's __ssz_schema__ against its fields, at class
    definition.

    Optional (T | None) fields require a schema naming their fork; the
    schema must cover exactly the model's SSZ fields; base fields must
    be required and appended fields Optional with a None default -- so
    a mis-declared container fails at import.
    """
    schema = model_cls.__ssz_schema__
    included = _included_fields(model_cls)
    optional = {
        name for name in included if _is_fork_optional(model_cls, name)
    }
    progressive = globals().get("ProgressiveModel")
    if progressive is not None and issubclass(model_cls, progressive):
        if schema is not None:
            raise TypeError(
                f"{model_cls.__name__}: __ssz_schema__ is not supported "
                f"on ProgressiveModel (progressive containers evolve via "
                f"__active_fields__)"
            )
        if optional:
            raise TypeError(
                f"{model_cls.__name__}: T | None fields are not supported "
                f"on ProgressiveModel; reserve future slots with 0s in "
                f"__active_fields__ instead"
            )
        return
    if schema is None:
        if optional:
            raise TypeError(
                f"{model_cls.__name__} has fork-optional fields "
                f"{sorted(optional)} but no __ssz_schema__ declaring "
                f"which fork introduces them"
            )
        return
    all_names = schema.all_fields()
    dupes = sorted({n for n in all_names if all_names.count(n) > 1})
    if dupes:
        raise TypeError(
            f"{model_cls.__name__}.__ssz_schema__ names fields more than "
            f"once: {dupes}"
        )
    declared = set(all_names)
    fields = set(included)
    if declared != fields:
        raise TypeError(
            f"{model_cls.__name__}.__ssz_schema__ does not match the "
            f"model: schema-only={sorted(declared - fields)} "
            f"model-only={sorted(fields - declared)}"
        )
    appended = fields - set(schema.base)
    if optional != appended:
        raise TypeError(
            f"{model_cls.__name__}: appended fields must be T | None and "
            f"base fields required; non-optional appended="
            f"{sorted(appended - optional)} optional base="
            f"{sorted(optional - appended)}"
        )
    no_default = sorted(
        name for name in appended if model_cls.model_fields[name].is_required()
    )
    if no_default:
        raise TypeError(
            f"{model_cls.__name__}: appended fields must default to None "
            f"(decode of older forks constructs without them): "
            f"{no_default}"
        )


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


@dataclass(frozen=True)
class _SSZExclude(_Marker):
    pass


def byte_list(limit: int) -> SSZByteList:
    """Annotate a Bytes field as a capped SSZ byte list."""
    return SSZByteList(limit)


def ssz_list(limit: int) -> _ListCap:
    """Annotate a list[...] field as a capped SSZ list."""
    return _ListCap(limit)


def ssz_vector(length: int) -> _VectorLen:
    """Annotate a list[...] field as a fixed SSZ vector."""
    return _VectorLen(length)


def bitvector(length: int) -> SSZBitvector:
    """Annotate a list[bool] field as a fixed SSZ bit vector."""
    return SSZBitvector(length)


def bitlist(limit: int) -> SSZBitlist:
    """Annotate a list[bool] field as a capped SSZ bit list."""
    return SSZBitlist(limit)


def progressive_list() -> _ProgressiveListMark:
    """Annotate a list[...] field as an uncapped progressive list."""
    return _ProgressiveListMark()


def progressive_bitlist() -> SSZProgressiveBitlist:
    """Annotate a list[bool] field as an uncapped progressive bit list."""
    return SSZProgressiveBitlist()


def ssz_exclude() -> _SSZExclude:
    """
    Annotate a field as JSON-only: SSZ ignores it entirely.

    Such a field must carry a default: decode never sees it on the wire
    and so cannot reconstruct it.
    """
    return _SSZExclude()


class SSZModel(CamelModel):
    """
    A pydantic model whose fields carry SSZ types.

    Every field must resolve to an SSZType, or be excluded from SSZ with
    an ssz_exclude() marker (JSON-only fields); each Annotated marker
    must be consistent with the field's Python type.
    """

    __ssz_schema__: ClassVar[Optional[SSZForkSchema]] = None

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Validate every field resolves to a consistent SSZ type."""
        super().__pydantic_init_subclass__(**kwargs)
        for name in cls.model_fields:
            if _is_ssz_excluded(cls, name):
                if cls.model_fields[name].is_required():
                    raise TypeError(
                        f"{cls.__name__}.{name} is SSZ-excluded but has "
                        f"no default; decode cannot reconstruct it"
                    )
                continue
            spec_of(cls, name)  # raises TypeError on unmapped/inconsistent
        _check_fork_schema(cls)


class ProgressiveModel(SSZModel):
    """
    A forward-compatible progressive container.

    __active_fields__ is the active-field bitvector; it defaults to all SSZ
    fields active. A 0 marks a reserved gap with no declared field, so new
    fields can be slotted in later without shifting existing roots -- the
    SSZ fields fill the 1 positions in order.
    """

    __active_fields__: ClassVar[Sequence[int]] = ()

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Check the active-field bitvector agrees with the field count."""
        super().__pydantic_init_subclass__(**kwargs)
        active = cls.__active_fields__
        included = len(_included_fields(cls))
        if active and sum(active) != included:
            raise TypeError(
                f"{cls.__name__}.__active_fields__ has {sum(active)} active "
                f"entries but the container declares "
                f"{included} SSZ fields"
            )


def _marker_in(metadata: Any) -> Any:
    """The first SSZ marker in metadata."""
    return next(
        (m for m in metadata if isinstance(m, (SSZType, _Marker))), None
    )


def _spec_for_type_bare(annotation: Any) -> SSZType:
    """Derive the SSZ type of a plain Python type."""
    ssz = getattr(annotation, "__ssz__", None)
    if isinstance(ssz, SSZType):
        return ssz
    if isinstance(annotation, type):
        if issubclass(annotation, FixedSizeBytes):
            return SSZByteVector(annotation.byte_length)
        if issubclass(annotation, ProgressiveModel):
            return SSZProgressiveContainer(annotation)
        if issubclass(annotation, SSZModel):
            return SSZContainer(annotation)
        if annotation is bool:
            return SSZBool()
    raise TypeError(f"no SSZ type for {annotation!r}")


def _spec_for_type(annotation: Any) -> SSZType:
    """Resolve an SSZ type, honoring an inner Annotated marker if present."""
    meta = getattr(annotation, "__metadata__", None)
    if meta is not None:
        return _resolve(_marker_in(meta), annotation.__origin__)
    return _spec_for_type_bare(annotation)


def _element_of(annotation: Any, ctx: str) -> SSZType:
    """Resolve the element SSZ type of a list[...] annotation."""
    if get_origin(annotation) not in (list, List):
        raise TypeError(f"{ctx} requires a list[...] field: {annotation!r}")
    args = get_args(annotation)
    if len(args) != 1:
        raise TypeError(f"{ctx} needs a single list element type")
    return _spec_for_type(args[0])


def _resolve(marker: Any, annotation: Any) -> SSZType:
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
        return SSZList(_element_of(annotation, "ssz_list"), marker.limit)
    if isinstance(marker, _VectorLen):
        return SSZVector(_element_of(annotation, "ssz_vector"), marker.length)
    if isinstance(marker, _ProgressiveListMark):
        return SSZProgressiveList(_element_of(annotation, "progressive_list"))
    if isinstance(marker, SSZByteList):
        is_bytes = isinstance(annotation, type) and issubclass(
            annotation, Bytes
        )
        if not is_bytes:
            raise TypeError(
                f"byte_list requires a Bytes field/element: {annotation!r}"
            )
        return marker
    if isinstance(marker, (SSZBitvector, SSZBitlist, SSZProgressiveBitlist)):
        if not isinstance(_element_of(annotation, "bit markers"), SSZBool):
            raise TypeError(
                f"bit markers require a list[bool] field: {annotation!r}"
            )
        return marker
    if isinstance(marker, _SSZExclude):
        raise TypeError(
            f"field is ssz_exclude()d; it has no SSZ type: {annotation!r}"
        )
    # Raw SSZType instances (SSZUint, SSZContainer, ...) as markers would
    # bypass the consistency checks above; only the marker helpers are
    # supported.
    raise TypeError(
        f"unsupported Annotated SSZ marker {marker!r}; use the marker "
        f"helpers (ssz_list, ssz_vector, byte_list, bitvector, ...)"
    )


@lru_cache(maxsize=None)
def spec_of(model_cls: Type["SSZModel"], name: str) -> SSZType:
    """
    The resolved SSZ type of a field.

    An Annotated marker takes precedence over the bare type; cap-only markers
    derive their element from the annotation, and every marker is checked for
    consistency with it. A T | None union resolves to T's SSZ type -- the
    None arm means "absent in older forks" (see SSZForkSchema), which is a
    schema fact, not an SSZ type. Cached per (model_cls, name).
    """
    field = model_cls.model_fields[name]
    annotation, _ = _unwrap_optional(field.annotation)
    if _is_ssz_excluded(model_cls, name):
        raise TypeError(
            f"{model_cls.__name__}.{name} is SSZ-excluded; it has no "
            f"SSZ type: {annotation!r}"
        )
    return _resolve(_marker_in(field.metadata), annotation)


def _rmk_type(spec: SSZType, fork: Optional[ForkKey] = None) -> Type[View]:
    if isinstance(spec, SSZUint):
        return _UINTS[spec.bits]
    if isinstance(spec, SSZByteVector):
        return ByteVector[spec.length]
    if isinstance(spec, SSZByteList):
        return ByteList[spec.limit]
    if isinstance(spec, SSZList):
        return RmkList[_rmk_type(spec.element, fork), spec.limit]
    if isinstance(spec, SSZVector):
        return RmkVector[_rmk_type(spec.element, fork), spec.length]
    if isinstance(spec, SSZBitvector):
        return RmkBitvector[spec.length]
    if isinstance(spec, SSZBitlist):
        return RmkBitlist[spec.limit]
    if isinstance(spec, SSZProgressiveList):
        return RmkProgressiveList[_rmk_type(spec.element, fork)]
    if isinstance(spec, SSZProgressiveBitlist):
        return RmkProgressiveBitlist
    if isinstance(spec, (SSZContainer, SSZProgressiveContainer)):
        return build_ssz_type(spec.model, _nested_fork(spec.model, fork))
    if isinstance(spec, SSZBool):
        return boolean
    raise TypeError(f"unhandled SSZ type {spec!r}")


def _active_fields(model_cls: Type["SSZModel"]) -> Sequence[int]:
    """The active-field bitvector, defaulting to every SSZ field active."""
    declared = getattr(model_cls, "__active_fields__", ())
    return declared if declared else [1] * len(_included_fields(model_cls))


def _nested_fork(
    model_cls: Type["SSZModel"], fork: Optional[ForkKey]
) -> Optional[ForkKey]:
    """
    The fork a nested container is projected at.

    One fork propagates down the whole value tree: everything inside one
    message is at the same chain fork, so a fork-scoped nested model
    inherits the outer fork, while a
    complete nested model takes no fork at all.
    """
    return fork if model_cls.__ssz_schema__ is not None else None


def _schema_fields(
    model_cls: Type["SSZModel"], fork: Optional[ForkKey]
) -> Tuple[str, ...]:
    """
    The SSZ field names of model_cls, in canonical order.

    A fork-scoped model requires fork and gets
    that fork's fields in the schema's order; a complete model forbids
    fork and gets every non-excluded field in declaration order.
    """
    schema = model_cls.__ssz_schema__
    if schema is None:
        if fork is not None:
            raise TypeError(
                f"{model_cls.__name__} is not fork-scoped; do not pass fork"
            )
        return _included_fields(model_cls)
    if fork is None:
        raise TypeError(
            f"{model_cls.__name__} is fork-scoped; pass fork= "
            f"(one of {schema.forks()})"
        )
    return schema.fields_at(fork)


def ssz_fields(
    model_cls: Type["SSZModel"], fork: Optional[ForkKey] = None
) -> Tuple[str, ...]:
    """
    The SSZ field names of model_cls, in canonical (wire) order.

    The public twin of the engine's internal field selection: callers
    (vector generators, fixtures tooling) can enumerate exactly the
    fields a model encodes -- per fork for fork-scoped models.
    """
    return _schema_fields(model_cls, fork)


def _check_populated(
    model: "SSZModel", names: Tuple[str, ...], fork: ForkKey
) -> None:
    """Raise unless the populated fields exactly match the fork schema."""
    missing = [n for n in names if getattr(model, n) is None]
    unexpected = sorted(
        n
        for n in _included_fields(type(model))
        if n not in names and getattr(model, n) is not None
    )
    if missing or unexpected:
        raise TypeError(
            f"{type(model).__name__} does not fit the {fork!r} SSZ schema: "
            f"missing={missing} unexpected={unexpected}; "
            f"refusing to drop data"
        )


def build_ssz_type(
    model_cls: Type["SSZModel"], fork: Optional[ForkKey] = None
) -> Type[Container]:
    """
    Build the remerkleable container type mirroring model_cls.

    Cached per (class object, fork) -- distinct same-named models get
    distinct types, and each fork of a fork-scoped model gets its own
    genuinely distinct container (different offsets and merkle shape).
    """
    return _build_ssz_type(model_cls, fork)


@lru_cache(maxsize=None)
def _build_ssz_type(
    model_cls: Type["SSZModel"], fork: Optional[ForkKey]
) -> Type[Container]:
    names = _schema_fields(model_cls, fork)
    anns = {name: _rmk_type(spec_of(model_cls, name), fork) for name in names}
    if issubclass(model_cls, ProgressiveModel):
        base: Any = ProgressiveContainer(
            active_fields=list(_active_fields(model_cls))
        )
    else:
        base = Container
    cls_name = model_cls.__name__ + (str(fork) if fork else "")
    return type(cls_name, (base,), {"__annotations__": anns})


def _to_rmk(spec: SSZType, value: Any, fork: Optional[ForkKey] = None) -> Any:
    if isinstance(spec, (SSZContainer, SSZProgressiveContainer)):
        return _rmk_instance(value, _nested_fork(spec.model, fork))
    if isinstance(spec, (SSZList, SSZVector, SSZProgressiveList)):
        return [_to_rmk(spec.element, v, fork) for v in value]
    if isinstance(spec, (SSZBitvector, SSZBitlist, SSZProgressiveBitlist)):
        return list(value)
    return value  # scalar / byte-vector / byte-list: remerkleable coerces


def _rmk_instance(
    model: "SSZModel", fork: Optional[ForkKey] = None
) -> Container:
    model_cls: Type[SSZModel] = type(model)
    names = _schema_fields(model_cls, fork)
    if fork is not None:
        _check_populated(model, names, fork)
    container = build_ssz_type(model_cls, fork)
    values = {
        name: _to_rmk(spec_of(model_cls, name), getattr(model, name), fork)
        for name in names
    }
    return container(**values)


def _to_py(spec: SSZType, value: Any, fork: Optional[ForkKey] = None) -> Any:
    if isinstance(spec, (SSZContainer, SSZProgressiveContainer)):
        nested = _nested_fork(spec.model, fork)
        return _view_to_model(
            spec.model, value, _schema_fields(spec.model, nested), nested
        )
    if isinstance(spec, (SSZList, SSZVector, SSZProgressiveList)):
        return [_to_py(spec.element, v, fork) for v in value]
    if isinstance(spec, (SSZBitvector, SSZBitlist, SSZProgressiveBitlist)):
        return [bool(b) for b in value]
    if isinstance(spec, (SSZByteVector, SSZByteList)):
        return bytes(value)
    if isinstance(spec, SSZUint):
        return int(value)
    if isinstance(spec, SSZBool):
        return bool(value)
    raise TypeError(f"unhandled SSZ type {spec!r}")


def _view_to_model(
    model_cls: Type[_M],
    view: Container,
    names: Optional[Tuple[str, ...]] = None,
    fork: Optional[ForkKey] = None,
) -> _M:
    if names is None:
        names = _included_fields(model_cls)
    # Fields beyond `names` (older-fork decodes) keep their None default.
    return model_cls(
        **{
            name: _to_py(spec_of(model_cls, name), getattr(view, name), fork)
            for name in names
        }
    )


def default_value(spec: SSZType, fork: Optional[ForkKey] = None) -> Any:
    """Return the SSZ default (zero) value for spec as a pydantic value."""
    if isinstance(spec, SSZUint):
        return 0
    if isinstance(spec, SSZByteVector):
        return b"\x00" * spec.length
    if isinstance(
        spec,
        (SSZByteList, SSZList, SSZBitlist, SSZProgressiveList),
    ):
        return []
    if isinstance(spec, SSZProgressiveBitlist):
        return []
    if isinstance(spec, SSZVector):
        # A fresh value per slot: container defaults are mutable, so a shared
        # [x] * n would alias one instance across every position.
        return [default_value(spec.element, fork) for _ in range(spec.length)]
    if isinstance(spec, SSZBitvector):
        return [False] * spec.length
    if isinstance(spec, (SSZContainer, SSZProgressiveContainer)):
        return ssz_default(spec.model, _nested_fork(spec.model, fork))
    if isinstance(spec, SSZBool):
        return False
    raise TypeError(f"no default for SSZ type {spec!r}")


def ssz_default(model_cls: Type[_M], fork: Optional[ForkKey] = None) -> _M:
    """
    Build the SSZ default (all-zero) instance of model_cls.

    Fork-scoped models require fork; fields beyond it stay None.
    """
    return model_cls(
        **{
            name: default_value(spec_of(model_cls, name), fork)
            for name in _schema_fields(model_cls, fork)
        }
    )


def describe_type(spec: SSZType) -> str:
    """Render an SSZ type as text (uint64, List[T, N], ...)."""
    if isinstance(spec, SSZUint):
        return f"uint{spec.bits}"
    if isinstance(spec, SSZByteVector):
        return f"ByteVector[{spec.length}]"
    if isinstance(spec, SSZByteList):
        return f"ByteList[{spec.limit}]"
    if isinstance(spec, SSZList):
        return f"List[{describe_type(spec.element)}, {spec.limit}]"
    if isinstance(spec, SSZVector):
        return f"Vector[{describe_type(spec.element)}, {spec.length}]"
    if isinstance(spec, SSZBitvector):
        return f"Bitvector[{spec.length}]"
    if isinstance(spec, SSZBitlist):
        return f"Bitlist[{spec.limit}]"
    if isinstance(spec, SSZProgressiveList):
        return f"ProgressiveList[{describe_type(spec.element)}]"
    if isinstance(spec, SSZProgressiveBitlist):
        return "ProgressiveBitlist"
    if isinstance(spec, SSZContainer):
        return spec.model.__name__
    if isinstance(spec, SSZProgressiveContainer):
        return f"Progressive[{spec.model.__name__}]"
    if isinstance(spec, SSZBool):
        return "boolean"
    raise TypeError(f"unhandled SSZ type {spec!r}")


def describe_schema(
    model_cls: Type["SSZModel"], fork: Optional[ForkKey] = None
) -> str:
    """
    Render the resolved SSZ layout, one 'field: type' line per field.

    Fork-scoped models require fork and render that fork's projection.
    """
    title = model_cls.__name__ + (f" @ {fork}" if fork else "")
    lines = [f"{title}:"]
    for name in _schema_fields(model_cls, fork):
        lines.append(f"    {name}: {describe_type(spec_of(model_cls, name))}")
    return "\n".join(lines)


def encode(model: "SSZModel", fork: Optional[ForkKey] = None) -> bytes:
    """
    Return the SSZ wire bytes of model.

    A fork-scoped model requires fork and is
    checked against that fork's schema before encoding.
    """
    return _rmk_instance(model, fork).encode_bytes()


def hash_tree_root(model: "SSZModel", fork: Optional[ForkKey] = None) -> bytes:
    """
    Return the 32-byte SSZ hash_tree_root of model.

    Fork-scoped models require fork, exactly as encode does.
    """
    return bytes(_rmk_instance(model, fork).hash_tree_root())


def decode(
    model_cls: Type[_M], data: bytes, fork: Optional[ForkKey] = None
) -> _M:
    """
    Decode SSZ data into an instance of model_cls.

    For a fork-scoped model, data is decoded as fork's container and
    fields beyond that fork come back as None.
    """
    view = build_ssz_type(model_cls, fork).decode_bytes(data)
    return _view_to_model(
        model_cls, view, _schema_fields(model_cls, fork), fork
    )


# width-carrying integer types (base_types.HexNumber underneath)
class _SizedUint(HexNumber):
    """
    A width-checked unsigned integer.
    """

    __bits__: ClassVar[int] = 0

    def __new__(cls, input_number: Any) -> "_SizedUint":
        """Create the integer, enforcing 0 <= value < 2**bits."""
        value = super().__new__(cls, input_number)
        if not 0 <= int(value) < (1 << cls.__bits__):
            raise ValueError(f"{cls.__name__} out of range: {int(value)}")
        return value


class Uint8(_SizedUint):
    """An 8-bit unsigned integer."""

    __bits__: ClassVar[int] = 8
    __ssz__: ClassVar[SSZType] = SSZUint(8)


class Uint16(_SizedUint):
    """A 16-bit unsigned integer."""

    __bits__: ClassVar[int] = 16
    __ssz__: ClassVar[SSZType] = SSZUint(16)


class Uint32(_SizedUint):
    """A 32-bit unsigned integer."""

    __bits__: ClassVar[int] = 32
    __ssz__: ClassVar[SSZType] = SSZUint(32)


class Uint64(_SizedUint):
    """A 64-bit unsigned integer."""

    __bits__: ClassVar[int] = 64
    __ssz__: ClassVar[SSZType] = SSZUint(64)


class Uint128(_SizedUint):
    """A 128-bit unsigned integer."""

    __bits__: ClassVar[int] = 128
    __ssz__: ClassVar[SSZType] = SSZUint(128)


class Uint256(_SizedUint):
    """A 256-bit unsigned integer."""

    __bits__: ClassVar[int] = 256
    __ssz__: ClassVar[SSZType] = SSZUint(256)


__all__ = [
    "ProgressiveModel",
    "SSZBitlist",
    "SSZBitvector",
    "SSZBool",
    "SSZByteList",
    "SSZByteVector",
    "SSZContainer",
    "SSZForkSchema",
    "SSZList",
    "SSZModel",
    "SSZProgressiveBitlist",
    "SSZProgressiveContainer",
    "SSZProgressiveList",
    "SSZType",
    "SSZUint",
    "SSZVector",
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
    "ssz_exclude",
    "ssz_fields",
    "ssz_list",
    "ssz_vector",
]
