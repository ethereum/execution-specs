"""
Out of gas undoes the transient storage writes from a call.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage/19_oogUndoesTransientStoreFiller.yml

contract code:
    push0
    calldataload
    push1 0xe0
    shr
    dup1
    push4 0xe2da2eb0
    eq
    push1 0x21
    jumpi
    push4 0x3f371692
    eq
    push1 0x19
    jumpi
    stop
    jumpdest
    push1 0x1f
    push1 0x31
    jump
    jumpdest
    stop
    ... (39 more instructions)
"""

import pytest
from execution_testing import (
    AccessList,
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
    ["tests/static/state_tests/Cancun/stEIP1153_transientStorage/19_oogUndoesTransientStoreFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_19_oog_undoes_transient_store(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Out of gas undoes the transient storage writes from a call.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xcef5f3b33e31360216fab2c61046840df9bd788e")
    contract = Address("0x6021c216382b18c6f19bdbec3c5b4201e92f87fd")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH0 + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.SHR + Op.DUP1
        + Op.PUSH4[0xe2da2eb0] + Op.EQ + Op.PUSH1[0x21] + Op.JUMPI
        + Op.PUSH4[0x3f371692] + Op.EQ + Op.PUSH1[0x19] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1f] + Op.PUSH1[0x31] + Op.JUMP + Op.JUMPDEST
        + Op.STOP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x1f] + Op.PUSH1[0xb] + Op.PUSH0
        + Op.TSTORE + Op.PUSH3[0x2fffff] + Op.PUSH0 + Op.SHA3 + Op.POP + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x4e] + Op.PUSH0 + Op.TSTORE + Op.PUSH0 + Op.TLOAD
        + Op.PUSH0 + Op.SSTORE + Op.PUSH4[0xe2da2eb] + Op.PUSH1[0xe4] + Op.SHL
        + Op.PUSH0 + Op.MSTORE + Op.PUSH0 + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2
        + Op.DUP1 + Op.ADDRESS + Op.PUSH2[0xc350] + Op.CALL + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH0 + Op.TLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.JUMP
    ),
        storage={0x0: 0xffff, 0x1: 0xffff, 0x2: 0xffff},
    )
    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xbe0e7d5fea1604bf57e004b0b414df8de04816dbb1c8f8719b725d0d6619b531"
        ),
        to=contract,
        data=bytes.fromhex("3f371692"),
        gas_limit=400000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=0,
        nonce=0,
        value=0,
        access_list=[],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
