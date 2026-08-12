"""Base fixture definitions used to define all fixture types."""

import hashlib
import json
from enum import Enum, auto
from functools import cached_property
from typing import (
    Annotated,
    Any,
    ClassVar,
    Dict,
    List,
    Protocol,
    Set,
    Type,
    Union,
)

import pytest
from pydantic import (
    Discriminator,
    Field,
    PlainSerializer,
    PlainValidator,
    Tag,
    TypeAdapter,
    model_validator,
)
from pydantic_core.core_schema import ValidatorFunctionWrapHandler

from execution_testing.base_types import CamelModel, ReferenceSpec
from execution_testing.fixtures.post_verifications import PostVerifications
from execution_testing.forks import Fork, TransitionFork


def fixture_format_discriminator(v: Any) -> str | None:
    """Discriminator function that returns the model type as a string."""
    if v is None:
        return None
    info_dict: Dict | None = None
    if isinstance(v, dict):
        info_dict = v.get("_info")
    elif hasattr(v, "info"):
        info_dict = v.info
    if info_dict is None:
        raise ValueError(
            "Fixture does not have an info field, "
            f"cannot determine fixture format: {v}"
        )
    fixture_format = info_dict.get("fixture-format")
    if not fixture_format:
        fixture_format = info_dict.get("fixture_format")
    if fixture_format is None:
        raise ValueError(
            f"Fixture format not found in info field: {info_dict}"
        )
    return fixture_format


class FixtureFillingPhase(Enum):
    """Execution phase for fixture generation."""

    FILL = auto()
    PRE_ALLOC_GENERATION = auto()
    FILL_AFTER_PRE_ALLOC_GENERATION = auto()
    FILL_STATEFUL = auto()


