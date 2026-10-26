"""
Operand-range tests for the introspection instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`TXPARAM`, `FRAMEPARAM`, `SIGPARAM`, `FRAMEDATALOAD`, `FRAMEDATACOPY`
and `SIGDATACOPY` take full 256-bit operands. An undefined selector, an
index past the end of the frame or signature list, a receipt field of
a frame that has not completed, and a read the entry's scheme does not
allow each halt exceptionally; offsets and lengths follow the
`CALLDATALOAD`/`CALLDATACOPY` rules, zero-filling past the end of the
data.

A halting probe runs in a `DEFAULT` frame, whose failure does not
invalidate the transaction, and the frame's receipt pins the halt: an
exceptional halt reports status `0` and consumes the frame's whole
execution budget, which neither a successful read nor a revert does.
Wide operands such as `0x100` and `2**256-1` catch clients that narrow
an operand before checking it.

The `*_first_*` cases restate the boundary values that
`test_introspection.py::test_introspection_halts` and
`test_frameparam_halts` already cover, under this receipt oracle: their
marker oracle cannot tell a halt from a revert.
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
    Conditional,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import (
    APPROVE_ALL,
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from .signature_helpers import (
    canonical_entry,
    valid_p256_entry,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

MAX_U256 = 2**256 - 1
"""Largest operand value."""

PROBE_GAS = 100_000
"""Execution gas budget of the probe frames."""

PROBE_DATA = Bytes(bytes(range(1, 41)))
"""Data of the probe frame: 40 bytes, so a word read is truncated."""

ARBITRARY_WITNESS = Bytes(bytes(range(0x81, 0x81 + 40)))
"""Raw bytes of the `ARBITRARY` signature entry: 40 bytes."""

ARBITRARY_MSG = Bytes(b"\x5a" * 32)
"""Explicit `msg` of the `ARBITRARY` signature entry."""

# Signature entries of the halting probe's transaction.
SIG_SECP256K1 = 0
SIG_P256 = 1
SIG_ARBITRARY = 2
SIGNATURE_COUNT = 3

# Frames of the halting probe's transaction.
PROBE_FRAME = 1
FRAME_COUNT = 2


def probe_signatures(sender: EOA) -> List[FrameSignature]:
    """
    Return the halting probe's signature entries: the sender's entry
    over the canonical hash, a valid P256 entry and an `ARBITRARY`
    entry, one per scheme.
    """
    return [
        canonical_entry(sender),
        valid_p256_entry(),
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            msg=ARBITRARY_MSG,
            signature=ARBITRARY_WITNESS,
        ),
    ]


def run_probe(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    probe_code: Bytecode,
    outcome: Outcome,
) -> None:
    """
    Run `probe_code` in frame 1 of a two-frame transaction carrying one
    signature entry of each scheme, and pin the probe frame's receipt
    to `outcome`.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(code=probe_code)
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=PROBE_GAS,
                data=PROBE_DATA,
                outcome=outcome,
            ),
        ],
        signatures=probe_signatures(sender),
    )
    assert tx.frames is not None and len(tx.frames) == FRAME_COUNT
    assert tx.signatures is not None
    assert len(tx.signatures) == SIGNATURE_COUNT
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(Op.TXPARAM(0x0D), id="txparam_first_undefined"),
        pytest.param(Op.TXPARAM(0x100), id="txparam_0x100"),
        pytest.param(Op.TXPARAM(MAX_U256), id="txparam_max"),
        pytest.param(
            Op.FRAMEPARAM(PROBE_FRAME, 0x0C), id="frameparam_first_undefined"
        ),
        pytest.param(Op.FRAMEPARAM(PROBE_FRAME, 0x100), id="frameparam_0x100"),
        pytest.param(
            Op.FRAMEPARAM(PROBE_FRAME, MAX_U256), id="frameparam_max"
        ),
        pytest.param(
            Op.SIGPARAM(SIG_SECP256K1, 0x04), id="sigparam_first_undefined"
        ),
        pytest.param(Op.SIGPARAM(SIG_SECP256K1, 0x101), id="sigparam_0x101"),
        pytest.param(Op.SIGPARAM(SIG_SECP256K1, MAX_U256), id="sigparam_max"),
    ],
)
def test_undefined_selector_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    read: Bytecode,
) -> None:
    """
    Halt on a selector past the defined ones, including values whose
    low byte is a defined selector (`0x100` reads as `TYPE` or
    `RESOLVED_TARGET`, `0x101` as `SCHEME` if narrowed to a byte).

    EIP-8141 §`TXPARAM`: "Undefined `param` values result in an
    exceptional halt." §`FRAMEPARAM` and §`SIGPARAM`, Notes: "Undefined
    `param` values result in an exceptional halt."
    """
    run_probe(state_test, pre, fork, Op.POP(read) + Op.STOP, Outcome.HALT)


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(
            Op.POP(Op.FRAMEPARAM(FRAME_COUNT, Spec.FRAMEPARAM_MODE)),
            id="frameparam_first_out_of_bounds",
        ),
        pytest.param(
            Op.POP(Op.FRAMEPARAM(0x100 + PROBE_FRAME, Spec.FRAMEPARAM_MODE)),
            id="frameparam_index_0x101",
        ),
        pytest.param(
            Op.POP(Op.FRAMEPARAM(MAX_U256, Spec.FRAMEPARAM_MODE)),
            id="frameparam_index_max",
        ),
        pytest.param(
            Op.POP(Op.FRAMEDATALOAD(0, 0x100 + PROBE_FRAME)),
            id="framedataload_index_0x101",
        ),
        pytest.param(
            Op.POP(Op.FRAMEDATALOAD(0, MAX_U256)),
            id="framedataload_index_max",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 32, 0x100 + PROBE_FRAME),
            id="framedatacopy_index_0x101",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 32, MAX_U256),
            id="framedatacopy_index_max",
        ),
        pytest.param(
            Op.FRAMEDATACOPY(0, 0, 0, FRAME_COUNT),
            id="framedatacopy_index_out_of_bounds_zero_length",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(SIGNATURE_COUNT, Spec.SIGPARAM_SCHEME)),
            id="sigparam_first_out_of_bounds",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(0x100 + SIG_SECP256K1, Spec.SIGPARAM_SCHEME)),
            id="sigparam_index_0x100",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(MAX_U256, Spec.SIGPARAM_SCHEME)),
            id="sigparam_index_max",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 32, 0x100 + SIG_ARBITRARY),
            id="sigdatacopy_index_0x102",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 0, SIGNATURE_COUNT),
            id="sigdatacopy_index_out_of_bounds_zero_length",
        ),
    ],
)
def test_out_of_bounds_index_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    read: Bytecode,
) -> None:
    """
    Halt on a frame or signature index at or past the end of its list,
    including indices whose low byte names an existing entry and copies
    of zero bytes.

    EIP-8141 §`FRAMEPARAM`, Notes: "Out-of-bounds access for
    `frameIndex` results in an exceptional halt." §`FRAMEDATALOAD` and
    §`FRAMEDATACOPY`: "When the `frameIndex` is out-of-bounds, an
    exceptional halt occurs." §`SIGPARAM`, Notes: "Out-of-bounds access
    for `signatureIndex` results in an exceptional halt."
    §`SIGDATACOPY`: "When the `signatureIndex` is out-of-bounds, an
    exceptional halt occurs." None of them exempts a zero `length`.
    """
    run_probe(state_test, pre, fork, read + Op.STOP, Outcome.HALT)


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(
            Op.POP(Op.SIGPARAM(SIG_P256, Spec.SIGPARAM_SIGNATURE_LENGTH)),
            id="sigparam_length_of_p256",
        ),
        pytest.param(
            Op.POP(Op.SIGPARAM(SIG_ARBITRARY, Spec.SIGPARAM_RESOLVED_SIGNER)),
            id="sigparam_signer_of_arbitrary",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 32, SIG_P256), id="sigdatacopy_of_p256"
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 0, SIG_P256),
            id="sigdatacopy_of_p256_zero_length",
        ),
        pytest.param(
            Op.SIGDATACOPY(0, 0, 0, SIG_SECP256K1),
            id="sigdatacopy_of_secp256k1_zero_length",
        ),
    ],
)
def test_scheme_restricted_read_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    read: Bytecode,
) -> None:
    """
    Halt on a signature read the entry's scheme does not define: the
    length or bytes of a protocol-validated entry, even zero bytes of
    them, and the resolved signer of an `ARBITRARY` entry.

    EIP-8141 §`SIGPARAM`, Notes: "For `ARBITRARY` signature entries,
    requesting `resolved_signer` results in an exceptional halt." and
    "For signature entries of any other `scheme`, requesting
    `len(signature)` results in an exceptional halt."
    §`SIGDATACOPY`: "If the referenced signature entry's `scheme` is
    not `ARBITRARY`, an exceptional halt occurs."
    """
    run_probe(state_test, pre, fork, read + Op.STOP, Outcome.HALT)


