"""
Check balance in blackbox, just fill the balance consumed

Ported from:
tests/static/state_tests/stStaticCall/static_CheckCallCostOOGFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xebe7ed7a6e995c9843a6df04e332981ebb2772e0
    push1 0x64
    staticcall
    stop

callee code:
    push1 0x01
    push1 0x01
    mstore
    push3 0x2fffff
    push1 0x00
    sha3
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
    ["tests/static/state_tests/stStaticCall/static_CheckCallCostOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        22000,
        1000000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_call_cost_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Check balance in blackbox, just fill the balance consumed."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x6a0ad26ecf17c7340ded4285f64e23b3aafcf346")
    contract = Address("0xb59292b3a630476adbc4a3643c0815b682a5009a")
    callee = Address("0xebe7ed7a6e995c9843a6df04e332981ebb2772e0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x5af3107a4000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xebe7ed7a6e995c9843a6df04e332981ebb2772e0] + Op.PUSH1[0x64]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH3[0x2fffff]
        + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x3327048bbc0b8c348a6352be62994144e64b8ff2cec68d9ff4ca4e911ecd5d22"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
