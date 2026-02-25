"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest265Filler.json

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
    extcodesize
    push32 0xc350
    push11 0x7f00000000000000000000
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    stop
    ... (10 more instructions)
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
    ["tests/static/state_tests/stRandom/randomStatetest265Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest265(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x897196687e79db7a21310478e9ba6cc9d6c1209e")

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
        "00000000000000000000000000000000000000000000000000000000c3503b7f00000000"
        "0000000000000000000000000000000000000000000000000000c3506a7f000000000000"
        "00000000000000000000000000000000000000000000000000017f000000000000000000"
        "000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000001"
        "0000000000000000000000000000000000000000745b9b824070397f921960005155"
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000000000000000000000000000000000000000c3507f0000"
            "00000000000000000000000000000000000000000000000000000000c3503b7f00000000"
            "0000000000000000000000000000000000000000000000000000c3506a7f000000000000"
            "00000000000000000000000000000000000000000000000000017f000000000000000000"
            "000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000001"
            "0000000000000000000000000000000000000000745b9b824070397f9219"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=571967067,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