class BaseFixture(CamelModel):
    """Represents a base Ethereum test fixture of any type."""

    # Base Fixture class properties
    formats: ClassVar[Dict[str, Type["BaseFixture"]]] = {}
    formats_type_adapter: ClassVar[TypeAdapter]

    info: Dict[str, Dict[str, Any] | str] = Field(
        default_factory=dict, alias="_info"
    )
    post_verifications: PostVerifications | None = Field(
        default=None, alias="postVerifications"
    )

    # Fixture format properties
    format_name: ClassVar[str] = ""
    output_file_extension: ClassVar[str] = ".json"
    description: ClassVar[str] = "Unknown fixture format; it has not been set."
    format_phases: ClassVar[Set[FixtureFillingPhase]] = {
        # Normal fixture types can be filled whether the pre-alloc phase was
        # executed or not.
        FixtureFillingPhase.FILL,
        FixtureFillingPhase.FILL_AFTER_PRE_ALLOC_GENERATION,
    }
    transition_tool_cache_key: ClassVar[str] = ""

    @classmethod
    def output_base_dir_name(cls) -> str:
        """
        Return name of the subdirectory where this type of fixture should be
        dumped to.
        """
        return cls.format_name.replace("test", "tests")

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Register all subclasses of BaseFixture with a fixture format name set
        as possible fixture formats.
        """
        if cls.format_name:
            # Register the new fixture format
            BaseFixture.formats[cls.format_name] = cls
            if len(BaseFixture.formats) > 1:
                BaseFixture.formats_type_adapter = TypeAdapter(
                    Annotated[
                        Union[
                            tuple(
                                Annotated[fixture_format, Tag(format_name)]
                                for (
                                    format_name,
                                    fixture_format,
                                ) in BaseFixture.formats.items()
                            )
                        ],
                        Discriminator(fixture_format_discriminator),
                    ]
                )
            else:
                BaseFixture.formats_type_adapter = TypeAdapter(cls)

    @model_validator(mode="wrap")
    @classmethod
    def _parse_into_subclass(
        cls, v: Any, handler: ValidatorFunctionWrapHandler
    ) -> "BaseFixture":
        """Parse the fixture into the correct subclass."""
        if cls is BaseFixture:
            return BaseFixture.formats_type_adapter.validate_python(v)
        return handler(v)

    @cached_property
    def json_dict(self) -> Dict[str, Any]:
        """Returns the JSON representation of the fixture."""
        return self.model_dump(
            mode="json", by_alias=True, exclude_none=True, exclude={"info"}
        )

    @cached_property
    def hash(self) -> str:
        """Returns the hash of the fixture."""
        json_str = json.dumps(
            self.json_dict, sort_keys=True, separators=(",", ":")
        )
        h = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
        return f"0x{h}"

    def json_dict_with_info(self, hash_only: bool = False) -> Dict[str, Any]:
        """Return JSON representation of the fixture with the info field."""
        dict_with_info = self.json_dict.copy()
        dict_with_info["_info"] = {"hash": self.hash}
        if not hash_only:
            dict_with_info["_info"].update(self.info)
        return dict_with_info

    def model_post_init(self, __context: Any, /) -> None:
        """
        Model post-init to assert that the custom pre-allocation was
        provided and the default was not used.
        """
        super().model_post_init(__context)
        self.info["fixture-format"] = self.format_name

    def fill_info(
        self,
        t8n_version: str,
        test_case_description: str,
        fixture_source_url: str,
        ref_spec: ReferenceSpec | None,
        _info_metadata: Dict[str, Any] | None,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Fill the info field for this fixture."""
        if "comment" not in self.info:
            self.info["comment"] = "`execution-specs` generated test"
        self.info["filling-transition-tool"] = t8n_version
        self.info["description"] = test_case_description
        self.info["url"] = fixture_source_url
        if metadata:
            self.info["metadata"] = metadata
        if ref_spec is not None:
            ref_spec.write_info(self.info)
        if _info_metadata:
            self.info.update(_info_metadata)

    def get_fork(self) -> Fork | TransitionFork | None:
        """Return fork of the fixture as a string."""
        raise NotImplementedError

    @classmethod
    def format_class(cls) -> "Type[BaseFixture]":
        """Get the fixture format."""
        return cls

    @classmethod
    def format_id(cls) -> str:
        """Get string used as identifier for this format."""
        return cls.format_name.lower()

    @classmethod
    def is_variant(cls, variant: str) -> bool:
        """
        Return whether this format is the named variant.

        A plain format never is: only a label can name a variant.
        """
        del variant
        return False

    @classmethod
    def with_label_suffix(
        cls,
        suffix: str,
        description: str | None = None,
        *,
        transition_tool_cache_key: str | None = None,
        variant: str | None = None,
    ) -> "LabeledFixtureFormat":
        """
        Return this format labeled `<format_id>_<suffix>`.

        Use this instead of building a `LabeledFixtureFormat` by hand when a
        spec type re-labels the formats of another one: the label is derived
        from `format_id()`, so a format that already carries a label derives a
        distinct label per label instead of collapsing them all onto its
        format name.

        `transition_tool_cache_key` defaults to this format's key, which is
        what a label that only renames the same fixture wants. A suffix that
        asks the transition tool for something different must pass its own
        key, or an empty string to opt out of caching.

        `variant` names what the label asks its spec type to fill differently,
        for that spec type to query with `is_variant()` rather than comparing
        formats.
        """
        return LabeledFixtureFormat(
            cls,
            f"{cls.format_id()}_{suffix}",
            description
            if description is not None
            else f"A {cls.format_id()} {suffix.replace('_', ' ')}",
            transition_tool_cache_key=transition_tool_cache_key,
            variant=variant,
        )

    @classmethod
    def marks(
        cls, *, transition_tool_cache_key: str | None = None
    ) -> List[pytest.MarkDecorator | pytest.Mark]:
        """
        Get list of pytest marks that need to be added to a test produced
        with this fixture format.

        `transition_tool_cache_key` overrides the format's own key.
        """
        cache_key = (
            cls.transition_tool_cache_key
            if transition_tool_cache_key is None
            else transition_tool_cache_key
        )
        marks: List[pytest.MarkDecorator | pytest.Mark] = [
            getattr(
                pytest.mark,
                cls.format_name.lower(),
            ),
        ]
        if cache_key:
            marks.append(pytest.mark.transition_tool_cache_key(cache_key))
        return marks

    @classmethod
    def supports_fork(cls, fork: Fork | TransitionFork) -> bool:
        """
        Return whether the fixture can be generated for the given fork.

        By default, all fixtures support all forks.
        """
        del fork
        return True

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fork: Fork | TransitionFork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard a fixture format from filling if the appropriate marker is
        used.
        """
        del fork, markers
        return False


class LabeledFixtureFormat:
    """
    Represents a fixture format with a custom label.

    This label will be used in the test id and also will be added as a marker
    to the generated test case when filling the test.
    """

    format: Type[BaseFixture]
    label: str
    description: str
    base: "LabeledFixtureFormat | None"
    _transition_tool_cache_key: str | None
    _variant: str | None

    registered_labels: ClassVar[Dict[str, "LabeledFixtureFormat"]] = {}

    def __init__(
        self,
        fixture_format: "Type[BaseFixture] | LabeledFixtureFormat",
        label: str,
        description: str,
        *,
        transition_tool_cache_key: str | None = None,
        variant: str | None = None,
    ):
        """
        Initialize the fixture format with a custom label.

        `transition_tool_cache_key` defaults to the wrapped format's key. A
        label that asks the transition tool for something different must set
        its own key, or an empty string to opt out of caching, since labels
        sharing a key also share cached output.

        `variant` names what this label asks its spec type to fill
        differently, and defaults to the wrapped label's variant.

        Wrapping a label rather than a plain format keeps what that inner
        label decided: its variant, its cache key and its fork/marker vetoes
        still apply, so re-labeling never silently reverts them to the plain
        format's.
        """
        self.format = fixture_format.format_class()
        self.base = (
            fixture_format
            if isinstance(fixture_format, LabeledFixtureFormat)
            else None
        )
        self.label = label
        self.description = description
        self._transition_tool_cache_key = transition_tool_cache_key
        self._variant = variant
        if label not in LabeledFixtureFormat.registered_labels:
            LabeledFixtureFormat.registered_labels[label] = self

    @property
    def format_name(self) -> str:
        """Get the filling format name."""
        return self.format.format_name

    @property
    def format_phases(self) -> Set[FixtureFillingPhase]:
        """Get the filling format phases where it should be included."""
        return self.format.format_phases

    def format_class(self) -> Type[BaseFixture]:
        """Get the format without label."""
        return self.format

    def supports_fork(self, fork: Fork | TransitionFork) -> bool:
        """
        Return whether this label can be filled for the given fork.

        Defers to the label this one was derived from, or to the wrapped
        format. A label whose fixture only makes sense for some forks
        overrides this.
        """
        if self.base is not None:
            return self.base.supports_fork(fork)
        return self.format.supports_fork(fork)

    def discard_fixture_format_by_marks(
        self,
        fork: Fork | TransitionFork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard this label from filling if the appropriate marker is used.

        Defers to the label this one was derived from, or to the wrapped
        format, so a label can veto itself without affecting the other labels
        of the same format.
        """
        if self.base is not None:
            return self.base.discard_fixture_format_by_marks(fork, markers)
        return self.format.discard_fixture_format_by_marks(fork, markers)

    def format_id(self) -> str:
        """Get string used as identifier for this format."""
        return self.label

    @property
    def variant(self) -> str | None:
        """
        Get what this label asks its spec type to fill differently.

        Falls back to the variant of the label this one was derived from, so a
        variant survives being re-labeled.
        """
        if self._variant is not None:
            return self._variant
        if self.base is not None:
            return self.base.variant
        return None

    def is_variant(self, variant: str) -> bool:
        """
        Return whether this label is the named variant.

        A spec type asks this instead of comparing the format it was handed
        against the label it declared: comparing cannot tell a variant from
        the plain format it wraps, and it stops matching as soon as another
        spec type re-labels the variant.
        """
        return self.variant == variant

    def labels(self) -> List[str]:
        """
        Get this label and every label it was derived from, outermost last.
        """
        labels = self.base.labels() if self.base is not None else []
        labels.append(self.label)
        return labels

    def with_label_suffix(
        self,
        suffix: str,
        description: str | None = None,
        *,
        transition_tool_cache_key: str | None = None,
        variant: str | None = None,
    ) -> "LabeledFixtureFormat":
        """
        Return this label re-labeled as `<label>_<suffix>`.

        The derived label keeps this label's fork/marker vetoes, so every label
        of one format derives its own distinct label rather than all of them
        collapsing onto the format name.

        `transition_tool_cache_key` defaults to this label's key, so a label
        that opted out of caching stays opted out. A suffix that asks the
        transition tool for something different must pass its own key.

        `variant` defaults to this label's variant, so re-labeling a variant
        keeps filling that variant.
        """
        return LabeledFixtureFormat(
            self,
            f"{self.format_id()}_{suffix}",
            description
            if description is not None
            else f"A {self.format_id()} {suffix.replace('_', ' ')}",
            transition_tool_cache_key=transition_tool_cache_key,
            variant=variant,
        )

    def marks(self) -> List[pytest.MarkDecorator | pytest.Mark]:
        """
        Get list of pytest marks that need to be added to a test produced
        with this fixture format.

        Every label this one was derived from is marked too, so selecting a
        label also selects the labels another spec type derived from it.
        """
        marks: List[pytest.MarkDecorator | pytest.Mark] = self.format.marks(
            transition_tool_cache_key=self.transition_tool_cache_key
        )
        for label in self.labels():
            if label.lower() != self.format.format_name.lower():
                marks.append(
                    getattr(
                        pytest.mark,
                        label.lower(),
                    ),
                )
        return marks

    @property
    def transition_tool_cache_key(self) -> str:
        """
        Get the transition tool cache key.

        Falls back to the key of the label this one was derived from, and then
        to the wrapped format's, so a label that opted out of caching does not
        opt back in when it is re-labeled.
        """
        if self._transition_tool_cache_key is not None:
            return self._transition_tool_cache_key
        if self.base is not None:
            return self.base.transition_tool_cache_key
        return self.format.transition_tool_cache_key

    def __eq__(self, other: Any) -> bool:
        """
        Check if two labeled fixture formats are equal.

        Two labeled formats are equal only when they share both format and
        label, so one format can carry more than one label.

        If the other object is a FixtureFormat type, the format of the labeled
        fixture format will be compared with the format of the other object.
        """
        if isinstance(other, LabeledFixtureFormat):
            return self.format == other.format and self.label == other.label
        if isinstance(other, type) and issubclass(other, BaseFixture):
            return self.format == other
        return False

    def __hash__(self) -> int:
        """
        Return the hash of the wrapped format.

        A labeled format compares equal to the plain format it wraps, so both
        must hash alike. Two labels of one format collide, which is allowed
        since they no longer compare equal.
        """
        return hash(self.format)


