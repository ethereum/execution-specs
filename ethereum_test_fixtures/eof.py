"""EOFTest Type Definitions."""

from typing import Any, ClassVar, Mapping

from pydantic import Field

from ethereum_test_base_types import Bytes, CamelModel, Number
from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList
from ethereum_test_types.eof.v1 import ContainerKind

from .base import BaseFixture


class Result(CamelModel):
    """Result for a single fork in a fixture."""

    exception: EOFExceptionInstanceOrList | None = None
    valid: bool = Field(..., alias="result")

    def model_post_init(self, __context: Any) -> None:
        """
        Cross-field validation that a test cannot have an empty exception if
        the valid is False.
        """
        if not self.valid and self.exception is None:
            raise ValueError("Invalid test: invalid but exception is not set")
        elif self.valid and self.exception is not None:
            raise ValueError("Invalid test: valid but exception is set")
        super().model_post_init(__context)


class Vector(CamelModel):
    """Single test vector in a fixture."""

    code: Bytes
    container_kind: ContainerKind = ContainerKind.RUNTIME
    results: Mapping[str, Result]


class EOFFixture(BaseFixture):
    """Fixture for a single EOFTest."""

    fixture_format_name: ClassVar[str] = "eof_test"
    description: ClassVar[str] = "Tests that generate an EOF test fixture."

    vectors: Mapping[Number, Vector]

    def get_fork(self) -> str | None:
        """Return fork of the fixture as a string."""
        return None
