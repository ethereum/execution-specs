"""
test_static_callcallcodecall_010_suicide_end

Ported from:
state_tests/stStaticCall/static_callcallcodecall_010_SuicideEndFiller.json
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
    ["state_tests/stStaticCall/static_callcallcodecall_010_SuicideEndFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecall_010_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_callcallcodecall_010_suicide_end"""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x249f0, address=0x92d7028788caa240253b7b2a92386464690cdc72, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x569cdc3b32cc3f9747bbde39fd70fead591d2f0d"),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=0x186a0, address=0xb7770360e0b87603e3d9c87c866451760c95abca, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x92d7028788caa240253b7b2a92386464690cdc72"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (SELFDESTRUCT <contract:0x1000000000000000000000000000000000000001>) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0xc350, address=0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.SELFDESTRUCT(address=0x92d7028788caa240253b7b2a92386464690cdc72)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xb7770360e0b87603e3d9c87c866451760c95abca"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=3000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1, 3: 0}),
        addr_0x1000000000000000000000000000000000000001: Account(balance=0x2540be400),
        addr_0x1000000000000000000000000000000000000003: Account(storage={3: 0}),
        sender: Account(storage={1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
