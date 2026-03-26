"""
test_refund_call_a_not_enough_gas_in_call

Ported from:
state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    """test_refund_call_a_not_enough_gas_in_call"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x7c857d62c76ce09f2e8ec3fa9277578c67b69c6547364568fddb841071e5bd7
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 0 ]] (CALL 5005 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x138d, address=0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x8329332ccfb6ae9df0412e842619fb1c989fbf48"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xf4240)
    # Source: lll
    # { [[ 1 ]] 0 }
    addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=85000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={1: 1}, balance=0xde0b6b3a764000a),
        coinbase: Account(balance=0),
        sender: Account(balance=0xa8df4, nonce=1),
        addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
