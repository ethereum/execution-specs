"""
Test_mem64kb_single_byte_minus_33.

Ported from:
state_tests/stMemoryTest/mem64kb_singleByte-33Filler.json
@manually-enhanced: Do not overwrite. tx `gas_limit` bumped on Amsterdam
to cover EIP-8037 state-gas spill; pre-EIP-8037 unchanged.

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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/mem64kb_singleByte-33Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem64kb_single_byte_minus_33(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_mem64kb_single_byte_minus_33."""
    # EIP-8037 state-gas spill on Amsterdam exceeds 100k tx_gas.
    tx_gas_limit = 100000
    if fork.is_eip_enabled(8037):
        tx_gas_limit = 1_000_000

    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x6400000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # { (MSTORE8 63966 42) [[ 0 ]] (MSIZE) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0xF9DE, value=0x2A)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=tx_gas_limit,
        value=10,
    )

    post = {
        target: Account(storage={0: 63968}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
