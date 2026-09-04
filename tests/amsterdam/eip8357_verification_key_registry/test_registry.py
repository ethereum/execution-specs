"""Runtime-interface tests for the EIP-8357 registry contract."""

from collections.abc import Mapping

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    EIPChecklist,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import Spec, ref_spec_8357

REFERENCE_SPEC_GIT_PATH = ref_spec_8357.git_path
REFERENCE_SPEC_VERSION = ref_spec_8357.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.pre_alloc_mutable,
]

VKEY_1 = 1
VKEY_2 = 2
VKEY_1_ACTIVATION_TIMESTAMP = 1
VKEY_2_ACTIVATION_TIMESTAMP = Spec.MAX_ACTIVATION_TIMESTAMP
VKEY_1_ACTIVATION_SLOT = int(
    "cc69885fda6bcc1a4ace058b4a62bf5e179ea78fd58a1ccd71c22cc9b688792f",
    16,
)
VKEY_2_ACTIVATION_SLOT = int(
    "d9d16d34ffb15ba3a3d852f0d403e2ce1d691fb54de27ac87cd2f993f3ec330f",
    16,
)

K1_STORAGE = {
    Spec.CURRENT_VERIFICATION_KEY_SLOT: VKEY_1,
    VKEY_1_ACTIVATION_SLOT: VKEY_1_ACTIVATION_TIMESTAMP,
}
K1_K2_STORAGE = {
    Spec.CURRENT_VERIFICATION_KEY_SLOT: VKEY_2,
    VKEY_1_ACTIVATION_SLOT: VKEY_1_ACTIVATION_TIMESTAMP,
    VKEY_2_ACTIVATION_SLOT: VKEY_2_ACTIVATION_TIMESTAMP,
}

CALL_SUCCESS_SLOT = 0
RETURN_DATA_SIZE_SLOT = 1
RETURN_DATA_WORD_0_SLOT = 2
RETURN_DATA_WORD_1_SLOT = 3
RECORDER_CANARY = 0xC0DE
RECORDER_PRE_STORAGE = {
    CALL_SUCCESS_SLOT: RECORDER_CANARY,
    RETURN_DATA_SIZE_SLOT: RECORDER_CANARY,
    RETURN_DATA_WORD_0_SLOT: RECORDER_CANARY,
    RETURN_DATA_WORD_1_SLOT: RECORDER_CANARY,
}


def _storage(values: Mapping[int, int]) -> Storage:
    """Convert integer storage vectors to the framework's storage type."""
    storage = Storage()
    for slot, value in values.items():
        storage[slot] = value
    return storage


def _call_recorder_code() -> Bytecode:
    """Return code that calls the registry and records its full result."""
    calldata_offset = 0x80
    return Bytecode(
        Op.CALLDATACOPY(calldata_offset, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            CALL_SUCCESS_SLOT,
            Op.CALL(
                gas=1_000_000,
                address=Spec.EVM_VK_REGISTRY_ADDRESS,
                value=Op.CALLVALUE,
                args_offset=calldata_offset,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=64,
            ),
        )
        + Op.SSTORE(RETURN_DATA_SIZE_SLOT, Op.RETURNDATASIZE)
        + Op.SSTORE(RETURN_DATA_WORD_0_SLOT, Op.MLOAD(0))
        + Op.SSTORE(RETURN_DATA_WORD_1_SLOT, Op.MLOAD(32))
        + Op.STOP
    )


def _word(data: bytes, offset: int) -> int:
    """Decode one zero-padded 32-byte word from returndata."""
    return int.from_bytes(data[offset : offset + 32].ljust(32, b"\x00"), "big")


