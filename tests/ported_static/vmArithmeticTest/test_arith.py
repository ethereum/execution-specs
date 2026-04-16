"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/arithFiller.yml
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
    ["state_tests/VMTests/vmArithmeticTest/arithFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_arith(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: raw
    # 0x600160019001600702600501600290046004906021900560170160030260059007600303600960110A60005560086000F3  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1] * 2
        + Op.SWAP1
        + Op.ADD(0x5, Op.MUL(0x7, Op.ADD))
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.DIV
        + Op.PUSH1[0x4]
        + Op.SWAP1
        + Op.PUSH1[0x21]
        + Op.SWAP1
        + Op.MUL(0x3, Op.ADD(0x17, Op.SDIV))
        + Op.PUSH1[0x5]
        + Op.SWAP1
        + Op.SUB(0x3, Op.SMOD)
        + Op.SSTORE(key=0x0, value=Op.EXP(0x11, 0x9))
        + Op.RETURN(offset=0x0, size=0x8),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x14814D06E93EFB1102A15D5881432C9FF6C91362),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=16777216,
        value=1,
    )

    post = {target: Account(storage={0: 0x1B9C636491})}

    state_test(env=env, pre=pre, post=post, tx=tx)
