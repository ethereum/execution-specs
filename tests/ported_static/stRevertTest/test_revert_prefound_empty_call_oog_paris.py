"""
Test_revert_prefound_empty_call_oog_paris.

Ported from:
state_tests/stRevertTest/RevertPrefoundEmptyCallOOG_ParisFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundEmptyCallOOG_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_empty_call_oog_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_prefound_empty_call_oog_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841
    # Source: lll
    # { [[0]] (CALL 50000 <eoa:0x7db299e0885c85039f56fa504a13dd8ce8a56aa7> 0 0 32 0 32) [[1]]12 [[2]]12 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xC350,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=0xC)
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.STOP,
        balance=1,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=63000,
    )

    post = {addr: Account(storage={}, code=b"", balance=10, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
