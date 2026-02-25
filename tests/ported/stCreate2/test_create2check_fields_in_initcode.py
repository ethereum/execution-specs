"""
Check opcode values in create2 init code. Create2 called with different call types. CREATE2 inside CRETE2 inside CALL, CALLCODE, DELEGATECALL, STATICCALL << test values of  SENDER,address and so on.

Ported from:
tests/static/state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf000000000000000000000000000000000000000
    gas
    call
    stop

callee_1 code:
    push1 0x00
    push1 0x24
    dup1
    push1 0x13
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    pop
    stop
    stop
    invalid
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf000000000000000000000000000000000000000
    gas
    ... (4 more instructions)

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf000000000000000000000000000000000000000
    gas
    callcode
    stop

callee_3 code:
    push1 0x00
    push1 0x24
    dup1
    push1 0x13
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    pop
    stop
    stop
    invalid
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf000000000000000000000000000000000000000
    gas
    ... (4 more instructions)

callee_4 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf000000000000000000000000000000000000000
    gas
    delegatecall
    pop
    stop
    stop

callee_5 code:
    push1 0x00
    push1 0x22
    dup1
    push1 0x13
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    pop
    stop
    stop
    invalid
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf000000000000000000000000000000000000000
    gas
    delegatecall
    ... (3 more instructions)

callee_6 code:
    push2 0x0100
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf200000000000000000000000000000000000000
    gas
    staticcall
    pop
    push1 0x00
    mload
    push1 0x0a
    sstore
    stop

callee_7 code:
    push1 0x00
    push1 0x29
    dup1
    push1 0x11
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    stop
    invalid
    push2 0x0100
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf200000000000000000000000000000000000000
    gas
    staticcall
    pop
    push1 0x00
    ... (5 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    call
    stop

callee_8 code:
    push1 0x00
    push1 0x23
    dup1
    push1 0x13
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    pop
    stop
    stop
    invalid
    address
    push1 0x00
    sstore
    address
    balance
    push1 0x01
    sstore
    ... (20 more instructions)

callee_9 code:
    push1 0x00
    push1 0x29
    dup1
    push1 0x11
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    stop
    invalid
    address
    push1 0x00
    mstore
    address
    balance
    push1 0x20
    mstore
    origin
    push1 0x40
    ... (21 more instructions)
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
    ["tests/static/state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000001000000000000000000000000000000000000000",
        "0000000000000000000000002000000000000000000000000000000000000000",
        "0000000000000000000000003000000000000000000000000000000000000000",
        "0000000000000000000000004000000000000000000000000000000000000000",
        "0000000000000000000000001100000000000000000000000000000000000000",
        "0000000000000000000000002200000000000000000000000000000000000000",
        "0000000000000000000000003300000000000000000000000000000000000000",
        "0000000000000000000000004400000000000000000000000000000000000000",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_create2check_fields_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Check opcode values in create2 init code. Create2 called with different call types. CREATE2 inside CRETE2 inside CALL, CALLCODE, DELEGATECALL, STATICCALL << test values of  SENDER,address and so on.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0x1000000000000000000000000000000000000000")
    callee_1 = Address("0x1100000000000000000000000000000000000000")
    callee_2 = Address("0x2000000000000000000000000000000000000000")
    callee_3 = Address("0x2200000000000000000000000000000000000000")
    callee_4 = Address("0x3000000000000000000000000000000000000000")
    callee_5 = Address("0x3300000000000000000000000000000000000000")
    callee_6 = Address("0x4000000000000000000000000000000000000000")
    callee_7 = Address("0x4400000000000000000000000000000000000000")
    callee_8 = Address("0xf000000000000000000000000000000000000000")
    callee_9 = Address("0xf200000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xf000000000000000000000000000000000000000]
        + Op.GAS + Op.CALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x24] + Op.DUP1 + Op.PUSH1[0x13] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.POP + Op.STOP
        + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf000000000000000000000000000000000000000] + Op.GAS + Op.CALL
        + Op.POP + Op.STOP + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xf000000000000000000000000000000000000000]
        + Op.GAS + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x24] + Op.DUP1 + Op.PUSH1[0x13] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.POP + Op.STOP
        + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf000000000000000000000000000000000000000] + Op.GAS + Op.CALLCODE
        + Op.POP + Op.STOP + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf000000000000000000000000000000000000000] + Op.GAS
        + Op.DELEGATECALL + Op.POP + Op.STOP + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x22] + Op.DUP1 + Op.PUSH1[0x13] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.POP + Op.STOP
        + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xf000000000000000000000000000000000000000]
        + Op.GAS + Op.DELEGATECALL + Op.POP + Op.STOP + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf200000000000000000000000000000000000000] + Op.GAS
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0xa]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x29] + Op.DUP1 + Op.PUSH1[0x11] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.STOP
        + Op.INVALID + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf200000000000000000000000000000000000000] + Op.GAS
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0xa]
        + Op.SSTORE + Op.STOP + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x56bc75e2d63100000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x23] + Op.DUP1 + Op.PUSH1[0x13] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.POP + Op.STOP
        + Op.STOP + Op.INVALID + Op.ADDRESS + Op.PUSH1[0x0] + Op.SSTORE + Op.ADDRESS
        + Op.BALANCE + Op.PUSH1[0x1] + Op.SSTORE + Op.ORIGIN + Op.PUSH1[0x2]
        + Op.SSTORE + Op.CALLER + Op.PUSH1[0x3] + Op.SSTORE + Op.CALLVALUE
        + Op.PUSH1[0x4] + Op.SSTORE + Op.CALLDATASIZE + Op.PUSH1[0x5] + Op.SSTORE
        + Op.CODESIZE + Op.PUSH1[0x6] + Op.SSTORE + Op.GASPRICE + Op.PUSH1[0x7]
        + Op.SSTORE + Op.STOP + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x29] + Op.DUP1 + Op.PUSH1[0x11] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.STOP
        + Op.INVALID + Op.ADDRESS + Op.PUSH1[0x0] + Op.MSTORE + Op.ADDRESS
        + Op.BALANCE + Op.PUSH1[0x20] + Op.MSTORE + Op.ORIGIN + Op.PUSH1[0x40]
        + Op.MSTORE + Op.CALLER + Op.PUSH1[0x60] + Op.MSTORE + Op.CALLVALUE
        + Op.PUSH1[0x80] + Op.MSTORE + Op.CALLDATASIZE + Op.PUSH1[0xa0] + Op.MSTORE
        + Op.CODESIZE + Op.PUSH1[0xc0] + Op.MSTORE + Op.GASPRICE + Op.PUSH1[0xe0]
        + Op.MSTORE + Op.PUSH2[0x100] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
