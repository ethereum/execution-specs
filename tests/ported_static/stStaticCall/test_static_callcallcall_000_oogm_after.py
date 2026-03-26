"""
test_static_callcallcall_000_oogm_after

Ported from:
state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json
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
    ["state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcall_000_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_callcallcall_000_oogm_after"""
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
    # {  [[ 0 ]] (STATICCALL 600150 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 111 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x92856, address=0x8ff16542095de9f85f7c395d6d543d19b30d97d7, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x6f, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x03681c634a188409b5f9b8ca2382c1a1499d8a0d"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 400080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (SSTORE 3 1)}
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x61ad0, address=0xc2234f6b4a777db8df1447c9c2d0c8cee376de76, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x8ff16542095de9f85f7c395d6d543d19b30d97d7"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x1d4d4, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc2234f6b4a777db8df1447c9c2d0c8cee376de76"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=1720000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 0, 1: 0, 2: 0, 3: 0, 111: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={2: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000003: Account(storage={3: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
