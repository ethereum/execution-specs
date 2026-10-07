"""Helpers for EIP-7906 transaction assertion tests."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

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
    Frame,
    FrameReceipt,
    Op,
    Storage,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    compute_create_address,
)

from tests.bogota.eip8141_frame_transactions.helpers import verify_frame
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .spec import Spec

SLOT_MARKER = 0x01
"""Storage slot a probe writes before a read that is expected to halt."""

MARKER = 0xFF
"""The value a probe writes into `SLOT_MARKER`."""

SLOT_A = 0x0A
SLOT_B = 0x0B

FUNDS = 10**18
"""Funding of a sender or sponsor whose balance a test pins."""

FEE_PER_GAS = 7
"""Gas price of a transaction whose payer balance a test pins."""

BOB_FUNDS = 1_000
CAROL_FUNDS = 1
"""Funding of an account the body never touches."""

NEVER_EXISTED = Address(0x7906000000000000000000000000000000000001)
"""An address with no account before or after the transaction."""

VALUE = 7

KEY_A = 0xA1
KEY_B = 0xB2
KEY_C = 0xC3
KEY_U = 0xD4
"""A slot the body reads but never writes."""

WRITER_STORAGE: Storage.StorageDictType = {KEY_B: 5, KEY_U: 3}
"""Storage the writer contracts start with."""

WRITER_CODE = (
    Op.SSTORE(KEY_C, 9)
    + Op.SSTORE(KEY_B, 7)
    + Op.SSTORE(KEY_A, 1)
    + Op.SSTORE(KEY_C, 0)
    + Op.STOP
)
"""
Write a slot that is then restored, update a set one, and set an empty
one, in descending key order, so only the last two appear in
`slots_changed` and the table's ascending key order is not the order
they were written in.
"""

WRITER_POST: Storage.StorageDictType = {KEY_A: 1, KEY_B: 7, KEY_C: 0, KEY_U: 3}
"""Storage a writer contract ends with."""

RESTORER_CODE = Op.SSTORE(KEY_A, 1) + Op.SSTORE(KEY_A, 0) + Op.STOP
"""Write a slot and restore it, leaving no net change."""

TOPIC_1 = 0x1111111111111111111111111111111111111111111111111111111111111111
TOPIC_2 = 0x2222222222222222222222222222222222222222222222222222222222222222
TOPIC_3 = 0x3333333333333333333333333333333333333333333333333333333333333333
TOPIC_4 = 0x4444444444444444444444444444444444444444444444444444444444444444

EVENT_DATA = bytes(range(1, 41))
"""Non-indexed data of the emitter's event: 40 bytes, over a word."""

EMITTER_CODE = (
    Op.MSTORE(0, int.from_bytes(EVENT_DATA[:32], "big"))
    + Op.MSTORE(32, int.from_bytes(EVENT_DATA[32:].ljust(32, b"\x00"), "big"))
    + Op.LOG2(0, len(EVENT_DATA), TOPIC_1, TOPIC_2)
    + Op.STOP
)
"""Emit one two-topic event carrying `EVENT_DATA`."""

SILENT_CODE = Op.LOG0(0, 0) + Op.STOP
"""Emit one topic-less, data-less event."""

FOUR_TOPIC_CODE = Op.LOG4(0, 0, TOPIC_1, TOPIC_2, TOPIC_3, TOPIC_4) + Op.STOP
"""Emit one data-less event with every topic position filled."""

DEPLOYED_RUNTIME = b"\x00"
"""Runtime code of the contract the factory deploys: a single `STOP`."""

INITCODE_DEPLOYING = Op.MSTORE8(0, 0) + Op.RETURN(0, 1)
INITCODE_EMPTY = Op.STOP


def initcode_word(initcode: Bytecode) -> int:
    """Return an initcode, at most a word long, left-aligned in a word."""
    raw = bytes(initcode)
    assert len(raw) <= 32
    return int.from_bytes(raw.ljust(32, b"\x00"), "big")


FACTORY_CODE = (
    Op.MSTORE(0, initcode_word(INITCODE_DEPLOYING))
    + Op.POP(Op.CREATE(0, 0, len(bytes(INITCODE_DEPLOYING))))
    + Op.MSTORE(0, initcode_word(INITCODE_EMPTY))
    + Op.POP(Op.CREATE(0, 0, len(bytes(INITCODE_EMPTY))))
    + Op.STOP
)
"""
Deploy one contract with runtime code and one whose initcode returns
nothing, so only the first appears in `contracts_deployed`.
"""


def as_int(address: Address | EOA) -> int:
    """Return an address as the integer the opcodes push it as."""
    return int.from_bytes(address, "big")


