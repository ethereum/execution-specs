"""External exception mapper loading and composition."""

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from .exception_mapper import ExceptionMapper
from .exceptions import ExceptionBase, UndefinedException

PatternMapping = Dict[ExceptionBase, List[str]]


class ExternalExceptionMapperConfig(BaseModel):
    """Schema for v1 YAML-backed exception mapper files."""

    model_config = ConfigDict(extra="forbid")

    version: int
    name: str | None = None
    substring: PatternMapping = Field(default_factory=dict)
    regex: PatternMapping = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: int) -> int:
        """Validate the external mapper schema version."""
        if value != 1:
            raise ValueError(f"Unsupported exception mapper version: {value}")
        return value

    @field_validator("substring", "regex", mode="before")
    @classmethod
    def validate_mapping(cls, value: Any) -> PatternMapping:
        """Normalize exception mappings from strings or string lists."""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("Mapping sections must be objects")

        normalized: PatternMapping = {}
        for key, raw_patterns in value.items():
            try:
                exception = ExceptionBase.from_str(key)
            except (AssertionError, ValueError) as exception_error:
                raise ValueError(
                    f"Unknown exception name: {key}"
                ) from exception_error

            if isinstance(raw_patterns, str):
                patterns = [raw_patterns]
            elif isinstance(raw_patterns, list) and all(
                isinstance(pattern, str) for pattern in raw_patterns
            ):
                patterns = raw_patterns
            else:
                raise ValueError(
                    f"Patterns for {key} must be a string or list of strings"
                )

            for pattern in patterns:
                if not pattern:
                    raise ValueError(f"Empty pattern for {key}")
            normalized[exception] = patterns

        return normalized

    @field_validator("regex")
    @classmethod
    def validate_regex(cls, value: PatternMapping) -> PatternMapping:
        """Validate regular expressions at load time."""
        for exception, patterns in value.items():
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as regex_error:
                    raise ValueError(
                        f"Invalid regex for {exception}: {pattern}"
                    ) from regex_error
        return value


class ExternalExceptionMapper(ExceptionMapper):
    """Exception mapper loaded from an external YAML file."""

    mapping_substring = {}
    mapping_regex = {}

    def __init__(self, config: ExternalExceptionMapperConfig) -> None:
        """Initialize an external mapper from validated config."""
        self.mapper_name = config.name or "ExternalExceptionMapper"
        self.substring = config.substring
        self.regex = config.regex
        self._compiled_regex: Dict[ExceptionBase, List[re.Pattern[str]]] = {
            exception: [re.compile(pattern) for pattern in patterns]
            for exception, patterns in self.regex.items()
        }

    def message_to_exception(
        self, exception_string: str
    ) -> List[ExceptionBase] | UndefinedException:
        """Match a formatted string to an exception."""
        exceptions: List[ExceptionBase] = []
        for exception, substrings in self.substring.items():
            if any(substring in exception_string for substring in substrings):
                exceptions.append(exception)
        for exception, patterns in self._compiled_regex.items():
            if (
                exception not in exceptions
                and any(
                    pattern.search(exception_string) for pattern in patterns
                )
            ):
                exceptions.append(exception)
        if exceptions:
            return exceptions
        return UndefinedException(
            exception_string, mapper_name=self.mapper_name
        )


class CompositeExceptionMapper(ExceptionMapper):
    """Exception mapper that combines built-in and external mappers."""

    mapping_substring = {}
    mapping_regex = {}

    def __init__(self, mappers: Iterable[ExceptionMapper]) -> None:
        """Initialize the composite mapper."""
        self.mappers = list(mappers)
        self.mapper_name = "+".join(
            mapper.mapper_name for mapper in self.mappers
        )
        self.reliable = all(mapper.reliable for mapper in self.mappers)

    def message_to_exception(
        self, exception_string: str
    ) -> List[ExceptionBase] | UndefinedException:
        """Return ordered, de-duplicated matches from all mappers."""
        exceptions: List[ExceptionBase] = []
        for mapper in self.mappers:
            mapped = mapper.message_to_exception(exception_string)
            if isinstance(mapped, UndefinedException):
                continue
            for exception in mapped:
                if exception not in exceptions:
                    exceptions.append(exception)
        if exceptions:
            return exceptions
        return UndefinedException(
            exception_string, mapper_name=self.mapper_name
        )


def load_external_exception_mapper(path: Path) -> ExternalExceptionMapper:
    """Load a YAML-backed exception mapper from disk."""
    try:
        loaded = yaml.safe_load(path.read_text())
    except yaml.YAMLError as yaml_error:
        raise ValueError(
            f"Invalid YAML exception mapper file {path}: {yaml_error}"
        ) from yaml_error

    if loaded is None:
        loaded = {}
    try:
        config = ExternalExceptionMapperConfig.model_validate(loaded)
    except ValidationError as validation_error:
        raise ValueError(
            f"Invalid exception mapper file {path}: {validation_error}"
        ) from validation_error
    return ExternalExceptionMapper(config)


def extend_exception_mapper(
    built_in: ExceptionMapper | None,
    external: ExternalExceptionMapper | None,
) -> ExceptionMapper | None:
    """Extend a built-in mapper with an optional external mapper."""
    if built_in is None:
        return external
    if external is None:
        return built_in
    return CompositeExceptionMapper([built_in, external])
