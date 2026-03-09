"""
Test ported from static filler.

Ported from:
tests/static/state_tests/Shanghai/stEIP3855_push0/push0GasFiller.yml
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
    ["tests/static/state_tests/Shanghai/stEIP3855_push0/push0GasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_push0_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDC4EFA209AECDD4C2D5201A419EA27506151B4EC687F14A613229E310932491B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x989680)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.GAS)
            + Op.PUSH0
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.SLOAD(key=0x0), Op.GAS))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc1aca9da71f5ea8db94b3428d8cbe5d544472ff7"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={0: 0x13496, 1: 22107}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
