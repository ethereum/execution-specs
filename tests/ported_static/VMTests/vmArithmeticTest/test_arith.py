"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/arithFiller.yml
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
    ["tests/static/state_tests/VMTests/vmArithmeticTest/arithFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_arith(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x1]
            + Op.PUSH1[0x1]
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
            + Op.RETURN(offset=0x0, size=0x8)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x14814d06e93efb1102a15d5881432c9ff6c91362"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=16777216,
        value=1,
    )

    post = {
        contract: Account(storage={0: 0x1B9C636491}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
