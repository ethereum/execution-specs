"""
Tests for [EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

The key set `[0]` aliases the sender's account nonce, and every other key
selects a sequence in the `NONCE_MANAGER` storage. The payment-scoped
`APPROVE` consumes the selected domains and charges one storage slot
creation of state gas per keyed domain used for the first time.
"""  # noqa: E501

from typing import Dict, List, Optional

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Conditional,
    Fork,
    Frame,
    FrameReceipt,
    FrameSignature,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    TransactionTestFiller,
    compute_create_address,
)

from ..eip8141_frame_transactions.helpers import (
    default_code_frame_gas,
    default_frame,
    sender_frame,
    verify_frame,
)
from ..eip8141_frame_transactions.spec import Spec as Spec8141
from .helpers import (
    NONCE_KEY,
    OTHER_KEY,
    keyed_nonce_access_cost,
    keyed_nonce_first_use,
    nonce_field_calldata,
    nonce_manager_with_slots,
    used_key_slots,
    verify_only_tx_gas_used,
)
from .spec import Spec, keyed_nonce_slot, nonce_keys_hash, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")

MAX_KEY = 2**256 - 1
"""The largest encodable nonce key."""

SLOT_RESULT = 0x01
"""Storage slot the probe contracts write what they read into."""

SLOT_LEGACY_NONCE = 0x02
"""Storage slot recording `TXPARAM` legacy nonce reads."""

SLOT_NONCE_SEQ = 0x03
"""Storage slot recording `TXPARAM` nonce sequence reads."""

SLOT_EXECUTED = 0x04
"""Storage slot a worker writes to record its execution."""

COLD_READS = 40
"""Number of cold balance reads lifting execution above the floor."""

COLD_READ_BASE = 0x10000
"""First of the untouched addresses whose balances are read cold."""

FLOOR_PADDING = bytes(30_000)
"""Frame data lifting the calldata floor above the standard cost."""


def delegated_sender_code(sender_work: Bytecode) -> Bytecode:
    """
    Return code for an EIP-7702 delegated sender that runs `sender_work`
    in a `SENDER` frame and approves the allowed scope in any other.
    """
    frame_index = Op.TXPARAM(Spec8141.TXPARAM_CURRENT_FRAME_INDEX)
    return Conditional(
        condition=Op.EQ(
            Op.FRAMEPARAM(frame_index, Spec8141.FRAMEPARAM_MODE),
            Spec8141.MODE_SENDER,
        ),
        if_true=sender_work,
        if_false=Op.APPROVE(
            0,
            0,
            Op.FRAMEPARAM(frame_index, Spec8141.FRAMEPARAM_ALLOWED_SCOPE),
        ),
    )


def default_verify_receipt(fork: Fork, state_gas_used: int) -> FrameReceipt:
    """
    Return the receipt of a default-code `VERIFY` frame resolving to the
    sender, charging `state_gas_used` for its nonce transition.
    """
    return FrameReceipt(
        status=Spec8141.STATUS_SUCCESS,
        gas_used=default_code_frame_gas(fork, target_warm=True),
        state_gas_used=state_gas_used,
    )


