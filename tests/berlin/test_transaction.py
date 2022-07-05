from functools import partial

import pytest

from ethereum import rlp
from ethereum.berlin.eth_types import LegacyTransaction
from ethereum.berlin.spec import calculate_intrinsic_cost, validate_transaction
from ethereum.utils.hexadecimal import hex_to_uint

from ..helpers.eth_types_helpers import load_test_transaction

test_dir = "tests/fixtures/TransactionTests"

load_berlin_transaction = partial(load_test_transaction, network="Berlin")


@pytest.mark.parametrize(
    "test_file_high_nonce",
    [
        "ttNonce/TransactionWithHighNonce64Minus1.json",
        "ttNonce/TransactionWithHighNonce64.json",
        "ttNonce/TransactionWithHighNonce64Plus1.json",
    ],
)
def test_high_nonce(test_file_high_nonce: str) -> None:
    test = load_berlin_transaction(test_dir, test_file_high_nonce)

    tx = rlp.decode_to(LegacyTransaction, test["tx_rlp"])

    assert validate_transaction(tx) == False


@pytest.mark.parametrize(
    "test_file_nonce",
    [
        "ttNonce/TransactionWithHighNonce32.json",
        "ttNonce/TransactionWithHighNonce64Minus2.json",
    ],
)
def test_nonce(test_file_nonce: str) -> None:
    test = load_berlin_transaction(test_dir, test_file_nonce)

    tx = rlp.decode_to(LegacyTransaction, test["tx_rlp"])

    result_intrinsic_gas_cost = hex_to_uint(
        test["test_result"]["intrinsicGas"]
    )

    assert validate_transaction(tx) == True
    assert calculate_intrinsic_cost(tx) == result_intrinsic_gas_cost
