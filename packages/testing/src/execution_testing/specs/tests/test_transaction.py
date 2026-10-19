"""Test suite for the transaction spec test generation."""

import json
from os.path import realpath
from pathlib import Path

import pytest

from execution_testing import TestAddress
from execution_testing.exceptions import TransactionException
from execution_testing.execution import MempoolAdmission
from execution_testing.fixtures import TransactionFixture
from execution_testing.forks import Amsterdam, Bogota, Fork, Shanghai
from execution_testing.test_types import EOA, Frame, Transaction

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


@pytest.mark.parametrize(
    "error,accepted",
    [
        pytest.param(None, True, id="valid"),
        pytest.param(TransactionException.NONCE_IS_MAX, False, id="invalid"),
    ],
)
def test_transaction_test_executes_as_mempool_admission(
    error: TransactionException | None, accepted: bool
) -> None:
    """
    Test that a transaction test executes as a mempool admission that
    expects a valid transaction admitted and an invalid one rejected.
    """
    tx = Transaction(gas_limit=0x5208, error=error)
    (execute_format,) = TransactionTest.supported_execute_formats
    admission = TransactionTest(tx=tx, fork=Shanghai).execute(
        execute_format=execute_format
    )
    assert isinstance(admission, MempoolAdmission)
    (entry,) = admission.txs
    assert entry.tx is tx
    assert entry.accepted is accepted


def test_valid_frame_transaction_test_leaves_its_verdict_to_policy() -> None:
    """
    Test that a valid frame transaction executes with no admission
    expectation, as the public mempool's validation prefix rules may
    refuse it.
    """
    tx = Transaction(sender=EOA(key=1), frames=[Frame(mode=1, flags=3)])
    (execute_format,) = TransactionTest.supported_execute_formats
    admission = TransactionTest(tx=tx, fork=Bogota).execute(
        execute_format=execute_format
    )
    assert isinstance(admission, MempoolAdmission)
    assert [entry.accepted for entry in admission.txs] == [None]
