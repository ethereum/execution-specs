"""Test the EELS transaction-test fixture consumer."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
from _pytest.config import Config
from ethereum_rlp.exceptions import RLPException
from execution_testing import TestAddress
from execution_testing.fixtures import TransactionFixture
from execution_testing.forks import (
    Amsterdam,
    Berlin,
    Fork,
    Frontier,
    London,
    Osaka,
    Prague,
    Shanghai,
)
from execution_testing.specs.transaction import TransactionTest
from execution_testing.test_types import Transaction

from ethereum.exceptions import EthereumException

from .helpers import load_transaction_tests
from .helpers.load_transaction_tests import (
    TransactionTestFixture,
    run_transaction_test_fixture,
)
from .helpers.transaction_test_adapter import validate_raw_transaction
from .stash_keys import desired_forks_key


def _transaction_fixture(
    fork: Fork,
    transaction: Transaction,
) -> TransactionFixture:
    """Generate a transaction fixture with context-dependent defaults."""
    fixture = (
        TransactionTest(tx=transaction, fork=fork)
        .generate(
            t8n=None,  # type: ignore[arg-type]
            fixture_format=TransactionFixture,
        )
        .fixture
    )
    assert isinstance(fixture, TransactionFixture)
    return fixture


def _raw_transaction(fork: Fork, transaction: Transaction) -> bytes:
    """Generate and return the raw transaction bytes from a fixture."""
    return bytes(_transaction_fixture(fork, transaction).transaction)


@pytest.mark.parametrize(
    "fork,transaction,expected_intrinsic_gas",
    [
        pytest.param(
            Frontier,
            Transaction(protected=False),
            21_000,
            id="pre_berlin_legacy",
        ),
        pytest.param(
            Berlin,
            Transaction(ty=1),
            21_000,
            id="typed_transaction",
        ),
        pytest.param(
            Prague,
            Transaction(),
            21_000,
            id="prague_split_intrinsic_gas",
        ),
        pytest.param(
            Osaka,
            Transaction(),
            21_000,
            id="osaka_split_intrinsic_gas",
        ),
        pytest.param(
            Amsterdam,
            Transaction(to=TestAddress),
            12_000,
            id="amsterdam_sender_dependent_intrinsic_gas",
        ),
    ],
)
def test_validate_raw_transaction(
    fork: Fork,
    transaction: Transaction,
    expected_intrinsic_gas: int,
) -> None:
    """Validate generated fixtures through each public validation path."""
    fixture = _transaction_fixture(fork, transaction)
    raw = bytes(fixture.transaction)

    result = validate_raw_transaction(fork.name(), raw)

    expected_result = next(iter(fixture.result.values()))
    assert expected_result.sender is not None
    assert expected_result.hash is not None
    assert result.sender == bytes(expected_result.sender)
    assert result.transaction_hash == bytes(expected_result.hash)
    assert result.intrinsic_gas == expected_intrinsic_gas
    assert result.intrinsic_gas == int(expected_result.intrinsic_gas)


def test_reject_typed_transaction_before_berlin() -> None:
    """Reject typed transaction envelopes on unsupported forks."""
    raw = _raw_transaction(Berlin, Transaction(ty=1))

    with pytest.raises(RLPException):
        validate_raw_transaction("Frontier", raw)


def test_reject_malformed_legacy_rlp() -> None:
    """Reject a malformed legacy transaction list."""
    with pytest.raises(RLPException):
        validate_raw_transaction("Frontier", b"\xc0")


def test_reject_semantically_invalid_transaction() -> None:
    """Reject a decoded transaction whose nonce overflows."""
    raw = _raw_transaction(
        Frontier,
        Transaction(nonce=2**64 - 1, protected=False),
    )

    with pytest.raises(EthereumException):
        validate_raw_transaction("Frontier", raw)


def test_reject_wrong_chain_id() -> None:
    """Reject a transaction protected for a different chain."""
    raw = _raw_transaction(London, Transaction(chain_id=2))

    with pytest.raises(EthereumException, match="expected chain_id `1`"):
        validate_raw_transaction("London", raw)


@pytest.mark.parametrize("fork", [Prague, Osaka])
def test_reject_empty_authorization_list(fork: Fork) -> None:
    """Apply the fork's public state-independent transaction validation."""
    raw = _raw_transaction(fork, Transaction(authorization_list=[]))

    with pytest.raises(EthereumException, match="empty authorization list"):
        validate_raw_transaction(fork.name(), raw)


