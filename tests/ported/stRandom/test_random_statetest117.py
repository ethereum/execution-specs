"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest117Filler.json

contract code:
    prevrandao
    push32 0x01
    push32 0x4f3f701464972e74606d6ea82d4d3080599a0e79
    timestamp
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0x010000000000000000000000000000000000000000
    push16 0x8aa4a4980274f18c6158368d41571455
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
    ["tests/static/state_tests/stRandom/randomStatetest117Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest117(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x3374b8f7389a6ecd92dc42cbc9bb4e7cc0dce3ff")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PREVRANDAO + Op.PUSH32[0x1]
        + Op.PUSH32[0x4f3f701464972e74606d6ea82d4d3080599a0e79] + Op.TIMESTAMP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH16[0x8aa4a4980274f18c6158368d41571455] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE
    ),
    )
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
            "447f00000000000000000000000000000000000000000000000000000000000000017f00"
            "00000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e79427f000000"
            "000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000"
            "00000000000100000000000000000000000000000000000000006f8aa4a4980274f18c61"
            "58368d415714"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1763362724,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
