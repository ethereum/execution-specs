"""
TransactionTest types
"""

from typing import ClassVar, Mapping

from pydantic import Field

from ethereum_test_base_types import Address, Bytes, Hash, ZeroPaddedHexNumber
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_types.types import CamelModel

from .base import BaseFixture


class FixtureResult(CamelModel):
    """
    The per-network (fork) result structure.
    """

    hash: Hash | None = None
    intrinsic_gas: ZeroPaddedHexNumber
    sender: Address | None = None
    exception: TransactionExceptionInstanceOrList | None = None


class Fixture(BaseFixture):
    """
    Fixture for a single TransactionTest.
    """

    fixture_format_name: ClassVar[str] = "transaction_test"
    description: ClassVar[str] = "Tests that generate a transaction test fixture."

    result: Mapping[str, FixtureResult]
    transaction: Bytes = Field(..., alias="txbytes")

    def get_fork(self) -> str | None:
        """
        Returns the fork of the fixture as a string.
        """
        forks = list(self.result.keys())
        assert len(forks) == 1, "Expected transaction test fixture with single fork"
        return forks[0]
