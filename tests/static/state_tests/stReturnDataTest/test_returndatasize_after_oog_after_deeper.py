"""
transaction calls A (CALL B(CALL C(RETURN) OOG) 'check buffers')

Ported from:
tests/static/state_tests/stReturnDataTest/returndatasize_after_oog_after_deeperFiller.json

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xcb33b9a773995316746a40201081d054635d02da
    push3 0x0186a0
    call
    push1 0x02
    sstore
    returndatasize
    push1 0x00
    sstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee code:
    push1 0xff
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x8e0c75135225713d8c9acbb889abba5a5f598920
    push3 0x0186a0
    call
    pop
    jumpdest
    push1 0x01
    iszero
    push1 0x34
    jumpi
    push1 0x01
    push1 0x00
    sstore
    push1 0x25
    jump
    jumpdest
    ... (1 more instructions)
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
    ["tests/static/state_tests/stReturnDataTest/returndatasize_after_oog_after_deeperFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_oog_after_deeper(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """transaction calls A (CALL B(CALL C(RETURN) OOG) 'check buffers')."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x73470b0c32d3f7811258f2bf112aa71e17b115c6")
    contract = Address("0x58eaa3041ad52c24e38e485222953f1cc19c7484")
    callee = Address("0x8e0c75135225713d8c9acbb889abba5a5f598920")
    callee_1 = Address("0xbda572e15071b6ab42cfec01423f1fbb1de68703")
    callee_2 = Address("0xcb33b9a773995316746a40201081d054635d02da")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xcb33b9a773995316746a40201081d054635d02da]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.RETURNDATASIZE
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0xffffffff, 0x1: 0xffffffff, 0x2: 0xffffffff},
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_1] = Account(balance=0x1000000000, nonce=0)
    pre[callee_2] = Account(
        balance=0x6400000000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x8e0c75135225713d8c9acbb889abba5a5f598920]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.POP + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.ISZERO + Op.PUSH1[0x34] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x25] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x987c63506890b18862bd2304513f21b726a7e35961c9214954326694141fdb46"
        ),
        to=contract,
        data=b"",
        gas_limit=200000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
