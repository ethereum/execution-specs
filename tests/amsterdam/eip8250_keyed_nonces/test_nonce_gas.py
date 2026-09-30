"""
Gas tests for
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

The encoding of `nonce_keys` followed by `nonce_seq` is priced as
transaction data, in both the standard intrinsic cost and the calldata
floor. Keyed nonce reads and writes are protocol bookkeeping: they warm
nothing, and the nonce manager's own code reverts every ordinary call.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import (
    default_code_frame_gas,
    default_frame,
    verify_frame,
)
from .helpers import FULL_WIDTH_KEY, KEY_A, set_keyed_nonces
from .spec import Spec, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")

PROBE_FRAME_GAS = 100_000
"""Execution gas budget of the frame running a probe."""

FLOOR_PADDING_DATA = b"\x00" * 30_000
"""Frame data driving the calldata floor above the standard cost."""

COLD_READS = 40
"""Number of cold balance reads lifting execution above the floor."""

COLD_READ_BASE = 0x10000
"""First of the untouched addresses whose balances the burner reads."""

BURNER_FRAME_GAS = 200_000
"""Execution gas budget of the frame running the cold reads."""

SLOT_MEASURED_GAS = 0x01
"""Slot the access probe stores its measured gas in."""

SLOT_CALL_RESULT = 0x02
"""Slot recording one plus the result of calling the nonce manager."""

SLOT_RETURN_SIZE = 0x03
"""Slot recording one plus the size of the nonce manager's return data."""

NONCE_KEY_SETS = [
    pytest.param([0], 0, id="legacy_keys"),
    pytest.param([KEY_A], 0, id="small_key"),
    pytest.param([FULL_WIDTH_KEY], 0, id="full_width_key"),
    pytest.param([KEY_A], 2**64 - 2, id="wide_seq"),
    pytest.param(
        [2**256 - Spec.MAX_NONCE_KEYS + i for i in range(Spec.MAX_NONCE_KEYS)],
        0,
        id="max_full_width_keys",
    ),
]
"""Nonce fields spanning the narrowest to the widest encoding."""


def keyed_state_gas(nonce_keys: List[int], nonce_seq: int) -> int:
    """
    Return the first-use state gas the approval charges, for a set whose
    keys are all unused exactly when `nonce_seq` is zero.
    """
    if nonce_keys == [0] or nonce_seq:
        return 0
    return len(nonce_keys) * Spec.KEYED_NONCE_FIRST_USE_STATE_GAS


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("nonce_keys,nonce_seq", NONCE_KEY_SETS)
def test_nonce_fields_priced_as_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Charge the nonce field encoding in the standard intrinsic cost.

    A `VERIFY` frame runs the default code and a second frame reads
    cold balances, so the gas used is the intrinsic cost, both frames'
    known execution gas and any first-use state gas. The cold reads lift
    execution above the calldata floor for every set.
    """
    if nonce_keys == [0]:
        sender = pre.fund_eoa(nonce=nonce_seq)
    else:
        sender = pre.fund_eoa()
        if nonce_seq:
            set_keyed_nonces(
                pre, [(sender, dict.fromkeys(nonce_keys, nonce_seq))]
            )
    state_gas = keyed_state_gas(nonce_keys, nonce_seq)
    burner_code = Bytecode()
    for account in range(COLD_READS):
        burner_code += Op.POP(
            Op.BALANCE(address=COLD_READ_BASE + account, address_warm=False)
        )
    burner_code += Op.STOP
    burner = pre.deploy_contract(code=burner_code)
    tx = Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=nonce_keys,
        frames=[
            verify_frame(state_gas_limit=state_gas),
            default_frame(
                target=burner, gas_limit=BURNER_FRAME_GAS, state_gas_limit=0
            ),
        ],
    )
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
        return_cost_deducted_prior_execution=True,
    )
    execution_used = (
        intrinsic
        + default_code_frame_gas(fork, target_warm=True)
        + fork.frame_entry_gas_calculator()()
        + burner_code.gas_cost(fork)
    )
    calldata_floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
    )
    assert calldata_floor < execution_used
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=execution_used + state_gas,
    )

    state_test(pre=pre, tx=tx, post={})


@pytest.mark.parametrize("nonce_keys,nonce_seq", NONCE_KEY_SETS[:3])
def test_nonce_fields_in_calldata_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Count the nonce field encoding's tokens in the calldata floor.

    Zero-byte padding in a second frame lifts the floor above the
    standard cost, so the transaction pays the floor plus its state gas.
    """
    sender = pre.fund_eoa()
    state_gas = keyed_state_gas(nonce_keys, nonce_seq)
    tx = Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=nonce_keys,
        frames=[
            verify_frame(
                gas_limit=default_code_frame_gas(fork, target_warm=True),
                state_gas_limit=state_gas,
            ),
            default_frame(
                target=pre.deploy_contract(code=Op.STOP),
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=0,
                data=FLOOR_PADDING_DATA,
            ),
        ],
    )
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    calldata_floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
    )
    standard_gas_limit = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
        return_cost_deducted_prior_execution=True,
    ) + sum(frame.gas_limit for frame in tx.frames)
    assert calldata_floor > standard_gas_limit
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=calldata_floor + state_gas,
    )

    state_test(pre=pre, tx=tx, post={})


def test_nonce_manager_stays_cold(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Leave the nonce manager cold after keyed validation and consumption.

    A frame after the approval measures `BALANCE` of the nonce manager
    and pays the cold account access.
    """
    sender = pre.fund_eoa()
    cold_access = Op.BALANCE(address_warm=False).gas_cost(fork)
    measured = Op.BALANCE(address=Spec.NONCE_MANAGER, address_warm=False)
    probe = pre.deploy_contract(
        code=CodeGasMeasure(
            code=measured,
            overhead_cost=measured.gas_cost(fork) - cold_access,
            extra_stack_items=1,
            sstore_key=SLOT_MEASURED_GAS,
        )
    )

    tx = Transaction(
        sender=sender,
        nonce_keys=[KEY_A],
        frames=[
            verify_frame(),
            default_frame(target=probe, gas_limit=PROBE_FRAME_GAS),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage={SLOT_MEASURED_GAS: cold_access})},
    )


def test_nonce_manager_reverts_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Revert an ordinary call to the nonce manager with empty return data.
    """
    sender = pre.fund_eoa()
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_CALL_RESULT,
            Op.ADD(1, Op.CALL(gas=Op.GAS, address=Spec.NONCE_MANAGER)),
        )
        + Op.SSTORE(SLOT_RETURN_SIZE, Op.ADD(1, Op.RETURNDATASIZE))
        + Op.STOP
    )

    tx = Transaction(sender=sender, to=caller, gas_limit=1_000_000)

    state_test(
        pre=pre,
        tx=tx,
        post={
            caller: Account(
                storage={SLOT_CALL_RESULT: 1, SLOT_RETURN_SIZE: 1}
            ),
        },
    )
