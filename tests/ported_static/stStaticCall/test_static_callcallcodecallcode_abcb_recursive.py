"""
test_static_callcallcodecallcode_abcb_recursive

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_ABCB_RECURSIVEFiller.json
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
    ["state_tests/stStaticCall/static_callcallcodecallcode_ABCB_RECURSIVEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_callcallcodecallcode_abcb_recursive"""
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
        gas_limit=3000000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x17d7840, address=0x2c81f66472668c71014ce3a9537b033db57af77b, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x0f30355d1f829e0dd67066517a43a738ac501d99"),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 1000000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=0xf4240, address=0xab5c6018cf3368381e283c1de7f906c456188bc3, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x2c81f66472668c71014ce3a9537b033db57af77b"),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=0x7a120, address=0x2c81f66472668c71014ce3a9537b033db57af77b, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xab5c6018cf3368381e283c1de7f906c456188bc3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 0, 2: 0}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
