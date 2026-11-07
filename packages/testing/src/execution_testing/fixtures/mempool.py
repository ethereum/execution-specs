"""MempoolTest types."""

from typing import Annotated, ClassVar, Dict, List

from pydantic import BeforeValidator, Field, PlainSerializer

from execution_testing.base_types import (
    Alloc,
    Bytes,
    CamelModel,
    ZeroPaddedHexNumber,
)
from execution_testing.exceptions import (
    MempoolException,
    TransactionException,
)
from execution_testing.exceptions.exceptions.base import (
    from_pipe_str,
    to_pipe_str,
)
from execution_testing.forks import Fork, TransitionFork

from .base import BaseFixture
from .state import FixtureConfig

MempoolRejection = Annotated[
    List[MempoolException] | TransactionException | MempoolException,
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]
"""
Reason the pool refuses a transaction, or a list of reasons any of which
a pool may report, for a transaction that breaks several rules at once.
"""


class FixtureHead(CamelModel):
    """Header fields of the chain head that the pool validates against."""

    number: ZeroPaddedHexNumber
    timestamp: ZeroPaddedHexNumber
    gas_limit: ZeroPaddedHexNumber
    gas_used: ZeroPaddedHexNumber
    base_fee_per_gas: ZeroPaddedHexNumber | None = None
    excess_blob_gas: ZeroPaddedHexNumber | None = None
    blob_gas_used: ZeroPaddedHexNumber | None = None


class FixtureNextBlock(CamelModel):
    """Values of the next block, derived from the head."""

    number: ZeroPaddedHexNumber
    timestamp: ZeroPaddedHexNumber
    base_fee_per_gas: ZeroPaddedHexNumber | None = None
    excess_blob_gas: ZeroPaddedHexNumber | None = None


class FixturePolicy(CamelModel):
    """Pool configuration the consumer applies."""

    min_tip: ZeroPaddedHexNumber = ZeroPaddedHexNumber(0)


class MempoolFixture(BaseFixture):
    """Fixture for a single MempoolTest."""

    format_name: ClassVar[str] = "mempool_test"
    description: ClassVar[str] = (
        "Tests whether a client admits a transaction to its mempool and "
        "broadcasts it."
    )

    network: Fork
    config: FixtureConfig
    head: FixtureHead
    next_block: FixtureNextBlock
    pre: Alloc
    transaction: Bytes = Field(..., alias="txbytes")
    policy: FixturePolicy = Field(default_factory=FixturePolicy)
    broadcast: bool
    exception: MempoolRejection | None = None
    mempool_rules: Dict[str, str] | None = None

    def get_fork(self) -> Fork | TransitionFork | None:
        """Return the fork of the fixture."""
        return self.network
