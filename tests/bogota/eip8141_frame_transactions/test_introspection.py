"""
Tests for the introspection instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`TXPARAM`, `FRAMEDATALOAD`, `FRAMEDATACOPY`, `FRAMEPARAM`, `SIGPARAM`
and `SIGDATACOPY` are exercised from a `DEFAULT` frame that stores what
it reads, so the post state pins the value each selector returns.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    DEFAULT_FRAME_GAS_LIMIT,
    DEFAULT_FRAME_STATE_GAS_LIMIT,
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import (
    APPROVE_ALL,
    CURRENT_FRAME_INDEX,
    FrameTransaction,
    default_frame,
    sender_frame,
    storage_set_cost,
    verify_frame,
)
from .signature_helpers import (
    DIGEST,
    P256_SIGNER,
    signed_digest_entry,
    valid_p256_entry,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_RESULT = 0x01
"""Storage slot the probe contract writes what it read into."""

PROBE_FRAME_DATA = Bytes(bytes(range(1, 41)))
"""Data of the probe frame: 40 bytes, so a word read is truncated."""

PROBE_FRAME_GAS = 500_000
"""Execution gas budget of the probe frames."""

PROBE_FRAME_STATE_GAS = 200_000
"""
State gas budget of the probe frames, distinct from the framework
default so a probe reading its own frame's budget pins the right one.
"""

MAX_PRIORITY_FEE = 7
MAX_FEE = 1_000_000_000

ARBITRARY_WITNESS = Bytes(b"\xab" * 5)


def probe_transaction(
    sender: EOA,
    probe: Address,
    signatures: List[FrameSignature] | None = None,
) -> Transaction:
    """
    Return a two frame transaction: a `VERIFY` frame approving through
    the sender's default code, followed by a `DEFAULT` frame calling
    the probe contract at index 1.
    """
    return Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
                data=PROBE_FRAME_DATA,
            ),
        ],
        signatures=signatures,
    )


@pytest.mark.parametrize(
    "param,expected",
    [
        pytest.param(Spec.TXPARAM_TYPE, Spec.FRAME_TX_TYPE, id="type"),
        pytest.param(Spec.TXPARAM_NONCE, 0, id="nonce"),
        pytest.param(
            Spec.TXPARAM_MAX_PRIORITY_FEE_PER_GAS,
            MAX_PRIORITY_FEE,
            id="priority_fee",
        ),
        pytest.param(Spec.TXPARAM_MAX_FEE, MAX_FEE, id="max_fee"),
        pytest.param(Spec.TXPARAM_BLOB_COUNT, 0, id="blob_count"),
        pytest.param(Spec.TXPARAM_FRAME_COUNT, 2, id="frame_count"),
        pytest.param(Spec.TXPARAM_CURRENT_FRAME_INDEX, 1, id="frame_index"),
        pytest.param(Spec.TXPARAM_SIGNATURE_COUNT, 1, id="signature_count"),
    ],
)
def test_txparam(
    state_test: StateTestFiller,
    pre: Alloc,
    param: int,
    expected: int,
) -> None:
    """Read transaction scoped information through `TXPARAM`."""
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.TXPARAM(param)) + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_txparam_sender_and_sig_hash(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the sender and the canonical signature hash through `TXPARAM`.

    The canonical hash covers the raw signature bytes of the entry
    signing it, so its value is not known when the test is authored and
    the probe can only pin that it reads back nonzero. The `msg`
    readback of an explicit-digest entry, by contrast, is pinned to the
    exact digest the entry was verified over.
    """
    explicit_msg = Bytes(b"\x5a" * 32)
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.TXPARAM(Spec.TXPARAM_SENDER))
        + Op.SSTORE(
            SLOT_RESULT + 1,
            Op.ISZERO(Op.TXPARAM(Spec.TXPARAM_SIG_HASH)),
        )
        + Op.SSTORE(SLOT_RESULT + 2, Op.SIGPARAM(1, Spec.SIGPARAM_MSG))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(
            sender,
            probe,
            signatures=[
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)
                ),
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1,
                    signer=Bytes(sender),
                    msg=explicit_msg,
                ),
            ],
        ),
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: sender,
                    SLOT_RESULT + 1: 0,
                    SLOT_RESULT + 2: int.from_bytes(explicit_msg, "big"),
                }
            )
        },
    )


