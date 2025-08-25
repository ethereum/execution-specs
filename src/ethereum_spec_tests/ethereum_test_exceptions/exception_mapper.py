"""EEST Exception mapper."""

import re
from abc import ABC
from typing import Any, ClassVar, Dict, Generic, List

from pydantic import BaseModel, BeforeValidator, ValidationInfo

from .exceptions import ExceptionBase, ExceptionBoundTypeVar, UndefinedException


class ExceptionMapper(ABC):
    """
    Translate between EEST exceptions and error strings returned by client's
    t8n or other tools.
    """

    mapper_name: str
    _mapping_compiled_regex: Dict[ExceptionBase, re.Pattern]

    mapping_substring: ClassVar[Dict[ExceptionBase, str]]
    """
    Mapping of exception to substring that should be present in the error message.

    Items in this mapping are used for substring matching (`substring in message`).
    """

    mapping_regex: ClassVar[Dict[ExceptionBase, str]]
    """
    Mapping of exception to regex that should be present in the error message.

    Items in this mapping are compiled into regex patterns for faster matching,
    and then used for regex matching (`pattern.search(message)`).
    """
    reliable: ClassVar[bool] = True
    """
    Whether the exceptions returned by the tool are reliable and can be accurately
    mapped to the exceptions in this class.
    """

    def __init__(self) -> None:
        """Initialize the exception mapper."""
        # Ensure that the subclass has properly defined mapping_substring before accessing it
        assert self.mapping_substring is not None, "mapping_substring must be defined in subclass"
        assert self.mapping_regex is not None, "mapping_regex must be defined in subclass"
        self.mapper_name = self.__class__.__name__
        self._mapping_compiled_regex = {
            exception: re.compile(message) for exception, message in self.mapping_regex.items()
        }

    def message_to_exception(
        self, exception_string: str
    ) -> List[ExceptionBase] | UndefinedException:
        """Match a formatted string to an exception."""
        exceptions: List[ExceptionBase] = []
        for exception, substring in self.mapping_substring.items():
            if substring in exception_string:
                exceptions.append(exception)
        for exception, pattern in self._mapping_compiled_regex.items():
            if pattern.search(exception_string):
                exceptions.append(exception)
        if exceptions:
            return exceptions
        return UndefinedException(exception_string, mapper_name=self.mapper_name)


class ExceptionWithMessage(BaseModel, Generic[ExceptionBoundTypeVar]):
    """
    Class that contains the exception along with the verbatim message from the external
    tool/client.
    """

    exceptions: List[ExceptionBoundTypeVar]
    message: str

    def __contains__(self, item: Any) -> bool:
        """Check if the item is in the exceptions list."""
        if isinstance(item, list):
            return any(exception in self.exceptions for exception in item)
        return item in self.exceptions

    def __str__(self):
        """Return the string representation of the exception message."""
        return f"[{' | '.join(str(e) for e in self.exceptions)}] {self.message}"


def mapper_validator(v: str, info: ValidationInfo) -> Dict[str, Any] | UndefinedException | None:
    """
    Use the exception mapper that must be included in the context to map the exception
    from the external tool.
    """
    if v is None:
        return v
    if not isinstance(info.context, dict):
        return UndefinedException(v, mapper_name="UndefinedExceptionMapper: No context")
    exception_mapper = info.context.get("exception_mapper")
    if exception_mapper is None:
        return UndefinedException(v, mapper_name="UndefinedExceptionMapper: No mapper")
    assert isinstance(exception_mapper, ExceptionMapper), (
        f"Invalid mapper provided {exception_mapper}"
    )
    exceptions = exception_mapper.message_to_exception(v)
    if isinstance(exceptions, UndefinedException):
        return exceptions
    return {
        "exceptions": exceptions,
        "message": v,
    }


ExceptionMapperValidator = BeforeValidator(mapper_validator)
"""
Validator that can be used to annotate a pydantic field in a model that is meant to be
parsed from an external tool or client.

The annotated type must be an union that can include `None`, `UndefinedException` and a
custom model as:
```
class BlockExceptionWithMessage(ExceptionWithMessage[BlockException]):
    pass
```
where `BlockException` can be any derivation of `ExceptionBase`.

The `message` attribute is the verbatim message received from the external tool or client,
and can be used to be printed for extra context information in case of failures.
"""
