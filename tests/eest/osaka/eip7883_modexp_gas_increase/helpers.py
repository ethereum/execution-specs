"""Helper functions for the EIP-7883 ModExp gas cost increase tests."""

import os
from typing import Annotated, List

import pytest
from pydantic import BaseModel, ConfigDict, Field, PlainValidator, RootModel, TypeAdapter
from pydantic.alias_generators import to_pascal

from ethereum_test_tools import Bytes

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput


def current_python_script_directory(*args: str) -> str:
    """Get the current Python script directory."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)


class Vector(BaseModel):
    """A vector for the ModExp gas cost increase tests."""

    modexp_input: Annotated[ModExpInput, PlainValidator(ModExpInput.from_bytes)] = Field(
        ..., alias="Input"
    )
    modexp_expected: Bytes = Field(..., alias="Expected")
    name: str = Field(..., alias="Name")
    gas_old: int | None = Field(default=None, alias="GasOld")
    gas_new: int | None = Field(default=None, alias="GasNew")

    model_config = ConfigDict(alias_generator=to_pascal)

    def to_pytest_param(self):
        """Convert the test vector to a tuple that can be used as a parameter in a pytest test."""
        return pytest.param(
            self.modexp_input, self.modexp_expected, self.gas_old, self.gas_new, id=self.name
        )


class VectorList(RootModel):
    """A list of test vectors for the ModExp gas cost increase tests."""

    root: List[Vector]


VectorListAdapter = TypeAdapter(VectorList)


def vectors_from_file(filename: str) -> List:
    """Load test vectors from a file."""
    with open(
        current_python_script_directory(
            "vector",
            filename,
        ),
        "rb",
    ) as f:
        return [v.to_pytest_param() for v in VectorListAdapter.validate_json(f.read()).root]
