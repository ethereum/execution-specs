"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest119Filler.json

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
    msize
    number
    push32 0x01
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0x010000000000000000000000000000000000000000
    push32 0x00
    push16 0x52503b127c115a9673a4313790956655
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
    ["tests/static/state_tests/stRandom/randomStatetest119Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest119(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xb49ce71df6647baf4ba00db0f0579cdbde684010")

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
        Op.GASLIMIT + Op.MSIZE + Op.NUMBER + Op.PUSH32[0x1]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0x10000000000000000000000000000000000000000] + Op.PUSH32[0x0]
        + Op.PUSH16[0x52503b127c115a9673a4313790956655] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "4559437f0000000000000000000000000000000000000000000000000000000000000001"
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000"
            "00000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000"
            "0000000000000100000000000000000000000000000000000000007f0000000000000000"
            "0000000000000000000000000000000000000000000000006f52503b127c115a9673a431"
            "37909566"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=412561866,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
