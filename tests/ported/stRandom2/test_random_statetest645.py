"""
Geth Failed this test on Frontier and Homestead

Ported from:
tests/static/state_tests/stRandom2/randomStatetest645Filler.json

callee code:
    pc
    push8 0x9b8e24022d8c28f3
    push3 0x0b55a0
    push4 0x84bc2f83
    sgt
    push6 0x15b61916f0f5
    push26 0xea3e9d28799d45aa77bf1fc1a84edf0193dea2d610209eaaf9c8
    eq

coinbase code:
    push4 0xcbb01282
    push3 0x1d72de
    mstore
    push9 0x022948f746c938a0cb
    push29 0x01ef17f23ed237d9f3262c4eb1b95112820595b127c516074df06223db
    push31 0x0c396eb18074f148d96fd766dda35b6cc250661b5f83f0ed625ba68a5ff49a
    log1
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
    ["tests/static/state_tests/stRandom2/randomStatetest645Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        4074160023,
        0,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_random_statetest645(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """Geth Failed this test on Frontier and Homestead."""
    coinbase = Address("0xaa0103980a7c3113d3a8f81478b0281492eb3d38")
    sender = Address("0xf2a0abc1a62216629b2c1aad302408e8e6054a61")
    contract = Address("0x0000000000000000000000000000000000000003")
    callee = Address("0x322c72dedad1a81092ab9ba908fbec8779ce1c32")
    callee_1 = Address("0x9e9c03f8f885c32813db5207fd04870f08327f30")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=13175566155172316,
    )

    pre[callee] = Account(
        balance=0xbcbaf5a33577f162,
        nonce=29,
        code=(
        Op.PC + Op.PUSH8[0x9b8e24022d8c28f3] + Op.PUSH3[0xb55a0]
        + Op.PUSH4[0x84bc2f83] + Op.SGT + Op.PUSH6[0x15b61916f0f5]
        + Op.PUSH26[0xea3e9d28799d45aa77bf1fc1a84edf0193dea2d610209eaaf9c8] + Op.EQ
    ),
    )
    pre[callee_1] = Account(balance=0xb3508c0f8a22f8a1, nonce=28)
    pre[coinbase] = Account(
        balance=0x2be1cfd5d6d6b0b7,
        nonce=175,
        code=(
        Op.PUSH4[0xcbb01282] + Op.PUSH3[0x1d72de] + Op.MSTORE
        + Op.PUSH9[0x22948f746c938a0cb]
        + Op.PUSH29[0x1ef17f23ed237d9f3262c4eb1b95112820595b127c516074df06223db]
        + Op.PUSH31[0xc396eb18074f148d96fd766dda35b6cc250661b5f83f0ed625ba68a5ff49a]
        + Op.LOG1
    ),
    )
    pre[sender] = Account(balance=0x6f1f70fea641f30a, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x0e5fb93861a38e5458e9d2ff0203d01d1d8167fa9c0db762cc5ca50eb43b3376"
        ),
        to=contract,
        data=bytes.fromhex("326e3696ffc10e3e95c67d29784a35ba967d416feb1e1712098bcbb4d20454c1681694f51d8591ff7b80f0e4da50c89a0a777fa7666abccfbd600e213bd71da4925c2a2115799e9c3bb1622f075452"),
        gas_limit=26970,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
