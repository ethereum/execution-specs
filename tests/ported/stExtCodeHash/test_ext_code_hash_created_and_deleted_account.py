"""
EXTCODEHASH/EXTCODESIZE of an account created then deleted in same transaction

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashCreatedAndDeletedAccountFiller.json

contract code:
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashCreatedAndDeletedAccountFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_created_and_deleted_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODEHASH/EXTCODESIZE of an account created then deleted in same transaction."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x244fd17492eb0414905d9d2405c78ab23c125495")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
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
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
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
