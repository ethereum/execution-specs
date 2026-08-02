"""
Test CREATE of an empty contract and measure the CREATE gas cost.

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractFiller.json
state_tests/stCreateTest/CREATE_EmptyContractWithBalanceFiller.json

@manually-enhanced: Do not overwrite. CREATE gas via CodeGasMeasure; dynamic
address + fork-derived cost; empty/with-balance folded into one parametrize.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_SLOT = 0x64


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EmptyContractFiller.json",
        "state_tests/stCreateTest/CREATE_EmptyContractWithBalanceFiller.json",
    ],
)
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.parametrize(
    "create_value",
    [
        pytest.param(0, id="empty_contract"),
        pytest.param(1, id="with_balance"),
    ],
)
def test_create_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_value: int,
) -> None:
    """CREATE an empty contract (empty init code) and measure its gas."""
    # CREATE with size=0x20 over never-written memory runs 32 zero bytes as
    # init code (STOP on the first byte), depositing no code -> an empty
    # account with nonce 1 (and the transferred value as balance).
    create_code = Op.CREATE(
        value=create_value,
        offset=0x0,
        size=0x20,
        new_memory_size=0x20,
        init_code_size=0x20,
    )
    contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=create_code,
            extra_stack_items=1,
            sstore_key=GAS_SLOT,
        ),
        balance=create_value,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    created = compute_create_address(address=contract, nonce=1)
    post = {
        contract: Account(
            storage={GAS_SLOT: create_code.gas_cost(fork)}, balance=0
        ),
        created: Account(nonce=1, balance=create_value),
    }

    state_test(pre=pre, post=post, tx=tx)
