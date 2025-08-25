"""Base classes and infrastructure for exceptions."""

from enum import Enum
from typing import Any, Dict

from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import (
    PlainValidatorFunctionSchema,
    no_info_plain_validator_function,
    to_string_ser_schema,
)

_exception_classes: Dict[str, type] = {}


class ExceptionBase(Enum):
    """Base class for exceptions."""

    def __init_subclass__(cls) -> None:
        """Register the exception class."""
        super().__init_subclass__()
        _exception_classes[cls.__name__] = cls

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> PlainValidatorFunctionSchema:
        """Call class constructor without info and appends the serialization schema."""
        return no_info_plain_validator_function(
            cls.from_str,
            serialization=to_string_ser_schema(),
        )

    @classmethod
    def from_str(cls, value: "str | ExceptionBase") -> "ExceptionBase":
        """Return ContainerKind enum value from a string."""
        if isinstance(value, ExceptionBase):
            return value

        class_name, enum_name = value.split(".")

        if cls == ExceptionBase:
            # Exception base automatically resolves the class
            assert class_name in _exception_classes, f"No such exception class: {class_name}"
            exception_class = _exception_classes[class_name]
        else:
            # Otherwise, use the class that the method is called on
            assert cls.__name__ == class_name, (
                f"Unexpected exception type: {class_name}, expected {cls.__name__}"
            )
            exception_class = cls

        exception = getattr(exception_class, enum_name, None)
        if exception is not None:
            return exception
        raise ValueError(f"No such exception in {class_name}: {value}")

    def __contains__(self, exception) -> bool:
        """Check if provided exception is equal to this."""
        return self == exception

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return f"{self.__class__.__name__}.{self.name}"


class UndefinedException(str):
    """Undefined Exception."""

    mapper_name: str | None

    def __new__(cls, value: str, *, mapper_name: str | None = None) -> "UndefinedException":
        """Create a new UndefinedException instance."""
        if isinstance(value, UndefinedException):
            return value
        assert isinstance(value, str)
        instance = super().__new__(cls, value)
        instance.mapper_name = mapper_name
        return instance

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> PlainValidatorFunctionSchema:
        """Call class constructor without info and appends the serialization schema."""
        return no_info_plain_validator_function(
            cls,
            serialization=to_string_ser_schema(),
        )


def to_pipe_str(value: Any) -> str:
    """
    Single pipe-separated string representation of an exception list.

    Obtain a deterministic ordering by ordering using the exception string
    representations.
    """
    if isinstance(value, list):
        return "|".join(str(exception) for exception in value)
    return str(value)


def from_pipe_str(value: Any) -> str | list[str]:
    """Parse a single string as a pipe separated list into enum exceptions."""
    if isinstance(value, str):
        exception_list = value.split("|")
        if len(exception_list) == 1:
            return exception_list[0]
        return exception_list
    return value
