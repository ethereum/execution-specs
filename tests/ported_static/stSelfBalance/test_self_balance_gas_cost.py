"""
Test_self_balance_gas_cost.

Ported from:
state_tests/stSelfBalance/selfBalanceGasCostFiller.json
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
    ["state_tests/stSelfBalance/selfBalanceGasCostFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_self_balance_gas_cost."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # (asm GAS SELFBALANCE GAS SWAP1 POP SWAP1 SUB 2 SWAP1 SUB 0x01 SSTORE)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.GAS
        + Op.SELFBALANCE
        + Op.GAS
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.SSTORE(key=0x1, value=Op.SUB)
        + Op.STOP,
        nonce=0,
        address=Address(0x20005B9A765D12C8F6AC08C2673B00FA6BE00486),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={1: 5})}

    state_test(env=env, pre=pre, post=post, tx=tx)
