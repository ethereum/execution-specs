"""
Test_delegatecall_before_transition.

Ported from:
state_tests/stTransitionTest/delegatecallBeforeTransitionFiller.json
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
    ["state_tests/stTransitionTest/delegatecallBeforeTransitionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_before_transition(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_before_transition."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 500000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 64 0 2 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x7A120,
                address=0xD3F6E432D6891A965FC56D39E729652A0762A,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x2,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x55BB8A8658B848EBBBB73CBF6AC9D59D715AEC58),  # noqa: E501
    )
    # Source: lll
    # {[[ 1 ]] (CALLER) [[ 2 ]] (CALLVALUE) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=Op.CALLER)
        + Op.SSTORE(key=0x2, value=Op.CALLVALUE)
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x000D3F6E432D6891A965FC56D39E729652A0762A),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(
            storage={
                0: 1,
                1: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
