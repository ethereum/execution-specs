"""
Measure CREATE of a codeless contract (optionally writing storage in its
init code) followed by a STATICCALL to it, via CodeGasMeasure.

Ported from:
state_tests/stStaticCall/static_CREATE_EmptyContractAndCallIt_0weiFiller.json
state_tests/stStaticCall/static_CREATE_EmptyContractWithStorageAndCallIt_0weiFiller.json

@manually-enhanced: Do not overwrite. Two fillers folded into one
parametrize; the storage-writing init code is composed (not hex blobs) so
the measured CREATE/STATICCALL expectations derive from the same bytecode;
the init code's inner CALL forwards all gas (the ported 0xEA60 budget OOGs
under EIP-8037); the STATICCALL success flag stays inside the measured
window. Replaces the prior EIP-8037 expect-any band-aid with fork-derived
gas assertions.
"""

import pytest
from execution_testing import (
    Account,
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

ADDRESS_SLOT = 0x1
CREATE_GAS_SLOT = 0x2
STATICCALL_FLAG_SLOT = 0x3
STATICCALL_GAS_SLOT = 0x64
STORED_VALUE = 0xC

FORWARDED_GAS = 0xEA60


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CREATE_EmptyContractAndCallIt_0weiFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_CREATE_EmptyContractWithStorageAndCallIt_0weiFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "with_storage",
    [
        pytest.param(False, id="empty_contract"),
        pytest.param(True, id="with_storage"),
    ],
)
def test_static_create_empty_contract_and_call_it_0wei(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    with_storage: bool,
) -> None:
    """Measure CREATE and STATICCALL gas for a created codeless account."""
    if with_storage:
        # Called by the init code below; writes one cold fresh slot.
        writer_store = Op.SSTORE(
            key=0x1,
            value=STORED_VALUE,
            key_warm=False,
            original_value=0,
            new_value=STORED_VALUE,
        )
        writer = pre.deploy_contract(code=writer_store + Op.STOP)

        # The init code writes the created account's own slot 0 and calls
        # the writer, then runs off its end (STOP) so no code is deposited.
        # The inner CALL forwards all remaining gas (default Op.GAS).
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
        assert len(initcode) <= 0x40, "init code must fit two words"

        # Memory is populated (and expanded to 0x40) before the measured
        # window, so the CREATE itself expands nothing.
        setup = Op.MSTORE(
            offset=0x0,
            value=initcode_bytes[:0x20],
        ) + Op.MSTORE(
            offset=0x20,
            value=initcode_bytes[0x20:].ljust(0x20, b"\x00"),
        )
        create_code = Op.CREATE(
            value=0x0,
            offset=0x0,
            size=len(initcode),
            new_memory_size=0x40,
            old_memory_size=0x40,
            init_code_size=len(initcode),
        )
        # The measured CREATE includes the child's work: the init code's
        # own consumption plus the writer's store it calls.
        child_cost = initcode.gas_cost(fork) + writer_store.gas_cost(fork)
    else:
        # CREATE over never-written memory runs 32 zero bytes as init code
        # (STOP on the first byte), depositing no code and consuming
        # nothing; the memory expansion happens inside the window.
        setup = Bytecode()
        create_code = Op.CREATE(
            value=0x0,
            offset=0x0,
            size=0x20,
            new_memory_size=0x20,
            init_code_size=0x20,
        )
        child_cost = 0

    # The created address is stored inside the measured window (as in the
    # ported filler) so the STATICCALL can target it at runtime.
    create_store = Op.SSTORE(
        key=ADDRESS_SLOT,
        value=create_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    # The created account exists (nonce 1) and is warm (CREATE accessed
    # it); the success flag is stored inside the measured window — a
    # wrongly failed STATICCALL would otherwise be unobservable.
    staticcall_code = Op.STATICCALL(
        gas=FORWARDED_GAS,
        address=Op.SLOAD(key=ADDRESS_SLOT, key_warm=True),
        address_warm=True,
    )
    staticcall_store = Op.SSTORE(
        key=STATICCALL_FLAG_SLOT,
        value=staticcall_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    contract = pre.deploy_contract(
        code=setup
        + CodeGasMeasure(
            code=create_store,
            extra_stack_items=0,
            sstore_key=CREATE_GAS_SLOT,
        )
        + CodeGasMeasure(
            code=staticcall_store,
            extra_stack_items=0,
            sstore_key=STATICCALL_GAS_SLOT,
        ),
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    measured_create = create_store.gas_cost(fork) + child_cost
    measured_staticcall = staticcall_store.gas_cost(fork)

    created = compute_create_address(address=contract, nonce=1)
    post = {
        contract: Account(
            storage={
                ADDRESS_SLOT: created,
                CREATE_GAS_SLOT: measured_create,
                STATICCALL_FLAG_SLOT: 1,
                STATICCALL_GAS_SLOT: measured_staticcall,
            },
        ),
        created: Account(
            nonce=1,
            storage={0: STORED_VALUE} if with_storage else {},
        ),
    }
    if with_storage:
        post[writer] = Account(storage={1: STORED_VALUE})

    state_test(pre=pre, post=post, tx=tx)