def _run_registry_call(
    *,
    state_test: StateTestFiller,
    pre: Alloc,
    system_caller: bool,
    calldata: bytes,
    initial_registry_storage: Mapping[int, int],
    expected_registry_storage: Mapping[int, int],
    expected_success: bool,
    expected_return_data: bytes = b"",
    value: int = 0,
) -> None:
    """Execute a registry call through a result-recording contract."""
    assert len(expected_return_data) in (0, 64)

    registry = Address(Spec.EVM_VK_REGISTRY_ADDRESS)
    pre[registry] = Account(
        nonce=1,
        code=Spec.REGISTRY_RUNTIME_CODE,
        storage=_storage(initial_registry_storage),
    )

    recorder_code = _call_recorder_code()
    if system_caller:
        caller = Address(Spec.SYSTEM_ADDRESS)
        pre[caller] = Account(
            nonce=1,
            code=recorder_code,
            storage=_storage(RECORDER_PRE_STORAGE),
        )
    else:
        caller = pre.deploy_contract(
            recorder_code,
            storage=_storage(RECORDER_PRE_STORAGE),
        )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=calldata,
            value=value,
            gas_limit=2_000_000,
        ),
        post={
            registry: Account(storage=_storage(expected_registry_storage)),
            caller: Account(
                balance=0 if expected_success else value,
                storage={
                    CALL_SUCCESS_SLOT: int(expected_success),
                    RETURN_DATA_SIZE_SLOT: len(expected_return_data),
                    RETURN_DATA_WORD_0_SLOT: _word(expected_return_data, 0),
                    RETURN_DATA_WORD_1_SLOT: _word(expected_return_data, 32),
                },
            ),
        },
    )


@EIPChecklist.SystemContract.Test.CallContexts.Normal()
@EIPChecklist.SystemContract.Test.Inputs.Valid()
@EIPChecklist.SystemContract.Test.Inputs.AllZeros()
@EIPChecklist.SystemContract.Test.InputLengths.Static.Correct()
@pytest.mark.parametrize(
    "query,initial_storage,expected_success,expected_return_data",
    [
        pytest.param(
            Hash(0), {}, False, b"", id="current_before_registration"
        ),
        pytest.param(
            Hash(0),
            K1_STORAGE,
            True,
            Hash(VKEY_1) + Hash(VKEY_1_ACTIVATION_TIMESTAMP),
            id="current",
        ),
        pytest.param(
            Hash(VKEY_1),
            K1_STORAGE,
            True,
            Hash(VKEY_1) + Hash(VKEY_1_ACTIVATION_TIMESTAMP),
            id="exact_current_vkey",
        ),
        pytest.param(
            Hash(VKEY_2),
            K1_STORAGE,
            False,
            b"",
            id="unregistered_vkey",
        ),
        pytest.param(
            Hash(VKEY_2),
            {
                **K1_K2_STORAGE,
                Spec.CURRENT_VERIFICATION_KEY_SLOT: VKEY_1,
            },
            True,
            Hash(VKEY_2) + Hash(VKEY_2_ACTIVATION_TIMESTAMP),
            id="exact_historical_vkey",
        ),
    ],
)
def test_registry_reads(
    state_test: StateTestFiller,
    pre: Alloc,
    query: bytes,
    initial_storage: Mapping[int, int],
    expected_success: bool,
    expected_return_data: bytes,
) -> None:
    """Read the current, exact-current, and historical registry entries."""
    _run_registry_call(
        state_test=state_test,
        pre=pre,
        system_caller=False,
        calldata=query,
        initial_registry_storage=initial_storage,
        expected_registry_storage=initial_storage,
        expected_success=expected_success,
        expected_return_data=expected_return_data,
    )


@EIPChecklist.SystemContract.Test.Inputs.Valid()
@EIPChecklist.SystemContract.Test.Inputs.Boundary()
@EIPChecklist.SystemContract.Test.Inputs.MaxValues()
@EIPChecklist.SystemContract.Test.OutOfBounds.Max()
@EIPChecklist.SystemContract.Test.InputLengths.Dynamic.Valid()
@pytest.mark.parametrize(
    "calldata,initial_storage,expected_storage",
    [
        pytest.param(
            Hash(VKEY_1) + Hash(VKEY_1_ACTIVATION_TIMESTAMP),
            {},
            K1_STORAGE,
            id="register_initial_vkey",
        ),
        pytest.param(
            Hash(VKEY_2) + Hash(VKEY_2_ACTIVATION_TIMESTAMP),
            K1_STORAGE,
            K1_K2_STORAGE,
            id="register_second_vkey",
        ),
        pytest.param(
            Hash(VKEY_1),
            K1_K2_STORAGE,
            {
                **K1_K2_STORAGE,
                Spec.CURRENT_VERIFICATION_KEY_SLOT: VKEY_1,
            },
            id="reactivate_historical_vkey",
        ),
    ],
)
def test_registry_updates(
    state_test: StateTestFiller,
    pre: Alloc,
    calldata: bytes,
    initial_storage: Mapping[int, int],
    expected_storage: Mapping[int, int],
) -> None:
    """Register new keys and reactivate a historical key."""
    _run_registry_call(
        state_test=state_test,
        pre=pre,
        system_caller=True,
        calldata=calldata,
        initial_registry_storage=initial_storage,
        expected_registry_storage=expected_storage,
        expected_success=True,
    )


