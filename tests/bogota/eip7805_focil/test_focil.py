"""Tests EIP-7805 FOCIL handling of IL txs included in the block body."""

import pytest
from execution_testing import (
    AccessList,
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
            top_frame = fork.transaction_top_frame_gas_calculator()(
                sends_value=True,
                recipient_type=RecipientType.EMPTY_ACCOUNT,
            )
            failing_il_tx = Transaction(
                sender=sender,
                to=recipient,
                value=1,
                gas_limit=intrinsic + top_frame - 1,
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
            top_frame = fork.transaction_top_frame_gas_calculator()(
                authorizations=[authorization],
            )
            failing_il_tx = Transaction(
                sender=sender,
                to=sender,
                authorization_list=[authorization],
                gas_limit=intrinsic + top_frame - 1,
            )
            # Out of gas rolls back the authorization, leaving the empty
            # authority undelegated.
            post[authority] = Account.NONEXISTENT
        case "creation_address_collision":
            # The creation target already has a nonce, so the contract
            # creation exceptionally aborts (EIP-684) and the pre-existing
            # account is left untouched.
            failing_il_tx = Transaction(sender=sender, to=None, data=Op.STOP)
            collision_address = failing_il_tx.created_contract
            pre[collision_address] = Account(nonce=1)
            post[collision_address] = Account(nonce=1)
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


def transfer_of_size(pre: Alloc, fork: Fork, size: int) -> Transaction:
    """Return a signed transfer whose RLP encoding is `size` bytes."""
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()
    calldata_size = size
    # Re-signing can shorten r or s by a leading zero byte, which can leave
    # the length search one byte either side of `size` for good, so a miss
    # also changes the calldata byte to draw a new signature.
    for calldata_byte in range(1, 256):
        calldata = bytes([calldata_byte]) * calldata_size
        tx = Transaction(
            sender=sender,
            nonce=0,
            to=recipient,
            data=calldata,
            gas_limit=fork.transaction_intrinsic_cost_calculator()(
                calldata=calldata
            ),
        ).with_signature_and_sender()
        encoded_size = len(tx.rlp())
        if encoded_size == size:
            return tx
        calldata_size += size - encoded_size
    raise AssertionError(f"no transfer encodes to {size} bytes")


@pytest.mark.parametrize("merged_lists", ["two_lists", "merged_list_limit"])
@pytest.mark.parametrize(
    "last_entry_in_block",
    [False, True],
    ids=["last_entry_omitted", "all_included"],
)
def test_inclusion_list_over_one_list_byte_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    merged_lists: str,
    last_entry_in_block: bool,
) -> None:
    """
    A payload's inclusion list may hold more bytes than one committee member
    can send, since the consensus layer merges several lists, and an entry
    past one list's limit still counts, up to the merged list's limit.
    """
    limit = fork.inclusion_list_transactions_size_limit()
    merged_limit = fork.inclusion_list_merged_transactions_size_limit()
    assert limit is not None and merged_limit is not None
    if merged_lists == "two_lists":
        entry_count = 2
    elif merged_lists == "merged_list_limit":
        entry_count = merged_limit // limit
        assert entry_count * limit == merged_limit
    else:
        raise ValueError(f"unknown merged lists: {merged_lists}")

    # Each entry fills one member's list, so every entry after the first
    # starts past one list's limit.
    entries = [transfer_of_size(pre, fork, limit) for _ in range(entry_count)]

    if last_entry_in_block:
        block_txs = entries
    else:
        block_txs = entries[:-1]

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=block_txs,
                inclusion_list_txs=entries,
                expected_inclusion_list_satisfied=last_entry_in_block,
            )
        ],
    )


@pytest.mark.parametrize(
    "entry",
    ["same_bytes", "access_list_changed", "authorization_list_changed"],
)
def test_il_entry_matched_to_block_tx_by_bytes(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    entry: str,
) -> None:
    """
    An IL entry counts as included only when a block tx has its exact bytes.

    The changed entries are a block tx with one list field changed. Its old
    signature now recovers to a different, funded sender, so the block left
    out an appendable transaction.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    recipient = pre.nonexistent_account()
    access_list = [AccessList(address=recipient, storage_keys=[])]
    authorization = AuthorizationTuple(
        address=recipient, signer=pre.fund_eoa()
    )
    extra_authorization = AuthorizationTuple(
        address=recipient, signer=pre.fund_eoa()
    )

    if entry == "same_bytes":
        # Satisfied under any matching rule, since including the tx spends
        # its nonce; this case shows the block tx it reuses is valid.
        block_tx = Transaction(
            ty=2, sender=pre.fund_eoa(), to=recipient, gas_limit=calc()
        ).with_signature_and_sender()
        il_entry = block_tx
        expected_satisfied = True
    elif entry == "access_list_changed":
        block_tx = Transaction(
            ty=2,
            sender=pre.fund_eoa(),
            to=recipient,
            # Room for the access list the IL entry adds.
            gas_limit=calc(access_list=access_list),
        ).with_signature_and_sender()
        il_entry = block_tx.copy(access_list=access_list, sender=None)
        expected_satisfied = False
    elif entry == "authorization_list_changed":
        block_tx = Transaction(
            ty=4,
            sender=pre.fund_eoa(),
            to=recipient,
            authorization_list=[authorization],
            # Room for the authorization the IL entry adds.
            gas_limit=calc(authorization_list_or_count=2),
        ).with_signature_and_sender()
        il_entry = block_tx.copy(
            authorization_list=[authorization, extra_authorization],
            sender=None,
        )
        expected_satisfied = False
    else:
        raise ValueError(f"unknown entry: {entry}")

    if il_entry is not block_tx:
        il_entry = il_entry.with_signature_and_sender()
        assert il_entry.sender is not None
        assert il_entry.sender != block_tx.sender
        pre.fund_address(il_entry.sender, 10**18)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[block_tx],
                inclusion_list_txs=[il_entry],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )
