import json
import os
import sys
from functools import partial

import pytest

from ethereum import rlp
from ethereum.frontier.eth_types import Transaction
from ethereum.frontier.spec import (
    calculate_intrinsic_cost,
    validate_transaction,
)
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_uint
from tests.frontier.blockchain_st_test_helpers import load_test_transaction

test_dir = "tests/fixtures/TransactionTests"

load_frontier_transaction = partial(load_test_transaction, network="Frontier")


@pytest.mark.parametrize(
    "test_file_high_nonce",
    [
        "ttNonce/TransactionWithHighNonce64Minus1.json",
        "ttNonce/TransactionWithHighNonce64.json",
        "ttNonce/TransactionWithHighNonce64Plus1.json",
    ],
)
def test_high_nonce(test_file_high_nonce: str) -> None:
    test = load_frontier_transaction(test_dir, test_file_high_nonce)

    assert validate_transaction(test["transaction"]) == False


@pytest.mark.parametrize(
    "test_file_nonce",
    [
        "ttNonce/TransactionWithHighNonce32.json",
        "ttNonce/TransactionWithHighNonce64Minus2.json",
    ],
)
def test_nonce(test_file_nonce: str) -> None:
    test = load_frontier_transaction(test_dir, test_file_nonce)

    result_intrinsic_gas_cost = hex_to_uint(
        test["test_result"]["intrinsicGas"]
    )

    assert validate_transaction(test["transaction"]) == True
    assert (
        calculate_intrinsic_cost(test["transaction"])
        == result_intrinsic_gas_cost
    )
