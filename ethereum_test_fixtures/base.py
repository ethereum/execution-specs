"""Base fixture definitions used to define all fixture types."""

import hashlib
import json
from functools import cached_property
from typing import Any, ClassVar, Dict, Type

from pydantic import Field

from ethereum_test_base_types import CamelModel, ReferenceSpec
from ethereum_test_forks import Fork


class BaseFixture(CamelModel):
    """Represents a base Ethereum test fixture of any type."""

    info: Dict[str, str] = Field(default_factory=dict, alias="_info")

    # Fixture format properties
    fixture_format_name: ClassVar[str] = "unset"
    output_file_extension: ClassVar[str] = ".json"
    description: ClassVar[str] = "Unknown fixture format; it has not been set."

    @classmethod
    def output_base_dir_name(cls) -> str:
        """Return name of the subdirectory where this type of fixture should be dumped to."""
        return cls.fixture_format_name.replace("test", "tests")

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
    ):
        """Fill the info field for this fixture."""
        if "comment" not in self.info:
            self.info["comment"] = "`execution-spec-tests` generated test"
        self.info["filling-transition-tool"] = t8n_version
        self.info["description"] = test_case_description
        self.info["url"] = fixture_source_url
        self.info["fixture_format"] = self.fixture_format_name
        if ref_spec is not None:
            ref_spec.write_info(self.info)

    def get_fork(self) -> str | None:
        """Return fork of the fixture as a string."""
        raise NotImplementedError

    @classmethod
    def supports_fork(cls, fork: Fork) -> bool:
        """
        Return whether the fixture can be generated for the given fork.

        By default, all fixtures support all forks.
        """
        return True


# Type alias for a base fixture class
FixtureFormat = Type[BaseFixture]
