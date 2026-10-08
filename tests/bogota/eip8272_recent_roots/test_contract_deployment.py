"""
Deployment tests for the recent root contract of
[EIP-8272: Recent Roots for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8272).

The recent root contract is an ordinary contract deployed by the
pre-signed creation transaction published in the EIP, from a synthetic
sender whose only transaction it is. The protocol does not install it at
activation, so these tests deploy it with that transaction before, at,
and after the fork block, and check that it lands at
`Spec.RECENT_ROOT_ADDRESS` with the canonical runtime code, that a root
published in the deployment block verifies in the next, and that a
verifier frame finds no contract before the deployment.
"""

from os.path import realpath
from pathlib import Path
from typing import Generator

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    DeploymentTestType,
    Environment,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    generate_system_contract_deploy_test,
)
from execution_testing.checklists import EIPChecklist
from execution_testing.forks import Bogota, TransitionFork

from ..eip8141_frame_transactions.helpers import sender_frame, verify_frame
from ..eip8141_frame_transactions.spec import Spec as FrameSpec
from .helpers import recent_root_frame, write_frame
from .spec import (
    Spec,
    entry_hash,
    ref_spec_8272,
    source_id,
    storage_key,
    validation_tuple,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_8272.git_path
REFERENCE_SPEC_VERSION = ref_spec_8272.version

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

SALT = bytes(32)
ROOT = (0xF0).to_bytes(32, "big")

WRITE_SLOT = 1_000
"""
Slot of the block publishing the root, past the slots of the generated
deployment blocks.
"""


@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.Deployment.Missing()
@generate_system_contract_deploy_test(
    fork=Bogota,
    tx_json_path=Path(realpath(__file__)).parent
    / "recent_root_deploy_tx.json",
    expected_deploy_address=Spec.RECENT_ROOT_ADDRESS,
    fail_on_empty_code=False,
)
def test_recent_root_contract_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    post: Alloc,
    test_type: DeploymentTestType,
) -> Generator[Block, None, None]:
    """
    Verify the recent root contract deployment and exercise the contract.

    Once the deployment transaction has run, a root published in the
    same block verifies through a recent root verifier frame in the next
    block, which shows the deployed code is reachable as both a root
    source target and a verifier frame target. A missing contract makes
    no block invalid: nothing in the protocol calls it, so a block
    without the contract is valid.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source = source_id(sender, SALT)

    publish = Transaction(
        sender=sender,
        frames=[verify_frame(), write_frame(SALT, ROOT)],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
            ],
        ),
    )
    yield Block(txs=[publish], slot_number=WRITE_SLOT)

    write_slot = WRITE_SLOT
    verify = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(validation_tuple(source, write_slot, ROOT)),
            verify_frame(),
            sender_frame(target=target),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS) for _ in range(3)
            ],
        ),
    )
    yield Block(txs=[verify], slot_number=WRITE_SLOT + 1)

    post[Spec.RECENT_ROOT_ADDRESS] = Account(
        nonce=Spec.RECENT_ROOT_NONCE,
        code=Spec.RECENT_ROOT_CODE,
        storage={
            storage_key(source, write_slot): int.from_bytes(
                entry_hash(source, write_slot, ROOT), "big"
            )
        },
    )
    post[target] = Account(storage={SLOT_EXECUTED: 1})


@pytest.mark.valid_from("Bogota")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_verifier_frame_before_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A recent root verifier frame executed before the contract is
    deployed finds no code at its target and runs EIP-8141's default
    `VERIFY` code, which fails because the frame's flags approve
    nothing; the transaction is invalid.
    """
    pre[Spec.RECENT_ROOT_ADDRESS] = Account(nonce=0, balance=1)
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    state_test(
        env=Environment(slot_number=Spec.VECTOR_CURRENT_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                recent_root_frame(
                    validation_tuple(
                        Spec.VECTOR_SOURCE_ID,
                        Spec.VECTOR_SLOT,
                        Spec.VECTOR_ROOT,
                    )
                ),
                verify_frame(),
                sender_frame(target=target),
            ],
            error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
        ),
        post={target: Account(storage={SLOT_EXECUTED: 0})},
    )
