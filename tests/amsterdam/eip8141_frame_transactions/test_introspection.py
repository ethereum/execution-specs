"""
Tests for the introspection instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`TXPARAM`, `FRAMEDATALOAD`, `FRAMEDATACOPY`, `FRAMEPARAM` and `SIGPARAM`
are exercised from a `DEFAULT` frame that stores what it reads, so the
post state pins the value each selector returns.
"""

from typing import List

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Frame,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_RESULT = 0x01
"""Storage slot the probe contract writes what it read into."""

PROBE_FRAME_DATA = Bytes(bytes(range(1, 41)))
"""Data of the probe frame: 40 bytes, so a word read is truncated."""

# A fresh SSTORE costs STATE_BYTES_PER_STORAGE_SET * COST_PER_STATE_BYTE
# of state gas under EIP-8037, and a frame transaction holds no state
# gas reservoir, so a probe writing two slots needs room for both.
PROBE_FRAME_GAS = 500_000

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
        max_fee_per_gas=MAX_FEE,
        frames=[
            verify_frame(),
            Frame(
                mode=Spec.MODE_DEFAULT,
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
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
            Spec.TXPARAM_MAX_PRIORITY_FEE, MAX_PRIORITY_FEE, id="priority_fee"
        ),
        pytest.param(Spec.TXPARAM_MAX_FEE, MAX_FEE, id="max_fee"),
        pytest.param(Spec.TXPARAM_MAX_BLOB_FEE, 0, id="max_blob_fee"),
        pytest.param(Spec.TXPARAM_BLOB_COUNT, 0, id="blob_count"),
        pytest.param(Spec.TXPARAM_FRAME_COUNT, 2, id="frame_count"),
        pytest.param(Spec.TXPARAM_FRAME_INDEX, 1, id="frame_index"),
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


def test_txparam_max_cost(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Check `TXPARAM`'s max cost selector against the payer's escrow.

    The maximum cost is charged to the payer in full when payment is
    approved and the surplus is only refunded at settlement, so during
    frame execution the sender's balance is short of its funding by
    exactly the value the selector reports.
    """
    sender_funds = 10**18
    sender = pre.fund_eoa(amount=sender_funds)
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_RESULT,
            Op.EQ(
                Op.TXPARAM(Spec.TXPARAM_MAX_COST),
                Op.SUB(
                    sender_funds,
                    Op.BALANCE(Op.TXPARAM(Spec.TXPARAM_SENDER)),
                ),
            ),
        )
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=probe_transaction(sender, probe),
        post={probe: Account(storage={SLOT_RESULT: 1})},
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
        pytest.param(0, Spec.FRAMEPARAM_GAS_LIMIT, 100_000, id="gas_limit"),
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
            1, Spec.FRAMEPARAM_GAS_LIMIT, PROBE_FRAME_GAS, id="own_gas_limit"
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
    """Read frame scoped information through `FRAMEPARAM`."""
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
        code=Op.SSTORE(SLOT_RESULT, Op.FRAMEPARAM(0, Spec.FRAMEPARAM_TARGET))
        + Op.SSTORE(SLOT_RESULT + 1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_TARGET))
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
        max_fee_per_gas=MAX_FEE,
        frames=[
            verify_frame(),
            Frame(
                mode=Spec.MODE_DEFAULT,
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
            ),
            Frame(
                mode=Spec.MODE_DEFAULT,
                gas_limit=100_000,
            ),
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


@pytest.mark.parametrize(
    "frame_index,param",
    [
        pytest.param(1, Spec.FRAMEPARAM_STATUS, id="status_of_current_frame"),
        pytest.param(2, Spec.FRAMEPARAM_MODE, id="frame_index_out_of_bounds"),
        pytest.param(0, 0x09, id="undefined_param"),
    ],
)
def test_frameparam_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_index: int,
    param: int,
) -> None:
    """
    `FRAMEPARAM` halts exceptionally on the status of the current
    frame, an out of bounds frame index, and an undefined selector.
    The halt fails the frame without invalidating the transaction,
    because the frame does not run in `VERIFY` mode.

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
            Op.POP(Op.TXPARAM(0x0C)),
            id="txparam_undefined_param",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0, 0x05)),
            id="sigparam_undefined_param",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_SCHEME)),
            id="sigparam_signature_index_out_of_bounds",
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
    `TXPARAM`, `SIGPARAM`, `FRAMEDATALOAD` and `FRAMEDATACOPY` halt
    exceptionally on undefined selectors and out of bounds indices.
    The halt fails the frame without invalidating the transaction,
    because the frame does not run in `VERIFY` mode.

    The probe transaction carries two frames and one signature entry,
    so frame index 2 and signature index 1 are the first indices out
    of bounds. The probe writes a marker before the halting read, so
    a read that returned a value instead of halting would leave the
    marker behind.
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
        pytest.param(
            0, Spec.SIGPARAM_SIGNATURE_LENGTH, 65, id="secp256k1_length"
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
        max_fee_per_gas=MAX_FEE,
        frames=[
            verify_frame(),
            Frame(
                mode=Spec.MODE_DEFAULT,
                target=resolved,
                gas_limit=PROBE_FRAME_GAS,
            ),
            Frame(
                mode=Spec.MODE_DEFAULT,
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


def sigparam_copy(
    signature_index: int,
    param: int,
    mem_offset: int,
    data_offset: int,
    length: int,
) -> Bytecode:
    """
    Return bytecode for `SIGPARAM`'s copy operation, whose five stack
    operands the opcode helper does not model.
    """
    return (
        Op.PUSH1(length)
        + Op.PUSH1(data_offset)
        + Op.PUSH1(mem_offset)
        + Op.PUSH1(param)
        + Op.PUSH1(signature_index)
        + Op.SIGPARAM
    )


def test_sigparam_copy_arbitrary(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Copy an `ARBITRARY` entry's raw signature bytes into memory, and
    check that the same copy against a protocol validated entry halts
    the frame instead.
    """
    sender = pre.fund_eoa()
    copied = pre.deploy_contract(
        code=sigparam_copy(1, Spec.SIGPARAM_COPY, 0, 0, 32)
        + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0))
        + Op.STOP
    )
    refused = pre.deploy_contract(
        code=sigparam_copy(0, Spec.SIGPARAM_COPY, 0, 0, 32)
        + Op.SSTORE(SLOT_RESULT, 1)
        + Op.STOP
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
        max_fee_per_gas=MAX_FEE,
        frames=[
            verify_frame(),
            Frame(
                mode=Spec.MODE_DEFAULT,
                target=copied,
                gas_limit=PROBE_FRAME_GAS,
            ),
            Frame(
                mode=Spec.MODE_DEFAULT,
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
