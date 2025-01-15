"""StateTest types."""

from typing import ClassVar, List, Mapping, Sequence

from pydantic import BaseModel, Field

from ethereum_test_base_types import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    Hash,
    ZeroPaddedHexNumber,
)
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_types.types import (
    AuthorizationTupleGeneric,
    CamelModel,
    EnvironmentGeneric,
    Transaction,
    TransactionFixtureConverter,
)

from .base import BaseFixture
from .common import FixtureBlobSchedule


class FixtureEnvironment(EnvironmentGeneric[ZeroPaddedHexNumber]):
    """Type used to describe the environment of a state test."""

    prev_randao: Hash | None = Field(None, alias="currentRandom")  # type: ignore


class FixtureAuthorizationTuple(AuthorizationTupleGeneric[ZeroPaddedHexNumber]):
    """Authorization tuple for fixture transactions."""

    signer: Address | None = None

    @classmethod
    def from_authorization_tuple(
        cls, auth_tuple: AuthorizationTupleGeneric
    ) -> "FixtureAuthorizationTuple":
        """Return FixtureAuthorizationTuple from an AuthorizationTuple."""
        return cls(**auth_tuple.model_dump())


class FixtureTransaction(TransactionFixtureConverter):
    """Type used to describe a transaction in a state test."""

    nonce: ZeroPaddedHexNumber
    gas_price: ZeroPaddedHexNumber | None = None
    max_priority_fee_per_gas: ZeroPaddedHexNumber | None = None
    max_fee_per_gas: ZeroPaddedHexNumber | None = None
    gas_limit: List[ZeroPaddedHexNumber]
    to: Address | None = None
    value: List[ZeroPaddedHexNumber]
    data: List[Bytes]
    access_lists: List[List[AccessList]] | None = None
    authorization_list: List[FixtureAuthorizationTuple] | None = None
    max_fee_per_blob_gas: ZeroPaddedHexNumber | None = None
    blob_versioned_hashes: Sequence[Hash] | None = None
    sender: Address | None = None
    secret_key: Hash | None = None

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """Return FixtureTransaction from a Transaction."""
        model_as_dict = tx.model_dump(
            exclude={"gas_limit", "value", "data", "access_list"}, exclude_none=True
        )
        model_as_dict["gas_limit"] = [tx.gas_limit]
        model_as_dict["value"] = [tx.value]
        model_as_dict["data"] = [tx.data]
        model_as_dict["access_lists"] = [tx.access_list] if tx.access_list is not None else None
        return cls(**model_as_dict)


class FixtureForkPostIndexes(BaseModel):
    """Type used to describe the indexes of a single post state of a single Fork."""

    data: int = 0
    gas: int = 0
    value: int = 0


class FixtureForkPost(CamelModel):
    """Type used to describe the post state of a single Fork."""

    state_root: Hash = Field(..., alias="hash")
    logs_hash: Hash = Field(..., alias="logs")
    tx_bytes: Bytes = Field(..., alias="txbytes")
    indexes: FixtureForkPostIndexes = Field(default_factory=FixtureForkPostIndexes)
    state: Alloc
    expect_exception: TransactionExceptionInstanceOrList | None = None


class FixtureConfig(CamelModel):
    """Chain configuration for a fixture."""

    blob_schedule: FixtureBlobSchedule | None = None


class StateFixture(BaseFixture):
    """Fixture for a single StateTest."""

    fixture_format_name: ClassVar[str] = "state_test"
    description: ClassVar[str] = "Tests that generate a state test fixture."

    env: FixtureEnvironment
    pre: Alloc
    transaction: FixtureTransaction
    post: Mapping[str, List[FixtureForkPost]]
    config: FixtureConfig

    def get_fork(self) -> str | None:
        """Return fork of the fixture as a string."""
        forks = list(self.post.keys())
        assert len(forks) == 1, "Expected state test fixture with single fork"
        return forks[0]
