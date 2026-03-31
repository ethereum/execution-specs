"""
Test_create_contract_sstore_during_init.

Ported from:
state_tests/stCreateTest/CREATE_ContractSSTOREDuringInitFiller.json
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
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CREATE_ContractSSTOREDuringInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_contract_sstore_during_init(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_create_contract_sstore_during_init."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x174876E800)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x0, value=0xFF),
        gas_limit=2150000 if fork >= Amsterdam else 150000,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={0: 255}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
