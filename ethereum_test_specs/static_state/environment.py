"""Environment structure of ethereum/tests fillers."""

from pydantic import BaseModel, Field, model_validator

from .common import AddressInFiller, ValueInFiller


class EnvironmentInStateTestFiller(BaseModel):
    """Class that represents an environment filler."""

    current_coinbase: AddressInFiller = Field(..., alias="currentCoinbase")
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
