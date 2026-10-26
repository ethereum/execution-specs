"""
Test_call_recursive_bomb_pre_call.

Ported from:
state_tests/stDelegatecallTestHomestead/CallRecursiveBombPreCallFiller.json
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

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stDelegatecallTestHomestead/CallRecursiveBombPreCallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_recursive_bomb_pre_call."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    # Source: lll
    # { (CALL 100000 0xbad304eb96065b2a98b57a48a06ae28d285a71b5 23 0 0 0 0)  (DELEGATECALL 0x7ffffffffffffff <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0)  }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x186A0,
                address=0xBAD304EB96065B2A98B57A48A06AE28D285A71B5,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.DELEGATECALL(
            gas=0x7FFFFFFFFFFFFFF,
            address=0x3046257C307A51F1A8AE73F6F6360937DD21138E,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        address=Address(0x7A11B1B8911ECCCFCCB030A17F9CEBDE63A92190),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (+ (SLOAD 0) 1) [[ 1 ]] (CALL (- (GAS) 224000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.SUB(Op.GAS, 0x36B00),
                address=0x3046257C307A51F1A8AE73F6F6360937DD21138E,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        address=Address(0x3046257C307A51F1A8AE73F6F6360937DD21138E),  # noqa: E501
    )

    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=9214364837600034817,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        addr: Account(storage={0: 1023, 1: 1}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
