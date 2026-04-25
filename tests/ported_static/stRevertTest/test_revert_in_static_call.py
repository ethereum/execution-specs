"""
Test_revert_in_static_call.

Ported from:
state_tests/stRevertTest/RevertInStaticCallFiller.json
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
    ["state_tests/stRevertTest/RevertInStaticCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_static_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_in_static_call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x5F5E100)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (REVERT 0 0) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT(offset=0x0, size=0x0) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [[ 0 ]] (STATICCALL 50000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 64 0 64 )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xC350,
                address=addr,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=1000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=105044,
    )

    post = {target: Account(storage={})}

    state_test(env=env, pre=pre, post=post, tx=tx)
