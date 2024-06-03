from functools import partial

import pytest

from ethereum import rlp
from ethereum.tangerine_whistle.fork import (
    calculate_intrinsic_cost,
    validate_transaction,
)
from ethereum.tangerine_whistle.transactions import Transaction
from ethereum.utils.hexadecimal import hex_to_uint
from tests.helpers import TEST_FIXTURES

from ..helpers.fork_types_helpers import load_test_transaction

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

test_dir = f"{ETHEREUM_TESTS_PATH}/TransactionTests"

load_tangerine_whistle_transaction = partial(
    load_test_transaction, network="EIP150"
)


@pytest.mark.parametrize(
    "test_file_high_nonce",
    [
        "ttNonce/TransactionWithHighNonce64Minus1.json",
        "ttNonce/TransactionWithHighNonce64.json",
        "ttNonce/TransactionWithHighNonce64Plus1.json",
    ],
)
def test_high_nonce(test_file_high_nonce: str) -> None:
    test = load_tangerine_whistle_transaction(test_dir, test_file_high_nonce)

    tx = rlp.decode_to(Transaction, test["tx_rlp"])

    assert validate_transaction(tx) == False


@pytest.mark.parametrize(
    "test_file_nonce",
    [
        "ttNonce/TransactionWithHighNonce32.json",
        "ttNonce/TransactionWithHighNonce64Minus2.json",
    ],
)
def test_nonce(test_file_nonce: str) -> None:
    test = load_tangerine_whistle_transaction(test_dir, test_file_nonce)

    tx = rlp.decode_to(Transaction, test["tx_rlp"])

    result_intrinsic_gas_cost = hex_to_uint(
        test["test_result"]["intrinsicGas"]
    )

    assert validate_transaction(tx) == True
    assert calculate_intrinsic_cost(tx) == result_intrinsic_gas_cost
