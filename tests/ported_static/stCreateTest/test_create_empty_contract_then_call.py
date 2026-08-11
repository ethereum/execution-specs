"""
Measure a CREATE of an empty contract followed by a CALL, targeting either
the contract just created or an account that does not exist.

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_0weiFiller.json
state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_1weiFiller.json
state_tests/stCreateTest/CREATE_EContract_ThenCALLToNonExistentAccFiller.json

@manually-enhanced: Do not overwrite. The ported absolute GAS snapshots
(slots 0/2/100) are re-expressed as two CodeGasMeasure windows asserted via
the fork's gas model, with the created address and the call's success flag
kept observable inside them; the three fillers, which share one program and
differ only in the call target, are folded into one parametrize.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
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
        "state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_0weiFiller.json",  # noqa: E501
        "state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_1weiFiller.json",  # noqa: E501
        "state_tests/stCreateTest/CREATE_EContract_ThenCALLToNonExistentAccFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "call_target, call_value",
    [
        pytest.param("created", 0, id="0wei"),
        pytest.param("created", 1, id="1wei"),
        # A value-bearing call is not exercised against the absent account:
        # it would create it, which is a different behavior entirely.
        pytest.param("nonexistent", 0, id="non_existent_acc"),
    ],
)
def test_create_empty_contract_then_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_target: str,
    call_value: int,
) -> None:
    """
    Measure a CREATE of an empty contract and the CALL that follows it.

    The created account exists but is empty, so calling it and calling an
    account that never existed both succeed and both leave the callee
    codeless; only the cold-access surcharge separates the two costs.
    """
    calls_created = call_target == "created"

    # CREATE over never-written memory: the all-STOP init code deposits
    # nothing, leaving an empty account with nonce 1. Storing the address
    # keeps it observable, lets the CALL target it at runtime, and folds the
    # store into the measured window (the address is non-zero, so the
    # placeholder new_value only sizes the zero->non-zero transition).
    create_code = Op.CREATE(
        value=0x0,
        offset=0x0,
        size=0x20,
        new_memory_size=0x20,
        init_code_size=0x20,
    )
    store_create = Op.SSTORE(
        ADDRESS_SLOT,
        create_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    absent = None if calls_created else pre.nonexistent_account()
    # CREATE both set the created account's nonce and accessed it, so calling
    # it is a warm call to an account that already exists.
    target: Bytecode | Address = (
        Op.SLOAD(key=ADDRESS_SLOT, key_warm=True) if absent is None else absent
    )

    # Either way the callee runs no code and consumes nothing, so the window
    # measures the CALL itself. Storing the success flag keeps it observable.
    call_code = Op.CALL(
        address=target,
        value=call_value,
        address_warm=calls_created,
        value_transfer=call_value > 0,
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
        ),
        balance=call_value,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    # A value-bearing CALL whose empty callee consumes nothing measures
    # gas_cost minus the stipend (forwarded, then returned unused).
    stipend = fork.gas_costs().CALL_STIPEND if call_value else 0
    created = compute_create_address(address=contract, nonce=1)
    post: dict = {
        contract: Account(
            storage={
                CREATE_GAS_SLOT: store_create.gas_cost(fork),
                ADDRESS_SLOT: created,
                CALL_GAS_SLOT: store_flag.gas_cost(fork) - stipend,
                FLAG_SLOT: 1,
            },
            balance=0,
        ),
        # The transferred value on the 1wei case proves the CALL executed.
        created: Account(
            nonce=1, code=b"", balance=call_value if calls_created else 0
        ),
    }
    if absent is not None:
        # A value-less call neither creates the account nor touches it.
        post[absent] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)
