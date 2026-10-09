"""
Deployment tests for the nonce manager of
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

The nonce manager is an ordinary contract deployed by the pre-signed
creation transaction published in the EIP, from a synthetic sender whose
only transaction it is. The protocol does not install it at activation,
so these tests deploy it with that transaction before, at, and after the
fork block, and check that it lands at `Spec.NONCE_MANAGER` with the
canonical runtime code and that a keyed nonce is then consumed into its
storage.
"""

from os.path import realpath
from pathlib import Path
from typing import Generator

from execution_testing import (
    Account,
    Alloc,
    Block,
    DeploymentTestType,
    Transaction,
    generate_system_contract_deploy_test,
)
from execution_testing.checklists import EIPChecklist
from execution_testing.forks import Bogota, TransitionFork

from ..eip8141_frame_transactions.helpers import verify_frame
from .helpers import NONCE_KEY
from .spec import Spec, keyed_nonce_slot, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version


@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.Deployment.Missing()
@generate_system_contract_deploy_test(
    fork=Bogota,
    tx_json_path=Path(realpath(__file__)).parent
    / "nonce_manager_deploy_tx.json",
    expected_deploy_address=Spec.NONCE_MANAGER,
    fail_on_empty_code=False,
)
def test_nonce_manager_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    post: Alloc,
    test_type: DeploymentTestType,
) -> Generator[Block, None, None]:
    """
    Verify the nonce manager deployment, then consume a keyed nonce into
    its storage.

    A fork block without the nonce manager is valid: clients do not
    check for it at the fork.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        nonce_keys=[NONCE_KEY],
        nonce=0,
    )

    yield Block(txs=[tx])

    post[Spec.NONCE_MANAGER] = Account(
        nonce=Spec.NONCE_MANAGER_NONCE,
        code=Spec.NONCE_MANAGER_CODE,
        storage={keyed_nonce_slot(sender, NONCE_KEY): 1},
    )
    post[sender] = Account(nonce=0)
