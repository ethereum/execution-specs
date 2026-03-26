"""
test_static_callcallcodecallcode_011

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_011Filler.json
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
    ["state_tests/stStaticCall/static_callcallcodecallcode_011Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_callcallcodecallcode_011"""
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
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x55730, address=0x2bf6d23c6cdd3a7712ad150dfa2680adabda8b82, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x5cd189bc46453773dd75bda72e7a7eee97d63bce"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (DELEGATECALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 1 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(Op.DELEGATECALL(gas=0x493e0, address=0x86add32e31aa6e47126bc308cf85b29d0c9a4234, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x2bf6d23c6cdd3a7712ad150dfa2680adabda8b82"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 11 1) (DELEGATECALL 250000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 11 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0xb, value=0x1)
        + Op.POP(Op.DELEGATECALL(gas=0x3d090, address=0x2a142c79a9b097c111ce945214226126b75e332c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0xb, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x86add32e31aa6e47126bc308cf85b29d0c9a4234"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x2a142c79a9b097c111ce945214226126b75e332c"),  # noqa: E501
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

    post = {target: Account(storage={0: 1, 1: 1, 3: 0, 4: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