def test_keyed_nonce_consumption(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Consume a fresh key: its slot becomes one, the approving frame pays
    one slot creation and the account nonce is untouched.
    """
    first_use = keyed_nonce_first_use(fork)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=0,
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=verify_only_tx_gas_used(fork, tx, first_uses=1),
        frame_receipts=[default_verify_receipt(fork, first_use)],
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                nonce=Spec.NONCE_MANAGER_NONCE,
                code=Spec.NONCE_MANAGER_CODE,
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1},
            ),
            sender: Account(nonce=0),
        },
    )


@pytest.mark.parametrize(
    "explicit_fields",
    [
        pytest.param(True, id="explicit_legacy_key_set"),
        pytest.param(False, id="unset_nonce_fields"),
    ],
)
def test_legacy_alias_key(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    explicit_fields: bool,
) -> None:
    """
    Select the account nonce with the key set `[0]`, which the framework
    also uses for unset nonce fields: the nonce increments with no state
    gas and the nonce manager's storage stays empty.
    """
    sender = pre.fund_eoa()
    nonce_fields = dict(nonce_keys=[0], nonce=0) if explicit_fields else {}
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        **nonce_fields,
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=verify_only_tx_gas_used(fork, tx, first_uses=0),
        frame_receipts=[default_verify_receipt(fork, 0)],
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                nonce=Spec.NONCE_MANAGER_NONCE,
                code=Spec.NONCE_MANAGER_CODE,
                storage={},
            ),
            sender: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "nonce_keys",
    [
        pytest.param([1, NONCE_KEY, MAX_KEY], id="three_keys_spanning_range"),
        pytest.param(
            list(range(1, Spec.MAX_NONCE_KEYS + 1)), id="max_key_count"
        ),
    ],
)
def test_multi_key_consumption(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
) -> None:
    """
    Consume a set of fresh keys: every slot becomes one and the
    approving frame pays one slot creation per key.
    """
    state_gas = keyed_nonce_first_use(fork) * len(nonce_keys)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(state_gas_limit=state_gas)],
        nonce_keys=nonce_keys,
        nonce=0,
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=verify_only_tx_gas_used(
            fork, tx, first_uses=len(nonce_keys)
        ),
        frame_receipts=[default_verify_receipt(fork, state_gas)],
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={
                    keyed_nonce_slot(sender, key): 1 for key in nonce_keys
                },
            ),
            sender: Account(nonce=0),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "current_seq",
    [
        pytest.param(1, id="second_use"),
        pytest.param(127, id="seq_before_rlp_prefix"),
        pytest.param(128, id="seq_with_rlp_prefix"),
        pytest.param(255, id="seq_last_one_byte"),
        pytest.param(256, id="seq_first_two_bytes"),
        pytest.param(Spec.MAX_NONCE_SEQ - 1, id="last_use_before_exhaustion"),
    ],
)
def test_used_key_pays_no_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    current_seq: int,
) -> None:
    """
    Reuse a key at its current sequence: the slot advances by one with
    no state gas, up to the last usable sequence.
    """
    sender = pre.fund_eoa()
    nonce_manager_with_slots(
        pre, used_key_slots(sender, {NONCE_KEY: current_seq})
    )
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=current_seq,
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=verify_only_tx_gas_used(fork, tx, first_uses=0),
        frame_receipts=[default_verify_receipt(fork, 0)],
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): current_seq + 1}
            ),
            sender: Account(nonce=0),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys",
    [
        pytest.param([NONCE_KEY, OTHER_KEY], id="two_keys"),
        pytest.param(
            list(range(1, Spec.MAX_NONCE_KEYS + 1)), id="max_key_count"
        ),
    ],
)
def test_used_key_set_needs_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
) -> None:
    """Advance a set of used keys from a frame with no state gas budget."""
    current_seq = 3
    sender = pre.fund_eoa()
    nonce_manager_with_slots(
        pre, used_key_slots(sender, dict.fromkeys(nonce_keys, current_seq))
    )
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(state_gas_limit=0)],
        nonce_keys=nonce_keys,
        nonce=current_seq,
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=verify_only_tx_gas_used(fork, tx, first_uses=0),
        frame_receipts=[default_verify_receipt(fork, 0)],
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage=used_key_slots(
                    sender, dict.fromkeys(nonce_keys, current_seq + 1)
                )
            ),
            sender: Account(nonce=0),
        },
    )


NONCE_FIELD_ENCODINGS = [
    pytest.param([0], 0, id="legacy_key_set"),
    pytest.param([NONCE_KEY], 0, id="small_key"),
    pytest.param([MAX_KEY], 0, id="full_width_key"),
    pytest.param([NONCE_KEY], Spec.MAX_NONCE_SEQ - 1, id="wide_seq"),
    pytest.param(
        list(range(MAX_KEY - Spec.MAX_NONCE_KEYS + 1, MAX_KEY + 1)),
        0,
        id="max_full_width_keys",
    ),
]
"""Nonce fields from the narrowest to the widest encoding."""


def sender_at_sequence(
    pre: Alloc, nonce_keys: List[int], nonce_seq: int
) -> EOA:
    """Return a sender whose selected domains all hold `nonce_seq`."""
    if not nonce_seq:
        return pre.fund_eoa()
    if nonce_keys == [0]:
        return pre.fund_eoa(nonce=nonce_seq)
    sender = pre.fund_eoa()
    nonce_manager_with_slots(
        pre, used_key_slots(sender, dict.fromkeys(nonce_keys, nonce_seq))
    )
    return sender


def first_use_count(nonce_keys: List[int], nonce_seq: int) -> int:
    """Return the slots a set creates, all of them fresh at sequence zero."""
    if nonce_keys == [0] or nonce_seq:
        return 0
    return len(nonce_keys)


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("nonce_keys,nonce_seq", NONCE_FIELD_ENCODINGS)
def test_nonce_fields_priced_as_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Price the nonce field encoding in the standard intrinsic cost of a
    transaction whose execution exceeds the calldata floor.
    """
    sender = sender_at_sequence(pre, nonce_keys, nonce_seq)
    first_uses = first_use_count(nonce_keys, nonce_seq)
    state_gas = first_uses * keyed_nonce_first_use(fork)
    burner_code = Bytecode()
    for account in range(COLD_READS):
        burner_code += Op.POP(
            Op.BALANCE(address=COLD_READ_BASE + account, address_warm=False)
        )
    burner_code += Op.STOP
    burner = pre.deploy_contract(code=burner_code)
    burner_gas = fork.frame_entry_gas_calculator()(
        target_warm=False
    ) + burner_code.gas_cost(fork)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(state_gas_limit=state_gas),
            default_frame(
                target=burner, gas_limit=burner_gas, state_gas_limit=0
            ),
        ],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
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
        intrinsic + default_code_frame_gas(fork, target_warm=True) + burner_gas
    )
    floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
    )
    assert floor < execution_used
    tx.expected_receipt = TransactionReceipt(
        payer=sender, cumulative_gas_used=execution_used + state_gas
    )
    state_test(pre=pre, tx=tx, post={})