def test_txparam_state_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read the executing frame's remaining state gas pool through
    `TXPARAM`, before and after a write that draws from it.

    The first read happens before any state charge, so it reports the
    frame's full budget; the write storing it creates a fresh slot, so
    the second read reports the budget less that slot's creation.
    """
    sender = pre.fund_eoa()
    first_write = Op.SSTORE(
        SLOT_RESULT, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)
    )
    probe = pre.deploy_contract(
        code=first_write
        + Op.SSTORE(SLOT_RESULT + 1, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: PROBE_FRAME_STATE_GAS,
                    SLOT_RESULT + 1: PROBE_FRAME_STATE_GAS
                    - first_write.state_cost(fork),
                }
            )
        },
    )


@pytest.mark.parametrize(
    "frame_index,param,expected",
    [
        pytest.param(0, Spec.FRAMEPARAM_MODE, Spec.MODE_VERIFY, id="mode"),
        pytest.param(
            0,
            Spec.FRAMEPARAM_FLAGS,
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="flags",
        ),
        pytest.param(
            0,
            Spec.FRAMEPARAM_ALLOWED_SCOPE,
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="allowed_scope",
        ),
        pytest.param(0, Spec.FRAMEPARAM_DATA_LENGTH, 0, id="empty_data"),
        pytest.param(
            0,
            Spec.FRAMEPARAM_EXECUTION_GAS_LIMIT,
            DEFAULT_FRAME_GAS_LIMIT,
            id="gas_limit",
        ),
        pytest.param(
            0,
            Spec.FRAMEPARAM_STATE_GAS_LIMIT,
            DEFAULT_FRAME_STATE_GAS_LIMIT,
            id="state_gas_limit",
        ),
        pytest.param(0, Spec.FRAMEPARAM_ATOMIC_BATCH, 0, id="atomic_batch"),
        pytest.param(
            0,
            Spec.FRAMEPARAM_STATUS,
            Spec.STATUS_SUCCESS,
            id="status_of_earlier_frame",
        ),
        pytest.param(
            1,
            Spec.FRAMEPARAM_DATA_LENGTH,
            len(PROBE_FRAME_DATA),
            id="data_length",
        ),
        pytest.param(1, Spec.FRAMEPARAM_VALUE, 0, id="value"),
        pytest.param(
            1,
            Spec.FRAMEPARAM_EXECUTION_GAS_LIMIT,
            PROBE_FRAME_GAS,
            id="own_gas_limit",
        ),
        pytest.param(
            1,
            Spec.FRAMEPARAM_STATE_GAS_LIMIT,
            PROBE_FRAME_STATE_GAS,
            id="own_state_gas_limit",
        ),
    ],
)
def test_frameparam(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    param: int,
    expected: int,
) -> None:
    """
    Read frame scoped information through `FRAMEPARAM`.

    Unlike the receipt-reported selectors, a frame's declared budgets
    are static data: reading the executing frame's own state gas
    budget is allowed.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.FRAMEPARAM(frame_index, param))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_frameparam_resolved_target(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    `FRAMEPARAM` reports the resolved target, so a frame with an empty
    target reads back as the transaction sender.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT, Op.FRAMEPARAM(0, Spec.FRAMEPARAM_RESOLVED_TARGET)
        )
        + Op.SSTORE(
            SLOT_RESULT + 1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_RESOLVED_TARGET)
        )
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={
            probe: Account(
                storage={SLOT_RESULT: sender, SLOT_RESULT + 1: probe}
            )
        },
    )


def test_frameparam_atomic_batch_set(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the atomic batch flag of a frame that carries it back as one
    through `FRAMEPARAM`, both via the dedicated selector and the raw
    flags.

    A flagged frame cannot be the transaction's last, so a `DEFAULT`
    frame targeting the sender trails the batch.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_ATOMIC_BATCH)
        )
        + Op.SSTORE(SLOT_RESULT + 1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_FLAGS))
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
            ),
            default_frame(),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: 1,
                    SLOT_RESULT + 1: Spec.ATOMIC_BATCH_FLAG,
                }
            )
        },
    )


