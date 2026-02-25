"""
A contract which performs SUICIDE, and is then attempted to be recreated (different code, same init-code) during the same transaction. This ought to fail, since the code is not cleaned out until after the transaction is ended.

Ported from:
tests/static/state_tests/stCreate2/create2collisionSelfdestructed2Filler.json

contract code:
    push1 0x10
    selfdestruct

callee_1 code:
    push1 0x10
    selfdestruct
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
    ["tests/static/state_tests/stCreate2/create2collisionSelfdestructed2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "6000600060006000600073fce41d047b4a1d4450382dcc29ec7e5fedc5f9a361c350f1506b620102036000526003601df36000526000600c60146000f500",
        "6000600060006000600073cff64f4c5df8f436c4f2c1af4b2e3f9e3004c77961c350f1506b626010ff6000526003601df36000526000600c60146000f500",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_selfdestructed2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """A contract which performs SUICIDE, and is then attempted to be recreated (different code, same init-code) during the same transaction. This ought to fail, since the code is not cleaned out until after the transaction is ended.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcff64f4c5df8f436c4f2c1af4b2e3f9e3004c779")
    callee_1 = Address("0xfce41d047b4a1d4450382dcc29ec7e5fedc5f9a3")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(balance=1, nonce=1, code=Op.PUSH1[0x10] + Op.SELFDESTRUCT)
    pre[callee_1] = Account(balance=1, nonce=0, code=Op.PUSH1[0x10] + Op.SELFDESTRUCT + Op.STOP)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
