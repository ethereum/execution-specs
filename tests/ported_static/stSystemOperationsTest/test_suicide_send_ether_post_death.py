"""
Test_suicide_send_ether_post_death.

Ported from:
state_tests/stSystemOperationsTest/suicideSendEtherPostDeathFiller.json
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
    [
        "state_tests/stSystemOperationsTest/suicideSendEtherPostDeathFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_send_ether_post_death(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_send_ether_post_death."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: hex
    # 0x60606040526000357c01000000000000000000000000000000000000000000000000000000009004806335f46994146100445780634d536fe31461005157610042565b005b61004f600450610072565b005b61005c60045061008d565b6040518082815260200191505060405180910390f35b3073ffffffffffffffffffffffffffffffffffffffff16ff5b565b600060003073ffffffffffffffffffffffffffffffffffffffff166335f46994604051817c01000000000000000000000000000000000000000000000000000000000281526004018090506000604051808303816000876161da5a03f115610002575050503073ffffffffffffffffffffffffffffffffffffffff163190503373ffffffffffffffffffffffffffffffffffffffff16600082604051809050600060405180830381858888f1935050505050809150610147565b509056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x40, value=0x60)
        + Op.CALLDATALOAD(offset=0x0)
        + Op.PUSH29[
            0x100000000000000000000000000000000000000000000000000000000
        ]
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=Op.PUSH2[0x44], condition=Op.EQ(0x35F46994, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x51], condition=Op.EQ(0x4D536FE3, Op.DUP1))
        + Op.JUMP(pc=Op.PUSH2[0x42])
        + Op.JUMPDEST
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x4F]
        + Op.POP(0x4)
        + Op.JUMP(pc=Op.PUSH2[0x72])
        + Op.JUMPDEST
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x5C]
        + Op.POP(0x4)
        + Op.JUMP(pc=Op.PUSH2[0x8D])
        + Op.JUMPDEST
        + Op.MLOAD(offset=0x40)
        + Op.DUP1
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.SWAP2
        + Op.POP * 2
        + Op.MLOAD(offset=0x40)
        + Op.DUP1
        + Op.SWAP2
        + Op.SUB
        + Op.SWAP1
        + Op.RETURN
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(
            address=Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.ADDRESS
            )
        )
        + Op.JUMPDEST
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0] * 2
        + Op.AND(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.ADDRESS)
        + Op.PUSH4[0x35F46994]
        + Op.MLOAD(offset=0x40)
        + Op.MSTORE(
            offset=Op.DUP2,
            value=Op.MUL(
                0x100000000000000000000000000000000000000000000000000000000,
                Op.DUP2,
            ),
        )
        + Op.PUSH1[0x4]
        + Op.ADD
        + Op.DUP1
        + Op.SWAP1
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0x2],
            condition=Op.ISZERO(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x61DA),
                    address=Op.DUP8,
                    value=0x0,
                    args_offset=Op.DUP2,
                    args_size=Op.SUB(Op.DUP4, Op.DUP1),
                    ret_offset=Op.MLOAD(offset=0x40),
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP * 3
        + Op.BALANCE(
            address=Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.ADDRESS
            )
        )
        + Op.SWAP1
        + Op.POP
        + Op.AND(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.CALLER)
        + Op.PUSH1[0x0]
        + Op.DUP3
        + Op.MLOAD(offset=0x40)
        + Op.DUP1
        + Op.SWAP1
        + Op.POP
        + Op.CALL(
            gas=Op.DUP9,
            address=Op.DUP9,
            value=Op.DUP6,
            args_offset=Op.DUP2,
            args_size=Op.SUB(Op.DUP4, Op.DUP1),
            ret_offset=Op.MLOAD(offset=0x40),
            ret_size=0x0,
        )
        + Op.SWAP4
        + Op.POP * 5
        + Op.DUP1
        + Op.SWAP2
        + Op.POP
        + Op.JUMP(pc=0x147)
        + Op.JUMPDEST
        + Op.POP
        + Op.SWAP1
        + Op.JUMP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA997455DCA526734F5607F7C452DE0CFB9AF19F4),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("4d536fe3"),
        gas_limit=3000000,
        value=0x186A0,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(
            storage={},
            code=bytes.fromhex(
                "60606040526000357c01000000000000000000000000000000000000000000000000000000009004806335f46994146100445780634d536fe31461005157610042565b005b61004f600450610072565b005b61005c60045061008d565b6040518082815260200191505060405180910390f35b3073ffffffffffffffffffffffffffffffffffffffff16ff5b565b600060003073ffffffffffffffffffffffffffffffffffffffff166335f46994604051817c01000000000000000000000000000000000000000000000000000000000281526004018090506000604051808303816000876161da5a03f115610002575050503073ffffffffffffffffffffffffffffffffffffffff163190503373ffffffffffffffffffffffffffffffffffffffff16600082604051809050600060405180830381858888f1935050505050809150610147565b509056"  # noqa: E501
            ),
            balance=0,
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
