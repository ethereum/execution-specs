"""
https://github.com/ethereum/tests/issues/493,  CODECOPY and EXTCODECOPY where codesize = 0

Ported from:
tests/static/state_tests/stExtCodeHash/codeCopyZero_ParisFiller.yml

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0xa222000000000000000000000000000000000000
    extcodecopy
    push1 0x00
    mload
    push1 0x10
    sstore
    push20 0xa222000000000000000000000000000000000000
    extcodesize
    push1 0x11
    sstore
    push20 0xa222000000000000000000000000000000000000
    extcodehash
    push1 0x12
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    ... (75 more instructions)

callee code:
    push1 0x00
    push1 0x39
    dup1
    push1 0x1a
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop
    stop
    invalid
    push1 0x20
    push1 0x00
    push1 0x00
    ... (34 more instructions)
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
    ["tests/static/state_tests/stExtCodeHash/codeCopyZero_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_code_copy_zero_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """https://github.com/ethereum/tests/issues/493,  CODECOPY and EXTCODECOPY where codesize = 0."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xa000000000000000000000000000000000000000")
    callee = Address("0xa100000000000000000000000000000000000000")
    callee_1 = Address("0xa200000000000000000000000000000000000000")
    callee_2 = Address("0xa300000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa222000000000000000000000000000000000000] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x10] + Op.SSTORE
        + Op.PUSH20[0xa222000000000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x11] + Op.SSTORE
        + Op.PUSH20[0xa222000000000000000000000000000000000000] + Op.EXTCODEHASH
        + Op.PUSH1[0x12] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa222000000000000000000000000000000000000] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0x13] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa200000000000000000000000000000000000000]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x20] + Op.SSTORE
        + Op.PUSH20[0xa200000000000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x21] + Op.SSTORE
        + Op.PUSH20[0xa200000000000000000000000000000000000000] + Op.EXTCODEHASH
        + Op.PUSH1[0x22] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa200000000000000000000000000000000000000] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0x23] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa300000000000000000000000000000000000000]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x30] + Op.SSTORE
        + Op.PUSH20[0xa300000000000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x31] + Op.SSTORE
        + Op.PUSH20[0xa300000000000000000000000000000000000000] + Op.EXTCODEHASH
        + Op.PUSH1[0x32] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa300000000000000000000000000000000000000] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0x33] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa100000000000000000000000000000000000000] + Op.PUSH3[0x86470]
        + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x40] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x39] + Op.DUP1 + Op.PUSH1[0x1a] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.STOP
        + Op.INVALID + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x50] + Op.SSTORE + Op.ADDRESS
        + Op.EXTCODESIZE + Op.PUSH1[0x51] + Op.SSTORE + Op.ADDRESS + Op.EXTCODEHASH
        + Op.PUSH1[0x52] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.ADDRESS + Op.PUSH2[0xc350] + Op.CALLCODE
        + Op.EXTCODESIZE + Op.PUSH1[0x53] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.ADDRESS + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x54] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(balance=10, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=1400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
