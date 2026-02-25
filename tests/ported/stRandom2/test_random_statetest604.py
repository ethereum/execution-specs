"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest604Filler.json

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
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0x010000000000000000000000000000000000000000
    number
    push32 0x00
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    prevrandao
    log4
    coinbase
    dup11
    dup4
    sub
    swap13
    sdiv
    dup8
    calldatasize
    extcodesize
    sdiv
    xor
    sha3
    blockhash
    ... (4 more instructions)
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
    ["tests/static/state_tests/stRandom2/randomStatetest604Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest604(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x7619f7a13ba66bb3e74b1d609bc4c979fdfda283")

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
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0x10000000000000000000000000000000000000000] + Op.NUMBER
        + Op.PUSH32[0x0]
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.PREVRANDAO + Op.LOG4 + Op.COINBASE + Op.DUP11 + Op.DUP4 + Op.SUB
        + Op.SWAP13 + Op.SDIV + Op.DUP8 + Op.CALLDATASIZE + Op.EXTCODESIZE + Op.SDIV
        + Op.XOR + Op.SHA3 + Op.BLOCKHASH + Op.MOD + Op.MOD + Op.GAS + Op.MOD
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000"
            "000000000000000000010000000000000000000000000000000000000000437f00000000"
            "000000000000000000000000000000000000000000000000000000007fffffffffffffff"
            "fffffffffffffffffffffffffffffffffffffffffffffffffe44a4418a83039c0587363b"
            "0518204006065a06"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1287981996,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
