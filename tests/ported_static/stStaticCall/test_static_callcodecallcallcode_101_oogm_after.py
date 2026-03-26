"""
test_static_callcodecallcallcode_101_oogm_after

Ported from:
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfterFiller.json
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
    ["state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfterFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_101_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_callcodecallcallcode_101_oogm_after"""
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
    # {  [[ 0 ]] (DELEGATECALL 60150 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0xeaf6, address=0x2865fd3572b0b77173e5ed91e968acad55701151, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xe79aee563c83547f229d955ecdcca0f01fed9aa9"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 40080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x9c90, address=0x2c0bffb833f0bd1bdcb227a4fe215cf640316bb, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x43, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x27) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x2865fd3572b0b77173e5ed91e968acad55701151"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (DELEGATECALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.DELEGATECALL(gas=0x4e34, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x02c0bffb833f0bd1bdcb227a4fe215cf640316bb"),  # noqa: E501
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
