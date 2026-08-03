"""
End-to-end state-divergence tests for the EIP-8297 partitioned binary
tree.

`test_differential_mpt.py` pins, at the provider level, that MPT keeps a
deleted account's storage trie while PBT (what `BinaryTree` uses) removes
it with the account; EIP-7610's `account_has_storage` gate on `CREATE2`
makes that divergence observable end-to-end. EIP-8297 settles the answer
for the tree, from whether a slot leaf of the address exists, and leaves
the Merkle Patricia Trie to the semantics it already had.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import FACTORY_CANARY_SLOT, create_contract_via_factory
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


@pytest.mark.pre_alloc_mutable()
def test_genesis_codeless_account_with_storage_persists(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a genesis allocation entry that is codeless (nonce zero, no
    code) but carries storage, unreachable by ordinary execution and
    only constructible directly via the pre-alloc API, fills and
    persists into the post state unchanged.
    """
    slot, value = 1, 0xABCD
    account = pre.deploy_contract(
        code=b"", storage={slot: value}, nonce=0, balance=0
    )

    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()
    tx = Transaction(sender=sender, to=recipient, value=1)

    state_test(
        pre=pre,
        post={
            account: Account(
                balance=0, nonce=0, code=b"", storage={slot: value}
            ),
            recipient: Account(balance=1),
        },
        tx=tx,
    )


@pytest.mark.pre_alloc_mutable()
def test_create2_after_eip161_clear_of_storage_holding_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Pin what the `BinaryTree` fork does when a CREATE2 call targets an
    address that held storage, was cleared under EIP-161 in an earlier
    block, and is retargeted by CREATE2 in a later block. This is the
    end-to-end shape of the divergence pinned at the provider level by
    `test_differential_mpt.py`'s
    `test_account_delete_diverges_on_account_has_storage`.

    This differs from MPT: there, the orphaned storage trie keeps
    `account_has_storage` true, so the same CREATE2 would be rejected
    as a collision. Under EIP-8297 an address has non-empty storage
    exactly when a slot leaf of it exists, and deleting the account
    removes its storage leaves, so no collision remains and CREATE2
    proceeds. The two answer differently because the tree has no
    `storage_root` node to consult; the Merkle Patricia Trie keeps the
    semantics it always had.

    The clearing step uses SELFDESTRUCT rather than a zero-value CALL:
    this fork's `modify_state` runs the destroy-if-empty check after
    every write it mediates, but a zero-value CALL's transfer step
    (`move_ether`) only runs when `message.value != 0`, so it never
    reaches `modify_state` for the recipient. SELFDESTRUCT always calls
    `move_ether` on the beneficiary, even for zero, so the destroy
    check is reached unconditionally.
    """
    old_slot, old_value = 3, 0xDEAD
    new_slot, new_value = 4, 0xC0DE
    salt = 0x51DE

    deploy_code = Op.STOP
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_prefix=Op.SSTORE(new_slot, new_value),
    )
    factory, target = create_contract_via_factory(
        pre, initcode, opcode=Op.CREATE2, salt=salt
    )
    pre[target] = Account(
        nonce=0, code=b"", balance=0, storage={old_slot: old_value}
    )

    # Zero balance itself: the sweep to `target` moves 0 wei, which is
    # enough to reach the destroy-if-empty check without introducing
    # any balance for `target` to clean up afterward.
    clearer = pre.deploy_contract(code=Op.SELFDESTRUCT(target), balance=0)
    sender = pre.fund_eoa()

    blocks = [
        Block(txs=[Transaction(sender=sender, to=clearer)]),
        Block(txs=[Transaction(sender=sender, to=factory)]),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            target: Account(
                nonce=1, code=deploy_code, storage={new_slot: new_value}
            ),
            factory: Account(nonce=2, storage={FACTORY_CANARY_SLOT: 1}),
        },
    )
