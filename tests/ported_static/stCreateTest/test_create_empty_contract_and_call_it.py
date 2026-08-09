"""
Test CREATE of an empty contract followed by a CALL to it, measuring the
CALL gas cost.

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_0weiFiller.json
state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_1weiFiller.json

@manually-enhanced: Do not overwrite. CALL gas via CodeGasMeasure; dynamic
address (runtime SLOAD); 0wei/1wei folded into one parametrize.
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

ADDRESS_SLOT = 0x1
GAS_SLOT = 0x64

FORWARDED_GAS = 0xEA60


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_0weiFiller.json",  # noqa: E501
        "state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_1weiFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "call_value",
    [
        pytest.param(0, id="0wei"),
        pytest.param(1, id="1wei"),
    ],
)
def test_create_empty_contract_and_call_it(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_value: int,
) -> None:
    """CREATE an empty contract, then CALL it and measure the CALL gas."""
    # CREATE over never-written memory deposits no code -> an empty account
    # with nonce 1. Its address is stored so the CALL can target it at
    # runtime (it is not known when the caller code is assembled).
    create_code = Op.CREATE(
        value=0x0,
        offset=0x0,
        size=0x20,
        new_memory_size=0x20,
        init_code_size=0x20,
    )
    # The created account already exists (CREATE set its nonce) and is warm
    # (CREATE accessed it), so the CALL is a warm call to an existing account.
    call_code = Op.CALL(
        gas=FORWARDED_GAS,
        address=Op.SLOAD(key=ADDRESS_SLOT, key_warm=True),
        value=call_value,
        args_offset=0x0,
        args_size=0x0,
        ret_offset=0x0,
        ret_size=0x0,
        address_warm=True,
        value_transfer=call_value > 0,
        account_new=False,
    )
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=ADDRESS_SLOT, value=create_code)
        + CodeGasMeasure(
            code=call_code,
            extra_stack_items=1,
            sstore_key=GAS_SLOT,
        ),
        balance=call_value,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    # A value-bearing CALL whose empty callee consumes nothing measures
    # gas_cost minus the stipend (forwarded then returned unused).
    stipend = fork.gas_costs().CALL_STIPEND if call_value else 0
    created = compute_create_address(address=contract, nonce=1)
    post = {
        contract: Account(
            storage={
                ADDRESS_SLOT: created,
                GAS_SLOT: call_code.gas_cost(fork) - stipend,
            },
            balance=0,
        ),
        # The transferred value on the 1wei case proves the CALL executed.
        created: Account(nonce=1, balance=call_value),
    }

    state_test(pre=pre, post=post, tx=tx)
