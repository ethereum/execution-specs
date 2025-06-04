"""Base fixture definitions used to define all fixture types."""

import hashlib
import json
from functools import cached_property
from typing import Annotated, Any, ClassVar, Dict, Type, Union

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

from ethereum_test_base_types import CamelModel, ReferenceSpec
from ethereum_test_forks import Fork


def fixture_format_discriminator(v: Any) -> str | None:
    """Discriminator function that returns the model type as a string."""
    if v is None:
        return None
    if isinstance(v, dict):
        info_dict = v.get("_info")
    elif hasattr(v, "info"):
        info_dict = v.info
    assert info_dict is not None, (
        f"Fixture does not have an info field, cannot determine fixture format: {v}"
    )
    fixture_format = info_dict.get("fixture-format")
    if not fixture_format:
        fixture_format = info_dict.get("fixture_format")
    assert fixture_format is not None, f"Fixture format not found in info field: {info_dict}"
    return fixture_format


class BaseFixture(CamelModel):
    """Represents a base Ethereum test fixture of any type."""

    # Base Fixture class properties
    formats: ClassVar[Dict[str, Type["BaseFixture"]]] = {}
    formats_type_adapter: ClassVar[TypeAdapter]

    info: Dict[str, Dict[str, Any] | str] = Field(default_factory=dict, alias="_info")

    # Fixture format properties
    format_name: ClassVar[str] = ""
    output_file_extension: ClassVar[str] = ".json"
    description: ClassVar[str] = "Unknown fixture format; it has not been set."

    @classmethod
    def output_base_dir_name(cls) -> str:
        """Return name of the subdirectory where this type of fixture should be dumped to."""
        return cls.format_name.replace("test", "tests")

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
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
    def _parse_into_subclass(cls, v: Any, handler: ValidatorFunctionWrapHandler) -> "BaseFixture":
        """Parse the fixture into the correct subclass."""
        if cls is BaseFixture:
            return BaseFixture.formats_type_adapter.validate_python(v)
        return handler(v)

    @cached_property
    def json_dict(self) -> Dict[str, Any]:
        """Returns the JSON representation of the fixture."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True, exclude={"info"})

    @cached_property
    def hash(self) -> str:
        """Returns the hash of the fixture."""
        json_str = json.dumps(self.json_dict, sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
        return f"0x{h}"

    def json_dict_with_info(self, hash_only: bool = False) -> Dict[str, Any]:
        """Return JSON representation of the fixture with the info field."""
        dict_with_info = self.json_dict.copy()
        dict_with_info["_info"] = {"hash": self.hash}
        if not hash_only:
            dict_with_info["_info"].update(self.info)
        return dict_with_info

    def fill_info(
        self,
        t8n_version: str,
        test_case_description: str,
        fixture_source_url: str,
        ref_spec: ReferenceSpec | None,
        _info_metadata: Dict[str, Any],
    ):
        """Fill the info field for this fixture."""
        if "comment" not in self.info:
            self.info["comment"] = "`execution-spec-tests` generated test"
        self.info["filling-transition-tool"] = t8n_version
        self.info["description"] = test_case_description
        self.info["url"] = fixture_source_url
        self.info["fixture-format"] = self.format_name
        if ref_spec is not None:
            ref_spec.write_info(self.info)
        if _info_metadata:
            self.info.update(_info_metadata)

    def get_fork(self) -> Fork | None:
        """Return fork of the fixture as a string."""
        raise NotImplementedError

    @classmethod
    def supports_fork(cls, fork: Fork) -> bool:
        """
        Return whether the fixture can be generated for the given fork.

        By default, all fixtures support all forks.
        """
        return True


class LabeledFixtureFormat:
    """
    Represents a fixture format with a custom label.

    This label will be used in the test id and also will be added as a marker to the
    generated test case when filling the test.
    """

    format: Type[BaseFixture]
    label: str
    description: str

    registered_labels: ClassVar[Dict[str, "LabeledFixtureFormat"]] = {}

    def __init__(
        self,
        fixture_format: "Type[BaseFixture] | LabeledFixtureFormat",
        label: str,
        description: str,
    ):
        """Initialize the fixture format with a custom label."""
        self.format = (
            fixture_format.format
            if isinstance(fixture_format, LabeledFixtureFormat)
            else fixture_format
        )
        self.label = label
        self.description = description
        if label not in LabeledFixtureFormat.registered_labels:
            LabeledFixtureFormat.registered_labels[label] = self

    @property
    def format_name(self) -> str:
        """Get the execute format name."""
        return self.format.format_name

    def __eq__(self, other: Any) -> bool:
        """
        Check if two labeled fixture formats are equal.

        If the other object is a FixtureFormat type, the format of the labeled fixture
        format will be compared with the format of the other object.
        """
        if isinstance(other, LabeledFixtureFormat):
            return self.format == other.format
        if isinstance(other, type) and issubclass(other, BaseFixture):
            return self.format == other
        return False


# Annotated type alias for a base fixture class
FixtureFormat = Annotated[
    Type[BaseFixture],
    PlainSerializer(lambda f: f.format_name),
    PlainValidator(lambda f: BaseFixture.formats[f] if f in BaseFixture.formats else f),
]
