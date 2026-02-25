"""
EXTCODEHASH/EXTCODESIZE of an account created then deleted in a CALL, checking results after the CALL returns

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashCreatedAndDeletedAccountRecheckInOuterCallFiller.json

callee code:
    push1 0x10
    push1 0x11
    dup1
    push1 0x44
    push1 0x80
    codecopy
    push1 0x80
    push1 0x00
    create2
    push1 0x00
    mstore
    push1 0x00
    mload
    extcodehash
    push1 0x00
    sstore
    push1 0x00
    mload
    extcodesize
    push1 0x01
    ... (36 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdeadbeef00000000000000000000000000000000
    push3 0x020000
    call
    pop
    push20 0x123f4c415171383dcf6f3ac6c3b70fe321e11b5e
    extcodehash
    push1 0x00
    sstore
    push20 0x123f4c415171383dcf6f3ac6c3b70fe321e11b5e
    extcodesize
    push1 0x01
    sstore
    stop
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashCreatedAndDeletedAccountRecheckInOuterCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_created_and_deleted_account_recheck_in_outer_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODEHASH/EXTCODESIZE of an account created then deleted in a CALL, checking results after the CALL returns."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xdeadbeef00000000000000000000000000000001")
    callee = Address("0xdeadbeef00000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0x11] + Op.DUP1 + Op.PUSH1[0x44] + Op.PUSH1[0x80]
        + Op.CODECOPY + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODEHASH + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODESIZE + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH3[0x10000] + Op.CALL
        + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODEHASH + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODESIZE + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP + Op.STOP + Op.INVALID + Op.PUSH1[0x4] + Op.DUP1
        + Op.PUSH1[0xd] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.SELFDESTRUCT + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000000]
        + Op.PUSH3[0x20000] + Op.CALL + Op.POP
        + Op.PUSH20[0x123f4c415171383dcf6f3ac6c3b70fe321e11b5e] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0x123f4c415171383dcf6f3ac6c3b70fe321e11b5e] + Op.EXTCODESIZE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
