"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP1559/valCausesOOFFiller.yml

contract code:
    push1 0x04
    calldataload
    jumpdest
    push1 0x00
    dup2
    gt
    push1 0x0c
    jumpi
    stop
    jumpdest
    push2 0x60a7
    dup2
    sstore
    push1 0x00
    not
    add
    push1 0x03
    jump
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
    ["tests/static/state_tests/stEIP1559/valCausesOOFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, tx_error",
    [
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 100000, 0, None, id="case0"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 100000, 1, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case1", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 90000, 0, None, id="case2"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 90000, 1, None, id="case3"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 110000, 0, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case4", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 110000, 1, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case5", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000002", 100000, 0, None, id="case6"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000002", 100000, 1, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case7", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000002", 90000, 0, None, id="case8"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000002", 90000, 1, None, id="case9"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000002", 110000, 0, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case10", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000002", 110000, 1, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case11", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_val_causes_oof(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    tx_error,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x1ed74322ae94e1786967b2bde918d4f6ea77b152")
    contract = Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x5f5e100, nonce=1)
    pre[contract] = Account(
        balance=0x5af3107a4000,
        nonce=0,
        code=(
        Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP2
        + Op.GT + Op.PUSH1[0xc] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x60a7]
        + Op.DUP2 + Op.SSTORE + Op.PUSH1[0x0] + Op.NOT + Op.ADD + Op.PUSH1[0x3]
        + Op.JUMP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x7608ab0a661408930040c5e3eb5b0c6520acbb6ce5b28ddbe53676109e8ea24b"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=0,
        nonce=1,
        value=tx_value,
        access_list=[],
        error=tx_error,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
