"""
A module for managing documentation-related configurations.

Classes:
- DocsConfig: Holds configurations for documentation generation.
"""

from pydantic import BaseModel


class DocsConfig(BaseModel):
    """
    A class for accessing documentation-related configurations.
    """

    TARGET_FORK: str = "Prague"
    """The target fork for the documentation."""

    GENERATE_UNTIL_FORK: str = "Osaka"
    """The fork until which documentation should be generated."""

    DOCS_BASE_URL: str = "https://ethereum.github.io/execution-spec-tests"

    # Documentation URLs prefixed with `DOCS_URL__` to avoid conflicts with other URLs
    DOCS_URL__WRITING_TESTS: str = f"{DOCS_BASE_URL}/main/writing_tests/"
