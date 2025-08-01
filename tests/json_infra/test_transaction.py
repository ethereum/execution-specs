from typing import Callable

import pytest
from ethereum_rlp import rlp

from ethereum.exceptions import NonceOverflowError
from ethereum.spurious_dragon.transactions import (
    Transaction,
    validate_transaction,
)
from ethereum.utils.hexadecimal import hex_to_uint

from . import FORKS, TEST_FIXTURES
from .conftest import pytest_config
from .helpers.load_transaction_tests import NoTestsFound, load_test_transaction

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

test_dir = f"{ETHEREUM_TESTS_PATH}/TransactionTests"


def _generate_high_nonce_tests_function(fork_name: str) -> Callable:
    @pytest.mark.parametrize(
        "test_file_high_nonce",
        [
            "ttNonce/TransactionWithHighNonce64Minus1.json",
            "ttNonce/TransactionWithHighNonce64.json",
            "ttNonce/TransactionWithHighNonce64Plus1.json",
        ],
    )
    def test_func(test_file_high_nonce: str) -> None:
        try:
            test = load_test_transaction(
                test_dir, test_file_high_nonce, fork_name
            )
        except NoTestsFound:
            pytest.skip(
                f"No tests found for {fork_name} in {test_file_high_nonce}"
            )

        tx = rlp.decode_to(Transaction, test["tx_rlp"])

        with pytest.raises(NonceOverflowError):
            validate_transaction(tx)

    test_func.__name__ = f"test_high_nonce_tests_{fork_name.lower()}"
    return test_func


def _generate_nonce_tests_function(fork_name: str) -> Callable:
    @pytest.mark.parametrize(
        "test_file_nonce",
        [
            "ttNonce/TransactionWithHighNonce32.json",
            "ttNonce/TransactionWithHighNonce64Minus2.json",
        ],
    )
    def test_func(test_file_nonce: str) -> None:
        try:
            test = load_test_transaction(test_dir, test_file_nonce, fork_name)
        except NoTestsFound:
            pytest.skip(f"No tests found for {fork_name} in {test_file_nonce}")

        tx = rlp.decode_to(Transaction, test["tx_rlp"])

        result_intrinsic_gas_cost = hex_to_uint(
            test["test_result"]["intrinsicGas"]
        )

        intrinsic_gas = validate_transaction(tx)
        assert intrinsic_gas == result_intrinsic_gas_cost

    test_func.__name__ = f"test_nonce_tests_{fork_name.lower()}"
    return test_func


# Determine which forks to generate tests for
if pytest_config and pytest_config.getoption("fork", None):
    # If --fork option is specified, only generate test for that fork
    fork_option = pytest_config.getoption("fork")
    if fork_option in FORKS:
        forks_to_test = [fork_option]
    else:
        # If specified fork is not valid, generate no tests
        forks_to_test = []
else:
    # If no --fork option, generate tests for all forks
    forks_to_test = list(FORKS.keys())

for fork_name in forks_to_test:
    locals()[
        f"test_high_nonce_tests_{fork_name.lower()}"
    ] = _generate_high_nonce_tests_function(fork_name)
    locals()[
        f"test_nonce_tests_{fork_name.lower()}"
    ] = _generate_nonce_tests_function(fork_name)
