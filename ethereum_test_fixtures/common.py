"""Common types used to define multiple fixture types."""

from typing import Dict

from pydantic import Field, model_serializer

from ethereum_test_base_types import (
    BlobSchedule,
    CamelModel,
    EthereumTestRootModel,
    ZeroPaddedHexNumber,
)
from ethereum_test_types.types import Address, AuthorizationTupleGeneric


class FixtureForkBlobSchedule(CamelModel):
    """Representation of the blob schedule of a given fork."""

    target_blobs_per_block: ZeroPaddedHexNumber = Field(..., alias="target")
    max_blobs_per_block: ZeroPaddedHexNumber = Field(..., alias="max")
    base_fee_update_fraction: ZeroPaddedHexNumber = Field(...)


class FixtureBlobSchedule(EthereumTestRootModel[Dict[str, FixtureForkBlobSchedule]]):
    """Blob schedule configuration dictionary."""

    root: Dict[str, FixtureForkBlobSchedule] = Field(default_factory=dict, validate_default=True)

    @classmethod
    def from_blob_schedule(
        cls, blob_schedule: BlobSchedule | None
    ) -> "FixtureBlobSchedule | None":
        """Return a FixtureBlobSchedule from a BlobSchedule."""
        if blob_schedule is None:
            return None
        return cls(
            root=blob_schedule.model_dump(),
        )


class FixtureAuthorizationTuple(AuthorizationTupleGeneric[ZeroPaddedHexNumber]):
    """Authorization tuple for fixture transactions."""

    signer: Address | None = None

    @classmethod
    def from_authorization_tuple(
        cls, auth_tuple: AuthorizationTupleGeneric
    ) -> "FixtureAuthorizationTuple":
        """Return FixtureAuthorizationTuple from an AuthorizationTuple."""
        return cls(**auth_tuple.model_dump())

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def duplicate_v_as_y_parity(self, serializer):
        """
        Add a duplicate 'yParity' field (same as `v`) in JSON fixtures.

        Background: https://github.com/erigontech/erigon/issues/14073
        """
        data = serializer(self)
        if "v" in data and data["v"] is not None:
            data["yParity"] = data["v"]
        return data