@pytest.mark.parametrize("nonce_keys,nonce_seq", NONCE_FIELD_ENCODINGS[:3])
def test_nonce_fields_in_calldata_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Count the nonce field encoding in the calldata floor of a
    transaction whose frame data lifts the floor above its standard cost.
    """
    sender = sender_at_sequence(pre, nonce_keys, nonce_seq)
    first_uses = first_use_count(nonce_keys, nonce_seq)
    state_gas = first_uses * keyed_nonce_first_use(fork)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(
                gas_limit=default_code_frame_gas(fork, target_warm=True),
                state_gas_limit=state_gas,
            ),
            default_frame(
                target=pre.deploy_contract(code=Op.STOP),
                gas_limit=fork.frame_entry_gas_calculator()(target_warm=False),
                state_gas_limit=0,
                data=FLOOR_PADDING,
            ),
        ],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
    )
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None
    floor = fork.frame_transaction_data_floor_cost_calculator()(
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
    assert floor > standard_gas_limit
    tx.expected_receipt = TransactionReceipt(
        payer=sender, cumulative_gas_used=floor + state_gas
    )
    state_test(pre=pre, tx=tx, post={})


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys,nonce_seq",
    [
        pytest.param([0], 0, id="legacy_key_set"),
        pytest.param([NONCE_KEY], 0, id="fresh_key"),
        pytest.param([NONCE_KEY], 1, id="used_key"),
        pytest.param([NONCE_KEY, OTHER_KEY], 0, id="two_keys"),
        pytest.param(
            list(range(1, Spec.MAX_NONCE_KEYS + 1)), 0, id="max_keys"
        ),
    ],
)
@pytest.mark.parametrize(
    "floor_bound", [False, True], ids=["standard", "floor"]
)
def test_keyed_nonce_access_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
    floor_bound: bool,
) -> None:
    """
    Charge `KEYED_NONCE_ACCESS_COST` for every non-zero nonce key in both
    the intrinsic cost and the calldata floor, so a transaction pays it
    whichever of the two binds. The legacy key set pays nothing, and a
    used key pays the same as a fresh one.

    The expected gas is built from the EIP's constant: the transaction
    priced with the legacy key set, which carries no access cost, with
    the calldata of its own nonce fields swapped in and the access cost
    added on each side.
    """
    sender = sender_at_sequence(pre, nonce_keys, nonce_seq)
    state_gas = first_use_count(nonce_keys, nonce_seq) * keyed_nonce_first_use(
        fork
    )
    if floor_bound:
        worker = pre.deploy_contract(code=Op.STOP)
        worker_gas = fork.frame_entry_gas_calculator()(target_warm=False)
        worker_data = FLOOR_PADDING
    else:
        worker_code = Bytecode()
        for account in range(COLD_READS):
            worker_code += Op.POP(
                Op.BALANCE(
                    address=COLD_READ_BASE + account, address_warm=False
                )
            )
        worker_code += Op.STOP
        worker = pre.deploy_contract(code=worker_code)
        worker_gas = fork.frame_entry_gas_calculator()(
            target_warm=False
        ) + worker_code.gas_cost(fork)
        worker_data = b""
    verify_gas = default_code_frame_gas(fork, target_warm=True)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(gas_limit=verify_gas, state_gas_limit=state_gas),
            default_frame(
                target=worker,
                gas_limit=worker_gas,
                state_gas_limit=0,
                data=worker_data,
            ),
        ],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
    )
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    access = keyed_nonce_access_cost(nonce_keys)
    own_nonce_data = nonce_field_calldata(nonce_keys, nonce_seq)
    legacy_nonce_data = nonce_field_calldata([0], 0)
    gas_costs = fork.gas_costs()
    calldata_gas = fork.calldata_gas_calculator()
    floor_gas_per_byte = (
        gas_costs.TX_DATA_TOKEN_STANDARD * gas_costs.TX_DATA_TOKEN_FLOOR
    )
    intrinsic_calculator = fork.frame_transaction_intrinsic_cost_calculator()
    floor_calculator = fork.frame_transaction_data_floor_cost_calculator()

    intrinsic = (
        intrinsic_calculator(
            frames=tx.frames,
            signatures=tx.signatures,
            nonce_keys=[0],
            nonce_seq=0,
            return_cost_deducted_prior_execution=True,
        )
        - calldata_gas(data=legacy_nonce_data)
        + calldata_gas(data=own_nonce_data)
        + access
    )
    floor = (
        floor_calculator(
            frames=tx.frames,
            signatures=tx.signatures,
            nonce_keys=[0],
            nonce_seq=0,
        )
        + (len(own_nonce_data) - len(legacy_nonce_data)) * floor_gas_per_byte
        + access
    )
    assert intrinsic == intrinsic_calculator(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
        return_cost_deducted_prior_execution=True,
    )
    assert floor == floor_calculator(
        frames=tx.frames,
        signatures=tx.signatures,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
    )

    execution_used = intrinsic + verify_gas + worker_gas
    assert (floor > execution_used) == floor_bound
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=max(execution_used, floor) + state_gas,
    )
    state_test(pre=pre, tx=tx, post={})


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys,nonce_seq,sender_nonce,used_keys,error",
    [
        pytest.param(
            [NONCE_KEY],
            1,
            0,
            {},
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="fresh_key_nonzero_seq",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [0],
            1,
            0,
            {},
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="legacy_alias_seq_too_high",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [0],
            0,
            1,
            {},
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="legacy_alias_seq_too_low",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY],
            2,
            0,
            {NONCE_KEY: 3},
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="used_key_seq_too_low",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY],
            4,
            0,
            {NONCE_KEY: 3},
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="used_key_seq_too_high",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY],
            Spec.MAX_NONCE_SEQ - 1,
            0,
            {NONCE_KEY: Spec.MAX_NONCE_SEQ},
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="exhausted_key",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY, OTHER_KEY],
            0,
            0,
            {NONCE_KEY: 1},
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="mixed_set_seq_of_fresh_key",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY, OTHER_KEY],
            1,
            0,
            {NONCE_KEY: 1},
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="mixed_set_seq_of_used_key",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY, OTHER_KEY],
            3,
            0,
            {NONCE_KEY: 3, OTHER_KEY: 4},
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="mixed_set_used_key_ahead",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY],
            Spec.MAX_NONCE_SEQ,
            0,
            {NONCE_KEY: Spec.MAX_NONCE_SEQ},
            TransactionException.NONCE_IS_MAX,
            id="exhausted_key_at_its_sequence",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            [NONCE_KEY],
            0,
            5,
            {},
            None,
            id="keyed_domain_ignores_account_nonce",
        ),
    ],
)
def test_stateful_validity(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
    sender_nonce: int,
    used_keys: Dict[int, int],
    error: Optional[TransactionException],
) -> None:
    """
    Reject a sequence that differs from any selected domain's current
    one, and ignore the account nonce for a keyed domain.
    """
    sender = pre.fund_eoa(nonce=sender_nonce)
    if used_keys:
        nonce_manager_with_slots(pre, used_key_slots(sender, used_keys))
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
        error=error,
    )
    post = {}
    if error is None:
        post[Spec.NONCE_MANAGER] = Account(
            storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
        )
        post[sender] = Account(nonce=sender_nonce)
    state_test(pre=pre, tx=tx, post=post)


KEY_SET_CASES = [
    pytest.param(
        [],
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="empty_key_set",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        list(range(1, Spec.MAX_NONCE_KEYS + 2)),
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_count_above_max",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [2, 1],
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="decreasing_keys",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [1, 1],
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="duplicate_keys",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [0, 1],
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="zero_key_first_in_multi_key_set",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [0, 0],
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="zero_key_repeated",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [2**256],
        0,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_beyond_width",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [NONCE_KEY],
        Spec.MAX_NONCE_SEQ,
        TransactionException.NONCE_IS_MAX,
        id="seq_at_max",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [NONCE_KEY],
        Spec.MAX_NONCE_SEQ + 1,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="seq_beyond_width",
        marks=pytest.mark.exception_test,
    ),
]
"""
Key sets and sequences rejected regardless of state: malformed sets,
values beyond their field widths, and the exhausted sequence.
"""


@pytest.mark.parametrize("nonce_keys,nonce_seq,error", KEY_SET_CASES)
def test_static_validity(
    state_test: StateTestFiller,
    pre: Alloc,
    nonce_keys: List[int],
    nonce_seq: int,
    error: TransactionException,
) -> None:
    """Reject a malformed key set or sequence and consume nothing."""
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
        error=error,
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(storage={}),
            sender: Account(nonce=0),
        },
    )


@pytest.mark.parametrize("nonce_keys,nonce_seq,error", KEY_SET_CASES)
def test_static_validity_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    nonce_keys: List[int],
    nonce_seq: int,
    error: TransactionException,
) -> None:
    """Reject the `test_static_validity` cases as transaction tests."""
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
        error=error,
    )
    transaction_test(pre=pre, tx=tx)


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys,nonce_seq",
    [
        pytest.param([5, 9], 0, id="keyed_set"),
        pytest.param([5, 9], 4, id="used_keyed_set"),
        pytest.param([0], 3, id="legacy_key_set"),
    ],
)
def test_txparam_nonce_fields(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Read the sequence, the pre-state legacy nonce, the key count, the
    key set hash and the first key through `TXPARAM`.
    """
    sender_nonce = 3
    storage = Storage()
    probe_code = (
        Op.SSTORE(
            storage.store_next(nonce_seq), Op.TXPARAM(Spec.TXPARAM_NONCE_SEQ)
        )
        + Op.SSTORE(
            storage.store_next(sender_nonce),
            Op.TXPARAM(Spec.TXPARAM_LEGACY_NONCE),
        )
        + Op.SSTORE(
            storage.store_next(len(nonce_keys)),
            Op.TXPARAM(Spec.TXPARAM_NONCE_KEY_COUNT),
        )
        + Op.SSTORE(
            storage.store_next(nonce_keys_hash(nonce_keys)),
            Op.TXPARAM(Spec.TXPARAM_NONCE_KEYS_HASH),
        )
        + Op.SSTORE(
            storage.store_next(nonce_keys[0]),
            Op.TXPARAM(Spec.TXPARAM_NONCE_KEY_0),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)
    sender = pre.fund_eoa(nonce=sender_nonce)
    if nonce_keys != [0] and nonce_seq:
        nonce_manager_with_slots(
            pre, used_key_slots(sender, dict.fromkeys(nonce_keys, nonce_seq))
        )
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                state_gas_limit=probe_code.state_cost(fork),
            ),
        ],
        nonce_keys=nonce_keys,
        nonce=nonce_seq,
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(storage=storage),
            sender: Account(
                nonce=sender_nonce + 1 if nonce_keys == [0] else sender_nonce
            ),
        },
    )


