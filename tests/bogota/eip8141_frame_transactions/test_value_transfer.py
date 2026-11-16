"""
Value transfer tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Only `SENDER` frames carry value. A frame paying an account other than
the sender is charged the value transfer cost — in the intrinsic cost
and the calldata floor alike — covering the recipient balance write
and the transfer log of [EIP-7708]; a frame paying the sender itself
is exempt and emits no log.

[EIP-7708]: https://eips.ethereum.org/EIPS/eip-7708
"""

from typing import Dict, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytes,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import (
    FrameTransaction,
    Outcome,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

TRANSFER_VALUE = 10**15
"""Value the frame under test transfers."""


@pytest.mark.parametrize(
    "target_kind",
    [
        pytest.param("other", id="target_other_account"),
        pytest.param("self_explicit", id="target_sender_explicitly"),
        pytest.param("self_empty", id="target_sender_via_empty_target"),
    ],
)
def test_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    target_kind: str,
) -> None:
    """
    Transfer value from a `SENDER` frame, pinning the transaction's
    cost and the frame receipt's logs.

    A frame whose explicit target differs from the sender is charged
    the value transfer cost — the pinned cost carries it in both
    settlement anchors — and its receipt holds the EIP-7708 transfer
    log. A frame paying the sender itself, explicitly or through an
    empty target resolving to it, is exempt and emits no log.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)

    if target_kind == "other":
        value_frame = sender_frame(
            target=recipient,
            value=TRANSFER_VALUE,
            logs=[transfer_log(sender, recipient, TRANSFER_VALUE)],
        )
    elif target_kind == "self_explicit":
        # The sender seeds the warm set, so its own entry access is
        # warm.
        value_frame = sender_frame(
            target=sender, value=TRANSFER_VALUE, warm=True, logs=[]
        )
    else:
        value_frame = sender_frame(value=TRANSFER_VALUE, logs=[])

    # Neither frame runs code beyond its target's entry access, so the
    # floor may bind; both anchors carry the value transfer cost, so
    # the pin exercises it either way.
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[verify_frame(logs=[]), value_frame],
    )

    post = {sender: Account(nonce=1)}
    if target_kind == "other":
        post[recipient] = Account(balance_change=TRANSFER_VALUE)

    state_test(pre=pre, tx=tx, post=post)


def transfer_exceeding_balance(
    pre: Alloc, fork: Fork, recipient: Address
) -> Tuple[Transaction, Dict[Address, Account]]:
    """
    Return a transaction whose `SENDER` frame sends `recipient` one wei
    more than the sender holds, with a sponsor paying, and its post-state.
    """
    sender = pre.fund_eoa(amount=TRANSFER_VALUE)
    payer = pre.fund_eoa()
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(
                target=recipient,
                value=TRANSFER_VALUE + 1,
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
    post = {
        sender: Account(nonce=1, balance_change=0),
        recipient: Account(balance_change=0),
    }
    return tx, post


@pytest.mark.parametrize(
    "recipient_delegated",
    [
        pytest.param(False, id="recipient_eoa"),
        pytest.param(True, id="recipient_delegated_eoa"),
    ],
)
def test_value_transfer_exceeding_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    recipient_delegated: bool,
) -> None:
    """
    Transfer more value than the sender holds, with a sponsor paying.

    The balance check happens after the target's access is charged, so
    the reverting frame's receipt reports that access rather than
    nothing. A delegated recipient's designation is resolved only when
    the frame is dispatched, after the balance check, so the failed
    frame neither pays for nor reads the delegate. A sponsor pays the
    gas, keeping the shortfall a property of the sender's balance
    alone, and a `SENDER` frame's failure leaves the transaction valid.
    """
    bal_accounts: Dict[Address, BalAccountExpectation | None] = {}
    if recipient_delegated:
        delegate = pre.deploy_contract(code=Op.STOP)
        recipient = pre.fund_eoa(amount=1, delegation=delegate)
        bal_accounts[delegate] = None
    else:
        recipient = pre.fund_eoa(amount=1)
    bal_accounts[recipient] = BalAccountExpectation.empty()
    tx, post = transfer_exceeding_balance(pre, fork, recipient)
    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=bal_accounts
        ),
    )


@pytest.mark.with_all_precompiles
def test_value_transfer_exceeding_balance_to_precompile_delegate(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: int,
) -> None:
    """
    Transfer more value than the sender holds to an account delegated to
    a precompile.

    A precompile is always warm, so a client that reads the delegate on
    the failed transfer pays nothing for it, and only the block access
    list, which must not list the precompile, shows the read.
    """
    recipient = pre.fund_eoa(amount=1, delegation=Address(precompile))
    tx, post = transfer_exceeding_balance(pre, fork, recipient)
    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                recipient: BalAccountExpectation.empty(),
                Address(precompile): None,
            }
        ),
    )
