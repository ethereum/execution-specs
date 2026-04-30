"""
Test_deleagate_call_after_value_transfer.

Ported from:
state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json
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
    [
        "state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_deleagate_call_after_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_deleagate_call_after_value_transfer."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x2386F26FC10000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (SSTORE 0 (CALLVALUE)) (SSTORE 1 (CALLER)) (SSTORE 2 (CALLDATALOAD 0)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x1, value=Op.CALLER)
        + Op.SSTORE(key=0x2, value=Op.CALLDATALOAD(offset=0x0))
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 0 0x01) (DELEGATECALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x1)
        + Op.DELEGATECALL(
            gas=0x186A0,
            address=addr,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x10C8E0,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=453081,
    )

    post = {
        target: Account(storage={0: 0, 1: sender, 2: 1}),
        addr: Account(storage={0: 0, 1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