def test_txparam_first_undefined_selector_halts(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Halt on the first `TXPARAM` selector past this EIP's, discarding a
    marker written before the read.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF)
        + Op.POP(Op.TXPARAM(Spec.TXPARAM_FIRST_UNDEFINED))
        + Op.STOP
    )
    probe_frame = default_frame(target=probe)
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), probe_frame],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                FrameReceipt(
                    status=Spec8141.STATUS_FAILURE,
                    gas_used=probe_frame.gas_limit,
                ),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage={SLOT_RESULT: 0})},
    )


@pytest.mark.pre_alloc_mutable
def test_legacy_nonce_txparam_stable_across_create(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Keep the legacy nonce `TXPARAM` at its pre-state value and the
    sequence at the keyed one after a `CREATE` bumps the account nonce.
    """
    sender_nonce = 3
    creator = pre.deploy_contract(
        code=delegated_sender_code(
            Op.POP(Op.CREATE(0, 0, 0))
            + Op.SSTORE(
                SLOT_LEGACY_NONCE, Op.TXPARAM(Spec.TXPARAM_LEGACY_NONCE)
            )
            + Op.SSTORE(SLOT_NONCE_SEQ, Op.TXPARAM(Spec.TXPARAM_NONCE_SEQ))
            + Op.STOP
        )
    )
    sender = pre.fund_eoa(nonce=sender_nonce, delegation=creator)
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), sender_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    state_gas_used=keyed_nonce_first_use(fork),
                ),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
            ],
        ),
    )
    created = compute_create_address(address=sender, nonce=sender_nonce)
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=sender_nonce + 1,
                storage={
                    SLOT_LEGACY_NONCE: sender_nonce,
                    SLOT_NONCE_SEQ: 0,
                },
            ),
            created: Account(nonce=1, code=b""),
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
        },
    )


def test_consumption_survives_frame_revert(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """Keep a consumed key and its state gas when a later frame reverts."""
    first_use = keyed_nonce_first_use(fork)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), sender_frame(target=reverter)],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                default_verify_receipt(fork, first_use),
                FrameReceipt(status=Spec8141.STATUS_FAILURE),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
            sender: Account(nonce=0),
        },
    )


def test_consumption_survives_atomic_batch_unroll(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Keep a consumed key, the payer and the state gas when an atomic
    batch after the approval unrolls.
    """
    first_use = keyed_nonce_first_use(fork)
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(target=writer, flags=Spec8141.ATOMIC_BATCH_FLAG),
            sender_frame(target=reverter),
        ],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                default_verify_receipt(fork, first_use),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
                FrameReceipt(status=Spec8141.STATUS_FAILURE),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
            writer: Account(storage={SLOT_EXECUTED: 0}),
            sender: Account(nonce=0),
        },
    )


