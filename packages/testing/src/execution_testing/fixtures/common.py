"""Common types used to define multiple fixture types."""

from typing import Any, Dict

from pydantic import AliasChoices, Field, model_validator

from execution_testing.base_types import (
    BlobSchedule,
    CamelModel,
    EthereumTestRootModel,
    SignableRLPSerializable,
    ZeroPaddedHexNumber,
)
from execution_testing.test_types.account_types import Address
from execution_testing.test_types.transaction_types import (
    AuthorizationTupleGeneric,
)


class FixtureForkBlobSchedule(CamelModel):
    """Representation of the blob schedule of a given fork."""

    target_blobs_per_block: ZeroPaddedHexNumber = Field(..., alias="target")
    max_blobs_per_block: ZeroPaddedHexNumber = Field(..., alias="max")
    base_fee_update_fraction: ZeroPaddedHexNumber = Field(...)


class FixtureBlobSchedule(
    EthereumTestRootModel[Dict[str, FixtureForkBlobSchedule]]
):
    """Blob schedule configuration dictionary."""

    root: Dict[str, FixtureForkBlobSchedule] = Field(
        default_factory=dict, validate_default=True
    )

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


class FixtureAuthorizationTuple(
    AuthorizationTupleGeneric[ZeroPaddedHexNumber], SignableRLPSerializable
):
    """Authorization tuple for fixture transactions."""

    # Allow extra fields: FixtureAuthorizationTuple is constructed from
    # AuthorizationTuple via model_dump(), which includes fields not in this model.
    model_config = CamelModel.model_config | {"extra": "ignore"}

    v: ZeroPaddedHexNumber = Field(
        validation_alias=AliasChoices("v", "yParity")
    )
    r: ZeroPaddedHexNumber
    s: ZeroPaddedHexNumber

    signer: Address | None = None

    @model_validator(mode="before")
    @classmethod
    def strip_y_parity_duplicate(cls, data: Any) -> Any:
        """
        Strip yParity if v is present since yParity is added as a duplicate
        during serialization for compatibility.
        """
        if isinstance(data, dict) and "v" in data and "yParity" in data:
            data.pop("yParity")
        return data

    @classmethod
    def from_authorization_tuple(
        cls, auth_tuple: AuthorizationTupleGeneric
    ) -> "FixtureAuthorizationTuple":
        """Return FixtureAuthorizationTuple from an AuthorizationTuple."""
        # Exclude fields that don't exist in FixtureAuthorizationTuple
        auth_dump = auth_tuple.model_dump()
        auth_dump.pop("secret_key", None)
        return cls(**auth_dump)

    def sign(self) -> None:
        """Sign the current object for further serialization."""
        # No-op, as the object is always already signed
        return
