"""
Test_call_recursive_bomb0.

Ported from:
state_tests/stSystemOperationsTest/CallRecursiveBomb0Filler.json
"""

import pytest
from execution_testing import (
    Account,
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
    ["state_tests/stSystemOperationsTest/CallRecursiveBomb0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_call_recursive_bomb0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_recursive_bomb0."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[ 0 ]] (+ (SLOAD 0) 1) [[ 1 ]] (CALL (- (GAS) 11000) (ADDRESS) 0 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.SUB(Op.GAS, 0x2AF8),
                address=Op.ADDRESS,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  (CALL 100000000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 0 0 0)  }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.CALL(
            gas=0x5F5E100,
            address=addr,
            value=0x17,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x77359400,
    )

    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000000,
        value=0x186A0,
    )

    post = {
        addr: Account(storage={0: 313, 1: 1}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