@EIPChecklist.SystemContract.Test.Inputs.Invalid.Checks()
@EIPChecklist.SystemContract.Test.OutOfBounds.MaxPlusOne()
@pytest.mark.parametrize(
    "calldata,initial_storage",
    [
        pytest.param(
            Hash(VKEY_1) + Hash(VKEY_2_ACTIVATION_TIMESTAMP),
            K1_STORAGE,
            id="duplicate_registration",
        ),
        pytest.param(
            Hash(0) + Hash(VKEY_1_ACTIVATION_TIMESTAMP),
            {},
            id="zero_vkey_registration",
        ),
        pytest.param(
            Hash(VKEY_1) + Hash(0),
            {},
            id="zero_activation_timestamp",
        ),
        pytest.param(
            Hash(VKEY_1) + Hash(Spec.MAX_ACTIVATION_TIMESTAMP + 1),
            {},
            id="activation_timestamp_too_large",
        ),
        pytest.param(Hash(0), K1_STORAGE, id="reactivate_zero_vkey"),
        pytest.param(
            Hash(VKEY_2),
            K1_STORAGE,
            id="reactivate_unregistered_vkey",
        ),
    ],
)
def test_registry_rejects_invalid_updates(
    state_test: StateTestFiller,
    pre: Alloc,
    calldata: bytes,
    initial_storage: Mapping[int, int],
) -> None:
    """Invalid registrations and reactivations revert without state changes."""
    _run_registry_call(
        state_test=state_test,
        pre=pre,
        system_caller=True,
        calldata=calldata,
        initial_registry_storage=initial_storage,
        expected_registry_storage=initial_storage,
        expected_success=False,
    )


@EIPChecklist.SystemContract.Test.InputLengths.Zero()
@EIPChecklist.SystemContract.Test.InputLengths.Static.TooShort()
@EIPChecklist.SystemContract.Test.InputLengths.Static.TooLong()
@EIPChecklist.SystemContract.Test.InputLengths.Dynamic.TooShort()
@EIPChecklist.SystemContract.Test.InputLengths.Dynamic.TooLong()
@pytest.mark.parametrize(
    "system_caller,calldata_length",
    [
        pytest.param(False, 0, id="read_zero_bytes"),
        pytest.param(False, 31, id="read_31_bytes"),
        pytest.param(False, 33, id="read_33_bytes"),
        pytest.param(False, 64, id="read_64_bytes"),
        pytest.param(True, 0, id="update_zero_bytes"),
        pytest.param(True, 31, id="update_31_bytes"),
        pytest.param(True, 33, id="update_33_bytes"),
        pytest.param(True, 63, id="update_63_bytes"),
        pytest.param(True, 65, id="update_65_bytes"),
    ],
)
def test_registry_rejects_invalid_calldata_lengths(
    state_test: StateTestFiller,
    pre: Alloc,
    system_caller: bool,
    calldata_length: int,
) -> None:
    """Reject calldata lengths outside the caller's accepted interface."""
    _run_registry_call(
        state_test=state_test,
        pre=pre,
        system_caller=system_caller,
        calldata=b"\x01" * calldata_length,
        initial_registry_storage={},
        expected_registry_storage={},
        expected_success=False,
    )


@EIPChecklist.SystemContract.Test.ValueTransfer.NoFee()
@pytest.mark.parametrize(
    "system_caller,calldata,initial_storage",
    [
        pytest.param(False, Hash(0), K1_STORAGE, id="read"),
        pytest.param(
            True,
            Hash(VKEY_1) + Hash(VKEY_1_ACTIVATION_TIMESTAMP),
            {},
            id="update",
        ),
    ],
)
def test_registry_rejects_nonzero_value(
    state_test: StateTestFiller,
    pre: Alloc,
    system_caller: bool,
    calldata: bytes,
    initial_storage: Mapping[int, int],
) -> None:
    """Both read and fork-update calls reject nonzero value."""
    _run_registry_call(
        state_test=state_test,
        pre=pre,
        system_caller=system_caller,
        calldata=calldata,
        initial_registry_storage=initial_storage,
        expected_registry_storage=initial_storage,
        expected_success=False,
        value=1,
    )