def test_frameparam_gas_used(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read a completed frame's receipt gas usage — both dimensions —
    through `FRAMEPARAM`.

    A worker frame performs one fresh storage write, so its receipt
    reports the frame entry's cold target access plus the write's
    execution gas in one dimension and the slot's creation in the
    other.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT_RESULT, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    probe_code = (
        Op.SSTORE(
            SLOT_RESULT,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_EXECUTION_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_RESULT + 1,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    worker_frame = default_frame(target=worker, code=worker_code)
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            worker_frame,
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
            ),
        ],
    )

    worker_receipt = worker_frame.receipt(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            worker: Account(storage={SLOT_RESULT: 1}),
            probe: Account(
                storage={
                    SLOT_RESULT: worker_receipt.gas_used,
                    SLOT_RESULT + 1: worker_receipt.state_gas_used,
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "frame_index,param",
    [
        pytest.param(1, Spec.FRAMEPARAM_STATUS, id="status_of_current_frame"),
        pytest.param(
            1,
            Spec.FRAMEPARAM_EXECUTION_GAS_USED,
            id="execution_gas_used_of_current_frame",
        ),
        pytest.param(
            1,
            Spec.FRAMEPARAM_STATE_GAS_USED,
            id="state_gas_used_of_current_frame",
        ),
        pytest.param(2, Spec.FRAMEPARAM_MODE, id="frame_index_out_of_bounds"),
        pytest.param(0, 0x0C, id="undefined_param"),
    ],
)
def test_frameparam_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    param: int,
) -> None:
    """
    `FRAMEPARAM` halts exceptionally on the receipt-reported selectors
    — status and gas usage — of the current frame, an out of bounds
    frame index, and an undefined selector. The halt fails the frame
    without invalidating the transaction, because the frame does not
    run in `VERIFY` mode.

    The probe writes a marker before the halting read, so a selector
    that returned zero instead of halting would leave the marker
    behind.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF)
        + Op.POP(Op.FRAMEPARAM(frame_index, param))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: 0})},
    )


@pytest.mark.parametrize(
    "halting_read",
    [
        pytest.param(
            Op.POP(Op.TXPARAM(0x0D)),
            id="txparam_undefined_param",
        ),
        # The per-gas and per-blob-gas fee caps and the maximum cost
        # selectors were removed with the `max_fee` budget.
        pytest.param(
            Op.POP(Op.TXPARAM(0x05)),
            id="txparam_removed_max_fee_per_blob_gas",
        ),
        pytest.param(
            Op.POP(Op.TXPARAM(0x06)),
            id="txparam_removed_max_cost",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, 0x04)),
            id="sigparam_undefined_copy_param",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, 0x05)),
            id="sigparam_undefined_param",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, Spec.SIGPARAM_SIGNATURE_LENGTH)),
            id="sigparam_length_of_protocol_validated_entry",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_SCHEME)),
            id="sigparam_signature_index_out_of_bounds",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 32, 1),
            id="sigdatacopy_signature_index_out_of_bounds",
        ),
        pytest.param(
            Op.POP(Op.FRAMEDATALOAD(0, 2)),
            id="framedataload_frame_index_out_of_bounds",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 32, 2),
            id="framedatacopy_frame_index_out_of_bounds",
        ),
    ],
)
def test_introspection_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    halting_read: Bytecode,
) -> None:
    """
    `TXPARAM`, `SIGPARAM`, `SIGDATACOPY`, `FRAMEDATALOAD` and
    `FRAMEDATACOPY` halt exceptionally on undefined selectors, out of
    bounds indices, and the signature length of a protocol-validated
    entry — the raw signature bytes the protocol validates are not
    introspectable, their length included. `SIGPARAM`'s former copy
    selector (`0x04`) is undefined. The halt fails the frame without
    invalidating the transaction, because the frame does not run in
    `VERIFY` mode.

    The probe transaction carries two frames and one protocol-validated
    signature entry, so frame index 2 and signature index 1 are the
    first indices out of bounds. The probe writes a marker before the
    halting read, so a read that returned a value instead of halting
    would leave the marker behind.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF) + halting_read + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: 0})},
    )


