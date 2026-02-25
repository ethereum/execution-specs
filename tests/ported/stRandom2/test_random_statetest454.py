"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest454Filler.json

contract code:
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    push32 0x00
    sstore
    push32 0x00
    push32 0x00
    sstore
    push32 0x4f3f701464972e74606d6ea82d4d3080599a0e79
    exp
    dup5
    caller
    swap2
    dup9
    push5 0x6595668352
    log0
    push2 0x8555
    push1 0x00
    mload
    sstore

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
    ["tests/static/state_tests/stRandom2/randomStatetest454Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest454(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x0089d9313f6c18f62805e3a145739544ee1459a7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.PUSH32[0x0] + Op.SSTORE + Op.PUSH32[0x0] + Op.PUSH32[0x0] + Op.SSTORE
        + Op.PUSH32[0x4f3f701464972e74606d6ea82d4d3080599a0e79] + Op.EXP + Op.DUP5
        + Op.CALLER + Op.SWAP2 + Op.DUP9 + Op.PUSH5[0x6595668352] + Op.LOG0
        + Op.PUSH2[0x8555] + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
    ),
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

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f0000"
            "000000000000000000000000000000000000000000000000000000000000557f00000000"
            "000000000000000000000000000000000000000000000000000000007f00000000000000"
            "00000000000000000000000000000000000000000000000000557f000000000000000000"
            "0000004f3f701464972e74606d6ea82d4d3080599a0e790a84339188646595668352a061"
            "85"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1431310051,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
