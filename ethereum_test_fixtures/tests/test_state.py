"""Test state spec types."""

from typing import Any, Dict

import pytest

from ethereum_test_base_types import Bytes, Hash, to_json
from ethereum_test_exceptions import TransactionException

from ..state import FixtureForkPost


@pytest.mark.parametrize(
    ["can_be_deserialized", "model_instance", "json"],
    [
        pytest.param(
            True,
            FixtureForkPost(
                state_root="0x00",
                logs_hash="0x01",
                tx_bytes="0x02",
                state={},
            ),
            {
                "hash": Hash(0).hex(),
                "logs": Hash(1).hex(),
                "txbytes": Bytes(b"\x02").hex(),
                "indexes": {"data": 0, "gas": 0, "value": 0},
                "state": {},
            },
            id="state_fixture_fork_post",
        ),
        pytest.param(
            True,
            FixtureForkPost(
                state_root="0x00",
                logs_hash="0x01",
                tx_bytes="0x02",
                expect_exception=TransactionException.INITCODE_SIZE_EXCEEDED,
                state={},
            ),
            {
                "hash": Hash(0).hex(),
                "logs": Hash(1).hex(),
                "txbytes": Bytes(b"\x02").hex(),
                "expectException": "TransactionException.INITCODE_SIZE_EXCEEDED",
                "indexes": {"data": 0, "gas": 0, "value": 0},
                "state": {},
            },
            id="state_fixture_fork_post_exception",
        ),
        pytest.param(
            False,  # Can not be deserialized: A single expect_exception str will not be
            # deserialized as a list and therefore will not match the model_instance definition.
            FixtureForkPost(
                state_root="0x00",
                logs_hash="0x01",
                tx_bytes="0x02",
                expect_exception=[TransactionException.INITCODE_SIZE_EXCEEDED],
                state={},
            ),
            {
                "hash": Hash(0).hex(),
                "logs": Hash(1).hex(),
                "txbytes": Bytes(b"\x02").hex(),
                "expectException": "TransactionException.INITCODE_SIZE_EXCEEDED",
                "indexes": {"data": 0, "gas": 0, "value": 0},
                "state": {},
            },
            id="state_fixture_fork_post_exception_list_1",
        ),
        pytest.param(
            True,
            FixtureForkPost(
                state_root="0x00",
                logs_hash="0x01",
                tx_bytes="0x02",
                expect_exception=[
                    TransactionException.INITCODE_SIZE_EXCEEDED,
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                ],
                state={},
            ),
            {
                "hash": Hash(0).hex(),
                "logs": Hash(1).hex(),
                "txbytes": Bytes(b"\x02").hex(),
                "expectException": "TransactionException.INITCODE_SIZE_EXCEEDED|"
                "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
                "indexes": {"data": 0, "gas": 0, "value": 0},
                "state": {},
            },
            id="state_fixture_fork_post_exception_list_2",
        ),
    ],
)
class TestPydanticModelConversion:
    """Test that Pydantic models are converted to and from JSON correctly."""

    def test_json_serialization(
        self, can_be_deserialized: bool, model_instance: Any, json: str | Dict[str, Any]
    ):
        """Test that to_json returns the expected JSON for the given object."""
        assert to_json(model_instance) == json

    def test_json_deserialization(
        self, can_be_deserialized: bool, model_instance: Any, json: str | Dict[str, Any]
    ):
        """Test that to_json returns the expected JSON for the given object."""
        if not can_be_deserialized:
            pytest.skip(reason="The model instance in this case can not be deserialized")
        model_type = type(model_instance)
        assert model_type(**json) == model_instance
