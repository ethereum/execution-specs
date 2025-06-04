"""Helper functions for the EIP-7883 ModExp gas cost increase tests."""

import json
import os
from typing import Annotated, List

from pydantic import BaseModel, Field, PlainValidator

from ethereum_test_tools import Bytes

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput


class Vector(BaseModel):
    """A vector for the ModExp gas cost increase tests."""

    input: Annotated[ModExpInput, PlainValidator(ModExpInput.from_bytes)] = Field(
        ..., alias="Input"
    )
    expected: Bytes = Field(..., alias="Expected")
    name: str = Field(..., alias="Name")
    gas_old: int | None = Field(..., alias="GasOld")
    gas_new: int | None = Field(..., alias="GasNew")

    @staticmethod
    def from_json(vector_json: dict) -> "Vector":
        """Create a Vector from a JSON dictionary."""
        return Vector.model_validate(vector_json)

    @staticmethod
    def from_file(filename: str) -> List["Vector"]:
        """Create a list of Vectors from a file."""
        with open(current_python_script_directory(filename), "r") as f:
            vectors_json = json.load(f)
            return [Vector.from_json(vector_json) for vector_json in vectors_json]


def current_python_script_directory(*args: str) -> str:
    """Get the current Python script directory."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)
