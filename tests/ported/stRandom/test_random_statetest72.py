"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest72Filler.json

coinbase code:
    push1 0x00
    calldataload
    sload
    iszero
    push1 0x09
    jumpi
    stop
    jumpdest
    push1 0x20
    calldataload
    push1 0x00
    calldataload
    sstore

contract code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffff
    coinbase
    push32 0x4f3f701464972e74606d6ea82d4d3080599a0e79
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    push6 0x688dff579830
    mulmod
    sgt
    div
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
    ["tests/static/state_tests/stRandom/randomStatetest72Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest72(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd8ae0334e34ce6256b4c50a0e7d74ffe2fcab7e8")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff] + Op.COINBASE
        + Op.PUSH32[0x4f3f701464972e74606d6ea82d4d3080599a0e79]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.PUSH6[0x688dff579830] + Op.MULMOD + Op.SGT + Op.DIV
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000"
            "00000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000"
            "00000000000000ffffffffffffffffffffffffffffffffffffffff417f00000000000000"
            "00000000004f3f701464972e74606d6ea82d4d3080599a0e797f00000000000000000000"
            "0000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffff"
            "fffffffffffffffffffffffffffffffffffffe65688dff579830091304"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1575824584,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
