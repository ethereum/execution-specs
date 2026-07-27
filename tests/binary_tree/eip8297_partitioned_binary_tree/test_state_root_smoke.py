"""
Smoke tests proving the BinaryTree fork fills end to end: pre-state
allocation, transaction execution through the EELS t8n, and state
roots committed through the EIP-8297 binary tree.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-8297.md"
REFERENCE_SPEC_VERSION = "draft"


@pytest.mark.valid_from("BinaryTree")
def test_storage_write_smoke(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A single transaction writing one storage slot fills and commits
    through the binary tree.
    """
    sender = pre.fund_eoa()
    contract = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)

    tx = Transaction(
        sender=sender,
        to=contract,
    )

    state_test(
        pre=pre,
        post={contract: Account(storage={0: 1})},
        tx=tx,
    )
