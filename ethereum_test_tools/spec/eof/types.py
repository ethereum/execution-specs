"""
EOFTest Type Definitions
"""


from typing import Any, ClassVar, Mapping

from pydantic import Field

from evm_transition_tool import FixtureFormats

from ...common.base_types import Bytes
from ...common.types import CamelModel
from ...exceptions import EOFException
from ..base.base_test import BaseFixture


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
    results: Mapping[str, Result]


class Fixture(BaseFixture):
    """
    Fixture for a single EOFTest.
    """

    vectors: Mapping[str, Vector]

    format: ClassVar[FixtureFormats] = FixtureFormats.EOF_TEST