@pytest.mark.parametrize(
    "key_count",
    [pytest.param(1, id="one_key"), pytest.param(2, id="two_keys")],
)
def test_first_use_state_gas_exact_budget(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, key_count: int
) -> None:
    """Approve with a state budget of exactly the first-use charge."""
    state_gas = keyed_nonce_first_use(fork) * key_count
    nonce_keys = [NONCE_KEY + index for index in range(key_count)]
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(state_gas_limit=state_gas)],
        nonce_keys=nonce_keys,
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[default_verify_receipt(fork, state_gas)],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={
                    keyed_nonce_slot(sender, key): 1 for key in nonce_keys
                }
            ),
        },
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "key_count",
    [pytest.param(1, id="one_key"), pytest.param(2, id="two_keys")],
)
def test_first_use_state_gas_short_budget_fails_verify(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, key_count: int
) -> None:
    """
    Invalidate the transaction when the approving `VERIFY` frame's state
    budget is one below the first-use charge.
    """
    state_gas = keyed_nonce_first_use(fork) * key_count
    nonce_keys = [NONCE_KEY + index for index in range(key_count)]
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(state_gas_limit=state_gas - 1)],
        nonce_keys=nonce_keys,
        nonce=0,
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )
    state_test(pre=pre, tx=tx, post={})


