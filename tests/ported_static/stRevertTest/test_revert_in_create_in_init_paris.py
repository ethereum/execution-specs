"""
Test_revert_in_create_in_init_paris.

Ported from:
state_tests/stRevertTest/RevertInCreateInInit_ParisFiller.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stRevertTest/RevertInCreateInInit_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_create_in_init_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_in_create_in_init_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x6400000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.POP(Op.ADDRESS)
        + Op.PUSH1[0xD]
        + Op.CODECOPY(dest_offset=0x0, offset=0x24, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
        gas_limit=200000,
    )

    post = {addr: Account(storage={0: 1}, balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
