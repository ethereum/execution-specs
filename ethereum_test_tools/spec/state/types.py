"""
StateTest types
"""

from typing import ClassVar, List, Mapping, Sequence

from pydantic import BaseModel, Field

from evm_transition_tool import FixtureFormats

from ...common.base_types import Address, Bytes, Hash, ZeroPaddedHexNumber
from ...common.types import (
    AccessList,
    Alloc,
    CamelModel,
    EnvironmentGeneric,
    Transaction,
    TransactionToEmptyStringHandler,
)
from ...exceptions import TransactionException, TransactionExceptionList
from ..base.base_test import BaseFixture


class FixtureEnvironment(EnvironmentGeneric[ZeroPaddedHexNumber]):
    """
    Type used to describe the environment of a state test.
    """

    prev_randao: Hash | None = Field(None, alias="currentRandom")  # type: ignore


class FixtureTransaction(TransactionToEmptyStringHandler):
    """
    Type used to describe a transaction in a state test.
    """

    nonce: ZeroPaddedHexNumber
    gas_price: ZeroPaddedHexNumber | None = None
    max_priority_fee_per_gas: ZeroPaddedHexNumber | None = None
    max_fee_per_gas: ZeroPaddedHexNumber | None = None
    gas_limit: List[ZeroPaddedHexNumber]
    to: Address | None = None
    value: List[ZeroPaddedHexNumber]
    data: List[Bytes]
    access_lists: List[List[AccessList]] | None = None
    max_fee_per_blob_gas: ZeroPaddedHexNumber | None = None
    blob_versioned_hashes: Sequence[Hash] | None = None
    sender: Address | None = None
    secret_key: Hash | None = None

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """
        Returns a FixtureTransaction from a Transaction.
        """
        return cls(
            **tx.model_dump(
                exclude={"gas_limit", "value", "data", "access_list"}, exclude_none=True
            ),
            gas_limit=[tx.gas_limit],
            value=[tx.value],
            data=[tx.data],
            access_lists=[tx.access_list] if tx.access_list is not None else None,
        )


class FixtureForkPostIndexes(BaseModel):
    """
    Type used to describe the indexes of a single post state of a single Fork.
    """

    data: int = 0
    gas: int = 0
    value: int = 0


class FixtureForkPost(CamelModel):
    """
    Type used to describe the post state of a single Fork.
    """

    state_root: Hash = Field(..., alias="hash")
    logs_hash: Hash = Field(..., alias="logs")
    tx_bytes: Bytes = Field(..., alias="txbytes")
    indexes: FixtureForkPostIndexes = Field(default_factory=FixtureForkPostIndexes)
    expect_exception: TransactionExceptionList | TransactionException | None = None


class Fixture(BaseFixture):
    """
    Fixture for a single StateTest.
    """

    env: FixtureEnvironment
    pre: Alloc
    transaction: FixtureTransaction
    post: Mapping[str, List[FixtureForkPost]]

    format: ClassVar[FixtureFormats] = FixtureFormats.STATE_TEST
