"""
Frame call environment tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each frame runs as a top-level call (§Behavior: "Execute a call with
the specified `mode`, `flags`, `target`, `limits`, `value`, and
`data`."). These tests pin what that call sees and what it reports:
`GASPRICE` and `CALLVALUE`, the value transfer's balance check and
transfer log, and the logs its receipt keeps.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Environment,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    TransactionLog,
    compute_create_address,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import (
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

BASE_FEE = 7
"""Base fee of the block the transactions land in."""

PRIORITY_FEE = 5
"""Tip per gas the `GASPRICE` transaction asks for."""

FRAME_GAS = 200_000
"""Execution gas budget of the frames whose code makes nested calls."""

CURRENT_FRAME_INDEX = Op.TXPARAM(Spec.TXPARAM_CURRENT_FRAME_INDEX)

FRAME_VALUE = 10**9
"""Value carried by the value-bearing `SENDER` frames."""


def test_gasprice_is_the_same_in_every_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Read `GASPRICE` in a `VERIFY` frame, a `SENDER` frame, a `DEFAULT`
    frame, a call nested in a `DEFAULT` frame and the initcode a
    `DEFAULT` frame creates: every read returns
    `base_fee_per_gas + max_priority_fee // max_gas`.

    EIP-8141 §Fee budget: "`GASPRICE` returns `base_fee_per_gas +
    max_priority_fee // max_gas`. It depends only on the transaction
    and the including block's base fees, so every frame observes the
    same value." with `max_priority_fee =
    min(tx.fees.max_priority_fee_per_gas * max_gas, tx.fees.max_fee -
    required_max_fee)`.

    The budget pays half the full tip, so `GASPRICE` is neither the
    base fee nor the base fee plus `max_priority_fee_per_gas`. The
    contract sender's `VERIFY` frame approves only if it reads the
    expected value; the other reads are recorded under their frame's
    index.
    """
    half_tip_per_gas = PRIORITY_FEE // 2
    gas_price = BASE_FEE + half_tip_per_gas
    record = Op.SSTORE(CURRENT_FRAME_INDEX, Op.GASPRICE) + Op.STOP
    recorder = pre.deploy_contract(code=record)
    caller = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=recorder)) + Op.STOP
    )
    factory = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(Op.CREATE(0, 0, Op.CALLDATASIZE))
        + Op.STOP
    )
    created = compute_create_address(address=factory, nonce=1)
    sender_code = Conditional(
        condition=Op.EQ(Op.GASPRICE, gas_price),
        if_true=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    slot_gas = record.state_cost(fork)
    frames: List[FrameCase] = [
        verify_frame(pin_gas=False),
        sender_frame(target=recorder, pin_gas=False, state_gas_used=slot_gas),
        default_frame(target=recorder, pin_gas=False, state_gas_used=slot_gas),
        default_frame(
            target=caller,
            gas_limit=FRAME_GAS,
            pin_gas=False,
            state_gas_used=slot_gas,
        ),
        default_frame(
            target=factory,
            data=Bytes(bytes(record)),
            gas_limit=FRAME_GAS,
            pin_gas=False,
            state_gas_used=fork.gas_costs().NEW_ACCOUNT + slot_gas,
        ),
    ]
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, signatures=[]
    )
    required_max_fee = max_gas * BASE_FEE
    max_fee = required_max_fee + PRIORITY_FEE * max_gas // 2
    # The premise: half the full tip, spread over `max_gas`.
    assert (max_fee - required_max_fee) // max_gas == half_tip_per_gas

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        signatures=[],
        max_fee=max_fee,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=frames,
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            recorder: Account(
                storage={1: gas_price, 2: gas_price, 3: gas_price}
            ),
            created: Account(storage={4: gas_price}),
        },
    )


