"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest481Filler.json

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
    prevrandao
    push32 0x01
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffff
    mulmod
    number
    push32 0x010000000000000000000000000000000000000000
    log2
    push10 0x5a7d52064361127350
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
    ["tests/static/state_tests/stRandom2/randomStatetest481Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest481(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x6566eb05c057cad2fd88c1fec362190264dde517")

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
        "447f00000000000000000000000000000000000000000000000000000000000000017f00"
        "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff7fffffffff"
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000"
        "0000000000ffffffffffffffffffffffffffffffffffffffff09437f0000000000000000"
        "000000010000000000000000000000000000000000000000a2695a7d52064361127350"
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "447f00000000000000000000000000000000000000000000000000000000000000017f00"
            "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff7fffffffff"
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000"
            "0000000000ffffffffffffffffffffffffffffffffffffffff09437f0000000000000000"
            "000000010000000000000000000000000000000000000000a2695a7d52064361127350"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1124860809,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
