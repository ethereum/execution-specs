"""
Test_mem64kb_minus_31.

Ported from:
state_tests/stMemoryTest/mem64kb-31Filler.json
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
    ["state_tests/stMemoryTest/mem64kb-31Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem64kb_minus_31(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mem64kb_minus_31."""
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

    # Source: lll
    # { (MSTORE 63937 42) [[ 1 ]] (MLOAD 63937) [[ 0 ]] (MSIZE) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0xF9C1, value=0x2A)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0xF9C1))
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
        value=10,
    )

    post = {
        target: Account(storage={0: 64000, 1: 42}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
