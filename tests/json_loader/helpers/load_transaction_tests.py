"""Helpers to load and run transaction tests from JSON files."""

from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

import pytest
from _pytest.config import Config
from ethereum_rlp.exceptions import RLPException

from ethereum.exceptions import EthereumException
from ethereum.utils.hexadecimal import hex_to_bytes

from ..stash_keys import desired_forks_key
from .fixtures import Fixture, FixturesFile, FixtureTestItem
from .transaction_test_adapter import validate_raw_transaction


def _fixture_format(test_dict: Mapping[str, Any]) -> str | None:
    """Return the fixture format declared in metadata, if present."""
    info = test_dict.get("_info")
    if not isinstance(info, Mapping):
        return None
    return info.get("fixture-format") or info.get("fixture_format")


def _fixture_fork_name(test_dict: Mapping[str, Any]) -> str:
    """Return the single fork declared by a transaction fixture."""
    result = test_dict.get("result")
    if not isinstance(result, Mapping) or len(result) != 1:
        raise ValueError(
            "transaction_test fixtures must contain exactly one result fork"
        )
    return next(iter(result))


def _hex_number(value: Any) -> int:
    """Parse a fixture JSON integer or hexadecimal string."""
    if isinstance(value, str):
        return int(value, 0)
    return int(value)


def run_transaction_test_fixture(test_dict: Mapping[str, Any]) -> None:
    """Validate one transaction fixture against EELS."""
    fork_name = _fixture_fork_name(test_dict)
    result_by_fork = test_dict["result"]
    assert isinstance(result_by_fork, Mapping)
    expected_result = result_by_fork[fork_name]
    assert isinstance(expected_result, Mapping)

    raw_value = test_dict["txbytes"]
    assert isinstance(raw_value, str)
    raw = hex_to_bytes(raw_value)
    expected_exception = expected_result.get("exception")

    try:
        actual = validate_raw_transaction(fork_name, raw)
    except (EthereumException, RLPException) as exception:
        if expected_exception is not None:
            return
        raise AssertionError(
            "EELS rejected a transaction fixture declared valid with "
            f"{type(exception).__name__}: {exception}"
        ) from exception

    assert expected_exception is None, (
        "EELS accepted a transaction fixture declared invalid: "
        f"expected {expected_exception}"
    )

    expected_sender = expected_result.get("sender")
    expected_hash = expected_result.get("hash")
    expected_intrinsic_gas = expected_result.get("intrinsicGas")
    assert expected_sender is not None
    assert expected_hash is not None
    assert expected_intrinsic_gas is not None

    assert actual.sender == hex_to_bytes(expected_sender)
    assert actual.transaction_hash == hex_to_bytes(expected_hash)
    assert actual.intrinsic_gas == _hex_number(expected_intrinsic_gas)


class TransactionTestFixture(Fixture, FixtureTestItem):
    """Single transaction test fixture from a JSON file."""

    fork_name: str

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a transaction fixture item."""
        super().__init__(*args, **kwargs)
        self.fork_name = _fixture_fork_name(self.test_dict)
        self.add_marker(pytest.mark.fork(self.fork_name))
        self.add_marker("json_transaction_tests")

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which this transaction was collected."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, FixturesFile)
        return parent

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load the transaction fixture from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def runtest(self) -> None:
        """Run a transaction fixture against EELS."""
        run_transaction_test_fixture(self.test_dict)

    def reportinfo(self) -> Tuple[Path, int, str]:
        """Return information for test reporting."""
        return self.path, 1, self.name

    @classmethod
    def is_format(cls, test_dict: Dict[str, Any]) -> bool:
        """Return whether the object is a transaction-test fixture."""
        fixture_format = _fixture_format(test_dict)
        if fixture_format is not None:
            return fixture_format == "transaction_test"
        return "txbytes" in test_dict and "result" in test_dict

    @classmethod
    def has_desired_fork(
        cls, test_dict: Dict[str, Any], config: Config
    ) -> bool:
        """Return whether the fixture belongs to a requested fork."""
        desired_forks = config.stash.get(desired_forks_key, None)
        return (
            desired_forks is None
            or _fixture_fork_name(test_dict) in desired_forks
        )
