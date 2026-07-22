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

Fork-scoped models: one model can serve every fork. Future-fork fields are
declared T | None (None == absent in older forks, omitted from JSON), and a
__ssz_schema__ = SszForkSchema(...) table beside the fields says which fork
introduces what, in canonical SSZ order (the class body's order stays free
for JSON). Such models require fork= on encode / hash_tree_root / decode /
ssz_default / describe_schema / build_ssz_type
"""

import ast
import inspect
import io
import re
import textwrap
import tokenize
from dataclasses import dataclass
from functools import lru_cache
from types import UnionType
from typing import (
    Any,
    ClassVar,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
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


@dataclass(frozen=True, eq=False)
class SszForkSchema:
    """
    Fork-scoped field sets for a fork-evolving container.

    One model declares every fork's fields; this table says which fields
    exist at which fork and in which SSZ order. base holds the fields of
    base_fork; appended maps each later fork (in order) to the fields it
    adds, which must be declared Optional (T | None) on the model.

    Fork keys are opaque strings: base_types knows nothing about forks;
    """

    base_fork: str
    base: Tuple[str, ...]
    appended: Mapping[str, Tuple[str, ...]]

    def forks(self) -> Tuple[str, ...]:
        """Every known fork key, oldest first."""
        return (self.base_fork, *self.appended)

    def fields_at(self, fork: str) -> Tuple[str, ...]:
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


def _is_fork_optional(model_cls: Type["SszModel"], name: str) -> bool:
    ann = model_cls.model_fields[name].annotation
    return _unwrap_optional(ann)[1]


_SSZ_EXCLUDE_COMMENT = re.compile(r"#\s*ssz_exclude\b")


@lru_cache(maxsize=None)
def _comment_excluded_names(klass: type) -> FrozenSet[str]:
    """
    Field names in klass's own body marked by a ``# ssz_exclude``
    comment.

    The comment must sit on the line directly above the field (or trail
    the field's own line). Classes whose source cannot be retrieved
    (built dynamically) contribute nothing; use the Annotated
    ssz_exclude() marker there.
    """
    try:
        source = textwrap.dedent(inspect.getsource(klass))
        tree = ast.parse(source)
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (OSError, TypeError, SyntaxError, tokenize.TokenError):
        return frozenset()
    marked: Set[int] = set()
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        if not _SSZ_EXCLUDE_COMMENT.match(tok.string):
            continue
        row, col = tok.start
        on_own_line = not tok.line[:col].strip()
        marked.add(row + 1 if on_own_line else row)
    class_def = tree.body[0]
    if not isinstance(class_def, ast.ClassDef):
        return frozenset()
    return frozenset(
        node.target.id
        for node in class_def.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.lineno in marked
    )


def _is_ssz_excluded(model_cls: Type["SszModel"], name: str) -> bool:
    metadata = model_cls.model_fields[name].metadata
    if any(isinstance(m, _SszExclude) for m in metadata):
        return True
    return any(
        name in _comment_excluded_names(klass)
        for klass in model_cls.__mro__
        if klass is not SszModel and issubclass(klass, SszModel)
    )


def _included_fields(model_cls: Type["SszModel"]) -> Tuple[str, ...]:
    """Every SSZ-participating field, in declaration order."""
    return tuple(
        name
        for name in model_cls.model_fields
        if not _is_ssz_excluded(model_cls, name)
    )


def _check_fork_schema(model_cls: Type["SszModel"]) -> None:
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
class _SszExclude(_Marker):
    pass


def byte_list(limit: int) -> SszByteList:
    """Annotate a Bytes field as a capped SSZ byte list."""
    return SszByteList(limit)


def ssz_list(limit: int) -> _ListCap:
    """Annotate a list[...] field as a capped SSZ list."""
    return _ListCap(limit)


def ssz_vector(length: int) -> _VectorLen:
    """Annotate a list[...] field as a fixed SSZ vector."""
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


def ssz_exclude() -> _SszExclude:
    """
    Annotate a field as JSON-only: the SSZ ignores it entirely.

    The usual spelling is a ``# ssz_exclude`` comment on the line
    directly above the field; this Annotated marker is the fallback for
    classes built dynamically, whose source the comment scan cannot
    read.
    """
    return _SszExclude()


class SszModel(CamelModel):
    """
    A pydantic model whose fields carry SSZ types.

    Every field must resolve to an SszType, or be excluded from SSZ
    with a ``# ssz_exclude`` comment on the line above it (JSON-only
    fields); each Annotated marker must be consistent with the field's
    Python type. Both are checked when the subclass is defined, so a
    mis-typed container fails at import, not at first encode.
    """

    __ssz_schema__: ClassVar[Optional[SszForkSchema]] = None

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


class ProgressiveModel(SszModel):
    """
    A forward-compatible progressive container.

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
    """The first SSZ marker in metadata."""
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
    if isinstance(marker, _SszExclude):
        raise TypeError(
            f"field is ssz_exclude()d; it has no SSZ type: {annotation!r}"
        )
    # Raw SszType instances (SszUint, SszContainer, ...) as markers would
    # bypass the consistency checks above; only the marker helpers are
    # supported.
    raise TypeError(
        f"unsupported Annotated SSZ marker {marker!r}; use the marker "
        f"helpers (ssz_list, ssz_vector, byte_list, bitvector, ...)"
    )


