"""
Test_call_lose_gas_oog.

Ported from:
state_tests/stDelegatecallTestHomestead/CallLoseGasOOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stDelegatecallTestHomestead/CallLoseGasOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_lose_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_lose_gas_oog."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    addr = pre.fund_eoa(amount=7000)  # noqa: F841
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL (ADD 1(MUL @@0 100000)) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x186A0)),
                address=0xBE855315B63D137B74D5EED6BE5CD9DDE6E2478D,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2, value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3E8))
        )
        + Op.STOP,
        balance=1024,
        nonce=0,
        address=Address(0xBE855315B63D137B74D5EED6BE5CD9DDE6E2478D),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
        value=10,
    )

    post = {target: Account(storage={0: 1, 2: 1001})}

    state_test(env=env, pre=pre, post=post, tx=tx)