def _valid_fixture() -> dict[str, Any]:
    """Create a valid transaction fixture for runner tests."""
    fixture = _transaction_fixture(Shanghai, Transaction())
    return fixture.json_dict_with_info()


def test_run_valid_transaction_fixture() -> None:
    """Compare all declared fields for a valid fixture."""
    run_transaction_test_fixture(_valid_fixture())


def test_run_invalid_transaction_fixture() -> None:
    """Accept a fixture rejection only for known protocol errors."""
    fixture = {
        "result": {
            "Frontier": {
                "exception": "TR_RLP_TOO_FEW_ELEMENTS",
                "intrinsicGas": "0x00",
            }
        },
        "txbytes": "0xc0",
    }

    run_transaction_test_fixture(fixture)


def test_unexpected_implementation_error_is_not_a_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not treat unrelated Python errors as expected rejection."""
    fixture = {
        "result": {
            "Frontier": {
                "exception": "TR_RLP_TOO_FEW_ELEMENTS",
                "intrinsicGas": "0x00",
            }
        },
        "txbytes": "0xc0",
    }

    def fail_unexpectedly(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise TypeError("implementation bug")

    monkeypatch.setattr(
        load_transaction_tests,
        "validate_raw_transaction",
        fail_unexpectedly,
    )

    with pytest.raises(TypeError, match="implementation bug"):
        run_transaction_test_fixture(fixture)


@pytest.mark.parametrize("metadata_key", ["fixture-format", "fixture_format"])
def test_recognize_transaction_fixture_metadata(metadata_key: str) -> None:
    """Recognize both fixture-format metadata spellings."""
    test_dict = {
        "_info": {metadata_key: "transaction_test"},
        "result": {"Frontier": {}},
        "txbytes": "0xc0",
    }

    assert TransactionTestFixture.is_format(test_dict)


def test_recognize_structural_transaction_fixture() -> None:
    """Recognize older transaction fixtures without format metadata."""
    assert TransactionTestFixture.is_format(
        {"result": {"Frontier": {}}, "txbytes": "0xc0"}
    )


def test_do_not_override_other_fixture_metadata() -> None:
    """Do not use the structural fallback for another declared format."""
    test_dict = {
        "_info": {"fixture_format": "state_test"},
        "result": {"Frontier": {}},
        "txbytes": "0xc0",
    }

    assert not TransactionTestFixture.is_format(test_dict)


def test_filter_transaction_fixture_fork() -> None:
    """Collect transaction fixtures only for requested forks."""
    test_dict = {"result": {"London": {}}, "txbytes": "0xc0"}
    config = cast(
        Config,
        SimpleNamespace(stash={desired_forks_key: ["London"]}),
    )

    assert TransactionTestFixture.has_desired_fork(test_dict, config)

    config.stash[desired_forks_key] = ["Frontier"]
    assert not TransactionTestFixture.has_desired_fork(test_dict, config)


def test_require_single_result_fork() -> None:
    """Reject ambiguous transaction fixtures containing multiple forks."""
    test_dict = {
        "result": {"Frontier": {}, "Homestead": {}},
        "txbytes": "0xc0",
    }
    config = cast(
        Config,
        SimpleNamespace(stash={desired_forks_key: ["Frontier"]}),
    )

    with pytest.raises(ValueError, match="exactly one result fork"):
        TransactionTestFixture.has_desired_fork(test_dict, config)
