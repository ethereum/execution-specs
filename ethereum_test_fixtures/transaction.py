"""TransactionTest types."""

from typing import ClassVar, Mapping

from pydantic import Field

from ethereum_test_base_types import Address, Bytes, CamelModel, Hash, ZeroPaddedHexNumber
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_forks import Fork

from .base import BaseFixture


class FixtureResult(CamelModel):
    """The per-network (fork) result structure."""

    hash: Hash | None = None
    intrinsic_gas: ZeroPaddedHexNumber
    sender: Address | None = None
    exception: TransactionExceptionInstanceOrList | None = None


class TransactionFixture(BaseFixture):
    """Fixture for a single TransactionTest."""

    format_name: ClassVar[str] = "transaction_test"
    description: ClassVar[str] = "Tests that generate a transaction test fixture."

    result: Mapping[Fork, FixtureResult]
    transaction: Bytes = Field(..., alias="txbytes")

    def get_fork(self) -> Fork | None:
        """Return the fork of the fixture as a string."""
        forks = list(self.result.keys())
        assert len(forks) == 1, "Expected transaction test fixture with single fork"
        return forks[0]