def frame_gas(fork: Fork) -> int:
    """
    Return the execution gas budget of a body or `POST_TX` frame: an
    equal share of the transaction gas cap among the most frames a
    transaction may carry.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    return cap // Spec8141.MAX_FRAMES


def post_tx_frame(fork: Fork, **overrides: Any) -> Frame:
    """
    Return a `POST_TX` frame, the trailing assertion frame.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_POST_TX,
        gas_limit=frame_gas(fork),
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def body_frame(fork: Fork, **overrides: Any) -> Frame:
    """
    Return a `SENDER` frame of the execution body.

    Keyword arguments override the corresponding frame fields.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec8141.MODE_SENDER,
        gas_limit=frame_gas(fork),
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def expect_eq(value: Bytecode | Op, expected: Any) -> Bytecode:
    """
    Return bytecode that reverts unless `value` evaluates to `expected`.

    An assertion contract is a sequence of these checks followed by
    `STOP`: the `POST_TX` frame succeeds only when every check holds,
    which the body's committed effects and the frame's receipt status
    then make observable.
    """
    return Conditional(
        condition=Op.EQ(value, expected),
        if_false=Op.REVERT(0, 0),
    )


def measured_gas(
    probe: Bytecode | Op, *, pushes_result: bool = True
) -> Bytecode:
    """
    Return bytecode that leaves the execution gas consumed by `probe`
    on the stack, including the probe's own operand pushes.

    The measurement brackets the probe with `GAS` reads: the first read
    is taken after its own charge and the second after its own, so the
    difference is the probe's operand pushes, the probe, the `POP` of
    its result when it pushes one, and the second `GAS`. Callers add
    that overhead with `probe_overhead`.
    """
    code = Op.GAS + probe
    if pushes_result:
        code += Op.POP
    return code + Op.GAS + Op.SWAP1 + Op.SUB


def probe_overhead(
    fork: Fork, probe: Bytecode, *, pushes_result: bool = True
) -> int:
    """
    Return the gas `measured_gas` adds around a probe: the probe's
    operand pushes, the `POP` of a pushed result, and the closing `GAS`.
    """
    opcode_gas = fork.opcode_gas_calculator()
    operand_pushes = sum(opcode_gas(op) for op in probe.opcode_list[:-1])
    closing = (Op.POP + Op.GAS) if pushes_result else (Bytecode() + Op.GAS)
    return operand_pushes + closing.gas_cost(fork)


def assertion_transaction(
    fork: Fork,
    sender: EOA,
    body: List[Frame],
    assertion: Address | List[Address],
    frame_receipts: List[FrameReceipt] | None = None,
    **overrides: Any,
) -> Transaction:
    """
    Return a frame transaction whose validation prefix is the sender's
    default-code `VERIFY` frame, followed by the body frames and one
    `POST_TX` frame per assertion contract, a single one usually.
    """
    assertions = assertion if isinstance(assertion, list) else [assertion]
    kwargs: Dict[str, Any] = dict(
        sender=sender,
        frames=[
            verify_frame(),
            *body,
            *[post_tx_frame(fork, target=target) for target in assertions],
        ],
    )
    if frame_receipts is not None:
        kwargs["expected_receipt"] = TransactionReceipt(
            payer=sender, frame_receipts=frame_receipts
        )
    kwargs.update(overrides)
    return Transaction(**kwargs)


def success_receipts(count: int) -> List[FrameReceipt]:
    """Return `count` frame receipts expecting success."""
    return [FrameReceipt(status=Spec8141.STATUS_SUCCESS) for _ in range(count)]


def reverted_body_receipts(
    fork: Fork, body_count: int, *, assertion_halts: bool = False
) -> List[FrameReceipt]:
    """
    Return the receipts of a transaction whose single `POST_TX` frame
    failed: the `VERIFY` frame succeeded, the body frames keep their
    success status with their logs emptied, and the assertion frame
    failed.

    An exceptional halt consumes the assertion frame's whole budget,
    which tells it apart from a revert that returns the rest.
    """
    return [
        FrameReceipt(status=Spec8141.STATUS_SUCCESS),
        *[
            FrameReceipt(status=Spec8141.STATUS_SUCCESS, logs=[])
            for _ in range(body_count)
        ],
        FrameReceipt(
            status=Spec8141.STATUS_FAILURE,
            gas_used=frame_gas(fork) if assertion_halts else None,
        ),
    ]


def frame_transaction_gas(
    fork: Fork,
    tx: Transaction,
    frame_receipts: List[FrameReceipt],
    refundable: int,
) -> Tuple[int, int]:
    """
    Return the gas a signed frame transaction charges its payer and the
    gas it adds to the block, from its frame receipts and the refund its
    surviving frames accrued.
    """
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        return_cost_deducted_prior_execution=True,
    )
    floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames, signatures=tx.signatures
    )
    execution_used = intrinsic
    state_used = 0
    for receipt in frame_receipts:
        assert receipt.gas_used is not None
        assert receipt.state_gas_used is not None
        execution_used += int(receipt.gas_used)
        state_used += int(receipt.state_gas_used)
    refund = min(
        refundable,
        (execution_used + state_used) // fork.max_refund_quotient(),
    )
    payer_used = max(execution_used - refund, floor) + state_used
    return payer_used, max(execution_used, floor, state_used)


@dataclass(frozen=True)
class BodyEffect:
    """
    Code of a body frame whose settlement a test pins, with the storage
    it leaves when kept and whether it emits an event.
    """

    code: Bytecode
    kept_storage: Storage.StorageDictType
    emits_event: bool


WORKER_STORAGE: Storage.StorageDictType = {SLOT_B: 1}
"""Storage a settlement worker starts with."""

SET_SLOT = Op.SSTORE(SLOT_A, 1, original_value=0, new_value=1)
"""Set an empty slot, charging state gas."""

CLEAR_SLOT = Op.SSTORE(
    SLOT_B, 0, original_value=1, current_value=1, new_value=0
)
"""Clear a set slot, accruing a refund."""

BODY_EFFECTS = [
    pytest.param(
        BodyEffect(SET_SLOT + Op.STOP, {SLOT_A: 1, SLOT_B: 1}, False),
        id="slot_set",
    ),
    pytest.param(
        BodyEffect(CLEAR_SLOT + Op.STOP, {SLOT_A: 0, SLOT_B: 0}, False),
        id="slot_cleared",
    ),
    pytest.param(
        BodyEffect(Op.LOG0(0, 0) + Op.STOP, WORKER_STORAGE, True),
        id="event",
    ),
    pytest.param(
        BodyEffect(
            SET_SLOT + CLEAR_SLOT + Op.LOG0(0, 0) + Op.STOP,
            {SLOT_A: 1, SLOT_B: 0},
            True,
        ),
        id="all_effects",
    ),
]
"""The effects a body frame settles: state gas, a refund and an event."""


def settled_receipt(
    fork: Fork, worker: Address, effect: BodyEffect, *, kept: bool
) -> FrameReceipt:
    """
    Return the receipt of a body frame running `effect` at `worker`,
    whose state gas and event survive only when the frame is kept.
    """
    return FrameReceipt(
        status=Spec8141.STATUS_SUCCESS,
        gas_used=fork.frame_entry_gas_calculator()()
        + effect.code.execution_cost(fork),
        state_gas_used=effect.code.state_cost(fork) if kept else 0,
        logs=[TransactionLog(address=worker, topics=[], data=Bytes())]
        if kept and effect.emits_event
        else [],
    )


def creation_state_gas(
    fork: Fork, *, creations: int, deposited_bytes: int = 0
) -> int:
    """
    Return the state gas a frame needs to create `creations` accounts
    and deposit `deposited_bytes` of runtime code.
    """
    create = Op.CREATE.with_metadata(account_new=True)
    deposit = Op.RETURN.with_metadata(code_deposit_size=deposited_bytes)
    return creations * create.state_cost(fork) + deposit.state_cost(fork)


def factory_state_gas(fork: Fork) -> int:
    """Return the state gas `FACTORY_CODE` needs."""
    return creation_state_gas(
        fork, creations=2, deposited_bytes=len(DEPLOYED_RUNTIME)
    )


@dataclass
class MixedBody:
    """
    The accounts of an execution body that writes slots, writes and
    restores one, transfers value and deploys contracts.
    """

    sender: EOA
    recipient: EOA
    untouched: EOA
    writer: Address
    restorer: Address
    factory: Address
    deployed: Address
    frames: List[Frame] = field(default_factory=list)

    def transaction(self, fork: Fork, assertion: Address) -> Transaction:
        """Return the body followed by one `POST_TX` frame that holds."""
        return assertion_transaction(
            fork,
            self.sender,
            body=self.frames,
            assertion=assertion,
            frame_receipts=success_receipts(len(self.frames) + 2),
        )

    def post(self) -> Dict[Address, Account]:
        """Return the post state the body leaves when it commits."""
        return {
            self.sender: Account(nonce=1),
            self.writer: Account(storage=WRITER_POST),
            self.restorer: Account(storage={KEY_A: 0}),
            self.recipient: Account(balance=BOB_FUNDS + VALUE),
            self.untouched: Account(balance=CAROL_FUNDS),
            self.factory: Account(nonce=3),
            self.deployed: Account(nonce=1, code=DEPLOYED_RUNTIME),
        }


def mixed_body(pre: Alloc, fork: Fork) -> MixedBody:
    """
    Return a body whose writer updates and sets slots, whose restorer
    leaves a slot unchanged, which pays a recipient and whose factory
    deploys a contract, beside an account the body never touches.
    """
    factory = pre.deploy_contract(code=FACTORY_CODE)
    body = MixedBody(
        sender=pre.fund_eoa(amount=FUNDS),
        recipient=pre.fund_eoa(amount=BOB_FUNDS),
        untouched=pre.fund_eoa(amount=CAROL_FUNDS),
        writer=pre.deploy_contract(code=WRITER_CODE, storage=WRITER_STORAGE),
        restorer=pre.deploy_contract(code=RESTORER_CODE),
        factory=factory,
        deployed=compute_create_address(address=factory, nonce=1),
    )
    body.frames = [
        body_frame(fork, target=body.writer),
        body_frame(fork, target=body.restorer),
        body_frame(fork, target=body.recipient, value=VALUE),
        body_frame(
            fork, target=body.factory, state_gas_limit=factory_state_gas(fork)
        ),
    ]
    return body
