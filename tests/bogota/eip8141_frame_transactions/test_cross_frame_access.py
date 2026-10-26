"""
Cross-frame warm and cold access tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The warm sets of EIP-2929 are journaled across the frames of one
transaction: what a successful frame warms stays warm for later frames,
while a frame that fails, including one that fails its value transfer
before running any code, takes back every access it warmed. Each probe
frame's receipt pins its gas, so a slot or address priced at the wrong
temperature shows as a receipt mismatch.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
)

from .helpers import (
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

SLOT = 0x05
"""The storage slot both frames read."""

ENDINGS = {
    Outcome.SUCCESS: Op.STOP,
    Outcome.REVERT: Op.REVERT(0, 0),
    Outcome.HALT: Op.INVALID,
}
"""How a frame's code ends for each outcome."""


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(Outcome.SUCCESS, id="success_keeps_slot_warm"),
        pytest.param(Outcome.REVERT, id="revert_cools_slot"),
        pytest.param(Outcome.HALT, id="halt_cools_slot"),
    ],
)
def test_slot_warmth_after_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: Outcome,
) -> None:
    """
    Read a storage slot in one frame and price its read in the next.

    EIP-8141 "Cross-frame interactions": "For the purposes of gas
    accounting of warm / cold state status, the journal of such touches
    is shared across frames", and "If a frame reverts, warm / cold
    status reverts to the state before the frame"; a frame that halts
    exceptionally is rolled back as one that reverts, consuming its
    budget besides.

    The first frame calls the reader, which reads the slot, and then
    succeeds, reverts or halts. The next frame runs the reader itself:
    after a success both the reader and its slot are warm; after a
    revert or a halt both are cold again. The reading frame's receipt
    prices the entry and the read at those temperatures, so a client
    that takes back the address but keeps the slot warm fails it.
    """
    sender = pre.fund_eoa()
    warm = outcome is Outcome.SUCCESS
    reader_code = Op.POP(Op.SLOAD(SLOT)) + Op.STOP
    reader = pre.deploy_contract(code=reader_code, storage={SLOT: 1})
    toucher_code = (
        Op.POP(Op.CALL(gas=Op.GAS, address=reader)) + ENDINGS[outcome]
    )
    toucher = pre.deploy_contract(code=toucher_code)
    second_read = Op.POP(Op.SLOAD(SLOT, key_warm=warm)) + Op.STOP

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=toucher,
                execution_gas=toucher_code.execution_cost(fork)
                + reader_code.execution_cost(fork),
                outcome=outcome,
            ),
            default_frame(target=reader, code=second_read, warm=warm),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_target_cold_after_value_balance_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Take back the warmth of a frame target whose value transfer failed
    its balance check.

    EIP-8141 "Behavior": the target's access is charged "before the
    balance check", and "if the caller does not have sufficient balance
    to transfer `frame.value`, the frame reverts"; "Cross-frame
    interactions": "If a frame reverts, warm / cold status reverts to
    the state before the frame."

    A sponsor pays, and the sender's `SENDER` frame sends a recipient
    one wei more than the sender holds. The frame pays the recipient's
    cold access at entry, then fails the balance check and reverts. A
    later frame reads the recipient's balance, priced cold again. A
    client that commits the entry access before the balance check
    prices that read warm.
    """
    value = 2
    sender = pre.fund_eoa(amount=value - 1)
    payer = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    probe_code: Bytecode = (
        Op.POP(Op.BALANCE(address=recipient, address_warm=False)) + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(
                target=recipient,
                value=value,
                state_gas_limit=0,
                outcome=Outcome.REVERT,
            ),
            default_frame(target=probe, code=probe_code, state_gas_limit=0),
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
        post={
            sender: Account(nonce=1, balance=value - 1),
            recipient: Account(balance=1),
        },
    )