@pytest.mark.parametrize(
    "copy",
    [
        pytest.param(
            Op.FRAMEDATACOPY(MAX_U256, 0, 1, PROBE_FRAME), id="frame"
        ),
        pytest.param(
            Op.SIGDATACOPY(MAX_U256, 0, 1, SIG_ARBITRARY), id="signature"
        ),
    ],
)
def test_copy_to_unreachable_memory_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    copy: Bytecode,
) -> None:
    """
    Copy one byte to memory offset `2**256-1`: the memory expansion
    cannot be paid, so the copy halts out of gas.

    EIP-8141 §`FRAMEDATACOPY`: "Its gas cost is calculated exactly as
    for `CALLDATACOPY`, including [...] the standard EVM memory
    expansion cost." §`SIGDATACOPY` states the same. The end of the
    region, `2**256`, overflows a 256-bit sum, so a client wrapping it
    to zero would skip the expansion and copy instead.
    """
    run_probe(state_test, pre, fork, copy + Op.STOP, Outcome.HALT)


SLOT_ZERO_LENGTH_COPY = 0x01
SLOT_LOAD_FAR = 0x02
SLOT_COPY_FAR = 0x03
SLOT_SIG_COPY_FAR = 0x04
SLOT_STRADDLE_HEAD = 0x05
SLOT_STRADDLE_TAIL = 0x06
SLOT_ORDERED_COPY = 0x07
SLOT_ORDERED_MSIZE = 0x08
SLOT_ORDERED_SIG_COPY = 0x09

