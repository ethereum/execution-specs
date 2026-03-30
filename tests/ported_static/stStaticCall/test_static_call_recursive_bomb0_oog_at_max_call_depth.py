"""
Test_static_call_recursive_bomb0_oog_at_max_call_depth.

Ported from:
state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json
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
    [
        "state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb0_oog_at_max_call_depth(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_recursive_bomb0_oog_at_max_call_depth."""
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
        gas_limit=110000000000,
    )

    # Source: lll
    # { (CALLCODE (GAS) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 0) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xBB09BB747BB11897420C59CACB65853142C67BB7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x4A20A569D7008020C8CD630CFF560F3E627522D3),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (+ (SLOAD 0) 1)) (MSTORE 2 (MUL (DIV (MLOAD 0) 0x0402) 0xfffffffffffffffffff)) (STATICCALL (- (GAS) 1024) (ADDRESS) 0 (MUL (DIV (MLOAD 0) 0x0402) 0xfffffffffffffffffff) 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.MSTORE(
            offset=0x2,
            value=Op.MUL(
                Op.DIV(Op.MLOAD(offset=0x0), 0x402), 0xFFFFFFFFFFFFFFFFFFF
            ),
        )
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x400),
            address=Op.ADDRESS,
            args_offset=0x0,
            args_size=Op.MUL(
                Op.DIV(Op.MLOAD(offset=0x0), 0x402), 0xFFFFFFFFFFFFFFFFFFF
            ),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0xBB09BB747BB11897420C59CACB65853142C67BB7),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000000000,
        value=0x186A0,
    )

    post = {target: Account(storage={1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
