"""
Ethereum test fixture verifyer abstract class.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .formats import FixtureFormats


class FixtureVerifier(ABC):
    """
    Abstract class for verifying Ethereum test fixtures.
    """

    @abstractmethod
    def verify_fixture(
        self,
        fixture_format: FixtureFormats,
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
