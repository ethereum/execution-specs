"""
test_static_call_recursive_bomb_pre_call

Ported from:
state_tests/stStaticCall/static_CallRecursiveBombPreCallFiller.json
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
    ["state_tests/stStaticCall/static_CallRecursiveBombPreCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_recursive_bomb_pre_call"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x77f65b71f1f16a75476f469f7106d1b60bfec266ae25b8da16a9091d223aa24a
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: lll
    # { (STATICCALL 100000 0xbad304eb96065b2a98b57a48a06ae28d285a71b5 0 0 0 0) [[ 0 ]] (DELEGATECALL 0x7ffffffffffffff <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0x186a0, address=0xbad304eb96065b2a98b57a48a06ae28d285a71b5, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x72e480206054168cfa7d5c6a1bd8c3ffe26a4d82, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xfffffffffffffffffffffffffffffff,
        nonce=0,
        address=Address("0x6a441a35b94353a66ffd7fd1e54550acecb81aaf"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (+ (MLOAD 0) 1)) (STATICCALL (- (GAS) 224000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.STATICCALL(gas=Op.SUB(Op.GAS, 0x36b00), address=0x72e480206054168cfa7d5c6a1bd8c3ffe26a4d82, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x72e480206054168cfa7d5c6a1bd8c3ffe26a4d82"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffff)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=9214364837600034817,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