def test_first_use_state_gas_halts_contract_approver(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Halt an approval from the sender's code in a `DEFAULT` frame whose
    state budget is one below the first-use charge, so a later `VERIFY`
    frame approves and consumes the key instead.
    """
    first_use = keyed_nonce_first_use(fork)
    approve = Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT)
    approver = pre.deploy_contract(code=approve)
    sender = pre.fund_eoa(delegation=approver)
    approving_frame = Frame(
        mode=Spec8141.MODE_DEFAULT,
        flags=Spec8141.APPROVE_EXECUTION_AND_PAYMENT,
        target=sender,
        state_gas_limit=first_use - 1,
    )
    tx = Transaction(
        sender=sender,
        frames=[approving_frame, verify_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec8141.STATUS_FAILURE,
                    gas_used=approving_frame.gas_limit,
                    state_gas_used=0,
                ),
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    # The failed frame's accesses are discarded, so the
                    # delegate is cold again at the second entry.
                    gas_used=fork.frame_entry_gas_calculator()(
                        target_warm=True, delegated=True
                    )
                    + approve.execution_cost(fork),
                    state_gas_used=first_use,
                ),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
            sender: Account(nonce=1),
        },
    )


def test_contract_approver_pays_first_use(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Approve from the sender's code in a `DEFAULT` frame whose receipt
    carries the first-use charge.
    """
    first_use = keyed_nonce_first_use(fork)
    approve = Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT)
    approver = pre.deploy_contract(code=approve)
    sender = pre.fund_eoa(delegation=approver)
    tx = Transaction(
        sender=sender,
        frames=[
            Frame(
                mode=Spec8141.MODE_DEFAULT,
                flags=Spec8141.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                state_gas_limit=first_use,
            ),
        ],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    gas_used=fork.frame_entry_gas_calculator()(
                        target_warm=True, delegated=True
                    )
                    + approve.execution_cost(fork),
                    state_gas_used=first_use,
                ),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
            # A delegated EOA starts at nonce one, having sent its
            # authorization.
            sender: Account(nonce=1),
        },
    )


