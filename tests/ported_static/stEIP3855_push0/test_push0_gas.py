"""
Test_push0_gas.

Ported from:
state_tests/Shanghai/stEIP3855_push0/push0GasFiller.yml
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
    ["state_tests/Shanghai/stEIP3855_push0/push0GasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_push0_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_push0_gas."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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
    # Source: raw
    # 0x5a6000555f5a6000540360015500
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.PUSH0
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.SLOAD(key=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0xC1ACA9DA71F5EA8DB94B3428D8CBE5D544472FF7),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 0x13496, 1: 22107})}

    state_test(env=env, pre=pre, post=post, tx=tx)
