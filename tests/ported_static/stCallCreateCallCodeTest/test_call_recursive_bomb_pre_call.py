"""
recursive call

Ported from:
state_tests/stCallCreateCallCodeTest/CallRecursiveBombPreCallFiller.json
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
    ["state_tests/stCallCreateCallCodeTest/CallRecursiveBombPreCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """recursive call"""
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
    # { (CALL 100000 0xbad304eb96065b2a98b57a48a06ae28d285a71b5 23 0 0 0 0)  (CALL 0x7ffffffffffffff <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 0 0 0)  }
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x186a0, address=0xbad304eb96065b2a98b57a48a06ae28d285a71b5, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.CALL(gas=0x7ffffffffffffff, address=0x1b3f200856856edc2e98efcd637775c6e341e3c0, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xfffffffffffffffffffffffffffffff,
        nonce=0,
        address=Address("0x55bd941930d381e552d261d75ed997be59e36350"),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (+ (SLOAD 0) 1) [[ 1 ]] (CALL (- (GAS) 224000) (ADDRESS) 0 0 0 0 0) }
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(key=0x1, value=Op.CALL(gas=Op.SUB(Op.GAS, 0x36b00), address=Op.ADDRESS, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x1b3f200856856edc2e98efcd637775c6e341e3c0"),  # noqa: E501
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
        addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={0: 1024, 1: 1}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
