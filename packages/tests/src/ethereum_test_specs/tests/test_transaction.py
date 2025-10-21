"""Test suite for the transaction spec test generation."""

import json
from os.path import realpath
from pathlib import Path

import pytest

from ethereum_test_fixtures import TransactionFixture
from ethereum_test_forks import Fork, Shanghai
from ethereum_test_types import Transaction

from ..transaction import TransactionTest
from .helpers import remove_info_metadata

CURRENT_FOLDER = Path(realpath(__file__)).parent
FIXTURES_FOLDER = CURRENT_FOLDER / "fixtures"


@pytest.mark.parametrize(
    "name, tx, fork",
    [
        pytest.param("simple_type_0", Transaction(), Shanghai),
    ],
)
def test_transaction_test_filling(
    name: str, tx: Transaction, fork: Fork
) -> None:
    """Test the transaction test filling."""
    generated_fixture = TransactionTest(
        tx=tx.with_signature_and_sender()
    ).generate(
        t8n=None,  # type: ignore
        fork=fork,
        fixture_format=TransactionFixture,
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