@lru_cache(maxsize=None)
def spec_of(model_cls: Type["SszModel"], name: str) -> SszType:
    """
    The resolved SSZ type of a field.

    An Annotated marker takes precedence over the bare type; cap-only markers
    derive their element from the annotation, and every marker is checked for
    consistency with it. A T | None union resolves to T's SSZ type -- the
    None arm means "absent in older forks" (see SszForkSchema), which is a
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


def _rmk_type(spec: SszType, fork: Optional[str] = None) -> Type[View]:
    if isinstance(spec, SszUint):
        return _UINTS[spec.bits]
    if isinstance(spec, SszByteVector):
        return ByteVector[spec.length]
    if isinstance(spec, SszByteList):
        return ByteList[spec.limit]
    if isinstance(spec, SszList):
        return RmkList[_rmk_type(spec.element, fork), spec.limit]
    if isinstance(spec, SszVector):
        return RmkVector[_rmk_type(spec.element, fork), spec.length]
    if isinstance(spec, SszBitvector):
        return RmkBitvector[spec.length]
    if isinstance(spec, SszBitlist):
        return RmkBitlist[spec.limit]
    if isinstance(spec, SszProgressiveList):
        return RmkProgressiveList[_rmk_type(spec.element, fork)]
    if isinstance(spec, SszProgressiveBitlist):
        return RmkProgressiveBitlist
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return build_ssz_type(spec.model, _nested_fork(spec.model, fork))
    if isinstance(spec, SszBool):
        return boolean
    raise TypeError(f"unhandled SSZ type {spec!r}")


def _active_fields(model_cls: Type["SszModel"]) -> Sequence[int]:
    declared = getattr(model_cls, "__active_fields__", ())
    return declared if declared else [1] * len(model_cls.model_fields)


def _nested_fork(
    model_cls: Type["SszModel"], fork: Optional[str]
) -> Optional[str]:
    """
    The fork a nested container is projected at.

    One fork propagates down the whole value tree: everything inside one
    message is at the same chain fork, so a fork-scoped nested model
    inherits the outer fork, while a
    complete nested model takes no fork at all.
    """
    return fork if model_cls.__ssz_schema__ is not None else None


def _schema_fields(
    model_cls: Type["SszModel"], fork: Optional[str]
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
    model_cls: Type["SszModel"], fork: Optional[str] = None
) -> Tuple[str, ...]:
    """
    The SSZ field names of model_cls, in canonical (wire) order.

    The public twin of the engine's internal field selection: callers
    (vector generators, fixtures tooling) can enumerate exactly the
    fields a model encodes -- per fork for fork-scoped models.
    """
    return _schema_fields(model_cls, fork)


def _check_populated(
    model: "SszModel", names: Tuple[str, ...], fork: str
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
    model_cls: Type["SszModel"], fork: Optional[str] = None
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
    model_cls: Type["SszModel"], fork: Optional[str]
) -> Type[Container]:
    names = _schema_fields(model_cls, fork)
    anns = {name: _rmk_type(spec_of(model_cls, name), fork) for name in names}
    if issubclass(model_cls, ProgressiveModel):
        base: Any = ProgressiveContainer(
            active_fields=list(_active_fields(model_cls))
        )
    else:
        base = Container
    cls_name = model_cls.__name__ + (fork if fork else "")
    return type(cls_name, (base,), {"__annotations__": anns})


def _to_rmk(spec: SszType, value: Any, fork: Optional[str] = None) -> Any:
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return _rmk_instance(value, _nested_fork(spec.model, fork))
    if isinstance(spec, (SszList, SszVector, SszProgressiveList)):
        return [_to_rmk(spec.element, v, fork) for v in value]
    if isinstance(spec, (SszBitvector, SszBitlist, SszProgressiveBitlist)):
        return list(value)
    return value  # scalar / byte-vector / byte-list: remerkleable coerces


def _rmk_instance(model: "SszModel", fork: Optional[str] = None) -> Container:
    model_cls: Type[SszModel] = type(model)
    names = _schema_fields(model_cls, fork)
    if fork is not None:
        _check_populated(model, names, fork)
    container = build_ssz_type(model_cls, fork)
    values = {
        name: _to_rmk(spec_of(model_cls, name), getattr(model, name), fork)
        for name in names
    }
    return container(**values)


def _to_py(spec: SszType, value: Any, fork: Optional[str] = None) -> Any:
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        nested = _nested_fork(spec.model, fork)
        return _view_to_model(
            spec.model, value, _schema_fields(spec.model, nested), nested
        )
    if isinstance(spec, (SszList, SszVector, SszProgressiveList)):
        return [_to_py(spec.element, v, fork) for v in value]
    if isinstance(spec, (SszBitvector, SszBitlist, SszProgressiveBitlist)):
        return [bool(b) for b in value]
    if isinstance(spec, (SszByteVector, SszByteList)):
        return bytes(value)
    if isinstance(spec, SszUint):
        return int(value)
    if isinstance(spec, SszBool):
        return bool(value)
    raise TypeError(f"unhandled SSZ type {spec!r}")


def _view_to_model(
    model_cls: Type[_M],
    view: Container,
    names: Optional[Tuple[str, ...]] = None,
    fork: Optional[str] = None,
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


def default_value(spec: SszType, fork: Optional[str] = None) -> Any:
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
        return [default_value(spec.element, fork) for _ in range(spec.length)]
    if isinstance(spec, SszBitvector):
        return [False] * spec.length
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return ssz_default(spec.model, _nested_fork(spec.model, fork))
    if isinstance(spec, SszBool):
        return False
    raise TypeError(f"no default for SSZ type {spec!r}")


def ssz_default(model_cls: Type[_M], fork: Optional[str] = None) -> _M:
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


def describe_type(spec: SszType) -> str:
    """Render an SSZ type as text (uint64, List[T, N], ...)."""
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


def describe_schema(
    model_cls: Type["SszModel"], fork: Optional[str] = None
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


def encode(model: "SszModel", fork: Optional[str] = None) -> bytes:
    """
    Return the SSZ wire bytes of model.

    A fork-scoped model requires fork and is
    checked against that fork's schema before encoding.
    """
    return _rmk_instance(model, fork).encode_bytes()


def hash_tree_root(model: "SszModel", fork: Optional[str] = None) -> bytes:
    """
    Return the 32-byte SSZ hash_tree_root of model.

    Fork-scoped models require fork, exactly as encode does.
    """
    return bytes(_rmk_instance(model, fork).hash_tree_root())


def decode(model_cls: Type[_M], data: bytes, fork: Optional[str] = None) -> _M:
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
    __ssz__: ClassVar[SszType] = SszUint(8)


class Uint16(_SizedUint):
    """A 16-bit unsigned integer."""

    __bits__: ClassVar[int] = 16
    __ssz__: ClassVar[SszType] = SszUint(16)


class Uint32(_SizedUint):
    """A 32-bit unsigned integer."""

    __bits__: ClassVar[int] = 32
    __ssz__: ClassVar[SszType] = SszUint(32)


class Uint64(_SizedUint):
    """A 64-bit unsigned integer."""

    __bits__: ClassVar[int] = 64
    __ssz__: ClassVar[SszType] = SszUint(64)


class Uint128(_SizedUint):
    """A 128-bit unsigned integer."""

    __bits__: ClassVar[int] = 128
    __ssz__: ClassVar[SszType] = SszUint(128)


class Uint256(_SizedUint):
    """A 256-bit unsigned integer."""

    __bits__: ClassVar[int] = 256
    __ssz__: ClassVar[SszType] = SszUint(256)


__all__ = [
    "ProgressiveModel",
    "SszBitlist",
    "SszBitvector",
    "SszBool",
    "SszByteList",
    "SszByteVector",
    "SszContainer",
    "SszForkSchema",
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
    "ssz_exclude",
    "ssz_fields",
    "ssz_list",
    "ssz_vector",
]