@pytest.mark.parametrize(
    "frame_index,offset,expected",
    [
        pytest.param(
            1,
            0,
            int.from_bytes(PROBE_FRAME_DATA[0:32], "big"),
            id="first_word",
        ),
        pytest.param(
            1,
            32,
            int.from_bytes(PROBE_FRAME_DATA[32:].ljust(32, b"\x00"), "big"),
            id="tail_zero_padded",
        ),
        pytest.param(1, 64, 0, id="past_the_end"),
        pytest.param(0, 0, 0, id="empty_frame_data"),
    ],
)
def test_framedataload(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    offset: int,
    expected: int,
) -> None:
    """
    Read a word of a frame's data through `FRAMEDATALOAD`, including
    reads that run past the end and read as zeroes.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.FRAMEDATALOAD(offset, frame_index))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_framedatacopy(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Copy a frame's data into memory through `FRAMEDATACOPY`, including
    a copy that straddles the end of the data and is zero filled.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.FRAMEDATACOPY(0, 0, 32, 1)
        + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0))
        + Op.FRAMEDATACOPY(32, 32, 32, 1)
        + Op.SSTORE(SLOT_RESULT + 1, Op.MLOAD(32))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={
            probe: Account(
                storage={
                    SLOT_RESULT: int.from_bytes(PROBE_FRAME_DATA[0:32], "big"),
                    SLOT_RESULT + 1: int.from_bytes(
                        PROBE_FRAME_DATA[32:].ljust(32, b"\x00"), "big"
                    ),
                }
            )
        },
    )


@pytest.mark.parametrize(
    "signature_index,param,expected",
    [
        pytest.param(
            0,
            Spec.SIGPARAM_SCHEME,
            Spec.SCHEME_SECP256K1,
            id="secp256k1_scheme",
        ),
        pytest.param(0, Spec.SIGPARAM_MSG, 0, id="canonical_hash_msg"),
        pytest.param(
            1,
            Spec.SIGPARAM_SCHEME,
            Spec.SCHEME_ARBITRARY,
            id="arbitrary_scheme",
        ),
        pytest.param(
            1,
            Spec.SIGPARAM_SIGNATURE_LENGTH,
            len(ARBITRARY_WITNESS),
            id="arbitrary_length",
        ),
    ],
)
def test_sigparam(
    state_test: StateTestFiller,
    pre: Alloc,
    signature_index: int,
    param: int,
    expected: int,
) -> None:
    """Read signature scoped metadata through `SIGPARAM`."""
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, Op.SIGPARAM(signature_index, param))
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(
            sender,
            probe,
            signatures=[
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)
                ),
                FrameSignature(
                    scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
                ),
            ],
        ),
        post={probe: Account(storage={SLOT_RESULT: expected})},
    )


def test_sigparam_resolved_signer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the resolved signer of a protocol-validated entry through
    `SIGPARAM`, and check the same read against an `ARBITRARY` entry
    halts the frame instead: the protocol assigns no signer to bytes
    it does not validate.

    The refused probe writes a marker before the halting read, so a
    read that returned a value instead of halting would leave the
    marker behind.
    """
    sender = pre.fund_eoa()
    resolved = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT, Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER)
        )
        + Op.STOP
    )
    refused = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 0xFF)
        + Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_RESOLVED_SIGNER))
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                target=resolved,
                gas_limit=PROBE_FRAME_GAS,
            ),
            default_frame(
                target=refused,
                gas_limit=PROBE_FRAME_GAS,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            resolved: Account(storage={SLOT_RESULT: sender}),
            refused: Account(storage={SLOT_RESULT: 0}),
        },
    )


