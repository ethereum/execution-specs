"""
Test_refund_call_a_oog.

Ported from:
state_tests/stRefundTest/refund_CallA_OOGFiller.json
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
    ["state_tests/stRefundTest/refund_CallA_OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_call_a_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_call_a_oog."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0x27B48AAA30A609C11C7ABA1CB67FC191B5B59F9FF876930F0085D5FAEF4A4824
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
    # { [[ 0 ]] (CALL 6000 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1770,
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
        address=Address(0x1B98D6B82E06B90C71C779925AE5B84E28401256),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2DC6C0)
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
        gas_limit=31069,
        value=10,
    )

    post = {
        target: Account(storage={1: 1}, balance=0xDE0B6B3A7640000),
        coinbase: Account(balance=0),
        sender: Account(balance=0x29091E, nonce=1),
        addr: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
