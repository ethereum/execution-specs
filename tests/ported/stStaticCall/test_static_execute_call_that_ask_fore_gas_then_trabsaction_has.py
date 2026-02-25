"""
Ported from:
tests/static/state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json

callee code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_1 code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x1c
    jumpi
    push1 0x01
    extcodesize
    pop
    push1 0x01
    push1 0x80
    mload
    add
    push1 0x80
    mstore
    push1 0x00
    jump
    jumpdest
    ... (1 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0927c0
    staticcall
    push1 0x01
    sstore
    stop

callee_2 code:
    push1 0x01
    push1 0x01
    sstore
    stop
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
    ["tests/static/state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000003dc16a13cf554533f380cc938a2c1ab04dac534f",
        "00000000000000000000000073ef1878a0f2c9629dedc1b1e9be8d77dcf93688",
        "000000000000000000000000ce4ccbffaf450ae2126eb96dcd7c891f37764f20",
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_static_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xabbef90b4b6d86caa8d6d6cd7f673a15a8de2d61")
    contract = Address("0xa256ebcc5536cda56e04c39fe9584ecc7594a438")
    callee = Address("0x3dc16a13cf554533f380cc938a2c1ab04dac534f")
    callee_1 = Address("0x73ef1878a0f2c9629dedc1b1e9be8d77dcf93688")
    callee_2 = Address("0xce4ccbffaf450ae2126eb96dcd7c891f37764f20")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0x186a0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x927c0] + Op.STATICCALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x989680, nonce=0)
    pre[callee_2] = Account(
        balance=0x186a0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xdc4efa209aecdd4c2d5201a419ea27506151b4ec687f14a613229e310932491b"
        ),
        to=contract,
        data=tx_data,
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
