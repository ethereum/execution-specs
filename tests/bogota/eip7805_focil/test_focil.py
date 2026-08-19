"""Tests EIP-7805 FOCIL handling of IL txs included in the block body."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Fork,
    Op,
    RecipientType,
    Transaction,
)

from .spec import ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]


@pytest.mark.parametrize("order", ["equal", "inverse"])
def test_block_with_same_sender_included_il_txs_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    order: str,
) -> None:
    """Including two IL txs from one sender keeps the payload valid."""
    alice = pre.fund_eoa()
    bob = pre.nonexistent_account()

    included_il_tx_0 = Transaction(sender=alice, to=bob, value=1)
    included_il_tx_1 = Transaction(sender=alice, to=bob, value=2)

    block_txs = [included_il_tx_0, included_il_tx_1]
    inclusion_list_txs = [included_il_tx_0, included_il_tx_1]
    if order == "inverse":
        inclusion_list_txs.reverse()

    blockchain_test(
        pre=pre,
        post={bob: Account(balance=3)},
        blocks=[
            Block(
                txs=block_txs,
                inclusion_list_txs=inclusion_list_txs,
                expected_inclusion_list_satisfied=True,
            )
        ],
    )


@pytest.mark.parametrize("excluded_position", ["start", "middle", "end"])
def test_block_with_same_sender_missing_il_txs_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    excluded_position: str,
) -> None:
    """
    Omitting a same-sender IL tx leaves the payload unsatisfied.

    Two of Alice's IL txs are in the block body, a third appears only in
    the inclusion list. After the body executes, Alice's nonce matches the
    omitted tx, so it is appendable and the block is IL unsatisfied
    regardless of the omitted tx's position in the list.
    """
    alice = pre.fund_eoa()
    bob = pre.nonexistent_account()

    included_il_tx_0 = Transaction(sender=alice, to=bob, value=1)
    included_il_tx_1 = Transaction(sender=alice, to=bob, value=2)

    block_txs = [included_il_tx_0, included_il_tx_1]
    inclusion_list_txs = [included_il_tx_0, included_il_tx_1]

    excluded_il_tx_0 = Transaction(sender=alice, to=bob, value=3)
    match excluded_position:
        case "start":
            inclusion_list_txs.insert(0, excluded_il_tx_0)
        case "middle":
            inclusion_list_txs.insert(1, excluded_il_tx_0)
        case "end":
            inclusion_list_txs.insert(2, excluded_il_tx_0)
        case _:
            raise ValueError(f"unknown position: {excluded_position}")

    blockchain_test(
        pre=pre,
        post={bob: Account(balance=3)},
        blocks=[
            Block(
                txs=block_txs,
                inclusion_list_txs=inclusion_list_txs,
                expected_inclusion_list_satisfied=False,
            )
        ],
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "call_reverts",
        "call_invalid",
        "creation_init_reverts",
        "value_to_new_account_oog",
        "delegate_to_new_account_oog",
        pytest.param(
            "creation_address_collision",
            marks=pytest.mark.pre_alloc_mutable,
        ),
    ],
)
def test_block_with_failing_included_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    scenario: str,
) -> None:
    """
    An IL tx that fails during execution is still counted as included.

    Each scenario places one transaction in both the block body and the
    inclusion list. The transaction is a valid, includable tx that
    nonetheless fails while executing: it reverts, hits an invalid opcode,
    fails or collides on contract creation, or runs out of gas on the
    top-frame surcharge charged after the intrinsic cost. Because the tx is
    present in the block body, the inclusion list check is satisfied and the
    block stays valid regardless of the execution failure.
    """
    sender = pre.fund_eoa()
    post: dict = {sender: Account(nonce=1)}

    match scenario:
        case "call_reverts":
            contract = pre.deploy_contract(code=Op.REVERT(0, 0))
            failing_il_tx = Transaction(sender=sender, to=contract)
        case "call_invalid":
            contract = pre.deploy_contract(code=Op.INVALID)
            failing_il_tx = Transaction(sender=sender, to=contract)
        case "creation_init_reverts":
            failing_il_tx = Transaction(
                sender=sender, to=None, data=Op.REVERT(0, 0)
            )
            # Init code reverted, so no contract is deployed.
            post[failing_il_tx.created_contract] = Account.NONEXISTENT
        case "value_to_new_account_oog":
            # Gas covers the intrinsic cost (so the tx is includable) but
            # not the top-frame ``NEW_ACCOUNT`` surcharge for creating the
            # empty recipient, so execution runs out of gas.
            recipient = pre.nonexistent_account()
            intrinsic = fork.transaction_intrinsic_cost_calculator()()
            top_frame_regular = fork.transaction_top_frame_gas_calculator()(
                sends_value=True,
                recipient_type=RecipientType.EMPTY_ACCOUNT,
            )
            top_frame_state = fork.transaction_top_frame_state_gas(
                sends_value=True,
                recipient_type=RecipientType.EMPTY_ACCOUNT,
            )
            failing_il_tx = Transaction(
                sender=sender,
                to=recipient,
                value=1,
                gas_limit=(
                    intrinsic + top_frame_regular + top_frame_state - 1
                ),
            )
            # Out of gas rolls back the value transfer to the new account.
            post[recipient] = Account.NONEXISTENT
        case "delegate_to_new_account_oog":
            # A type-4 tx whose authority is an empty account: the
            # top-frame ``AUTH_PER_EMPTY_ACCOUNT`` charge is left one gas
            # short, so the authorization phase runs out of gas.
            authority = pre.fund_eoa(amount=0)
            delegate_target = pre.deploy_contract(code=Op.STOP)
            authorization = AuthorizationTuple(
                address=delegate_target, signer=authority
            )
            intrinsic = fork.transaction_intrinsic_cost_calculator()(
                authorization_list_or_count=1
            )
            top_frame_regular = fork.transaction_top_frame_gas_calculator()(
                authorizations=[authorization],
            )
            top_frame_state = fork.transaction_top_frame_state_gas(
                authorizations=[authorization],
            )
            failing_il_tx = Transaction(
                sender=sender,
                to=sender,
                authorization_list=[authorization],
                gas_limit=(
                    intrinsic + top_frame_regular + top_frame_state - 1
                ),
            )
            # Out of gas rolls back the authorization, leaving the empty
            # authority undelegated.
            post[authority] = Account.NONEXISTENT
        case "creation_address_collision":
            # The creation target already has non-empty storage, so the
            # contract creation exceptionally aborts (EIP-7610) and the
            # pre-existing account is left untouched.
            failing_il_tx = Transaction(sender=sender, to=None, data=Op.STOP)
            collision_address = failing_il_tx.created_contract
            pre[collision_address] = Account(storage={0x01: 0x01})
            post[collision_address] = Account(storage={0x01: 0x01})
        case _:
            raise ValueError(f"unknown scenario: {scenario}")

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[failing_il_tx],
                inclusion_list_txs=[failing_il_tx],
                expected_inclusion_list_satisfied=True,
            )
        ],
    )
