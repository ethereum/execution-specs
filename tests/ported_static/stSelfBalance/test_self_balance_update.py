"""
Test_self_balance_update.

Ported from:
state_tests/stSelfBalance/selfBalanceUpdateFiller.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stSelfBalance/selfBalanceUpdateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance_update(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_self_balance_update."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: lll
    # (asm SELFBALANCE DUP1 1 SSTORE 0 0 0 0 1 0 0 CALL POP SELFBALANCE DUP1 2 SSTORE SWAP1 SUB 3 SSTORE)  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFBALANCE
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x0,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SELFBALANCE
        + Op.SSTORE(key=0x2, value=Op.DUP1)
        + Op.SWAP1
        + Op.SSTORE(key=0x3, value=Op.SUB)
        + Op.STOP,
        balance=500,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
    )

    post = {target: Account(storage={1: 500, 2: 499, 3: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