def test_sigdatacopy(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Copy an `ARBITRARY` entry's raw signature bytes into memory
    through `SIGDATACOPY`, including the zero fill past the end of the
    signature, and check that the same copy against a protocol
    validated entry halts the frame instead.
    """
    sender = pre.fund_eoa()
    copied = pre.deploy_contract(
        code=Op.SIGDATACOPY(0, 0, 32, 1)
        + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0))
        + Op.STOP
    )
    refused = pre.deploy_contract(
        code=Op.SIGDATACOPY(0, 0, 32, 0) + Op.SSTORE(SLOT_RESULT, 1) + Op.STOP
    )

    signatures = [
        FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
        ),
    ]

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
        max_fee=MAX_FEE,
        frames=[
            verify_frame(),
            default_frame(
                target=copied,
                gas_limit=PROBE_FRAME_GAS,
            ),
            default_frame(
                target=refused,
                gas_limit=PROBE_FRAME_GAS,
            ),
        ],
        signatures=signatures,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            copied: Account(
                storage={
                    SLOT_RESULT: int.from_bytes(
                        bytes(ARBITRARY_WITNESS).ljust(32, b"\x00"), "big"
                    )
                }
            ),
            refused: Account(storage={SLOT_RESULT: 0}),
        },
    )


ARBITRARY_MSG = Bytes(b"\x5a" * 32)
"""Explicit `msg` of an `ARBITRARY` signature entry."""

FRAME_VALUE = 123
"""Value a value-bearing `SENDER` frame carries."""

SLOT_SIGNER = 0x00
"""Base of the slots recording each entry's resolved signer."""

SLOT_SCHEME = 0x10
"""Base of the slots recording each entry's scheme, plus one."""

SLOT_MSG = 0x20
"""Base of the slots recording each entry's `msg`, plus one."""


def test_sigparam_reads_every_scheme(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read the resolved signer, scheme and `msg` of four entries: the
    sender's secp256k1 entry with an empty signer and `msg`, a
    secp256k1 entry from another key with an explicit signer and
    `msg`, a P256 entry, and an `ARBITRARY` entry with a `msg`.

    EIP-8141 §Transaction Signatures: "For `SECP256K1` and `P256`, the
    `signer` is a 20-byte Ethereum address. If absent, `tx.sender` is
    used (for introspections as well)." and "The explicit 32-byte zero
    digest is invalid. This reserves the zero stack value as the
    EVM-visible representation of the transaction signing hash case."
    §`SIGPARAM`: `SIGPARAM_RESOLVED_SIGNER` returns `resolved_signer`,
    `SIGPARAM_SCHEME` returns `scheme`, `SIGPARAM_MSG` returns `msg`.
    `ARBITRARY` entries have no resolved signer, so theirs is not read.

    Scheme and `msg` are stored plus one, since `ARBITRARY` is scheme 0
    and an empty `msg` reads as 0.
    """
    sender = pre.fund_eoa()
    other = pre.fund_eoa()
    assert other.key is not None
    signatures = [
        FrameSignature(scheme=Spec.SCHEME_SECP256K1, secret_key=sender.key),
        signed_digest_entry(other.key, signer=Bytes(other)),
        valid_p256_entry(),
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            msg=ARBITRARY_MSG,
            signature=ARBITRARY_WITNESS,
        ),
    ]
    signers: List[Address | Bytes] = [sender, other, P256_SIGNER]
    schemes = [
        Spec.SCHEME_SECP256K1,
        Spec.SCHEME_SECP256K1,
        Spec.SCHEME_P256,
        Spec.SCHEME_ARBITRARY,
    ]
    msgs = [0, int.from_bytes(DIGEST, "big"), int.from_bytes(DIGEST, "big")]
    msgs.append(int.from_bytes(ARBITRARY_MSG, "big"))

    probe_code = Bytecode()
    expected: Dict[int, int] = {}
    for index in range(len(signatures)):
        if index < len(signers):
            probe_code += Op.SSTORE(
                SLOT_SIGNER + index,
                Op.SIGPARAM(index, Spec.SIGPARAM_RESOLVED_SIGNER),
            )
            expected[SLOT_SIGNER + index] = int.from_bytes(
                bytes(signers[index]), "big"
            )
        probe_code += Op.SSTORE(
            SLOT_SCHEME + index,
            Op.ADD(1, Op.SIGPARAM(index, Spec.SIGPARAM_SCHEME)),
        ) + Op.SSTORE(
            SLOT_MSG + index, Op.ADD(1, Op.SIGPARAM(index, Spec.SIGPARAM_MSG))
        )
        expected[SLOT_SCHEME + index] = int(schemes[index]) + 1
        expected[SLOT_MSG + index] = msgs[index] + 1
    probe_code += Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit_delta=fork.gas_costs().CALL_STIPEND + 1,
                state_gas_limit_delta=0,
            ),
        ],
        signatures=signatures,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage=expected)},
    )


@pytest.mark.pre_alloc_mutable
def test_txparam_nonce_is_the_transaction_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    After the sender's approval incremented its account nonce, read
    `TXPARAM_NONCE`: it still reports the transaction's nonce.

    EIP-8141 §`TXPARAM`: `TXPARAM_NONCE` returns `nonce`, the
    transaction field. §`APPROVE` Behavior increments "the sender's
    nonce" in the state, which is one higher by the time the probe
    runs.
    """
    tx_nonce = 5
    sender = pre.fund_eoa(nonce=tx_nonce)
    probe_code = (
        Op.SSTORE(SLOT_SIGNER, Op.TXPARAM(Spec.TXPARAM_NONCE)) + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=tx_nonce,
        frames=[
            verify_frame(),
            default_frame(target=probe, code=probe_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=tx_nonce + 1),
            probe: Account(storage={SLOT_SIGNER: tx_nonce}),
        },
    )


def test_frameparam_allowed_scope_masks_batch_flag(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A probe in an atomic batch frame reads its own allowed scope and
    flags, and the first frame's: the allowed scope drops the batch
    flag, which the flags keep.

    EIP-8141 §`FRAMEPARAM`: `FRAMEPARAM_ALLOWED_SCOPE` returns
    "`allowed_scope` (`frame.flags & APPROVE_SCOPE_MASK`)" and
    `FRAMEPARAM_FLAGS` returns `flags`. The probe's flags are
    `ATOMIC_BATCH_FLAG` alone, so its allowed scope is 0; values are
    stored plus one.
    """
    sender = pre.fund_eoa()
    probe_code = Bytecode()
    for index in (0, 1):
        probe_code += Op.SSTORE(
            index,
            Op.ADD(1, Op.FRAMEPARAM(index, Spec.FRAMEPARAM_ALLOWED_SCOPE)),
        ) + Op.SSTORE(
            0x10 + index,
            Op.ADD(1, Op.FRAMEPARAM(index, Spec.FRAMEPARAM_FLAGS)),
        )
    probe_code += Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=probe,
                code=probe_code,
                gas_limit_delta=fork.gas_costs().CALL_STIPEND + 1,
            ),
            # The batch terminator, codeless at the warm sender.
            default_frame(target=sender, warm=True),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    0: Spec.APPROVE_EXECUTION_AND_PAYMENT + 1,
                    1: 1,
                    0x10: Spec.APPROVE_EXECUTION_AND_PAYMENT + 1,
                    0x11: Spec.ATOMIC_BATCH_FLAG + 1,
                }
            )
        },
    )


SLOT_MODE = 0x00
"""Base of the slots recording each frame's mode, plus one."""

SLOT_VALUE = 0x10
"""Base of the slots recording each frame's value, plus one."""


def test_frameparam_mode_and_value_of_own_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    One probe runs in a `SENDER` frame carrying value and in a
    `DEFAULT` frame, and each time records its own frame's mode and
    value, keyed by its frame index.

    EIP-8141 §`FRAMEPARAM`: `FRAMEPARAM_MODE` returns `mode` and
    `FRAMEPARAM_VALUE` returns `value`. §Mode: mode 0 is `DEFAULT`, 2
    is `SENDER`. Values are stored plus one, since the
    `DEFAULT` frame's mode and value are both 0.
    """
    sender = pre.fund_eoa()
    probe_code = (
        Op.SSTORE(
            Op.ADD(SLOT_MODE, CURRENT_FRAME_INDEX),
            Op.ADD(
                1, Op.FRAMEPARAM(CURRENT_FRAME_INDEX, Spec.FRAMEPARAM_MODE)
            ),
        )
        + Op.SSTORE(
            Op.ADD(SLOT_VALUE, CURRENT_FRAME_INDEX),
            Op.ADD(
                1, Op.FRAMEPARAM(CURRENT_FRAME_INDEX, Spec.FRAMEPARAM_VALUE)
            ),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                target=probe,
                value=FRAME_VALUE,
                code=probe_code,
                logs=[transfer_log(sender, probe, FRAME_VALUE)],
            ),
            default_frame(target=probe, code=probe_code, warm=True),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                balance=FRAME_VALUE,
                storage={
                    SLOT_MODE + 1: Spec.MODE_SENDER + 1,
                    SLOT_VALUE + 1: FRAME_VALUE + 1,
                    SLOT_MODE + 2: Spec.MODE_DEFAULT + 1,
                    SLOT_VALUE + 2: 1,
                },
            )
        },
    )


SLOT_REFILLED = 0x05
"""Storage slot the first frame creates and the second clears."""

SLOT_BEFORE_REFILL = 0x10
"""Slot recording the first frame's state gas before the refill."""

SLOT_AFTER_REFILL = 0x11
"""Slot recording the first frame's state gas after the refill."""


def test_frameparam_state_gas_used_is_live(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Frame 1 creates a storage slot; frame 2 reads frame 1's state gas,
    clears the slot, and reads it again; frame 3 reads both frames'
    state gas. The refill lowers frame 1's reported state gas at once,
    inside frame 2, not at the end of frame 2.

    EIP-8141 §`FRAMEPARAM`, Notes: "The `gas_used.execution` (0x0A)
    and `gas_used.state` (0x0B) fields return the current values
    recorded in the frame's receipt. [...] A completed frame's
    `gas_used.state` may subsequently decrease when another frame
    refills state gas attributed to it". §Receipt Encoding: "A later
    frame may therefore reduce an earlier frame's `gas_used.state`."

    Frame 2's two records create two slots of its own, which frame 3
    reads back as frame 2's state gas. Values are stored plus one.
    """
    sender = pre.fund_eoa()
    slot_gas = storage_set_cost(fork)
    read_first = Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED))
    clearer = (
        Op.SSTORE(SLOT_BEFORE_REFILL, read_first)
        + Op.SSTORE(SLOT_REFILLED, 0)
        + Op.SSTORE(SLOT_AFTER_REFILL, read_first)
    )
    # The first frame supplies no calldata, the second one byte.
    worker_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=clearer + Op.STOP,
        if_false=Op.SSTORE(SLOT_REFILLED, 1) + Op.STOP,
    )
    worker = pre.deploy_contract(code=worker_code)
    probe_code = (
        Op.SSTORE(1, read_first)
        + Op.SSTORE(
            2, Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATE_GAS_USED))
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            # Frame 2's refill leaves frame 1 with no state gas.
            default_frame(target=worker, pin_gas=False, state_gas_used=0),
            default_frame(
                target=worker,
                data=Bytes(b"\x01"),
                pin_gas=False,
                state_gas_used=2 * slot_gas,
            ),
            default_frame(
                target=probe, pin_gas=False, state_gas_used=2 * slot_gas
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            worker: Account(
                storage={
                    SLOT_REFILLED: 0,
                    SLOT_BEFORE_REFILL: slot_gas + 1,
                    SLOT_AFTER_REFILL: 1,
                }
            ),
            probe: Account(storage={1: 1, 2: 2 * slot_gas + 1}),
        },
    )


def test_txparam_current_frame_index_in_every_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read `TXPARAM_CURRENT_FRAME_INDEX` in a `VERIFY` frame and in three
    `DEFAULT` frames running the same probe: each read is the index of
    the frame running it.

    EIP-8141 §`TXPARAM`: `TXPARAM_CURRENT_FRAME_INDEX` returns the
    "currently executing frame index". The contract sender's `VERIFY`
    frame approves only if it reads 0; the probe records, under its
    frame's index, that index plus one.
    """
    sender_code = Conditional(
        condition=Op.ISZERO(CURRENT_FRAME_INDEX),
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)
    probe_code = (
        Op.SSTORE(CURRENT_FRAME_INDEX, Op.ADD(1, CURRENT_FRAME_INDEX))
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)
    probe_frames = [1, 2, 3]

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(pin_gas=False),
            *(
                default_frame(
                    target=probe,
                    pin_gas=False,
                    state_gas_used=probe_code.state_cost(fork),
                )
                for _ in probe_frames
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            probe: Account(
                storage={index: index + 1 for index in probe_frames}
            ),
        },
    )
