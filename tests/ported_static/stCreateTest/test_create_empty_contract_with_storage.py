"""
Measure CREATE of a codeless-but-storage-writing contract, and optionally
a following CALL to it, via CodeGasMeasure.

The init code writes the created account's own storage and calls a
storage-writer contract, then deposits no code: the result is an "empty"
(codeless) account with storage and nonce 1.

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractWithStorageFiller.json
state_tests/stCreateTest/CREATE_EmptyContractWithStorageAndCallIt_0weiFiller.json
state_tests/stCreateTest/CREATE_EmptyContractWithStorageAndCallIt_1weiFiller.json

@manually-enhanced: Do not overwrite. Three fillers folded into one
parametrize; the init code is composed (not hex blobs) so the measured
CREATE/CALL expectations derive from the same bytecode; the init code's
inner CALL forwards all gas (the ported 0xEA60 budget OOGs under
EIP-8037); the CALL success flag stays inside the measured window.
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
CREATE_GAS_SLOT = 0x2
CALL_FLAG_SLOT = 0x3
CALL_GAS_SLOT = 0x64
STORED_VALUE = 0xC

FORWARDED_GAS = 0xEA60


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EmptyContractWithStorageFiller.json",
        "state_tests/stCreateTest/CREATE_EmptyContractWithStorageAndCallIt_0weiFiller.json",  # noqa: E501
        "state_tests/stCreateTest/CREATE_EmptyContractWithStorageAndCallIt_1weiFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "call_created, call_value",
    [
        pytest.param(False, 0, id="with_storage"),
        pytest.param(True, 0, id="and_call_it_0wei"),
        pytest.param(True, 1, id="and_call_it_1wei"),
    ],
)
def test_create_empty_contract_with_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_created: bool,
    call_value: int,
) -> None:
    """Measure CREATE (and optionally CALL) gas for a storage-only account."""
    # Called by the init code below; writes one cold fresh slot.
    writer_store = Op.SSTORE(
        key=0x1,
        value=STORED_VALUE,
        key_warm=False,
        original_value=0,
        new_value=STORED_VALUE,
    )
    writer = pre.deploy_contract(code=writer_store + Op.STOP)

    # The init code writes the created account's own slot 0 and calls the
    # writer, then runs off its end (STOP) so no code is deposited. The
    # inner CALL forwards all remaining gas (default Op.GAS operand).
    initcode = Op.SSTORE(
        key=0x0,
        value=STORED_VALUE,
        key_warm=False,
        original_value=0,
        new_value=STORED_VALUE,
    ) + Op.CALL(
        address=writer,
        address_warm=False,
        value_transfer=False,
        account_new=False,
    )
    initcode_bytes = bytes(initcode)
    assert len(initcode_bytes) <= 0x40, "init code must fit two MSTORE words"

    # Memory is populated (and expanded to 0x40) before the measured
    # window, so the CREATE itself expands nothing.
    setup = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(
            initcode_bytes[:0x20].ljust(0x20, b"\x00"), "big"
        ),
    ) + Op.MSTORE(
        offset=0x20,
        value=int.from_bytes(
            initcode_bytes[0x20:].ljust(0x20, b"\x00"), "big"
        ),
    )

    create_code = Op.CREATE(
        value=0x0,
        offset=0x0,
        size=len(initcode_bytes),
        new_memory_size=0x40,
        old_memory_size=0x40,
        init_code_size=len(initcode_bytes),
    )
    # The created address is stored inside the measured window (as in the
    # ported filler) so the optional CALL can target it at runtime.
    create_store = Op.SSTORE(
        key=ADDRESS_SLOT,
        value=create_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    # The created account exists (nonce 1) and is warm (CREATE accessed
    # it); the CALL success flag is stored inside the measured window — a
    # wrongly failed call would otherwise be unobservable for the 0wei arm.
    call_code = Op.CALL(
        gas=FORWARDED_GAS,
        address=Op.SLOAD(key=ADDRESS_SLOT, key_warm=True),
        value=call_value,
        address_warm=True,
        value_transfer=call_value > 0,
        account_new=False,
    )
    call_store = Op.SSTORE(
        key=CALL_FLAG_SLOT,
        value=call_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    code = setup + CodeGasMeasure(
        code=create_store,
        extra_stack_items=0,
        sstore_key=CREATE_GAS_SLOT,
    )
    if call_created:
        code += CodeGasMeasure(
            code=call_store,
            extra_stack_items=0,
            sstore_key=CALL_GAS_SLOT,
        )
    contract = pre.deploy_contract(code=code, balance=call_value)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    # The measured CREATE includes the child's work: the init code's own
    # consumption plus the writer's store it calls.
    measured_create = (
        create_store.gas_cost(fork)
        + initcode.gas_cost(fork)
        + writer_store.gas_cost(fork)
    )
    # A value-bearing CALL whose codeless callee consumes nothing measures
    # gas_cost minus the stipend (forwarded then returned unused).
    stipend = fork.gas_costs().CALL_STIPEND if call_value else 0
    measured_call = call_store.gas_cost(fork) - stipend

    created = compute_create_address(address=contract, nonce=1)
    contract_storage: dict = {
        ADDRESS_SLOT: created,
        CREATE_GAS_SLOT: measured_create,
    }
    if call_created:
        contract_storage[CALL_FLAG_SLOT] = 1
        contract_storage[CALL_GAS_SLOT] = measured_call

    post = {
        contract: Account(storage=contract_storage, balance=0),
        # Codeless, but with storage and (for the 1wei arm) the value the
        # measured CALL transferred — proving both the init code and the
        # CALL executed.
        created: Account(
            nonce=1,
            balance=call_value if call_created else 0,
            storage={0: STORED_VALUE},
        ),
        writer: Account(storage={1: STORED_VALUE}),
    }

    state_test(pre=pre, post=post, tx=tx)
