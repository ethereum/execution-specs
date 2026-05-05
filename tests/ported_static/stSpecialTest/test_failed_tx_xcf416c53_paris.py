"""
Test_failed_tx_xcf416c53_paris.

Ported from:
state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_failed_tx_xcf416c53_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_failed_tx_xcf416c53_paris."""
    coinbase = Address(0x68795C4AA09D6F4ED3E5DEDDF8C2AD3049A601DA)
    addr = Address(0x0000000000000000000000000000000000000003)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=200000000,
    )

    pre[addr] = Account(balance=10)
    # Source: raw
    # 0x7c0100000000000000000000000000000000000000000000000000000000600035046397dd3054811415610065576004356040526024356060526040516060515b808212156100625760006000600060006000866000f150600182019150610040565b50505b50  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DIV(
            Op.CALLDATALOAD(offset=0x0),
            0x100000000000000000000000000000000000000000000000000000000,
        )
        + Op.JUMPI(
            pc=Op.PUSH2[0x65], condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x97DD3054))
        )
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MLOAD(offset=0x40)
        + Op.MLOAD(offset=0x60)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x62], condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1))
        )
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=Op.DUP7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.ADD(Op.DUP3, 0x1)
        + Op.SWAP2
        + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0x40])
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMPDEST
        + Op.POP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("97dd3054") + Hash(0x0) + Hash(0x2BC),
        gas_limit=16300000,
        nonce=1,
    )

    post = {
        sender: Account(nonce=2),
        addr: Account(balance=10),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
