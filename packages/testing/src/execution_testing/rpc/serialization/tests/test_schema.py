"""Test validation of projected responses against the OpenRPC schema."""

from typing import Any, Dict

import pytest

from execution_testing.rpc.serialization import (
    SchemaViolationError,
    block_response,
    openrpc_spec,
    receipt_responses,
    validate_partial_result,
    validate_result,
)

from .test_projection import make_block, make_receipt, make_transaction


@pytest.fixture
def block_result() -> Dict[str, Any]:
    """Return a projected `eth_getBlockByNumber` result."""
    block = make_block(
        [make_transaction()], [make_receipt(21_000)], base_fee_per_gas=7
    )
    return block_response(block).to_rpc()


@pytest.fixture
def receipt_result() -> Dict[str, Any]:
    """Return a projected `eth_getTransactionReceipt` result."""
    block = make_block(
        [make_transaction()], [make_receipt(21_000)], base_fee_per_gas=7
    )
    return receipt_responses(block)[0].to_rpc()


def test_vendored_spec_loads() -> None:
    """The vendored schema parses and carries the methods we project."""
    names = {entry["name"] for entry in openrpc_spec()["methods"]}

    assert "eth_getBlockByNumber" in names
    assert "eth_getTransactionReceipt" in names


def test_unknown_method_is_rejected() -> None:
    """Validating an unknown method is a mistake, not a silent pass."""
    with pytest.raises(KeyError, match="eth_notAMethod"):
        validate_result("eth_notAMethod", {})


def test_projected_block_conforms(block_result: Dict[str, Any]) -> None:
    """A projected block satisfies its result schema."""
    validate_result("eth_getBlockByNumber", block_result)


def test_projected_receipt_conforms(receipt_result: Dict[str, Any]) -> None:
    """A projected receipt satisfies its result schema."""
    validate_result("eth_getTransactionReceipt", receipt_result)


@pytest.mark.parametrize(
    "field,value",
    [
        pytest.param("number", "0x01", id="zero_padded_quantity"),
        pytest.param("gasUsed", 21_000, id="quantity_as_integer"),
        pytest.param("hash", "0xdeadbeef", id="undersized_hash"),
        pytest.param("miner", "0x1234", id="malformed_address"),
    ],
)
def test_malformed_block_fields_are_caught(
    block_result: Dict[str, Any], field: str, value: Any
) -> None:
    """
    Known-bad values are rejected rather than passing silently.

    Without this the conformance suite could report success purely because
    the schema is permissive.
    """
    block_result[field] = value

    with pytest.raises(SchemaViolationError, match="eth_getBlockByNumber"):
        validate_result("eth_getBlockByNumber", block_result)


@pytest.mark.parametrize(
    "field",
    ["size", "transactions", "logsBloom", "number"],
)
def test_missing_required_block_fields_are_caught(
    block_result: Dict[str, Any], field: str
) -> None:
    """Dropping a required field is a violation."""
    del block_result[field]

    with pytest.raises(SchemaViolationError):
        validate_result("eth_getBlockByNumber", block_result)


@pytest.mark.parametrize(
    "field",
    ["effectiveGasPrice", "from", "cumulativeGasUsed", "logs"],
)
def test_missing_required_receipt_fields_are_caught(
    receipt_result: Dict[str, Any], field: str
) -> None:
    """Dropping a required receipt field is a violation."""
    del receipt_result[field]

    with pytest.raises(SchemaViolationError):
        validate_result("eth_getTransactionReceipt", receipt_result)


def test_violation_message_names_the_offending_field(
    receipt_result: Dict[str, Any],
) -> None:
    """The error identifies where the response went wrong."""
    receipt_result["logsBloom"] = "0x00"

    with pytest.raises(SchemaViolationError, match="logsBloom"):
        validate_result("eth_getTransactionReceipt", receipt_result)


@pytest.mark.parametrize(
    "field",
    ["size", "transactions", "logsBloom", "number"],
)
def test_partial_validation_waives_completeness(
    block_result: Dict[str, Any], field: str
) -> None:
    """
    An expectation naming only some fields is accepted.

    This is the whole difference between the two validators, and the
    reason `eth_config` can assert the five fields the spec reproduces
    without inventing the sixth.
    """
    del block_result[field]

    with pytest.raises(SchemaViolationError):
        validate_result("eth_getBlockByNumber", block_result)
    validate_partial_result("eth_getBlockByNumber", block_result)


@pytest.mark.parametrize(
    "field,value",
    [
        pytest.param("number", "0x01", id="zero_padded_quantity"),
        pytest.param("gasUsed", 21_000, id="quantity_as_integer"),
        pytest.param("hash", "0xdeadbeef", id="undersized_hash"),
        pytest.param("miner", "0x1234", id="malformed_address"),
    ],
)
def test_partial_validation_still_rejects_bad_values(
    field: str, value: Any
) -> None:
    """
    Only completeness is waived; every other clause still binds.

    Otherwise the partial tier would be a hole in the guard rather than a
    narrowing of it, and a projection bug in an asserted field would reach
    a released fixture.
    """
    partial = {field: value}

    with pytest.raises(SchemaViolationError):
        validate_partial_result("eth_getBlockByNumber", partial)


def test_partial_validation_rejects_an_unmodelled_field() -> None:
    """
    A field the schema does not define is still a projection bug.

    Receipts set `additionalProperties: false`, so asserting a field no
    conforming client returns could never be satisfied.
    """
    with pytest.raises(SchemaViolationError, match="invented"):
        validate_partial_result(
            "eth_getTransactionReceipt", {"invented": "0x1"}
        )


def test_partial_validation_accepts_a_single_field_of_a_one_of() -> None:
    """
    Relaxing an exclusive choice does not make a valid subset ambiguous.

    `eth_config` nests two `oneOf`s of a fork configuration and null, and
    a subset of the configuration matches the relaxed form of both
    branches. Under `oneOf` that is a failure; the relaxation turns it
    into `anyOf` precisely so it is not.
    """
    validate_partial_result("eth_config", {"current": {"chainId": "0x1"}})
