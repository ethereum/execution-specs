"""
Test_delegatecall_sender_check.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallSenderCheckFiller.json
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
        "state_tests/stDelegatecallTestHomestead/delegatecallSenderCheckFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_sender_check(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_sender_check."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {[[ 1 ]] (CALLER)}
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=Op.CALLER) + Op.STOP,
        balance=23,
        nonce=0,
    )
    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 500000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 64 0 2 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x7A120,
                address=addr,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x2,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {target: Account(storage={0: 1, 1: sender})}

    state_test(env=env, pre=pre, post=post, tx=tx)
