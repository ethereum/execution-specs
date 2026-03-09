"""
collision with the contract that already has the same init code that we are...

Ported from:
tests/static/state_tests/stCreate2/create2collisionCode2Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/create2collisionCode2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "6b620102036000526003601df36000526000600c60146000f500",
        "6b620102036000526003601df36000526000600c60146001f500",
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_code2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Collision with the contract that already has the same init code..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SUB(Op.MUL, Op.ADD),
        address=Address("0xfce41d047b4a1d4450382dcc29ec7e5fedc5f9a3"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=400000,
        value=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
