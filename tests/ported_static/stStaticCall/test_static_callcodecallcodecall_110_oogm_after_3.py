"""
test_static_callcodecallcodecall_110_oogm_after_3

Ported from:
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_3Filler.json
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
    ["state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcodecall_110_oogm_after_3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_callcodecallcodecall_110_oogm_after_3"""
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
    # {  [[ 0 ]] (CALLCODE 60150 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 )  [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0xeaf6, address=0xdf60cb36bcf8892d8a68903b2d2e455037149e48, value=Op.CALLVALUE, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x81450e6893351d2c0c43648338c0f2ae8d435bc1"),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 40080 <contract:0x1000000000000000000000000000000000000002> (- (CALLVALUE) 1) 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.CALLCODE(gas=0x9c90, address=0xeedcbac77fbd73bf2d0d7fedd710d089b466138d, value=Op.SUB(Op.CALLVALUE, 0x1), args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x42, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x26) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0xdf60cb36bcf8892d8a68903b2d2e455037149e48"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x4e34, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        nonce=0,
        address=Address("0xeedcbac77fbd73bf2d0d7fedd710d089b466138d"),  # noqa: E501
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
        gas_limit=172000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
