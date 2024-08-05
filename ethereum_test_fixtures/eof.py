"""
EOFTest Type Definitions
"""


from typing import Any, ClassVar, Mapping

from pydantic import Field

from ethereum_test_base_types import Bytes, CamelModel, Number
from ethereum_test_exceptions import EOFException
from ethereum_test_types.eof.v1 import ContainerKind

from .base import BaseFixture
from .formats import FixtureFormats


class Result(CamelModel):
    """
    Result for a single fork in a fixture.
    """

    exception: EOFException | None = None
    valid: bool = Field(..., alias="result")

    def model_post_init(self, __context: Any) -> None:
        """
        Simple cross-field validation that a test cannot have an empty exception if
        the valid is False.
        """
        if not self.valid and self.exception is None:
            raise ValueError("Invalid test: invalid but exception is not set")
        elif self.valid and self.exception is not None:
            raise ValueError("Invalid test: valid but exception is set")
        super().model_post_init(__context)


class Vector(CamelModel):
    """
    Single test vector in a fixture.
    """

    code: Bytes
    container_kind: ContainerKind = ContainerKind.RUNTIME
    results: Mapping[str, Result]


class Fixture(BaseFixture):
    """
    Fixture for a single EOFTest.
    """

    vectors: Mapping[Number, Vector]

    format: ClassVar[FixtureFormats] = FixtureFormats.EOF_TEST

    def get_fork(self) -> str | None:
        """
        Returns the fork of the fixture as a string.
        """
        return None
