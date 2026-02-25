"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest524Filler.json

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
    gaslimit
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    timestamp
    push32 0xffffffffffffffffffffffffffffffffffffffff
    calldataload
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0x00
    push32 0x00
    callvalue
    sha3
    dup11
    callvalue
    exp
    swap15
    sstore
    push1 0x00
    mload
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
    ["tests/static/state_tests/stRandom2/randomStatetest524Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest524(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xaa56ee356b0dd8022ad49a794fb5a37c554b32aa")

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
        Op.GASLIMIT
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.TIMESTAMP + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.CALLDATALOAD + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0x0] + Op.PUSH32[0x0] + Op.CALLVALUE + Op.SHA3 + Op.DUP11
        + Op.CALLVALUE + Op.EXP + Op.SWAP15 + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "457ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe427f"
            "000000000000000000000000ffffffffffffffffffffffffffffffffffffffff357f0000"
            "00000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000"
            "0000000000000000000000000000000000000000000000000000007f0000000000000000"
            "00000000000000000000000000000000000000000000000034208a340a9e"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1968091255,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
