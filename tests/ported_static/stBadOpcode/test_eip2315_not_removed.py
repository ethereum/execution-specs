"""
Test_eip2315_not_removed.

Ported from:
state_tests/stBadOpcode/eip2315NotRemovedFiller.json
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
    ["state_tests/stBadOpcode/eip2315NotRemovedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_eip2315_not_removed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_eip2315_not_removed."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x7FFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x60045e005c60016000555d
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x4]
        + Op.MCOPY
        + Op.STOP
        + Op.TLOAD
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.TSTORE,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
    )

    post = {target: Account(storage={})}

    state_test(env=env, pre=pre, post=post, tx=tx)
