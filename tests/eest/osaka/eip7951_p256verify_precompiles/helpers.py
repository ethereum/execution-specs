"""Helper functions for the EIP-7951 P256VERIFY precompiles tests."""

import os
from typing import Annotated, List

import pytest
from pydantic import BaseModel, BeforeValidator, ConfigDict, RootModel, TypeAdapter
from pydantic.alias_generators import to_pascal


def current_python_script_directory(*args: str) -> str:
    """Get the current Python script directory, optionally appending additional path components."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)


class Vector(BaseModel):
    """Test vector for the secp256r1 precompile."""

    input: Annotated[bytes, BeforeValidator(bytes.fromhex)]
    expected: Annotated[bytes, BeforeValidator(bytes.fromhex)]
    gas: int
    name: str

    model_config = ConfigDict(alias_generator=to_pascal)

    def to_pytest_param(self):
        """Convert the test vector to a tuple that can be used as a parameter in a pytest test."""
        return pytest.param(self.input, self.expected, self.gas, id=self.name)


class FailVector(BaseModel):
    """Test vector for the BLS12-381 precompiles."""

    input: Annotated[bytes, BeforeValidator(bytes.fromhex)]
    expected_error: str
    name: str

    model_config = ConfigDict(alias_generator=to_pascal)

    def to_pytest_param(self):
        """Convert the test vector to a tuple that can be used as a parameter in a pytest test."""
        return pytest.param(self.input, id=self.name)


class VectorList(RootModel):
    """List of test vectors for the secp256r1 precompile."""

    root: List[Vector | FailVector]


VectorListAdapter = TypeAdapter(VectorList)


def vectors_from_file(filename: str) -> List:
    """Load test vectors from a file."""
    with open(
        current_python_script_directory(
            "vectors",
            filename,
        ),
        "rb",
    ) as f:
        vectors_list = VectorListAdapter.validate_json(f.read())
        all_inputs = set()
        for vector in vectors_list.root:
            if vector.input in all_inputs:
                raise ValueError(f"Duplicate input: {vector.input.hex()}")
            all_inputs.add(vector.input)
        return [v.to_pytest_param() for v in vectors_list.root]
