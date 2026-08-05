"""
Verify a CREATE of an empty contract followed by a CALL to a non-existent
account: both operations are gas-measured, the created address and the
call's success flag are stored, and the absent callee stays non-existent.

Ported from:
state_tests/stCreateTest/CREATE_EContract_ThenCALLToNonExistentAccFiller.json

@manually-enhanced: Do not overwrite. The ported absolute GAS snapshots
(slots 0/2/100) are re-expressed as two CodeGasMeasure windows asserted
via the fork's gas model, the created address and call flag stay in the
measured windows' SSTOREs, and the callee is a dynamic non-existent
account called with all gas forwarded.
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

CREATE_GAS_SLOT = 0x0
ADDRESS_SLOT = 0x1
CALL_GAS_SLOT = 0x2
FLAG_SLOT = 0x3


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EContract_ThenCALLToNonExistentAccFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_create_e_contract_then_call_to_non_existent_acc(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure a CREATE of an empty contract and a call to no account."""
    absent = pre.nonexistent_account()

    # CREATE over never-written memory: the all-STOP init code deposits
    # nothing, leaving an empty account with nonce 1.
    create_code = Op.CREATE(
        value=0x0,
        offset=0x0,
        size=0x20,
        new_memory_size=0x20,
        init_code_size=0x20,
    )
    # Storing the created address keeps it observable and folds the
    # store into the measured window (the address is non-zero, so the
    # placeholder new_value only sizes the zero->non-zero transition).
    store_create = Op.SSTORE(
        ADDRESS_SLOT,
        create_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    # A value-less call to an absent account creates nothing on any
    # fork; the callee consumes no gas, so the window measures only the
    # cold CALL itself. Storing the success flag keeps it observable.
    call_code = Op.CALL(
        address=absent,
        address_warm=False,
        value_transfer=False,
        account_new=False,
    )
    store_flag = Op.SSTORE(
        FLAG_SLOT,
        call_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=store_create,
            sstore_key=CREATE_GAS_SLOT,
        )
        + CodeGasMeasure(
            code=store_flag,
            sstore_key=CALL_GAS_SLOT,
        )
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    post = {
        contract: Account(
            storage={
                CREATE_GAS_SLOT: store_create.gas_cost(fork),
                ADDRESS_SLOT: compute_create_address(
                    address=contract, nonce=1
                ),
                CALL_GAS_SLOT: store_flag.gas_cost(fork),
                FLAG_SLOT: 1,
            },
        ),
        compute_create_address(address=contract, nonce=1): Account(
            nonce=1, code=b"", balance=0
        ),
        absent: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
