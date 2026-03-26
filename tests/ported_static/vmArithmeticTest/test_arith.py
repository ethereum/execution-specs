"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/arithFiller.yml
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
    ["state_tests/VMTests/vmArithmeticTest/arithFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_arith(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x600160019001600702600501600290046004906021900560170160030260059007600303600960110A60005560086000F3
    target = pre.deploy_contract(
        code=Op.PUSH1[0x1] * 2 + Op.SWAP1 + Op.ADD(0x5, Op.MUL(0x7, Op.ADD))
        + Op.PUSH1[0x2] + Op.SWAP1 + Op.DIV + Op.PUSH1[0x4] + Op.SWAP1
        + Op.PUSH1[0x21] + Op.SWAP1 + Op.MUL(0x3, Op.ADD(0x17, Op.SDIV))
        + Op.PUSH1[0x5] + Op.SWAP1 + Op.SUB(0x3, Op.SMOD)
        + Op.SSTORE(key=0x0, value=Op.EXP(0x11, 0x9))
        + Op.RETURN(offset=0x0, size=0x8),
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x14814d06e93efb1102a15d5881432c9ff6c91362"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=16777216,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0x1b9c636491})}

    state_test(env=env, pre=pre, post=post, tx=tx)
