"""
Test_call_recursive_bomb0_oog_at_max_call_depth.

Ported from:
state_tests/stSystemOperationsTest/CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json
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
        "state_tests/stSystemOperationsTest/CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_bomb0_oog_at_max_call_depth(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_recursive_bomb0_oog_at_max_call_depth."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=110000000000,
    )

    # Source: lll
    # { [[ 0 ]] (+ (SLOAD 0) 1) [[ 2 ]] (MUL (DIV @@0 0x0402) 0xfffffffffffffffffff) [[ 1 ]] (CALL (- (GAS) 1024) (ADDRESS) 0 0 (MUL (DIV @@0 0x0402) 0xfffffffffffffffffff) 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x2,
            value=Op.MUL(
                Op.DIV(Op.SLOAD(key=0x0), 0x402), 0xFFFFFFFFFFFFFFFFFFF
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.SUB(Op.GAS, 0x400),
                address=Op.ADDRESS,
                value=0x0,
                args_offset=0x0,
                args_size=Op.MUL(
                    Op.DIV(Op.SLOAD(key=0x0), 0x402), 0xFFFFFFFFFFFFFFFFFFF
                ),
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 749, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
