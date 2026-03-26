"""
test_refund_single_suicide

Ported from:
state_tests/stRefundTest/refund_singleSuicideFiller.json
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
    ["state_tests/stRefundTest/refund_singleSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_single_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_refund_single_suicide"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x2b75d0c814eb07c075fccbdd9a036faf651d9c46d7477d6c4f30772cfca90d38
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw
    # 0x606060405260e060020a600035046309e587a58114602e5780632e4699ed146049578063c040622614609b575b005b602c3373ffffffffffffffffffffffffffffffffffffffff16ff5b602c5b60003090508073ffffffffffffffffffffffffffffffffffffffff166309e587a56040518160e060020a0281526004018090506000604051808303816000876161da5a03f11560025750505050565b60a5600060b9604c565b604080519115158252519081900360200190f35b5060019056
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x40, value=0x60)
        + Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xe0))
        + Op.JUMPI(pc=0x2e, condition=Op.EQ(Op.DUP2, 0x9e587a5))
        + Op.JUMPI(pc=0x49, condition=Op.EQ(0x2e4699ed, Op.DUP1))
        + Op.JUMPI(pc=0x9b, condition=Op.EQ(0xc0406226, Op.DUP1)) + Op.JUMPDEST
        + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x2c]
        + Op.SELFDESTRUCT(address=Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.CALLER))
        + Op.JUMPDEST + Op.PUSH1[0x2c] + Op.JUMPDEST + Op.PUSH1[0x0] + Op.ADDRESS
        + Op.SWAP1 + Op.POP
        + Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.DUP1)
        + Op.PUSH4[0x9e587a5] + Op.MLOAD(offset=0x40)
        + Op.MSTORE(offset=Op.DUP2, value=Op.MUL(Op.EXP(0x2, 0xe0), Op.DUP2))
        + Op.PUSH1[0x4] + Op.ADD + Op.DUP1 + Op.SWAP1 + Op.POP
        + Op.JUMPI(pc=0x2, condition=Op.ISZERO(Op.CALL(gas=Op.SUB(Op.GAS, 0x61da), address=Op.DUP8, value=0x0, args_offset=Op.DUP2, args_size=Op.SUB(Op.DUP4, Op.DUP1), ret_offset=Op.MLOAD(offset=0x40), ret_size=0x0)))
        + Op.POP * 4 + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0xa5] + Op.PUSH1[0x0]
        + Op.PUSH1[0xb9] + Op.JUMP(pc=0x4c) + Op.JUMPDEST + Op.PUSH1[0x40]
        + Op.MLOAD(offset=Op.DUP1) + Op.SWAP2
        + Op.MSTORE(offset=Op.DUP3, value=Op.ISZERO(Op.ISZERO)) + Op.MLOAD
        + Op.SWAP1 + Op.DUP2 + Op.SWAP1 + Op.ADD(0x20, Op.SUB) + Op.SWAP1
        + Op.RETURN + Op.JUMPDEST + Op.POP + Op.PUSH1[0x1] + Op.SWAP1 + Op.JUMP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xfc2c9403120f755b844fd30d99c231483e701631"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1c9c380)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("c0406226"),
        gas_limit=300000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(balance=0xde0b6b3a7640000),
        coinbase: Account(balance=0),
        sender: Account(balance=0x1c5af34, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
