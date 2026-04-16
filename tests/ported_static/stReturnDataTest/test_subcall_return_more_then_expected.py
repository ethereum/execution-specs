"""
Https://github.com/ethereum/tests/issues/558 (subcall/opcode return...

Ported from:
state_tests/stReturnDataTest/subcallReturnMoreThenExpectedFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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
    """Https://github."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # {
    #   (MSTORE 0  0x1122334455667788991011121314151617181920212223242526272829303132)  # noqa: E501
    #   (MSTORE 32 0x3334353637383940414243444546474849505152535455565758596061626364)  # noqa: E501
    #   (RETURN 0 64)
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x3334353637383940414243444546474849505152535455565758596061626364,  # noqa: E501
        )
        + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA8592F39B32943F9F464090497722B4F9C15F598),  # noqa: E501
    )
    # Source: lll
    # {
    #   (MSTORE 0  0x1122334455667788991011121314151617181920212223242526272829303132)  # noqa: E501
    #   (MSTORE 32 0x3334353637383940414243444546474849505152535455565758596061626364)  # noqa: E501
    #   (REVERT 0 64)
    # }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x3334353637383940414243444546474849505152535455565758596061626364,  # noqa: E501
        )
        + Op.REVERT(offset=0x0, size=0x40)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x028CDAFC3D5D27D006FFB88E1ECF2FA4B412EE4F),  # noqa: E501
    )
    # Source: lll
    # {
    #   ;; Get returndata from a subcall
    #   (CALL 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)  # noqa: E501
    #   [[0]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (DELEGATECALL 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)  # noqa: E501
    #   [[1]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (STATICCALL 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)  # noqa: E501
    #   [[2]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (CALLCODE 200000 <contract:0x194f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)  # noqa: E501
    #   [[3]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #
    #   ;; Get revert data from a subcall
    #   (CALL 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)  # noqa: E501
    #   [[4]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (DELEGATECALL 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)  # noqa: E501
    #   [[5]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (STATICCALL 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 12)  # noqa: E501
    #   [[6]] (MLOAD 0)
    #   (MSTORE 0 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (CALLCODE 200000 <contract:0x294f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 12)  # noqa: E501
    #   [[7]] (MLOAD 0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x30D40,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x30D40,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.STATICCALL(
                gas=0x30D40,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x30D40,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.CALL(
                gas=0x30D40,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x4, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x30D40,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x5, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.STATICCALL(
                gas=0x30D40,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x6, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x30D40,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0xC,
            )
        )
        + Op.SSTORE(key=0x7, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xCA70835D5E9B8C8E139A9693AB05705D291F86BB),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
        value=1,
    )

    post = {
        target: Account(
            storage={
                0: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                1: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                2: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                3: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                4: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                5: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                6: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
                7: 0x1122334455667788991011120000000000000000000000000000000000000000,  # noqa: E501
            },
            balance=0xDE0B6B3A7640001,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
