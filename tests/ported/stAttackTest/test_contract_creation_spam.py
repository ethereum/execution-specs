"""
Ported from:
tests/static/state_tests/stAttackTest/ContractCreationSpamFiller.json

contract code:
    push32 0x6004600c60003960046000f3600035ff00000000000000000000000000000000
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    push1 0x00
    create
    push1 0x00
    sload
    dup1
    jumpdest
    push1 0x01
    add
    dup1
    push1 0x00
    mstore
    push1 0x00
    dup1
    push1 0x20
    dup2
    ... (558 more instructions)
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
    ["tests/static/state_tests/stAttackTest/ContractCreationSpamFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_contract_creation_spam(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x6a0a0fc761c612c340a0e98d33b37a75e5268472")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0x6004600c60003960046000f3600035ff00000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH1[0x0] + Op.SLOAD + Op.DUP1 + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL
        + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8
        + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20]
        + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP8 + Op.PUSH1[0x6]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1
        + Op.DUP8 + Op.PUSH1[0x6] + Op.CALL + Op.POP + Op.GAS + Op.PUSH2[0x6000]
        + Op.LT + Op.PUSH3[0x2f] + Op.JUMPI + Op.PUSH1[0x0] + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0xc9f2c9cd04674edea40000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
