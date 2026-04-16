"""
Test_refund_multimple_suicide.

Ported from:
state_tests/stRefundTest/refund_multimpleSuicideFiller.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stRefundTest/refund_multimpleSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_multimple_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_multimple_suicide."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0x623A7C0)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw
    # 0x606060405260e060020a600035046309e587a58114610031578063c04062261461004d578063dd4f1f2a1461005a575b005b61002f3373ffffffffffffffffffffffffffffffffffffffff16ff5b6100f5600061010961005e565b61002f5b60003090508073ffffffffffffffffffffffffffffffffffffffff166309e587a56040518160e060020a0281526004018090506000604051808303816000876161da5a03f1156100025750604080517f09e587a500000000000000000000000000000000000000000000000000000000815290516004828101926000929190829003018183876161da5a03f1156100025750505050565b604080519115158252519081900360200190f35b5060019056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x40, value=0x60)
        + Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xE0))
        + Op.JUMPI(pc=Op.PUSH2[0x31], condition=Op.EQ(Op.DUP2, 0x9E587A5))
        + Op.JUMPI(pc=Op.PUSH2[0x4D], condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x5A], condition=Op.EQ(0xDD4F1F2A, Op.DUP1))
        + Op.JUMPDEST
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x2F]
        + Op.SELFDESTRUCT(
            address=Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.CALLER
            )
        )
        + Op.JUMPDEST
        + Op.PUSH2[0xF5]
        + Op.PUSH1[0x0]
        + Op.PUSH2[0x109]
        + Op.JUMP(pc=Op.PUSH2[0x5E])
        + Op.JUMPDEST
        + Op.PUSH2[0x2F]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.ADDRESS
        + Op.SWAP1
        + Op.POP
        + Op.AND(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.DUP1)
        + Op.PUSH4[0x9E587A5]
        + Op.MLOAD(offset=0x40)
        + Op.MSTORE(offset=Op.DUP2, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP2))
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
        + Op.POP
        + Op.PUSH1[0x40]
        + Op.MLOAD(offset=Op.DUP1)
        + Op.MSTORE(
            offset=Op.DUP2,
            value=0x9E587A500000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.SWAP1
        + Op.MLOAD
        + Op.PUSH1[0x4]
        + Op.ADD(Op.DUP2, Op.DUP3)
        + Op.SWAP3
        + Op.PUSH1[0x0]
        + Op.SWAP3
        + Op.SWAP2
        + Op.SWAP1
        + Op.DUP3
        + Op.SWAP1
        + Op.SUB
        + Op.ADD
        + Op.DUP2
        + Op.DUP4
        + Op.DUP8
        + Op.SUB(Op.GAS, 0x61DA)
        + Op.JUMPI(pc=Op.PUSH2[0x2], condition=Op.ISZERO(Op.CALL))
        + Op.POP * 4
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x40]
        + Op.MLOAD(offset=Op.DUP1)
        + Op.SWAP2
        + Op.MSTORE(offset=Op.DUP3, value=Op.ISZERO(Op.ISZERO))
        + Op.MLOAD
        + Op.SWAP1
        + Op.DUP2
        + Op.SWAP1
        + Op.ADD(0x20, Op.SUB)
        + Op.SWAP1
        + Op.RETURN
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.JUMP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=300000,
    )

    post = {
        target: Account(balance=0xDE0B6B3A7640000),
        coinbase: Account(balance=0),
        sender: Account(balance=0x61EC43A, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
