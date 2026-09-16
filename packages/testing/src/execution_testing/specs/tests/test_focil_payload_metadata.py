"""Regression tests for Engine API inclusion-list payload metadata."""

from typing import Any

import pytest

from execution_testing.fixtures.blockchain import FixtureEngineNewPayload

from ..blockchain import BuiltBlock


@pytest.mark.parametrize(
    "validation_error,inclusion_list_satisfied,expected",
    [
        pytest.param(None, True, True, id="valid-satisfied"),
        pytest.param(None, False, False, id="valid-unsatisfied"),
        pytest.param(object(), True, None, id="invalid-satisfied"),
        pytest.param(object(), False, None, id="invalid-unsatisfied"),
    ],
)
def test_inclusion_list_result_only_emitted_for_valid_payloads(
    monkeypatch: pytest.MonkeyPatch,
    validation_error: object | None,
    inclusion_list_satisfied: bool,
    expected: bool | None,
) -> None:
    """Invalid payload fixtures must carry a null inclusion-list result."""
    captured: dict[str, Any] = {}
    sentinel = object()

    def capture(**kwargs: Any) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(
        FixtureEngineNewPayload,
        "from_fixture_header",
        staticmethod(capture),
    )

    # `model_construct` skips validation and
    # `get_fixture_engine_new_payload` only forwards these fields, so the
    # sentinels never need to satisfy the model's field types. Splat them
    # from an untyped dict so the type checker does not require them to.
    fields: dict[str, Any] = dict(
        fork=object(),
        header=object(),
        txs=[],
        withdrawals=None,
        requests=None,
        block_access_list=None,
        inclusion_list_txs=None,
        inclusion_list_satisfied=inclusion_list_satisfied,
        expected_exception=validation_error,
        engine_api_error_code=None,
        rlp_modifier=None,
        engine_new_payload_block_access_list=None,
        engine_new_payload_slot_number=None,
    )
    block = BuiltBlock.model_construct(**fields)

    assert block.get_fixture_engine_new_payload() is sentinel
    assert captured["inclusion_list_satisfied"] is expected
