"""
This is a canon example of a test found by fuzzing with EVMlab, demoing how a suicide-created-but-empty account has a non-zero codehash in geth

Ported from:
tests/static/state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192Filler.json

contract code:
    push3 0xabcdef
    selfdestruct

coinbase code:
    push2 0xdead
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0xdead
    gas
    call
    push3 0xabcdef
    extcodehash
    push1 0x01
    sstore
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
    ["tests/static/state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest_default_tue_07_58_41_15153_575192(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """This is a canon example of a test found by fuzzing with EVMlab, demoing how a suicide-created-but-empty account has a non-zero codehash in geth."""
    coinbase = Address("0xdf5277352f687058bec2d433f2e2d1b7f0c970ae")
    sender = Address("0x739940fcce39246c4bfe61029c0abd378f93a2ac")
    contract = Address("0x589d1b72331c25effee38732d79f48f729681853")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    pre[contract] = Account(balance=0, nonce=28, code=Op.PUSH3[0xabcdef] + Op.SELFDESTRUCT)
    pre[sender] = Account(balance=0x5d8fdd3ff54298b4, nonce=28)
    pre[coinbase] = Account(
        balance=0,
        nonce=28,
        code=(
        Op.PUSH2[0xdead] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL
        + Op.PUSH3[0xabcdef] + Op.EXTCODEHASH + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xeddb5b1a0109f06919449a6279e9de92a892086bdd851894eb8ffa6c8ff4e563"
        ),
        to=coinbase,
        data=b"",
        gas_limit=6282759,
        gas_price=11,
        nonce=28,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest_default_tue_07_58_41_15153_575192_london(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """This is a canon example of a test found by fuzzing with EVMlab, demoing how a suicide-created-but-empty account has a non-zero codehash in geth."""
    coinbase = Address("0xdf5277352f687058bec2d433f2e2d1b7f0c970ae")
    sender = Address("0x739940fcce39246c4bfe61029c0abd378f93a2ac")
    contract = Address("0x589d1b72331c25effee38732d79f48f729681853")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    pre[contract] = Account(balance=0, nonce=28, code=Op.PUSH3[0xabcdef] + Op.SELFDESTRUCT)
    pre[sender] = Account(balance=0x5d8fdd3ff54298b4, nonce=28)
    pre[coinbase] = Account(
        balance=0,
        nonce=28,
        code=(
        Op.PUSH2[0xdead] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL
        + Op.PUSH3[0xabcdef] + Op.EXTCODEHASH + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xeddb5b1a0109f06919449a6279e9de92a892086bdd851894eb8ffa6c8ff4e563"
        ),
        to=coinbase,
        data=b"",
        gas_limit=6282759,
        gas_price=10,
        nonce=28,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
