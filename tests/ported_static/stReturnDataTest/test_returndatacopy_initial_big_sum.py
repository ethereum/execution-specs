"""
Test_returndatacopy_initial_big_sum.

Ported from:
state_tests/stReturnDataTest/returndatacopy_initial_big_sumFiller.json
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
    ["state_tests/stReturnDataTest/returndatacopy_initial_big_sumFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_initial_big_sum(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_initial_big_sum."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x6400000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: lll
    # { (MSTORE 0 0x112233445566778899aabbccddeeff) (RETURNDATACOPY 0 (EXP 2 63) (EXP 2 63)) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x112233445566778899AABBCCDDEEFF)
        + Op.RETURNDATACOPY(
            dest_offset=0x0, offset=Op.EXP(0x2, 0x3F), size=Op.EXP(0x2, 0x3F)
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
