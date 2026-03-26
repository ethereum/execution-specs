"""
test_ab_acalls0

Ported from:
state_tests/stSystemOperationsTest/ABAcalls0Filler.json
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
    ["state_tests/stSystemOperationsTest/ABAcalls0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ab_acalls0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_ab_acalls0"""
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
        gas_limit=10000000,
    )

    # Source: lll
    # {  [[ (PC) ]] (CALL 100000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 24 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=Op.CALL(gas=0x186a0, address=0x44eb1162303b6a60f2f8882d43d661787b3011e6, value=0x18, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd6cd6ec9adca299f2bbfd754ff8bcf6a4b9aae40"),  # noqa: E501
    )
    # Source: lll
    # { [[ (PC) ]] (ADD 1 (CALL 50000 <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 23 0 0 0 0)) }
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=Op.ADD(0x1, Op.CALL(gas=0xc350, address=0xd6cd6ec9adca299f2bbfd754ff8bcf6a4b9aae40, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)))  # noqa: E501
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0x44eb1162303b6a60f2f8882d43d661787b3011e6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=1000000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={36: 1}),
        addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={38: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
