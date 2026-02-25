"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP1559/outOfFundsOldTypesFiller.yml

contract code:
    push1 0x02
    push1 0x00
    sstore
    stop
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/outOfFundsOldTypesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, tx_access_list, tx_error",
    [
        pytest.param("00", 16777216, 0, None, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case0", marks=pytest.mark.exception_test),
        pytest.param("00", 16777216, 1000000000000000000, None, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case1", marks=pytest.mark.exception_test),
        pytest.param("00", 40000, 0, None, None, id="case2"),
        pytest.param("00", 40000, 1000000000000000000, None, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case3", marks=pytest.mark.exception_test),
        pytest.param("01", 16777216, 0, [], TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case4", marks=pytest.mark.exception_test),
        pytest.param("01", 16777216, 1000000000000000000, [], TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case5", marks=pytest.mark.exception_test),
        pytest.param("01", 40000, 0, [], None, id="case6"),
        pytest.param("01", 40000, 1000000000000000000, [], TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case7", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_funds_old_types(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    tx_access_list,
    tx_error,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x8dab845a8398167a1c204f0e79540d619be8b473")
    contract = Address("0xd71b14c239fc39327f25764dd784c85ef0285fda")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=100000000000,
        nonce=1,
        value=tx_value,
        access_list=tx_access_list,
        error=tx_error,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