def test_callvalue_is_the_frame_value(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    One recorder runs in a `SENDER` frame carrying value and in a
    `DEFAULT` frame, and records `CALLVALUE` under its frame's index:
    the frame's value, then zero.

    EIP-8141 §Behavior: "In the top-level frame call, `CALLVALUE` is
    `frame.value`." A `DEFAULT` frame's value is zero (§Constraints:
    "`assert frame.mode == SENDER or frame.value == 0`"). The
    `DEFAULT` frame's slot holds a nonzero value beforehand, so a zero
    recorded there is told apart from a slot never written.
    """
    sender = pre.fund_eoa()
    record = Op.SSTORE(CURRENT_FRAME_INDEX, Op.CALLVALUE) + Op.STOP
    recorder = pre.deploy_contract(code=record, storage={2: 0xDEAD})

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                target=recorder,
                value=FRAME_VALUE,
                pin_gas=False,
                state_gas_used=record.state_cost(fork),
                logs=[transfer_log(sender, recorder, FRAME_VALUE)],
            ),
            default_frame(target=recorder, pin_gas=False, logs=[]),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            recorder: Account(
                balance=FRAME_VALUE, storage={1: FRAME_VALUE, 2: 0}
            ),
        },
    )


LOG_TOPIC = 0x01
"""Topic of the log the value frame's target emits."""


def test_transfer_log_precedes_target_logs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A `SENDER` frame sends value to a contract whose code emits a log:
    the frame's receipt lists the transfer log first, then the code's
    log.

    EIP-8141 §Behavior: "A non-zero value transfer to an address other
    than `tx.sender` emits the transfer log specified by EIP-7708."
    The transfer happens in the frame's top-level call, "As with an
    ordinary `CALL`", before the target's code runs, which is also
    where EIP-7708 places a transaction's own transfer log: ahead of
    every log the called code emits.
    """
    sender = pre.fund_eoa()
    target_code = Op.LOG1(0, 0, LOG_TOPIC) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                target=target,
                value=FRAME_VALUE,
                code=target_code,
                logs=[
                    transfer_log(sender, target, FRAME_VALUE),
                    TransactionLog(address=target, topics=[LOG_TOPIC]),
                ],
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={target: Account(balance=FRAME_VALUE)},
    )


def test_frame_receipt_drops_logs_of_reverted_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Three `DEFAULT` frames emit logs; the third first calls a contract
    that emits a log and reverts. Each frame's receipt holds its own
    logs, and the third frame's holds only the log of its own code.

    EIP-8141 §Receipt Encoding: "`frame_receipt = [status, gas_used,
    logs]`". §Behavior: "If a frame's execution reverts, its state
    changes [...] are discarded", and a reverted call inside a frame
    discards its logs as in any other transaction.
    """
    sender = pre.fund_eoa()

    def emitter(topic: int) -> Bytecode:
        return Op.LOG1(0, 0, topic)

    first = pre.deploy_contract(code=emitter(1) + Op.STOP)
    second = pre.deploy_contract(code=emitter(2) + Op.STOP)
    reverting = pre.deploy_contract(code=emitter(3) + Op.REVERT(0, 0))
    third = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=reverting))
        + emitter(4)
        + Op.STOP
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(logs=[]),
            default_frame(
                target=first,
                pin_gas=False,
                logs=[TransactionLog(address=first, topics=[1])],
            ),
            default_frame(
                target=second,
                pin_gas=False,
                logs=[TransactionLog(address=second, topics=[2])],
            ),
            default_frame(
                target=third,
                gas_limit=FRAME_GAS,
                pin_gas=False,
                logs=[TransactionLog(address=third, topics=[4])],
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "explicit_target",
    [
        pytest.param(False, id="empty_target"),
        pytest.param(True, id="sender_as_target"),
    ],
)
def test_self_transfer_exceeding_balance_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    explicit_target: bool,
) -> None:
    """
    A `SENDER` frame sends the sender one wei more than it holds, to
    itself: the frame reverts on the balance check, although a
    transfer to itself would leave every balance unchanged.

    EIP-8141 §Behavior: "As with an ordinary `CALL`, if the caller does
    not have sufficient balance to transfer `frame.value`, the frame
    reverts, consuming the gas charged so far." The check has no
    exemption for a target equal to the caller. The receipt reports
    the sender's warm entry access, the only gas charged before the
    check, and the sender keeps its balance. A sponsor pays, so the
    sender's balance is fixed by the pre-state alone.
    """
    sender_balance = 1
    sender = pre.fund_eoa(amount=sender_balance)
    payer = pre.fund_eoa()

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(
                target=sender if explicit_target else None,
                value=sender_balance + 1,
                # The sender is warm from the start of the transaction.
                warm=True,
                outcome=Outcome.REVERT,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1, balance=sender_balance)},
    )
