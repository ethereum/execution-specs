"""
Create2 inside Create2 inside Create2....

Ported from:
tests/static/state_tests/stCreate2/Create2RecursiveFiller.json

contract code:
    push30 0x606460006000396103e85a10601b576000606460006000f5601d565b5a5b
    push1 0x00
    mstore
    push1 0x00
    push1 0x1e
    push1 0x02
    push1 0x00
    create2
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
    ["tests/static/state_tests/stCreate2/Create2RecursiveFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        9151314442816847871,
        20070000000000,
        20080000000000,
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_create2_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Create2 inside Create2 inside Create2....."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(
        balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        nonce=0,
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH30[0x606460006000396103e85a10601b576000606460006000f5601d565b5a5b]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1e] + Op.PUSH1[0x2]
        + Op.PUSH1[0x0] + Op.CREATE2 + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
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
