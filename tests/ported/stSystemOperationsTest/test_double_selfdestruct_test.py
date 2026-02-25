"""
The first test case required here 
https://github.com/ethereum/tests/issues/431#issue-306081539

Implements: SUC007.0, SUC007.1, SUC007.2, SUC007.3,
            SUC008.0, SUC008.1, SUC008.2, SUC008.3


Ported from:
tests/static/state_tests/stSystemOperationsTest/doubleSelfdestructTestFiller.yml

contract code:
    push1 0x02
    calldatasize
    gt
    push1 0x17
    jumpi
    push1 0x00
    calldataload
    push1 0xf0
    shr
    calldatasize
    push1 0x02
    eq
    push1 0x15
    jumpi
    stop
    jumpdest
    selfdestruct
    jumpdest
    push1 0x00
    calldataload
    ... (94 more instructions)
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSystemOperationsTest/doubleSelfdestructTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "f210011002",
        "f410011002",
        "f110011002",
        "fa1001c0de",
        "fa10011002",
        "f21001c0de",
        "f41001c0de",
        "f11001c0de",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_double_selfdestruct_test(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """The first test case required here 
https://github.com/ethereum/tests/issues/431#issue-306081539

Implements: SUC007.0, SUC007.1, SUC007.2, SUC007.3,
            SUC008.0, SUC008.1, SUC008.2, SUC008.3
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x000000000000000000000000000000000000c0de")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre[contract] = Account(
        balance=0xf4240,
        nonce=1,
        code=(
        Op.PUSH1[0x2] + Op.CALLDATASIZE + Op.GT + Op.PUSH1[0x17] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xf0] + Op.SHR + Op.CALLDATASIZE
        + Op.PUSH1[0x2] + Op.EQ + Op.PUSH1[0x15] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.SELFDESTRUCT + Op.JUMPDEST + Op.PUSH1[0x0] + Op.CALLDATALOAD
        + Op.PUSH1[0xf8] + Op.SHR + Op.PUSH1[0xfa] + Op.PUSH2[0xffff] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.PUSH1[0xe8] + Op.SHR + Op.AND + Op.SWAP2
        + Op.PUSH1[0xff] + Op.PUSH2[0xffff] + Op.PUSH1[0x0] + Op.CALLDATALOAD
        + Op.PUSH1[0xd8] + Op.SHR + Op.AND + Op.DUP2 + Op.DUP2 + Op.PUSH1[0x8]
        + Op.SHR + Op.AND + Op.PUSH1[0x0] + Op.MSTORE8 + Op.AND + Op.PUSH1[0x1]
        + Op.MSTORE8 + Op.PUSH1[0xf1] + Op.DUP2 + Op.EQ + Op.PUSH1[0x90] + Op.JUMPI
        + Op.JUMPDEST + Op.PUSH1[0xf2] + Op.DUP2 + Op.EQ + Op.PUSH1[0x7f] + Op.JUMPI
        + Op.JUMPDEST + Op.PUSH1[0xf4] + Op.DUP2 + Op.EQ + Op.PUSH1[0x6f] + Op.JUMPI
        + Op.JUMPDEST + Op.EQ + Op.PUSH1[0x61] + Op.JUMPI + Op.SELFDESTRUCT
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH2[0xc0de] + Op.GAS + Op.STATICCALL + Op.POP + Op.SELFDESTRUCT
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH2[0xc0de] + Op.GAS + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x5b]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x2] + Op.DUP2
        + Op.DUP1 + Op.PUSH2[0xc0de] + Op.GAS + Op.CALLCODE + Op.POP + Op.PUSH1[0x53]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x2] + Op.DUP2
        + Op.DUP1 + Op.PUSH2[0xc0de] + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x4b]
        + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=1,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
