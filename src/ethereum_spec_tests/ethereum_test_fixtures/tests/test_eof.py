"""Test the EOF fixture types."""

from typing import Any, Dict

import pytest

from ethereum_test_base_types import Bytes, to_json
from ethereum_test_exceptions import EOFException

from ..eof import ContainerKind, EOFFixture, Result, Vector


@pytest.mark.parametrize(
    ["can_be_deserialized", "model_instance", "json_repr"],
    [
        pytest.param(
            True,
            EOFFixture(
                vectors={
                    1: Vector(
                        code=Bytes(b"\x00"),
                        container_kind=ContainerKind.INITCODE,
                        results={
                            "Paris": Result(
                                exception=None,
                                valid=True,
                            ),
                        },
                    ),
                }
            ),
            {
                "vectors": {
                    "1": {
                        "code": "0x00",
                        "containerKind": "INITCODE",
                        "results": {
                            "Paris": {
                                "result": True,
                            },
                        },
                    },
                },
            },
            id="eof_fixture",
        ),
        pytest.param(
            True,
            EOFFixture(
                vectors={
                    1: Vector(
                        code=Bytes(b"\x00"),
                        container_kind=ContainerKind.RUNTIME,
                        results={
                            "Paris": Result(
                                exception=EOFException.INVALID_MAGIC,
                                valid=False,
                            ),
                        },
                    ),
                }
            ),
            {
                "vectors": {
                    "1": {
                        "code": "0x00",
                        "containerKind": "RUNTIME",
                        "results": {
                            "Paris": {
                                "exception": "EOFException.INVALID_MAGIC",
                                "result": False,
                            },
                        },
                    },
                },
            },
            id="eof_fixture_with_exception",
        ),
    ],
)
class TestPydanticModelConversion:
    """Test that Pydantic models are converted to and from JSON correctly."""

    def test_json_serialization(
        self, can_be_deserialized: bool, model_instance: Any, json_repr: str | Dict[str, Any]
    ):
        """Test that to_json returns the expected JSON for the given object."""
        serialized = to_json(model_instance)
        serialized.pop("_info")
        assert serialized == json_repr

    def test_json_deserialization(
        self, can_be_deserialized: bool, model_instance: Any, json_repr: str | Dict[str, Any]
    ):
        """Test that to_json returns the expected JSON for the given object."""
        if not can_be_deserialized:
            pytest.skip(reason="The model instance in this case can not be deserialized")
        model_type = type(model_instance)
        assert model_type(**json_repr) == model_instance
