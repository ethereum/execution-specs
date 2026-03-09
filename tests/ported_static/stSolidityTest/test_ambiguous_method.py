"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest/AmbiguousMethodFiller.json
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
    ["tests/static/state_tests/stSolidityTest/AmbiguousMethodFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ambiguous_method(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA9AE12CB2700C0214F86B9796881BC03A1FD5605D0E76D2DA2CA592E62D53E52
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
            Op.CALLDATALOAD(offset=0x0)
            + Op.EXP(0x2, 0xE0)
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=0x15, condition=Op.EQ(0xC0406226, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1B]
            + Op.JUMP(pc=0x21)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH2[0x14F]
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x235c9320b0f4d30204334c1ddb008dfe1d75b1b9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x12A05F200)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=300000,
        value=1,
    )

    post = {
        contract: Account(storage={0: 335}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