ALL_ONES = MAX_U256
"""Memory canary a zero-filling copy has to overwrite."""


COPY_PROBE_GAS = 500_000
"""Execution gas budget of the probes that record several reads."""


def test_copy_and_load_operand_ranges(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read the probe frame's data and the `ARBITRARY` entry's bytes with
    offsets past their end and with distinct operands, in two probes
    whose writes pin each result.

    The probes check that:

    - a zero-length copy to memory offset `2**256-1` succeeds without
      expanding memory (`MSIZE` stays 0);
    - `FRAMEDATALOAD` at offset `2**256-1` reads zero;
    - a 32-byte copy from data offset `2**256-1` writes 32 zero bytes
      over a canary, for frame data and signature bytes alike;
    - a copy straddling the end of the data writes the tail and then
      zeroes over a second canary;
    - `FRAMEDATACOPY(memOffset=64, dataOffset=8, length=16, i)` and its
      `SIGDATACOPY` twin copy `data[8:24]` to memory offset 64; the
      first leaves `MSIZE` at 96 (`memOffset + length = 80` rounded up
      to a word), read before anything else touches memory, which pins
      the operand order.

    EIP-8141 §`FRAMEDATALOAD`: "The operation semantics match
    CALLDATALOAD". §`FRAMEDATACOPY`: "The operation semantics match
    CALLDATACOPY, copying `length` bytes from the chosen frame's
    `data`, starting at the given byte `dataOffset`, into a memory
    region starting at `memOffset`." with stack `memOffset`,
    `dataOffset`, `length`, `frameIndex` from the top. §`SIGDATACOPY`:
    "Bytes beyond the end of the signature are copied as zeroes."

    Values that may be zero are stored plus one, so a zero read is told
    apart from a write that never happened.
    """
    canary = Op.MSTORE(0, ALL_ONES)
    probe_code = (
        Op.FRAMEDATACOPY(MAX_U256, 0, 0, PROBE_FRAME)
        + Op.SSTORE(SLOT_ZERO_LENGTH_COPY, Op.ADD(1, Op.MSIZE))
        + Op.SSTORE(
            SLOT_LOAD_FAR, Op.ADD(1, Op.FRAMEDATALOAD(MAX_U256, PROBE_FRAME))
        )
        + canary
        + Op.FRAMEDATACOPY(0, MAX_U256, 32, PROBE_FRAME)
        + Op.SSTORE(SLOT_COPY_FAR, Op.ADD(1, Op.MLOAD(0)))
        + canary
        + Op.SIGDATACOPY(0, MAX_U256, 32, SIG_ARBITRARY)
        + Op.SSTORE(SLOT_SIG_COPY_FAR, Op.ADD(1, Op.MLOAD(0)))
        + Op.MSTORE(32, ALL_ONES)
        + Op.FRAMEDATACOPY(0, 8, 64, PROBE_FRAME)
        + Op.SSTORE(SLOT_STRADDLE_HEAD, Op.MLOAD(0))
        + Op.SSTORE(SLOT_STRADDLE_TAIL, Op.ADD(1, Op.MLOAD(32)))
        + Op.STOP
    )
    # A fresh memory for the operand-order copies, so `MSIZE` reports
    # their expansion alone.
    ordered_code = (
        Op.FRAMEDATACOPY(64, 8, 16, PROBE_FRAME)
        + Op.SSTORE(SLOT_ORDERED_MSIZE, Op.MSIZE)
        + Op.SSTORE(SLOT_ORDERED_COPY, Op.MLOAD(64))
        + Op.SIGDATACOPY(64, 8, 16, SIG_ARBITRARY)
        + Op.SSTORE(SLOT_ORDERED_SIG_COPY, Op.MLOAD(64))
        + Op.STOP
    )
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(code=probe_code)
    ordered = pre.deploy_contract(code=ordered_code)

    def frame(target: Address, code: Bytecode) -> FrameCase:
        return default_frame(
            target=target,
            gas_limit=COPY_PROBE_GAS,
            data=PROBE_DATA,
            pin_gas=False,
            state_gas_limit=code.state_cost(fork),
            state_gas_used=code.state_cost(fork),
        )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            frame(probe, probe_code),
            frame(ordered, ordered_code),
        ],
        signatures=probe_signatures(sender),
    )

    def word(data: bytes) -> int:
        return int.from_bytes(data.ljust(32, b"\x00")[:32], "big")

    state_test(
        pre=pre,
        tx=tx,
        post={
            probe: Account(
                storage={
                    SLOT_ZERO_LENGTH_COPY: 1,
                    SLOT_LOAD_FAR: 1,
                    SLOT_COPY_FAR: 1,
                    SLOT_SIG_COPY_FAR: 1,
                    SLOT_STRADDLE_HEAD: word(PROBE_DATA[8:40]),
                    SLOT_STRADDLE_TAIL: 1,
                }
            ),
            ordered: Account(
                storage={
                    SLOT_ORDERED_COPY: word(PROBE_DATA[8:24]),
                    SLOT_ORDERED_MSIZE: 96,
                    SLOT_ORDERED_SIG_COPY: word(ARBITRARY_WITNESS[8:24]),
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "frame_index,outcome",
    [
        pytest.param(0, Outcome.SUCCESS, id="earlier_frame"),
        pytest.param(2, Outcome.HALT, id="later_frame"),
    ],
)
@pytest.mark.parametrize(
    "param",
    [
        pytest.param(Spec.FRAMEPARAM_STATUS, id="status"),
        pytest.param(
            Spec.FRAMEPARAM_EXECUTION_GAS_USED, id="execution_gas_used"
        ),
        pytest.param(Spec.FRAMEPARAM_STATE_GAS_USED, id="state_gas_used"),
    ],
)
def test_receipt_field_of_later_frame_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_index: int,
    outcome: Outcome,
    param: int,
) -> None:
    """
    Read a receipt field of a frame that has not run yet, one after the
    reader's own: the read halts. The same read of an earlier frame is
    the control and succeeds; the values it reads are pinned in
    `test_introspection.py` (`test_frameparam[status_of_earlier_frame]`
    and `test_frameparam_gas_used`).

    EIP-8141 §`FRAMEPARAM`, Notes: "Like `status`, they are defined
    only for frames that have completed; accessing them for the current
    frame or a subsequent frame results in an exceptional halt." and
    "Attempting to access the return `status` of the current frame or
    a subsequent frame results in an exceptional halt."
    """
    sender = pre.fund_eoa()
    probe_code = Op.POP(Op.FRAMEPARAM(frame_index, param)) + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=PROBE_GAS,
                outcome=outcome,
            ),
            # The frame read, which runs codeless at the warm sender.
            default_frame(target=sender, warm=True),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


LATER_FRAME_VALUE = 123
"""Value the later `SENDER` frame carries."""

LATER_FRAME_DATA = Bytes(b"\x42" * 32)
"""Data the later `SENDER` frame carries."""


def test_verify_frame_reads_later_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A contract sender's `VERIFY` frame approves only after checking the
    `SENDER` frame that follows it: its resolved target, mode, value,
    data length and data. Every read succeeds, so the transaction is
    valid.

    EIP-8141 §`FRAMEPARAM`: only the receipt fields `status`,
    `gas_used.execution` and `gas_used.state` halt for "the current
    frame or a subsequent frame"; the frame's other fields are not
    restricted. §Security Considerations, Cross-frame Data Visibility
    During Validation: "`FRAMEPARAM`, `FRAMEDATALOAD`, and
    `FRAMEDATACOPY` allow validation code to inspect other frames,
    including later `SENDER` frames and their `value`s."
    """
    recipient = pre.fund_eoa(amount=1)
    later = 1
    checks = [
        Op.EQ(
            Op.FRAMEPARAM(later, Spec.FRAMEPARAM_RESOLVED_TARGET), recipient
        ),
        Op.EQ(Op.FRAMEPARAM(later, Spec.FRAMEPARAM_MODE), Spec.MODE_SENDER),
        Op.EQ(Op.FRAMEPARAM(later, Spec.FRAMEPARAM_VALUE), LATER_FRAME_VALUE),
        Op.EQ(
            Op.FRAMEPARAM(later, Spec.FRAMEPARAM_DATA_LENGTH),
            len(LATER_FRAME_DATA),
        ),
        Op.EQ(
            Op.FRAMEDATALOAD(0, later),
            int.from_bytes(LATER_FRAME_DATA, "big"),
        ),
    ]
    condition = checks[0]
    for check in checks[1:]:
        condition = Op.AND(condition, check)
    sender_code = Conditional(
        condition=condition,
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(pin_gas=False),
            sender_frame(
                target=recipient,
                value=LATER_FRAME_VALUE,
                data=LATER_FRAME_DATA,
                logs=[transfer_log(sender, recipient, LATER_FRAME_VALUE)],
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            recipient: Account(balance=1 + LATER_FRAME_VALUE),
        },
    )


def test_sigparam_with_no_signature_entries_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    In a transaction with no signature entry, read the scheme of entry
    0: the read halts.

    EIP-8141 §`SIGPARAM`, Notes: "Out-of-bounds access for
    `signatureIndex` results in an exceptional halt." With an empty
    list, every index is out of bounds. The sender is a contract that
    approves through its code, so the transaction needs no entry.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    probe_code = Op.POP(Op.SIGPARAM(0, Spec.SIGPARAM_SCHEME)) + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        signatures=[],
        frames=[
            verify_frame(pin_gas=False),
            default_frame(
                target=probe,
                code=probe_code,
                gas_limit=PROBE_GAS,
                outcome=Outcome.HALT,
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})
