"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest313Filler.json

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
    signextend
    push32 0x01
    extcodecopy
    push32 0xc350
    log3
    gaslimit
    gaslimit
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    dup3
    dup8
    log3
    sha3
    dup13
    dup13
    gas
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
    ["tests/static/state_tests/stRandom/randomStatetest313Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest313(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x9f0b64fb000394e77826ea5ee94fe9cf30284bf2")

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
        Op.SIGNEXTEND + Op.PUSH32[0x1] + Op.EXTCODECOPY + Op.PUSH32[0xc350]
        + Op.LOG3 + Op.GASLIMIT + Op.GASLIMIT
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP3 + Op.DUP8 + Op.LOG3 + Op.SHA3 + Op.DUP13 + Op.DUP13 + Op.GAS
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "0b7f00000000000000000000000000000000000000000000000000000000000000013c7f"
            "000000000000000000000000000000000000000000000000000000000000c350a345457f"
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8287a320"
            "8c8c5a"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=827973881,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
