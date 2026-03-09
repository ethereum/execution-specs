"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSpecialTest/JUMPDEST_AttackwithJumpFiller.json
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
        "tests/static/state_tests/stSpecialTest/JUMPDEST_AttackwithJumpFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_jumpdest_attackwith_jump(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.JUMP(pc=0x3)
            + Op.JUMPDEST
            + Op.CALL(
                gas=Op.SUB(Op.GAS, 0xC350),
                address=Op.ADDRESS,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.JUMPDEST * 15000
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x3f9d62603c0d43765c8bc6ef623e68a4fc7d78eb"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