def test_sponsor_pays_first_use(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Charge the sender's first use to the sponsor's `VERIFY` frame, which
    approves payment, and nothing to the sender's execution approval.
    """
    first_use = keyed_nonce_first_use(fork)
    sender = pre.fund_eoa()
    payer = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            verify_frame(flags=Spec8141.APPROVE_PAYMENT, target=payer),
        ],
        signatures=[
            FrameSignature(
                scheme=Spec8141.SCHEME_SECP256K1,
                signer=Bytes(sender),
            ),
            FrameSignature(
                scheme=Spec8141.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=payer,
            frame_receipts=[
                default_verify_receipt(fork, 0),
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    gas_used=default_code_frame_gas(fork, target_warm=False),
                    state_gas_used=first_use,
                ),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
            sender: Account(nonce=0),
            payer: Account(nonce=0),
        },
    )


@pytest.mark.parametrize(
    "scopes",
    [
        pytest.param(
            [Spec8141.APPROVE_EXECUTION, Spec8141.APPROVE_PAYMENT],
            id="payment_after_execution",
        ),
        pytest.param(
            [Spec8141.APPROVE_EXECUTION_AND_PAYMENT],
            id="execution_and_payment",
        ),
    ],
)
def test_payment_scope_consumes(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, scopes: List[int]
) -> None:
    """
    Consume the key once, on the payment-scoped `APPROVE`, with no state
    gas charged to an execution-only approval before it.
    """
    first_use = keyed_nonce_first_use(fork)
    approver = pre.deploy_contract(code=delegated_sender_code(Op.STOP))
    sender = pre.fund_eoa(delegation=approver)
    receipts = [
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0)
        for _ in scopes[:-1]
    ]
    receipts.append(
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=first_use)
    )
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(flags=scope) for scope in scopes],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender, frame_receipts=receipts
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
            sender: Account(nonce=1),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_legacy_nonce_exhaustion_halts_approval(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Halt a legacy payment approval in a `SENDER` frame whose `CREATE`
    consumed the last nonce, so the frame fails with its gas spent and
    its `CREATE` undone, and a later `VERIFY` frame approves.
    """
    sender_nonce = Spec.MAX_NONCE_SEQ - 1
    frame_index = Op.TXPARAM(Spec8141.TXPARAM_CURRENT_FRAME_INDEX)
    exhauster = pre.deploy_contract(
        code=delegated_sender_code(
            Op.POP(Op.CREATE(0, 0, 0))
            + Op.APPROVE(
                0,
                0,
                Op.FRAMEPARAM(frame_index, Spec8141.FRAMEPARAM_ALLOWED_SCOPE),
            )
        )
    )
    sender = pre.fund_eoa(nonce=sender_nonce, delegation=exhauster)
    exhausting_frame = sender_frame(flags=Spec8141.APPROVE_PAYMENT)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            exhausting_frame,
            verify_frame(flags=Spec8141.APPROVE_PAYMENT),
        ],
        nonce_keys=[0],
        nonce=sender_nonce,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
                FrameReceipt(
                    status=Spec8141.STATUS_FAILURE,
                    gas_used=exhausting_frame.gas_limit,
                    state_gas_used=0,
                ),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
            ],
        ),
    )
    created = compute_create_address(address=sender, nonce=sender_nonce)
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=Spec.MAX_NONCE_SEQ),
            created: Account.NONEXISTENT,
            Spec.NONCE_MANAGER: Account(storage={}),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_legacy_nonce_exhaustion_halts_nested_approval(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Halt a legacy payment approval made by a nested call after its
    `CREATE` consumed the last nonce: only the call fails, the `SENDER`
    frame succeeds and a later `VERIFY` frame approves.
    """
    sender_nonce = Spec.MAX_NONCE_SEQ - 1
    frame_index = Op.TXPARAM(Spec8141.TXPARAM_CURRENT_FRAME_INDEX)
    nested_work = Op.POP(Op.CREATE(0, 0, 0)) + Op.APPROVE(
        0, 0, Op.FRAMEPARAM(frame_index, Spec8141.FRAMEPARAM_ALLOWED_SCOPE)
    )
    nested_call_gas = nested_work.gas_cost(fork)
    nested_call = Op.CALL(
        gas=nested_call_gas,
        address=Op.ADDRESS,
        args_size=1,
        # The first frame warmed both the sender and its delegate.
        address_warm=True,
        delegated_address=True,
        delegated_address_warm=True,
        new_memory_size=32,
    )
    measure_nested_call = CodeGasMeasure(
        code=nested_call, extra_stack_items=1, sstore_key=SLOT_RESULT
    )
    outer_work = measure_nested_call + Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    exhauster_code = Conditional(
        # Only the nested call has calldata.
        condition=Op.CALLDATASIZE,
        if_true=nested_work,
        if_false=delegated_sender_code(outer_work),
    )
    exhauster = pre.deploy_contract(code=exhauster_code)
    sender = pre.fund_eoa(nonce=sender_nonce, delegation=exhauster)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            sender_frame(
                flags=Spec8141.APPROVE_PAYMENT,
                gas_limit=nested_call_gas + exhauster_code.gas_cost(fork),
            ),
            verify_frame(flags=Spec8141.APPROVE_PAYMENT),
        ],
        nonce_keys=[0],
        nonce=sender_nonce,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
                # The halted call's `CREATE` state gas is refilled.
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    state_gas_used=outer_work.state_cost(fork),
                ),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
            ],
        ),
    )
    created = compute_create_address(address=sender, nonce=sender_nonce)
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=Spec.MAX_NONCE_SEQ,
                storage={
                    # The halt forfeits all of the call's gas.
                    SLOT_RESULT: nested_call.execution_cost(fork)
                    + nested_call_gas,
                    SLOT_EXECUTED: 1,
                },
            ),
            created: Account.NONEXISTENT,
            Spec.NONCE_MANAGER: Account(storage={}),
        },
    )


def test_nonce_manager_direct_call_reverts(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Revert a `CALL` and a `STATICCALL` to the nonce manager with empty
    return data, leaving its code and protocol-written slot in place.
    """
    storage = Storage()
    caller_code = (
        Op.SSTORE(
            storage.store_next(1),
            Op.ADD(1, Op.CALL(address=Spec.NONCE_MANAGER)),
        )
        + Op.SSTORE(storage.store_next(1), Op.ADD(1, Op.RETURNDATASIZE))
        + Op.SSTORE(
            storage.store_next(1),
            Op.ADD(1, Op.STATICCALL(address=Spec.NONCE_MANAGER)),
        )
        + Op.SSTORE(storage.store_next(1), Op.ADD(1, Op.RETURNDATASIZE))
        + Op.SSTORE(
            storage.store_next(len(Spec.NONCE_MANAGER_CODE)),
            Op.EXTCODESIZE(Spec.NONCE_MANAGER),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=caller,
                state_gas_limit=caller_code.state_cost(fork),
            ),
        ],
        nonce_keys=[NONCE_KEY],
        nonce=0,
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            caller: Account(storage=storage),
            Spec.NONCE_MANAGER: Account(
                nonce=Spec.NONCE_MANAGER_NONCE,
                code=Spec.NONCE_MANAGER_CODE,
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1},
            ),
        },
    )


