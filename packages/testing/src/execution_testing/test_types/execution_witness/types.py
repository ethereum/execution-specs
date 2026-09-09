"""Execution witness types."""

from typing import List

from pydantic import Field

from execution_testing.base_types import (
    Bytes,
    CamelModel,
)


class ExecutionWitness(CamelModel):
    """Execution witness for stateless validation."""

    state: List[Bytes] = Field(default_factory=list)
    codes: List[Bytes] = Field(default_factory=list)
    headers: List[Bytes] = Field(default_factory=list)
