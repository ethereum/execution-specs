"""
https://github.com/ethereum/tests/issues/558 (subcall/opcode return more data then expected)

Ported from:
state_tests/stReturnDataTest/subcallReturnMoreThenExpectedFiller.yml
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
    ["state_tests/stReturnDataTest/subcallReturnMoreThenExpectedFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_subcall_return_more_then_expected(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """https://github."""
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
    # {
    #   ;; Get returndata from a subcall
    #   (CALL 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)
    #   [[0]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    #   (DELEGATECALL 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)
    #   [[1]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    #   (STATICCALL 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)
    #   [[2]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    #   (CALLCODE 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)
    #   [[3]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    # 
    #   ;; Get revert data from a subcall
    #   (CALL 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)
    #   [[4]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    #   (DELEGATECALL 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)
    #   [[5]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    #   (STATICCALL 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)
    #   [[6]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)
    #   (CALLCODE 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)
    #   [[7]] (MLOAD 0)
    # }
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x30d40, address=0xa8592f39b32943f9f464090497722b4f9c15f598, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.DELEGATECALL(gas=0x30d40, address=0xa8592f39b32943f9f464090497722b4f9c15f598, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.STATICCALL(gas=0x30d40, address=0xa8592f39b32943f9f464090497722b4f9c15f598, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.CALLCODE(gas=0x30d40, address=0xa8592f39b32943f9f464090497722b4f9c15f598, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.CALL(gas=0x30d40, address=0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x4, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.DELEGATECALL(gas=0x30d40, address=0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x5, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.STATICCALL(gas=0x30d40, address=0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x6, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(Op.CALLCODE(gas=0x30d40, address=0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xc))
        + Op.SSTORE(key=0x7, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xca70835d5e9b8c8e139a9693ab05705d291f86bb"),  # noqa: E501
    )
    # Source: lll
    # {
    #   (MSTORE 0  0x1122334455667788991011121314151617181920212223242526272829303132)
    #   (MSTORE 32 0x3334353637383940414243444546474849505152535455565758596061626364)
    #   (RETURN 0 64)
    # }
    addr_0x194f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1122334455667788991011121314151617181920212223242526272829303132)
        + Op.MSTORE(offset=0x20, value=0x3334353637383940414243444546474849505152535455565758596061626364)
        + Op.RETURN(offset=0x0, size=0x40) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa8592f39b32943f9f464090497722b4f9c15f598"),  # noqa: E501
    )
    # Source: lll
    # {
    #   (MSTORE 0  0x1122334455667788991011121314151617181920212223242526272829303132)
    #   (MSTORE 32 0x3334353637383940414243444546474849505152535455565758596061626364)
    #   (REVERT 0 64)
    # }
    addr_0x294f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1122334455667788991011121314151617181920212223242526272829303132)
        + Op.MSTORE(offset=0x20, value=0x3334353637383940414243444546474849505152535455565758596061626364)
        + Op.REVERT(offset=0x0, size=0x40) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x028cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=400000,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0x1122334455667788991011120000000000000000000000000000000000000000,
            1: 0x1122334455667788991011120000000000000000000000000000000000000000,
            2: 0x1122334455667788991011120000000000000000000000000000000000000000,
            3: 0x1122334455667788991011120000000000000000000000000000000000000000,
            4: 0x1122334455667788991011120000000000000000000000000000000000000000,
            5: 0x1122334455667788991011120000000000000000000000000000000000000000,
            6: 0x1122334455667788991011120000000000000000000000000000000000000000,
            7: 0x1122334455667788991011120000000000000000000000000000000000000000,
        },
                balance=0xde0b6b3a7640001,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
