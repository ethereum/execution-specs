"""
Ported from:
tests/static/state_tests/stSpecialTest/eoaEmptyParisFiller.yml

contract code:
    origin
    dup1
    push1 0x00
    sstore
    dup1
    balance
    push1 0x31
    sstore
    dup1
    extcodesize
    push1 0x3b
    sstore
    dup1
    extcodehash
    push1 0x3f
    sstore
    push1 0x01
    dup2
    add
    extcodehash
    ... (55 more instructions)

callee_4 code:
    origin
    selfdestruct
"""

import pytest
from execution_testing import (
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
    ["tests/static/state_tests/stSpecialTest/eoaEmptyParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, tx_error",
    [
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000000", 10000000, 0, None, id="case0"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000000", 10000000, 100, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case1", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000000", 9999999, 0, None, id="case2"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000000", 9999999, 100, None, id="case3"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 10000000, 0, None, id="case4"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 10000000, 100, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, id="case5", marks=pytest.mark.exception_test),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 9999999, 0, None, id="case6"),
        pytest.param("693c61390000000000000000000000000000000000000000000000000000000000000001", 9999999, 100, None, id="case7"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eoa_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    tx_error,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x000000000000000000000000000000000000c0de")
    callee = Address("0x000000000000000000000000000000000000bad1")
    callee_1 = Address("0x000000000000000000000000000000000000bad2")
    callee_2 = Address("0x000000000000000000000000000000000000bad3")
    callee_3 = Address("0x000000000000000000000000000000000000bad4")
    callee_4 = Address("0x000000000000000000000000000000000000dead")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=0, nonce=1)
    pre[callee_2] = Account(balance=1, nonce=1)
    pre[callee_3] = Account(balance=10, nonce=0, storage={0xdead: 0xbeef})
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.ORIGIN + Op.DUP1 + Op.PUSH1[0x0] + Op.SSTORE + Op.DUP1 + Op.BALANCE
        + Op.PUSH1[0x31] + Op.SSTORE + Op.DUP1 + Op.EXTCODESIZE + Op.PUSH1[0x3b]
        + Op.SSTORE + Op.DUP1 + Op.EXTCODEHASH + Op.PUSH1[0x3f] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.ADD + Op.EXTCODEHASH + Op.PUSH2[0x13f]
        + Op.SSTORE + Op.PUSH2[0xbad1] + Op.EXTCODEHASH + Op.PUSH2[0xbad1] + Op.SSTORE
        + Op.PUSH2[0xbad2] + Op.EXTCODEHASH + Op.PUSH2[0xbad2] + Op.SSTORE
        + Op.PUSH2[0xbad3] + Op.EXTCODEHASH + Op.PUSH2[0xbad3] + Op.SSTORE
        + Op.PUSH2[0xbad4] + Op.EXTCODEHASH + Op.PUSH2[0xbad4] + Op.SSTORE
        + Op.PUSH2[0xbad5] + Op.EXTCODEHASH + Op.PUSH2[0xbad5] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.GAS + Op.SWAP5
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.SWAP1 + Op.GAS + Op.CALL + Op.POP
        + Op.GAS + Op.SWAP1 + Op.SUB + Op.PUSH1[0xf1] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH2[0xdead]
        + Op.GAS + Op.CALL + Op.POP + Op.GAS + Op.SWAP1 + Op.SUB + Op.PUSH1[0xff]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(balance=0x2710, nonce=1, code=Op.ORIGIN + Op.SELFDESTRUCT)
    pre[sender] = Account(balance=0x3b9aca00, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=100,
        nonce=0,
        value=tx_value,
        error=tx_error,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
