"""
Ethereum test fixture verifyer abstract class.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .base import FixtureFormat


class FixtureVerifier(ABC):
    """
    Abstract class for verifying Ethereum test fixtures.
    """

    def is_verifiable(
        self,
        fixture_format: FixtureFormat,
    ) -> bool:
        """
        Returns whether the fixture format is verifiable by this verifier.
        """
        return False

    @abstractmethod
    def verify_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: str | None = None,
        debug_output_path: Path | None = None,
    ):
        """
        Executes `evm [state|block]test` to verify the fixture at `fixture_path`.

        Currently only implemented by geth's evm.
        """
        raise NotImplementedError(
            "The `verify_fixture()` function is not supported by this tool. Use geth's evm tool."
        )
