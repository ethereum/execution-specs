"""
Deployment tests for the expiry verifier contract of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The expiry verifier is an ordinary contract deployed by the pre-signed
creation transaction published in the EIP, from a synthetic sender whose
only transaction it is. The protocol does not install it at activation,
so these tests deploy it with that transaction before, at, and after the
fork block, and check that it lands at `Spec.EXPIRY_VERIFIER` with the
canonical runtime code and that an expiry frame then executes against
it.
"""

from os.path import realpath
from pathlib import Path
from typing import Generator

from execution_testing import (
    Account,
    Alloc,
    Block,
    DeploymentTestType,
    FrameReceipt,
    Op,
    Transaction,
    TransactionReceipt,
    generate_system_contract_deploy_test,
)
from execution_testing.checklists import EIPChecklist
from execution_testing.forks import Bogota, TransitionFork

from .helpers import expiry_frame, sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""


@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.Deployment.Missing()
@generate_system_contract_deploy_test(
    fork=Bogota,
    tx_json_path=Path(realpath(__file__)).parent
    / "expiry_verifier_deploy_tx.json",
    expected_deploy_address=Spec.EXPIRY_VERIFIER,
    fail_on_empty_code=False,
)
def test_expiry_verifier_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    post: Alloc,
    test_type: DeploymentTestType,
) -> Generator[Block, None, None]:
    """
    Verify the expiry verifier deployment and exercise the contract.

    Once the deployment transaction has run, a frame transaction
    carrying an expiry frame with a far-future expiry succeeds, which
    shows the deployed code is reachable as an expiry verifier frame
    target. A missing verifier makes no block invalid: nothing in the
    protocol calls it, so a block without the contract is valid.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            expiry_frame(),
            sender_frame(target=target),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS) for _ in range(3)
            ],
        ),
    )

    yield Block(txs=[tx])

    post[target] = Account(storage={SLOT_EXECUTED: 1})
