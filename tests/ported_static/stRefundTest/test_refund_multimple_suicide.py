"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refund_multimpleSuicideFiller.json
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
    [
        "tests/static/state_tests/stRefundTest/refund_multimpleSuicideFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_multimple_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xC69694690A07D1418B0AADFD424A00EA9F25D84B94FECEF12943DE9CD38EDE14
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x623A7C0)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x40, value=0x60)
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
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    Op.CALLER,
                ),
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
            + Op.MSTORE(
                offset=Op.DUP2, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP2)
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
                    ),
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.JUMP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x8b9574e5049501f581886404adf7037002276e78"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=300000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
