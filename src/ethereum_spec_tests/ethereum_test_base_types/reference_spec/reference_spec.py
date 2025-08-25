"""
Types used to describe a reference specification and versioning used to write
Ethereum tests.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional


# Exceptions
class NoLatestKnownVersionError(Exception):
    """
    Exception used to signal that the reference specification does not have a
    latest known version.
    """

    pass


class ParseModuleError(Exception):
    """
    Exception used to signal that module's reference spec could not be parsed
    using the given class.
    """

    pass


class ReferenceSpec:
    """Reference Specification Description Abstract Class."""

    @abstractmethod
    def name(self) -> str:
        """Return the name of the spec."""
        pass

    @abstractmethod
    def has_known_version(self) -> bool:
        """Return true if the reference spec object is hard-coded with a latest known version."""
        pass

    @abstractmethod
    def known_version(self) -> str:
        """Return the latest known version in the reference."""
        pass

    @abstractmethod
    def api_url(self) -> str:
        """Return the URL required to poll the version from an API, if needed."""
        pass

    @abstractmethod
    def latest_version(self) -> str:
        """Return a digest that points to the latest version of the spec."""
        pass

    @abstractmethod
    def is_outdated(self) -> bool:
        """
        Check whether the reference specification has been updated since the
        test was last updated.
        """
        pass

    @abstractmethod
    def write_info(self, info: Dict[str, Dict[str, Any] | str]):
        """Write info about the reference specification used into the output fixture."""
        pass

    @staticmethod
    @abstractmethod
    def parseable_from_module(module_dict: Dict[str, Any]) -> bool:
        """Check whether the module's dict contains required reference spec information."""
        pass

    @staticmethod
    @abstractmethod
    def parse_from_module(
        module_dict: Dict[str, Any], github_token: Optional[str] = None
    ) -> "ReferenceSpec":
        """
        Parse the module's dict into a reference spec.

        Args:
            module_dict: Dictionary containing module information
            github_token: Optional GitHub token for API authentication

        """
        pass
