"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest85Filler.json

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
    push32 0xc350
    push32 0xc350
    push32 0x00
    push32 0x00
    push32 0x4f3f701464972e74606d6ea82d4d3080599a0e79
    push32 0x01
    push32 0x01
    push32 0xc350
    callcode
    jumpdest
    sstore
    push31 0x348ff374819d123109539b55
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
    ["tests/static/state_tests/stRandom/randomStatetest85Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest85(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd2fd98d49a70f7c4b524b8e53c8e5fc695555554")

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
        code=bytes.fromhex(
        "7f000000000000000000000000000000000000000000000000000000000000c3507f0000"
        "00000000000000000000000000000000000000000000000000000000c3507f0000000000"
        "0000000000000000000000000000000000000000000000000000007f0000000000000000"
        "0000000000000000000000000000000000000000000000007f0000000000000000000000"
        "004f3f701464972e74606d6ea82d4d3080599a0e797f0000000000000000000000000000"
        "0000000000000000000000000000000000017f0000000000000000000000000000000000"
        "0000000000000000000000000000017f0000000000000000000000000000000000000000"
        "00000000000000000000c350f25b557e348ff374819d123109539b55"
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000000000000000000000000000000000000000c3507f0000"
            "00000000000000000000000000000000000000000000000000000000c3507f0000000000"
            "0000000000000000000000000000000000000000000000000000007f0000000000000000"
            "0000000000000000000000000000000000000000000000007f0000000000000000000000"
            "004f3f701464972e74606d6ea82d4d3080599a0e797f0000000000000000000000000000"
            "0000000000000000000000000000000000017f0000000000000000000000000000000000"
            "0000000000000000000000000000017f0000000000000000000000000000000000000000"
            "00000000000000000000c350f25b557e348ff374819d123109539b"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=994504369,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
