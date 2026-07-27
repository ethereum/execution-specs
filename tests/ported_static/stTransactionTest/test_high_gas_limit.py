"""
Test_high_gas_limit.

Ported from:
state_tests/stTransactionTest/HighGasLimitFiller.json

@manually-enhanced: Do not overwrite. The tx sends value to an empty
recipient, so EIP-2780 charges ``NEW_ACCOUNT`` state gas at the top
frame; with the default zero state-gas reservoir that charge spills into
regular gas. Instead of the original hardcoded ``gas_limit``, lift the
100000 base by ``fork.transaction_top_frame_state_gas`` so the budget
covers the spillover and stays exactly 0 on pre-EIP-2780 forks.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    RecipientType,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/HighGasLimitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_high_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_high_gas_limit."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=2**128 - 1)

    # EIP-2780 charges ``NEW_ACCOUNT`` state gas at the top frame when
    # value is sent to an empty recipient; with the default zero
    # state-gas reservoir that charge spills into regular gas, so lift
    # ``gas_limit`` by exactly that amount (0 on pre-EIP-2780 forks).
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    tx = Transaction(
        sender=sender,
        to=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        data=Bytes("3240349548983454"),
        gas_limit=100000 + top_frame_state_gas,
        value=900,
    )

    post = {
        sender: Account(nonce=1),
        Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B): Account(
            balance=900
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
