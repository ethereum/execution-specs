"""Environment structure of ethereum/tests fillers."""

from typing import Any, Dict

from pydantic import BaseModel, Field, model_validator

from ethereum_test_base_types import Address
from ethereum_test_types import Environment

from .common import AddressOrTagInFiller, Tag, TagDict, ValueInFiller


class EnvironmentInStateTestFiller(BaseModel):
    """Class that represents an environment filler."""

    current_coinbase: AddressOrTagInFiller = Field(..., alias="currentCoinbase")
    current_gas_limit: ValueInFiller = Field(..., alias="currentGasLimit")
    current_number: ValueInFiller = Field(..., alias="currentNumber")
    current_timestamp: ValueInFiller = Field(..., alias="currentTimestamp")

    current_difficulty: ValueInFiller | None = Field(
        ValueInFiller("0x020000"), alias="currentDifficulty"
    )
    current_random: ValueInFiller | None = Field(ValueInFiller("0x020000"), alias="currentRandom")
    current_base_fee: ValueInFiller | None = Field(ValueInFiller("0x0a"), alias="currentBaseFee")

    current_excess_blob_gas: ValueInFiller | None = Field(None, alias="currentExcessBlobGas")

    class Config:
        """Model Config."""

        extra = "forbid"

    @model_validator(mode="after")
    def check_fields(self) -> "EnvironmentInStateTestFiller":
        """Validate all fields are set."""
        if self.current_difficulty is None:
            if self.current_random is None:
                raise ValueError("If `currentDifficulty` is not set, `currentRandom` must be set!")
        return self

    def get_environment(self, tags: TagDict) -> Environment:
        """Get the environment."""
        kwargs: Dict[str, Any] = {}
        if isinstance(self.current_coinbase, Tag):
            assert self.current_coinbase.name in tags, (
                f"Tag {self.current_coinbase.name} to resolve coinbase not found in tags"
            )
            kwargs["fee_recipient"] = self.current_coinbase.resolve(tags)
        else:
            kwargs["fee_recipient"] = Address(self.current_coinbase)
        if self.current_difficulty is not None:
            kwargs["difficulty"] = self.current_difficulty
        if self.current_random is not None:
            kwargs["prev_randao"] = self.current_random
        if self.current_gas_limit is not None:
            kwargs["gas_limit"] = self.current_gas_limit
        if self.current_number is not None:
            kwargs["number"] = self.current_number
        if self.current_timestamp is not None:
            kwargs["timestamp"] = self.current_timestamp
        if self.current_base_fee is not None:
            kwargs["base_fee_per_gas"] = self.current_base_fee
        if self.current_excess_blob_gas is not None:
            kwargs["excess_blob_gas"] = self.current_excess_blob_gas
        return Environment(**kwargs)
