"""
Transient storage can't be manipulated from nested staticcall.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage/14_revertAfterNestedStaticcallFiller.yml

contract code:
    push0
    calldataload
    push1 0xe0
    shr
    dup1
    push4 0xf5f40590
    eq
    push1 0x2f
    jumpi
    dup1
    push4 0xf8dfc2d0
    eq
    push1 0x2b
    jumpi
    push4 0x62fdb9be
    eq
    push1 0x23
    jumpi
    stop
    jumpdest
    ... (65 more instructions)
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
    ["tests/static/state_tests/Cancun/stEIP1153_transientStorage/14_revertAfterNestedStaticcallFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_14_revert_after_nested_staticcall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Transient storage can't be manipulated from nested staticcall.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xcef5f3b33e31360216fab2c61046840df9bd788e")
    contract = Address("0x1150baff55fdcea5fd92b0995358ec0c416debe3")

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
        + Op.PUSH4[0xf5f40590] + Op.EQ + Op.PUSH1[0x2f] + Op.JUMPI + Op.DUP1
        + Op.PUSH4[0xf8dfc2d0] + Op.EQ + Op.PUSH1[0x2b] + Op.JUMPI
        + Op.PUSH4[0x62fdb9be] + Op.EQ + Op.PUSH1[0x23] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x29] + Op.PUSH1[0x77] + Op.JUMP + Op.JUMPDEST
        + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x5d] + Op.JUMP + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x29] + Op.PUSH1[0xa] + Op.PUSH0 + Op.TSTORE + Op.PUSH0 + Op.TLOAD
        + Op.PUSH0 + Op.SSTORE + Op.PUSH4[0xf8dfc2d] + Op.PUSH1[0xe4] + Op.SHL
        + Op.PUSH0 + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH0 + Op.DUP2 + Op.DUP2
        + Op.ADDRESS + Op.PUSH2[0xffff] + Op.STATICCALL + Op.PUSH0 + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH0 + Op.TLOAD
        + Op.PUSH1[0x3] + Op.SSTORE + Op.JUMP + Op.JUMPDEST + Op.PUSH4[0x317edcdf]
        + Op.PUSH1[0xe1] + Op.SHL + Op.PUSH0 + Op.MSTORE + Op.PUSH0 + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.ADDRESS + Op.GAS + Op.CALL
        + Op.PUSH0 + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH0 + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0xb] + Op.PUSH0 + Op.TSTORE + Op.JUMP
    ),
        storage={0x1: 0xffff},
    )
    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xbe0e7d5fea1604bf57e004b0b414df8de04816dbb1c8f8719b725d0d6619b531"
        ),
        to=contract,
        data=bytes.fromhex("f5f40590"),
        gas_limit=400000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=0,
        nonce=0,
        value=0,
        access_list=[],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
