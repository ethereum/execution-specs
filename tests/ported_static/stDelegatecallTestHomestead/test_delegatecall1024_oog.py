"""
Test_delegatecall1024_oog.

Ported from:
state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall1024_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall1024_oog."""
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
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL (MUL (SUB (GAS) 10000) (SUB 1 (DIV @@0 1025))) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=Op.MUL(
                    Op.SUB(Op.GAS, 0x2710),
                    Op.SUB(0x1, Op.DIV(Op.SLOAD(key=0x0), 0x401)),
                ),
                address=0x62C5C9278DA01E6594D6FEDE061838CF5E597F2B,
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
        address=Address(0x62C5C9278DA01E6594D6FEDE061838CF5E597F2B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=15720826,
        value=10,
    )

    post = {target: Account(storage={0: 146, 1: 1, 2: 0x23A51})}

    state_test(env=env, pre=pre, post=post, tx=tx)
