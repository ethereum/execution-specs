"""
Test_refund_call_a_not_enough_gas_in_call.

Ported from:
state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json
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
    ["state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_call_a_not_enough_gas_in_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_call_a_not_enough_gas_in_call."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0x7C857D62C76CE09F2E8EC3FA9277578C67B69C6547364568FDDB841071E5BD7
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 0 ]] (CALL 5005 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x138D,
                address=0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x8329332CCFB6AE9DF0412E842619FB1C989FBF48),  # noqa: E501
    )
    pre[sender] = Account(balance=0xF4240)
    # Source: lll
    # { [[ 1 ]] 0 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=85000,
        value=10,
    )

    post = {
        target: Account(storage={1: 1}, balance=0xDE0B6B3A764000A),
        coinbase: Account(balance=0),
        sender: Account(balance=0xA8DF4, nonce=1),
        addr: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
