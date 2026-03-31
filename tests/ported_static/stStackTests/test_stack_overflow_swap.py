"""
Test_stack_overflow_swap.

Ported from:
state_tests/stStackTests/stackOverflowSWAPFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStackTests/stackOverflowSWAPFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_stack_overflow_swap(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_stack_overflow_swap."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    pre[contract_0] = Account(balance=0xE8D4A5100000000000)
    pre[sender] = Account(balance=0xE8D4A5100000000000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0x0] * 1024 + Op.SWAP1,
        gas_limit=6000000,
        value=1,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(balance=1)
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
