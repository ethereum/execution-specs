"""
Test_internal_call_hitting_gas_limit2.

Ported from:
state_tests/stTransactionTest/InternalCallHittingGasLimit2Filler.json
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
    ["state_tests/stTransactionTest/InternalCallHittingGasLimit2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_internal_call_hitting_gas_limit2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_internal_call_hitting_gas_limit2."""
    coinbase = Address(0x2ADF5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47766,
    )

    # Source: lll
    # {[[1]]55}
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x37) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (CALL 25000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x61A8,
            address=addr,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=47766,
        value=10,
    )

    post = {addr: Account(storage={}, balance=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
