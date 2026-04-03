"""
Test_mem_return.

Ported from:
state_tests/stMemoryTest/memReturnFiller.json
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
    ["state_tests/stMemoryTest/memReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mem_return."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    # Source: lll
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) (RETURN 0 (MSIZE))  }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.RETURN(offset=0x0, size=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x80349881D6A01127FFE2A32D172EE0599D94C87E),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "ff55883355001144bbccddffeeaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # noqa: E501
        ),
        gas_limit=100000,
        value=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
