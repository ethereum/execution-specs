"""EEST Exception mapper."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from bidict import frozenbidict

from .exceptions import ExceptionBase, UndefinedException


@dataclass
class ExceptionMessage:
    """Defines a mapping between an exception and a message."""

    exception: ExceptionBase
    message: str


class ExceptionMapper(ABC):
    """
    Translate between EEST exceptions and error strings returned by client's
    t8n or other tools.
    """

    def __init__(self) -> None:
        """Initialize the exception mapper."""
        # Ensure that the subclass has properly defined _mapping_data before accessing it
        assert self._mapping_data is not None, "_mapping_data must be defined in subclass"

        assert len({entry.exception for entry in self._mapping_data}) == len(
            self._mapping_data
        ), "Duplicate exception in _mapping_data"
        assert len({entry.message for entry in self._mapping_data}) == len(
            self._mapping_data
        ), "Duplicate message in _mapping_data"
        self.exception_to_message_map: frozenbidict = frozenbidict(
            {entry.exception: entry.message for entry in self._mapping_data}
        )

    @property
    @abstractmethod
    def _mapping_data(self):
        """Should be overridden in the subclass to provide mapping data."""
        pass

    def exception_to_message(self, exception: ExceptionBase) -> str | None:
        """Exception and to formatted string."""
        message = self.exception_to_message_map.get(exception, None)
        return message

    def message_to_exception(self, exception_string: str) -> ExceptionBase:
        """Match a formatted string to an exception."""
        for entry in self._mapping_data:
            if entry.message in exception_string:
                return entry.exception
        return UndefinedException.UNDEFINED_EXCEPTION
