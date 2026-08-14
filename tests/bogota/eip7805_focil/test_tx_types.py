"""Tests EIP-7805 FOCIL inclusion-list handling across transaction types."""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from .spec import ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]


@pytest.mark.parametrize(
    "scenario",
    [
        "type_0_protected",
        "type_0_unprotected",
        "type_0_creation",
        "type_1_access_list",
        "type_1_creation",
        "type_2",
        "type_2_creation",
        "type_4_delegation",
    ],
)
def test_included_il_tx_of_each_type_is_readable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """
    Every transaction type is decodable in the inclusion list.

    Each scenario places one transaction of a given type in both the block
    body and the inclusion list. Because the transaction is present in the
    block body, the inclusion list check is satisfied only if the execution
    layer can decode it as a transaction type valid for the active fork.
    The post-state confirms the transaction also executed as expected.
    """
    sender = pre.fund_eoa()
    post: dict = {}

    match scenario:
        case "type_0_protected":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(
                ty=0, sender=sender, to=recipient, value=1, protected=True
            )
            post[recipient] = Account(balance=1)
        case "type_0_unprotected":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(
                ty=0, sender=sender, to=recipient, value=1, protected=False
            )
            post[recipient] = Account(balance=1)
        case "type_0_creation":
            il_tx = Transaction(ty=0, sender=sender, to=None, data=Op.STOP)
            post[il_tx.created_contract] = Account(nonce=1)
        case "type_1_access_list":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(
                ty=1,
                sender=sender,
                to=recipient,
                value=1,
                access_list=[
                    AccessList(address=recipient, storage_keys=[0x01])
                ],
            )
            post[recipient] = Account(balance=1)
        case "type_1_creation":
            il_tx = Transaction(
                ty=1,
                sender=sender,
                to=None,
                data=Op.STOP,
                access_list=[AccessList(address=sender, storage_keys=[0x01])],
            )
            post[il_tx.created_contract] = Account(nonce=1)
        case "type_2":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(ty=2, sender=sender, to=recipient, value=1)
            post[recipient] = Account(balance=1)
        case "type_2_creation":
            il_tx = Transaction(ty=2, sender=sender, to=None, data=Op.STOP)
            post[il_tx.created_contract] = Account(nonce=1)
        case "type_4_delegation":
            authority = pre.fund_eoa()
            delegate_target = pre.deploy_contract(code=Op.STOP)
            il_tx = Transaction(
                ty=4,
                sender=sender,
                to=sender,
                authorization_list=[
                    AuthorizationTuple(
                        address=delegate_target, signer=authority
                    )
                ],
            )
            # A valid authorization bumps the authority's nonce and sets its
            # delegation designation.
            post[authority] = Account(nonce=1)
        case _:
            raise ValueError(f"unknown scenario: {scenario}")

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[il_tx],
                inclusion_list_txs=[il_tx],
                expected_inclusion_list_satisfied=True,
            )
        ],
    )
