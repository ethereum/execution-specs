"""
test_static_call_recursive_bomb0_oog_at_max_call_depth

Ported from:
state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json
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
    ["state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb0_oog_at_max_call_depth(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_recursive_bomb0_oog_at_max_call_depth"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=110000000000,
    )

    # Source: lll
    # { (CALLCODE (GAS) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.POP(Op.CALLCODE(gas=Op.GAS, address=0xbb09bb747bb11897420c59cacb65853142c67bb7, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x1312d00,
        nonce=0,
        address=Address("0x4a20a569d7008020c8cd630cff560f3e627522d3"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (+ (SLOAD 0) 1)) (MSTORE 2 (MUL (DIV (MLOAD 0) 0x0402) 0xfffffffffffffffffff)) (STATICCALL (- (GAS) 1024) (ADDRESS) 0 (MUL (DIV (MLOAD 0) 0x0402) 0xfffffffffffffffffff) 0 0) }
    addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.MSTORE(offset=0x2, value=Op.MUL(Op.DIV(Op.MLOAD(offset=0x0), 0x402), 0xfffffffffffffffffff))
        + Op.STATICCALL(gas=Op.SUB(Op.GAS, 0x400), address=Op.ADDRESS, args_offset=0x0, args_size=Op.MUL(Op.DIV(Op.MLOAD(offset=0x0), 0x402), 0xfffffffffffffffffff), ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0x1312d00,
        nonce=0,
        address=Address("0xbb09bb747bb11897420c59cacb65853142c67bb7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=100000000000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
