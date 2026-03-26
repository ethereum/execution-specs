"""
test_static_call_to_return1

Ported from:
state_tests/stStaticCall/static_CallToReturn1Filler.json
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
    ["state_tests/stStaticCall/static_CallToReturn1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_to_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_to_return1"""
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
    # { [[ 0 ]] (STATICCALL 1000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 31 1) [[ 1 ]] @0 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x3e8, address=0xd0a322c1ea1978a5d1edb863e5a6c9027039bf6c, args_offset=0x0, args_size=0x0, ret_offset=0x1f, ret_size=0x1))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x60f1c8af50c827c6787a7bc5249e9bdde475a4ba"),  # noqa: E501
    )
    # Source: raw
    # 0x602a601f536001601ff3
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x1f, value=0x2a) + Op.RETURN(offset=0x1f, size=0x1),
        balance=23,
        nonce=0,
        address=Address("0xd0a322c1ea1978a5d1edb863e5a6c9027039bf6c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=300000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1, 1: 42}, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
