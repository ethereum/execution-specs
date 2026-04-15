"""
Test_create_empty_contract_with_balance.

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractWithBalanceFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CREATE_EmptyContractWithBalanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_empty_contract_with_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_empty_contract_with_balance."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { [[0]](GAS) [[1]] (CREATE 1 0 32) [[100]] (GAS) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x1, offset=0x0, size=0x20))
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
        balance=1,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0x8D5B6,
                1: compute_create_address(address=contract_0, nonce=0),
                100: 0x7ABF8,
            },
        ),
        compute_create_address(address=contract_0, nonce=0): Account(
            balance=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
