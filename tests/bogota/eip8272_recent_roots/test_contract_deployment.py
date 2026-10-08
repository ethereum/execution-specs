"""
Deployment tests for the recent root contract of
[EIP-8272: Recent Roots for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8272).

The recent root contract is an ordinary contract deployed by the
pre-signed creation transaction published in the EIP, from a synthetic
sender whose only transaction it is. The protocol does not install it at
activation, so these tests deploy it with that transaction before, at,
and after the fork block, and check that it lands at
`Spec.RECENT_ROOT_ADDRESS` with the canonical runtime code and that a
root can then be published and verified through it.
"""

from os.path import realpath
from pathlib import Path
from typing import Generator

from execution_testing import (
    Account,
    Alloc,
    Block,
    DeploymentTestType,
    Op,
    Transaction,
    generate_system_contract_deploy_test,
)
from execution_testing.checklists import EIPChecklist
from execution_testing.forks import Bogota, TransitionFork

from ..eip8141_frame_transactions.helpers import sender_frame, verify_frame
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

PUBLISH_SLOT = 1_000
"""Slot of the block publishing a root after the deployment."""

SALT = bytes(32)

ROOT = (0xF0).to_bytes(32, "big")


@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.Deployment.Missing()
@generate_system_contract_deploy_test(
    fork=Bogota,
    tx_json_path=Path(realpath(__file__)).parent
    / "recent_root_deploy_tx.json",
    expected_deploy_address=Spec.RECENT_ROOT_ADDRESS,
    fail_on_empty_code=False,
)
def test_recent_root_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    post: Alloc,
    test_type: DeploymentTestType,
) -> Generator[Block, None, None]:
    """
    Verify the recent root contract deployment and exercise the contract.

    Once the deployment transaction has run, a frame transaction
    publishes a root and a frame transaction in the next slot verifies
    it, which shows the deployed code is reachable both as a call target
    and as a recent root verifier frame target. A missing contract makes
    no block invalid: nothing in the protocol calls it, so a block
    without the contract is valid.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source = source_id(sender, SALT)

    yield Block(
        slot_number=PUBLISH_SLOT,
        txs=[
            Transaction(
                sender=sender,
                frames=[verify_frame(), write_frame(SALT, ROOT)],
            )
        ],
    )
    yield Block(
        slot_number=PUBLISH_SLOT + 1,
        txs=[
            Transaction(
                sender=sender,
                frames=[
                    recent_root_frame(
                        validation_tuple(source, PUBLISH_SLOT, ROOT)
                    ),
                    verify_frame(),
                    sender_frame(target=target),
                ],
            )
        ],
    )

    deployed = post[Spec.RECENT_ROOT_ADDRESS]
    assert deployed is not None
    post[Spec.RECENT_ROOT_ADDRESS] = Account(
        nonce=deployed.nonce,
        code=deployed.code,
        storage={
            storage_key(source, PUBLISH_SLOT): int.from_bytes(
                entry_hash(source, PUBLISH_SLOT, ROOT), "big"
            )
        },
    )
    post[target] = Account(storage={SLOT_EXECUTED: 1})
