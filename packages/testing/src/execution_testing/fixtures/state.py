"""StateTest types."""

from typing import ClassVar, List, Mapping, Sequence

from pydantic import BaseModel, Field

from execution_testing.base_types import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    CamelModel,
    Hash,
    ZeroPaddedHexNumber,
)
from execution_testing.exceptions import TransactionExceptionInstanceOrList
from execution_testing.forks import Fork
from execution_testing.test_types.block_types import EnvironmentGeneric
from execution_testing.test_types.transaction_types import (
    Transaction,
    TransactionFixtureConverter,
)

from .base import BaseFixture
from .common import (
    FixtureAuthorizationTuple,
    FixtureBlobSchedule,
    FixtureTransactionReceipt,
)


class FixtureEnvironment(EnvironmentGeneric[ZeroPaddedHexNumber]):
    """Type used to describe the environment of a state test."""

    # Allow extra fields: FixtureEnvironment is constructed from Environment
    # via model_dump(), which includes many fields not in EnvironmentGeneric.
    model_config = CamelModel.model_config | {"extra": "ignore"}

    prev_randao: Hash | None = Field(None, alias="currentRandom")  # type: ignore


class FixtureTransaction(TransactionFixtureConverter):
    """Type used to describe a transaction in a state test."""

    # Allow extra fields: FixtureTransaction is constructed from Transaction
    # via model_dump(), which includes many fields not in this model.
    model_config = CamelModel.model_config | {"extra": "ignore"}

    nonce: ZeroPaddedHexNumber
    gas_price: ZeroPaddedHexNumber | None = None
    max_priority_fee_per_gas: ZeroPaddedHexNumber | None = None
    max_fee_per_gas: ZeroPaddedHexNumber | None = None
    gas_limit: List[ZeroPaddedHexNumber]
    to: Address | None = None
    value: List[ZeroPaddedHexNumber]
    data: List[Bytes]
    access_lists: List[List[AccessList] | None] | None = None
    authorization_list: List[FixtureAuthorizationTuple] | None = None
    initcodes: List[Bytes] | None = None
    max_fee_per_blob_gas: ZeroPaddedHexNumber | None = None
    blob_versioned_hashes: Sequence[Hash] | None = None
    sender: Address | None = None
    secret_key: Hash | None = None

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """Return FixtureTransaction from a Transaction."""
        model_as_dict = tx.model_dump(
            exclude={"gas_limit", "value", "data", "access_list"},
            exclude_none=True,
        )
        model_as_dict["gas_limit"] = [tx.gas_limit]
        model_as_dict["value"] = [tx.value]
        model_as_dict["data"] = [tx.data]
        model_as_dict["access_lists"] = (
            [tx.access_list] if tx.access_list is not None else None
        )
        return cls(**model_as_dict)


class FixtureForkPostIndexes(BaseModel):
    """
    Type used to describe the indexes of a single post state of a single Fork.
    """

    data: int = 0
    gas: int = 0
    value: int = 0


class FixtureForkPost(CamelModel):
    """Type used to describe the post state of a single Fork."""

    state_root: Hash = Field(..., alias="hash")
    logs_hash: Hash = Field(..., alias="logs")
    receipt: FixtureTransactionReceipt | None = None
    tx_bytes: Bytes = Field(..., alias="txbytes")
    indexes: FixtureForkPostIndexes = Field(
        default_factory=FixtureForkPostIndexes
    )
    state: Alloc
    expect_exception: TransactionExceptionInstanceOrList | None = None


class FixtureConfig(CamelModel):
    """Chain configuration for a fixture."""

    blob_schedule: FixtureBlobSchedule | None = None
    chain_id: ZeroPaddedHexNumber = Field(
        ZeroPaddedHexNumber(1), alias="chainid"
    )


class StateFixture(BaseFixture):
    """Fixture for a single StateTest."""

    format_name: ClassVar[str] = "state_test"
    description: ClassVar[str] = "Tests that generate a state test fixture."

    env: FixtureEnvironment
    pre: Alloc
    transaction: FixtureTransaction
    post: Mapping[Fork, List[FixtureForkPost]]
    config: FixtureConfig

    def get_fork(self) -> Fork | None:
        """Return fork of the fixture as a string."""
        forks = list(self.post.keys())
        assert len(forks) == 1, "Expected state test fixture with single fork"
        return forks[0]
