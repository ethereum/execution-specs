"""
Storage access tests for the public mempool rules of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Before the payer is set, the validation prefix may only read the storage of
`tx.sender`, including through the contracts it calls. A read of any other
account's storage is valid on chain, but the mempool refuses the
transaction, since a write to that storage could invalidate it.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    Frame,
    MempoolTestFiller,
    Op,
    Transaction,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    APPROVE_ALL,
)

from .spec import MempoolRule, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

STORED_VALUE = 0x01
"""Value held in slot 0 of the account the validation prefix reads."""


@pytest.mark.parametrize(
    "storage_owner", ["sender", "callee"], ids=["sender", "callee"]
)
def test_sload_in_validation_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_owner: str,
) -> None:
    """
    Read a storage slot in the self-verifying `VERIFY` frame: the sender's
    own slot is admitted, while a slot of a contract the frame calls makes
    the mempool refuse the transaction.
    """
    if storage_owner == "sender":
        sender_code = Op.POP(Op.SLOAD(0)) + APPROVE_ALL
        sender = pre.deploy_contract(
            code=sender_code, storage={0: STORED_VALUE}, balance=10**18
        )
        broadcast = True
    elif storage_owner == "callee":
        callee = pre.deploy_contract(
            code=Op.POP(Op.SLOAD(0)) + Op.STOP, storage={0: STORED_VALUE}
        )
        sender_code = Op.POP(Op.CALL(gas=Op.GAS, address=callee)) + APPROVE_ALL
        sender = pre.deploy_contract(code=sender_code, balance=10**18)
        broadcast = False
    else:
        raise ValueError(f"unknown storage owner: {storage_owner}")

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame.verify()],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=broadcast,
        rules=[MempoolRule.STORAGE_OUTSIDE_SENDER],
    )
