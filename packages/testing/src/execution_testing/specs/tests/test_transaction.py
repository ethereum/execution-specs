"""Test suite for the transaction spec test generation."""

import json
from os.path import realpath
from pathlib import Path

import pytest

from execution_testing import TestAddress
from execution_testing.fixtures import TransactionFixture
from execution_testing.forks import Amsterdam, Fork, Shanghai
from execution_testing.test_types import Transaction

from ..transaction import TransactionTest
from .helpers import remove_info_metadata

CURRENT_FOLDER = Path(realpath(__file__)).parent
FIXTURES_FOLDER = CURRENT_FOLDER / "fixtures"


@pytest.mark.parametrize(
    "name, tx, fork",
    [
        pytest.param("simple_type_0", Transaction(gas_limit=0x5208), Shanghai),
    ],
)
def test_transaction_test_filling(
    name: str, tx: Transaction, fork: Fork
) -> None:
    """Test the transaction test filling."""
    generated_fixture = (
        TransactionTest(
            tx=tx.with_signature_and_sender(),
            fork=fork,
        )
        .generate(
            t8n=None,  # type: ignore
            fixture_format=TransactionFixture,
        )
        .fixture
    )
    assert generated_fixture.__class__ == TransactionFixture
    fixture_json_dict = generated_fixture.json_dict_with_info()
    fixture = {
        "fixture": fixture_json_dict,
    }

    expected_json_file = f"tx_{name}_{fork.name().lower()}.json"

    expected = json.loads((FIXTURES_FOLDER / expected_json_file).read_text())
    remove_info_metadata(expected)

    remove_info_metadata(fixture)
    assert fixture == expected


@pytest.mark.parametrize(
    "tx,expected_intrinsic_gas",
    [
        pytest.param(
            Transaction(gas_limit=100_000),
            15_000,
            id="non_value_transfer",
        ),
        pytest.param(
            Transaction(gas_limit=100_000, value=1),
            21_000,
            id="value_transfer",
        ),
        pytest.param(
            Transaction(gas_limit=100_000, to=TestAddress),
            12_000,
            id="self_transfer",
        ),
    ],
)
def test_amsterdam_transaction_fixture_intrinsic_gas(
    tx: Transaction,
    expected_intrinsic_gas: int,
) -> None:
    """Calculate Amsterdam intrinsic gas from transaction context."""
    fixture = (
        TransactionTest(
            tx=tx.with_signature_and_sender(),
            fork=Amsterdam,
        )
        .generate(
            t8n=None,  # type: ignore
            fixture_format=TransactionFixture,
        )
        .fixture
    )
    assert isinstance(fixture, TransactionFixture)
    result = next(iter(fixture.result.values()))
    assert result.intrinsic_gas == expected_intrinsic_gas
