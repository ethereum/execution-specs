"""
RevertOpcodeCreate for CREATE2

Ported from:
tests/static/state_tests/stCreate2/RevertOpcodeCreateFiller.json

contract code:
    push15 0x600160005560016000fd6011600155
    push1 0x00
    mstore
    push1 0x00
    push1 0x0f
    push1 0x11
    push1 0x01
    create2
    push1 0x01
    sstore
    push1 0x0c
    push1 0x00
    sstore
    stop
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
    ["tests/static/state_tests/stCreate2/RevertOpcodeCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        460000,
        70000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_create(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """RevertOpcodeCreate for CREATE2."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[contract] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH15[0x600160005560016000fd6011600155] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0xf] + Op.PUSH1[0x11] + Op.PUSH1[0x1] + Op.CREATE2
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("600160005560016000fe6011600155"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
