"""EIP-7702 delegation lifecycle under the EIP-8297 binary tree."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


def test_same_target_reauthorization_keeps_designator(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify re-authorizing the same delegate twice bumps the nonce
    while the designator stays resident and keeps executing.
    """
    counter_slot = 1
    delegate = pre.deploy_contract(
        code=Op.SSTORE(counter_slot, Op.ADD(Op.SLOAD(counter_slot), 1))
        + Op.STOP
    )
    authority = pre.fund_eoa(0, delegation=delegate)
    authority_nonce = authority.nonce
    sender = pre.fund_eoa()

    def reauthorize(tuple_nonce: int) -> Transaction:
        return Transaction(
            sender=sender,
            to=authority,
            authorization_list=[
                AuthorizationTuple(
                    address=delegate,
                    nonce=tuple_nonce,
                    signer=authority,
                )
            ],
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[reauthorize(authority_nonce)]),
            Block(txs=[reauthorize(authority_nonce + 1)]),
        ],
        post={
            authority: Account(
                nonce=authority_nonce + 2,
                code=Spec7702.delegation_designation(delegate),
                storage={counter_slot: 2},
            ),
            delegate: Account(storage={}),
        },
    )
