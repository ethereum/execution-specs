"""
This test checks that the returndata buffer is changed when a subcall REVERTs.  In each test case, a non-empty returndata buffer is set up, and then calls into a contract that REVERTs.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json

callee code:
    push1 0x0c
    push1 0x01
    mstore
    push1 0x40
    push1 0x00
    return
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x127eaf7e31d691a8393b7a2f84a6e94372190c01
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x03f7a0
    call
    push1 0x0a
    sstore
    ... (1 more instructions)

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x127eaf7e31d691a8393b7a2f84a6e94372190c01
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xea519c47889074e6378b0d83747f2c3ea0b9cbc9
    push3 0x0186a0
    call
    push1 0x00
    sstore
    returndatasize
    ... (3 more instructions)

callee_2 code:
    push1 0x0c
    push1 0x01
    sstore
    push1 0x01
    push1 0x00
    revert
    push1 0x0d
    push1 0x03
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x127eaf7e31d691a8393b7a2f84a6e94372190c01
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b
    push2 0xc350
    callcode
    push1 0x00
    sstore
    returndatasize
    ... (3 more instructions)

callee_4 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x127eaf7e31d691a8393b7a2f84a6e94372190c01
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b
    push2 0xc350
    call
    push1 0x00
    sstore
    returndatasize
    ... (3 more instructions)

callee_5 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x127eaf7e31d691a8393b7a2f84a6e94372190c01
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b
    push2 0xc350
    call
    push1 0x04
    sstore
    returndatasize
    ... (3 more instructions)

callee_6 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x127eaf7e31d691a8393b7a2f84a6e94372190c01
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b
    push2 0xc350
    delegatecall
    push1 0x00
    sstore
    returndatasize
    push1 0x02
    ... (2 more instructions)
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
    ["tests/static/state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit",
    [
        ("000000000000000000000000e73611b5b479b30c93ac377aeb3bfb199764f3c3", 860000),
        ("000000000000000000000000e73611b5b479b30c93ac377aeb3bfb199764f3c3", 28000),
        ("000000000000000000000000c9da6cd8413f64323f12cd44c99671f280f15e1c", 860000),
        ("000000000000000000000000c9da6cd8413f64323f12cd44c99671f280f15e1c", 28000),
        ("000000000000000000000000f20ccaf271beaa36e7cf4c9ced2867fac9558f14", 860000),
        ("000000000000000000000000f20ccaf271beaa36e7cf4c9ced2867fac9558f14", 28000),
        ("0000000000000000000000006bacdfa8216dbb2a09819f8739e57ae3574c9fff", 860000),
        ("0000000000000000000000006bacdfa8216dbb2a09819f8739e57ae3574c9fff", 28000),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_calls_on_non_empty_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
) -> None:
    """This test checks that the returndata buffer is changed when a subcall REVERTs.  In each test case, a non-empty returndata buffer is set up, and then calls into a contract that REVERTs.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x172a8f572404293aa810685dfdc6f740c300cc4b")
    callee = Address("0x127eaf7e31d691a8393b7a2f84a6e94372190c01")
    callee_1 = Address("0x6bacdfa8216dbb2a09819f8739e57ae3574c9fff")
    callee_2 = Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b")
    callee_3 = Address("0xc9da6cd8413f64323f12cd44c99671f280f15e1c")
    callee_4 = Address("0xe73611b5b479b30c93ac377aeb3bfb199764f3c3")
    callee_5 = Address("0xea519c47889074e6378b0d83747f2c3ea0b9cbc9")
    callee_6 = Address("0xf20ccaf271beaa36e7cf4c9ced2867fac9558f14")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x127eaf7e31d691a8393b7a2f84a6e94372190c01]
        + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.PUSH3[0x3f7a0] + Op.CALL + Op.PUSH1[0xa] + Op.SSTORE
        + Op.STOP
    ),
        storage={0xa: 0xff},
    )
    pre[callee_1] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x127eaf7e31d691a8393b7a2f84a6e94372190c01]
        + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xea519c47889074e6378b0d83747f2c3ea0b9cbc9] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.REVERT + Op.PUSH1[0xd] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x127eaf7e31d691a8393b7a2f84a6e94372190c01]
        + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x127eaf7e31d691a8393b7a2f84a6e94372190c01]
        + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b] + Op.PUSH2[0xc350]
        + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x127eaf7e31d691a8393b7a2f84a6e94372190c01]
        + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b] + Op.PUSH2[0xc350]
        + Op.CALL + Op.PUSH1[0x4] + Op.SSTORE + Op.RETURNDATASIZE + Op.PUSH1[0x5]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x127eaf7e31d691a8393b7a2f84a6e94372190c01]
        + Op.PUSH1[0x0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.RETURNDATASIZE
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
