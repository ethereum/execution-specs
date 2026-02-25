"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest620Filler.json

contract code:
    push32 0xffffffffffffffffffffffffffffffffffffffff
    timestamp
    push32 0x010000000000000000000000000000000000000000
    gaslimit
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    push32 0xc350
    push32 0x00
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push16 0x6c54a420327d73727d9d1a667bf38955
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
    ["tests/static/state_tests/stRandom2/randomStatetest620Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest620(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x388b9f8645907d4c06dee4ebab70d61e76fa253c")

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
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff] + Op.TIMESTAMP
        + Op.PUSH32[0x10000000000000000000000000000000000000000] + Op.GASLIMIT
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.PUSH32[0xc350] + Op.PUSH32[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0x6c54a420327d73727d9d1a667bf38955] + Op.PUSH1[0x0] + Op.MLOAD
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
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff427f00"
            "00000000000000000000010000000000000000000000000000000000000000457fffffff"
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000"
            "000000000000000000000000000000000000000000000000c3507f000000000000000000"
            "00000000000000000000000000000000000000000000007fffffffffffffffffffffffff"
            "ffffffffffffffffffffffffffffffffffffffff6f6c54a420327d73727d9d1a667bf389"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1643601446,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
