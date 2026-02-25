"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest368Filler.json

contract code:
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0x00
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    mulmod
    push32 0x00
    push32 0x945304eb96065b2a98b57a48a06ae28d285a71b5
    timestamp
    mod
    create
    push14 0x870339356057907760005155

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
    ["tests/static/state_tests/stRandom/randomStatetest368Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest368(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

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
        code=bytes.fromhex(
        "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000"
        "0000000000000000000000000000000000000000000000000000000000007fffffffffff"
        "fffffffffffffffffffffffffffffffffffffffffffffffffffffe7f0000000000000000"
        "00000000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffff"
        "fffffffffffffffffffffffffffffffffffffffffe097f00000000000000000000000000"
        "000000000000000000000000000000000000007f000000000000000000000000945304eb"
        "96065b2a98b57a48a06ae28d285a71b54206f06d870339356057907760005155"
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
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000"
            "0000000000000000000000000000000000000000000000000000000000007fffffffffff"
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffe7f0000000000000000"
            "00000000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffff"
            "fffffffffffffffffffffffffffffffffffffffffe097f00000000000000000000000000"
            "000000000000000000000000000000000000007f000000000000000000000000945304eb"
            "96065b2a98b57a48a06ae28d285a71b54206f06d8703393560579077"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1135359124,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