def test_nonce_manager_stays_cold(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Pay the cold access for a `BALANCE` of the nonce manager after a
    keyed approval, which warms nothing.
    """
    first_use = keyed_nonce_first_use(fork)
    measured = Op.BALANCE(address=Spec.NONCE_MANAGER, address_warm=False)
    access_gas = Op.BALANCE(address_warm=False).gas_cost(fork)
    probe_code = CodeGasMeasure(
        code=measured,
        overhead_cost=measured.gas_cost(fork) - access_gas,
        extra_stack_items=1,
        sstore_key=SLOT_RESULT,
    )
    probe = pre.deploy_contract(code=probe_code)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), default_frame(target=probe)],
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                default_verify_receipt(fork, first_use),
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    gas_used=fork.gas_costs().COLD_ACCOUNT_ACCESS
                    + probe_code.execution_cost(fork),
                    state_gas_used=probe_code.state_cost(fork),
                ),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage={SLOT_RESULT: access_gas})},
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("changed_field", ["keys", "sequence"])
@pytest.mark.parametrize(
    "resign",
    [pytest.param(False, marks=pytest.mark.exception_test), True],
)
def test_signature_binds_nonce_fields(
    state_test: StateTestFiller,
    pre: Alloc,
    changed_field: str,
    resign: bool,
) -> None:
    """Reject changed nonce fields unless the sender signs them again."""
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=0,
    )
    tx.sign()
    changed_keys = (
        [NONCE_KEY, OTHER_KEY] if changed_field == "keys" else [NONCE_KEY]
    )
    changed_seq = 1 if changed_field == "sequence" else 0
    slots = used_key_slots(sender, {NONCE_KEY: 1}) if changed_seq else {}
    if slots:
        nonce_manager_with_slots(pre, slots)
    tx = tx.copy(nonce_keys=changed_keys, nonce=changed_seq)
    if resign:
        tx.signatures = None
        slots = {
            keyed_nonce_slot(sender, key): changed_seq + 1
            for key in changed_keys
        }
    else:
        # Recovery over the changed digest no longer yields the signer.
        tx.error = TransactionException.TYPE_6_INVALID_FRAME_FORMAT
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=0),
            Spec.NONCE_MANAGER: Account(storage=slots),
        },
    )


@pytest.mark.parametrize("revert_outer", [False, True])
def test_nested_approval_follows_enclosing_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    revert_outer: bool,
) -> None:
    """Commit a nested approval only when its enclosing frame succeeds."""
    first_use = keyed_nonce_first_use(fork)
    approver = pre.deploy_contract(
        Conditional(
            condition=Op.CALLDATASIZE,
            if_true=Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT),
            if_false=Op.POP(Op.CALL(address=Op.ADDRESS, args_size=1))
            + (Op.REVERT(0, 0) if revert_outer else Op.STOP),
        )
    )
    sender = pre.fund_eoa(delegation=approver)
    frames = [
        default_frame(
            target=sender,
            flags=Spec8141.APPROVE_EXECUTION_AND_PAYMENT,
            state_gas_limit=first_use,
        )
    ]
    receipts = [
        FrameReceipt(
            status=Spec8141.STATUS_FAILURE
            if revert_outer
            else Spec8141.STATUS_SUCCESS,
            state_gas_used=0 if revert_outer else first_use,
        )
    ]
    if revert_outer:
        frames.append(verify_frame(data=b"\x01", state_gas_limit=first_use))
        receipts.append(
            FrameReceipt(
                status=Spec8141.STATUS_SUCCESS, state_gas_used=first_use
            )
        )
    tx = Transaction(
        sender=sender,
        frames=frames,
        nonce_keys=[NONCE_KEY],
        nonce=0,
        expected_receipt=TransactionReceipt(
            payer=sender, frame_receipts=receipts
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            Spec.NONCE_MANAGER: Account(
                storage={keyed_nonce_slot(sender, NONCE_KEY): 1}
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "sender_nonce",
    [
        3,
        Spec.MAX_NONCE_SEQ - 2,
        pytest.param(
            Spec.MAX_NONCE_SEQ - 1,
            id="overflow_halts_verify",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_legacy_approval_increments_live_nonce(
    state_test: StateTestFiller, pre: Alloc, sender_nonce: int
) -> None:
    """
    Keep a successful CREATE nonce increment when payment is approved,
    and invalidate the transaction when the approval would overflow it.
    """
    creator = pre.deploy_contract(
        delegated_sender_code(Op.POP(Op.CREATE(0, 0, 0)) + Op.STOP)
    )
    sender = pre.fund_eoa(nonce=sender_nonce, delegation=creator)
    overflows = sender_nonce + 2 > Spec.MAX_NONCE_SEQ
    tx = Transaction(
        sender=sender,
        nonce_keys=[0],
        nonce=sender_nonce,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            sender_frame(),
            verify_frame(flags=Spec8141.APPROVE_PAYMENT),
        ],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if overflows
            else None
        ),
    )
    if not overflows:
        tx.expected_receipt = TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS) for _ in range(3)
            ],
        )
    created = compute_create_address(address=sender, nonce=sender_nonce)
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=sender_nonce if overflows else sender_nonce + 2
            ),
            created: Account.NONEXISTENT if overflows else Account(nonce=1),
            Spec.NONCE_MANAGER: Account(storage={}),
        },
    )
