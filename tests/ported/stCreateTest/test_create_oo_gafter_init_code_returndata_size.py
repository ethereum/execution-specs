"""
Calls a contract that runs CREATE which deploy a code. then OOG happens upon deployment of the actual code. check the RETURNDATASIZE after create. fails with OOG if RETURNDATASIZE != 0

Ported from:
tests/static/state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json

contract code:
    push19 0x6960016001556001600255600052600a6016f3
    push1 0x00
    mstore
    push1 0x13
    push1 0x0d
    push1 0x00
    create
    pop
    returndatasize
    push1 0x02
    exp
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
    ["tests/static/state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_init_code_returndata_size(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calls a contract that runs CREATE which deploy a code. then OOG happens upon deployment of the actual code. check the RETURNDATASIZE after create. fails with OOG if RETURNDATASIZE != 0."""
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
        balance=0,
        nonce=0,
        code=(
        Op.PUSH19[0x6960016001556001600255600052600a6016f3] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x13] + Op.PUSH1[0xd] + Op.PUSH1[0x0] + Op.CREATE
        + Op.POP + Op.RETURNDATASIZE + Op.PUSH1[0x2] + Op.EXP + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=55054,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
