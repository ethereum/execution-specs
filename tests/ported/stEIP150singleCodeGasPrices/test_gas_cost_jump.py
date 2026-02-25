"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostJumpFiller.yml

callee code:
    push1 0x00
    push1 0x00
    jumpdest
    jumpdest
    stop

callee_1 code:
    push1 0x00
    push1 0x05
    jump
    jumpdest
    stop

callee_2 code:
    push1 0x01
    push1 0x05
    jumpi
    jumpdest
    stop

callee_3 code:
    push1 0x00
    push1 0x05
    jumpi
    jumpdest
    stop

contract code:
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0x1000
    push3 0x010000
    call
    pop
    gas
    push1 0x00
    mload
    sub
    push1 0x20
    mstore
    push1 0x01
    push1 0x04
    ... (99 more instructions)
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
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostJumpFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004",
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006",
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000006",
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_jump(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0x0000000000000000000000000000000000001000")
    callee_1 = Address("0x0000000000000000000000000000000000002000")
    callee_2 = Address("0x0000000000000000000000000000000000003000")
    callee_3 = Address("0x0000000000000000000000000000000000004000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.JUMPDEST + Op.JUMPDEST + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.JUMP + Op.JUMPDEST + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x5] + Op.JUMPI + Op.JUMPDEST + Op.STOP,
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.JUMPI + Op.JUMPDEST + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x1000]
        + Op.PUSH3[0x10000] + Op.CALL + Op.POP + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SUB + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.EQ + Op.PUSH1[0x2e] + Op.JUMPI + Op.PUSH1[0x0] + Op.POP
        + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.PUSH3[0x10000] + Op.CALL + Op.POP
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x40] + Op.MSTORE
        + Op.JUMPDEST + Op.PUSH1[0x2] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ
        + Op.PUSH1[0x5e] + Op.JUMPI + Op.PUSH1[0x0] + Op.POP + Op.PUSH1[0x7e]
        + Op.JUMP + Op.JUMPDEST + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0x3000] + Op.PUSH3[0x10000] + Op.CALL + Op.POP + Op.GAS
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x40] + Op.MSTORE + Op.JUMPDEST
        + Op.PUSH1[0x3] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.EQ + Op.PUSH1[0x8e]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.POP + Op.PUSH1[0xae] + Op.JUMP + Op.JUMPDEST
        + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x4000]
        + Op.PUSH3[0x10000] + Op.CALL + Op.POP + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SUB + Op.PUSH1[0x40] + Op.MSTORE + Op.JUMPDEST + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x40] + Op.MLOAD
        + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
