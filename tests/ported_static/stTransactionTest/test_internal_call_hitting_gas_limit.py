"""
Test_internal_call_hitting_gas_limit.

Ported from:
state_tests/stTransactionTest/InternalCallHittingGasLimitFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stTransactionTest/InternalCallHittingGasLimitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_internal_call_hitting_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_internal_call_hitting_gas_limit."""
    coinbase = Address(0x2ADF5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000,
    )

    pre[sender] = Account(balance=0x3B9ACA00)
    # Source: lll
    # { (CALL 5000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x1388,
            address=0x9F499A40CBC961C5230197401CE369D5C53ED896,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xF4240,
        nonce=0,
        address=Address(0xB208128346FE6A0C4EFA386C0C411A56E4557E2A),  # noqa: E501
    )
    # Source: lll
    # {[[1]]55}
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x37) + Op.STOP,
        nonce=0,
        address=Address(0x9F499A40CBC961C5230197401CE369D5C53ED896),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=21100,
        value=10,
    )

    post = {addr: Account(storage={}, balance=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
