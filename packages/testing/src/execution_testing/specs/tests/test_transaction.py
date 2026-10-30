"""Test suite for the transaction spec test generation."""

import json
from os.path import realpath
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from execution_testing import TestAddress
from execution_testing.base_types import Bytes
from execution_testing.client_clis import (
    ExecutionSpecsTransitionTool,
    TransitionTool,
)
from execution_testing.exceptions import TransactionException
from execution_testing.fixtures import TransactionFixture
from execution_testing.forks import (
    Amsterdam,
    Berlin,
    Cancun,
    Fork,
    Frontier,
    Shanghai,
)
from execution_testing.test_types import Transaction

from .. import transaction as transaction_module
from ..helpers import (
    UnexpectedExecutionFailError,
    UnexpectedExecutionSuccessError,
)
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


def fill_transaction_test(
    tx: Transaction, fork: Fork, t8n: TransitionTool
) -> TransactionFixture:
    """Fill a transaction test, marked as an exception test if needed."""
    fixture = (
        TransactionTest(
            tx=tx,
            fork=fork,
            is_exception_test=tx.error is not None,
        )
        .generate(t8n=t8n, fixture_format=TransactionFixture)
        .fixture
    )
    assert isinstance(fixture, TransactionFixture)
    return fixture


def with_rlp_override(
    rlp: bytes, error: TransactionException | None
) -> Transaction:
    """Return a transaction whose serialization is the given bytes."""
    tx = Transaction(gas_limit=0x5208, error=error)
    tx.rlp_override = Bytes(rlp)
    return tx


# A type-2 transaction whose payload is a one-element list.
UNDECODABLE_RLP = b"\x02\xc1\x80"


@pytest.mark.parametrize(
    "tx,fork",
    [
        pytest.param(
            Transaction(gas_limit=0x5208), Frontier, id="legacy_frontier"
        ),
        pytest.param(
            Transaction(gas_limit=0x5208), Berlin, id="legacy_berlin"
        ),
        pytest.param(
            Transaction(gas_limit=0x5208), Amsterdam, id="legacy_amsterdam"
        ),
        pytest.param(
            Transaction(ty=1, gas_limit=0x5208), Berlin, id="type_1_berlin"
        ),
        pytest.param(
            Transaction(ty=2, gas_limit=0x5208), Cancun, id="type_2_cancun"
        ),
    ],
)
def test_reference_check_accepts_valid_transaction(
    tx: Transaction, fork: Fork
) -> None:
    """Fill a transaction the reference implementation decodes."""
    fill_transaction_test(
        tx.with_signature_and_sender(), fork, ExecutionSpecsTransitionTool()
    )


@pytest.mark.parametrize(
    "rlp,fork",
    [
        pytest.param(UNDECODABLE_RLP, Cancun, id="typed_cancun"),
        pytest.param(UNDECODABLE_RLP, Frontier, id="typed_frontier"),
        pytest.param(b"\xc1\x80", Cancun, id="legacy_cancun"),
        pytest.param(b"\x02", Cancun, id="type_byte_only_cancun"),
        pytest.param(b"", Frontier, id="empty_frontier"),
        pytest.param(b"", Cancun, id="empty_cancun"),
    ],
)
def test_reference_check_undecodable_bytes(rlp: bytes, fork: Fork) -> None:
    """
    Fill undecodable bytes only when the test expects the transaction to
    fail.
    """
    t8n = ExecutionSpecsTransitionTool()
    fixture = fill_transaction_test(
        with_rlp_override(rlp, TransactionException.RLP_TOO_FEW_ELEMENTS),
        fork,
        t8n,
    )
    assert fixture.transaction == rlp

    with pytest.raises(UnexpectedExecutionFailError):
        fill_transaction_test(with_rlp_override(rlp, None), fork, t8n)


def test_reference_check_skipped_for_other_transition_tools() -> None:
    """Run the check only with the in-process reference implementation."""
    fixture = fill_transaction_test(
        with_rlp_override(UNDECODABLE_RLP, None),
        Cancun,
        Mock(spec=TransitionTool),
    )
    assert fixture.transaction == UNDECODABLE_RLP


class FrameTransaction:
    """Stand-in for a fork's frame transaction class."""


def test_reference_check_rejects_accepted_frame_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Reject `error=` on a frame transaction the fork accepts.

    No fork on this branch ships `FrameTransaction`, so a fake fork
    stands in: its decoder returns a frame transaction and its
    validation accepts it.
    """
    validate_frame_transaction = Mock()
    modules = {
        "transactions": SimpleNamespace(
            decode_transaction=lambda _raw: FrameTransaction(),
            FrameTransaction=FrameTransaction,
        ),
        "transactions.frame_transaction": SimpleNamespace(
            validate_frame_transaction=validate_frame_transaction
        ),
    }
    monkeypatch.setattr(
        transaction_module,
        "resolve_fork",
        lambda _name: SimpleNamespace(module=modules.__getitem__),
    )
    tx = Transaction(
        ty=2,
        gas_limit=0x5208,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    ).with_signature_and_sender()

    with pytest.raises(UnexpectedExecutionSuccessError):
        fill_transaction_test(tx, Cancun, ExecutionSpecsTransitionTool())
    validate_frame_transaction.assert_called_once()