# Annotated type alias for a base fixture class
FixtureFormat = Annotated[
    Type[BaseFixture],
    PlainSerializer(lambda f: f.format_name),
    PlainValidator(
        lambda f: BaseFixture.formats[f] if f in BaseFixture.formats else f
    ),
]


class PytestItemProtocol(Protocol):
    """Protocol that resembles pytest.Item."""

    @property
    def nodeid(self) -> str:
        """Return the nodeid of the item."""
        ...

    def get_closest_marker(self, name: str) -> pytest.Mark | None:
        """Return the closest marker with the given name."""
        ...


def strip_fixture_format_from_node(
    item: PytestItemProtocol,
) -> str:
    """
    Remove fixture format suffix from a test nodeid.

    Used for cache keys and xdist grouping to ensure related fixture formats
    (e.g., blockchain_test and blockchain_test_engine) share the same key.

    Example:
        'test.py::test[fork_Osaka-state_test]' -> 'test.py::test[fork_Osaka]'

    """
    fixture_format_id_marker = item.get_closest_marker("fixture_format_id")
    nodeid = item.nodeid
    if fixture_format_id_marker is None:
        return nodeid
    assert len(fixture_format_id_marker.args) == 1
    fixture_id = fixture_format_id_marker.args[0]
    if fixture_id not in nodeid:
        return nodeid
    return nodeid.replace(fixture_id, "")
