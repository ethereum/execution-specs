"""
End-to-end state-divergence tests for the EIP-8297 partitioned binary
tree.

`tests/binary_trie/test_differential_mpt.py` pins, at the raw
state-provider level, that the MPT provider keeps a deleted account's
storage trie around while the PBT provider (what the `BinaryTree` fork
actually uses) pops it in the same step that pops the account. This is
reachable through EIP-7610, which gates `CREATE2` on
`account_has_storage`. These tests pin the END-TO-END consequence of
that divergence as observed through the EEST `fill` pipeline under
`BinaryTree`, as CURRENT behavior — not as an endorsement of either
provider's choice.
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

from .helpers import create_contract_via_factory
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
    code) but carries storage — a shape ordinary execution can never
    reach on its own, only the pre-alloc API can construct it directly
    — fills and persists into the post state unchanged.

    `deploy_contract` is the API that accepts this combination
    directly (`fund_eoa`'s `storage` parameter is typed `Storage`
    only, not the broader `Storage | StorageRootType` a plain dict
    literal satisfies); passing `code=b""` is what makes the account
    genuinely codeless, and overriding its default `nonce=1` down to
    `0` is what makes the resulting shape -- codeless, yet holding
    storage -- unreachable by ordinary execution, exactly the
    "impossible" mutation `pre_alloc_mutable` exists for.
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
    Pin what the `BinaryTree` fork actually does when a CREATE2 call
    targets an address that held storage, was cleared under EIP-161 in
    an earlier block, and is retargeted by CREATE2 in a later block —
    the end-to-end shape of the divergence pinned by
    `tests/binary_trie/test_differential_mpt.py`'s
    `test_account_delete_diverges_on_account_has_storage`.

    THIS OUTCOME DIFFERS FROM THE MPT PROVIDERS': under MPT, the
    orphaned storage trie would still make `account_has_storage` true
    for this address, so the SAME CREATE2 would be rejected as a
    collision and the address would keep its stale storage untouched.
    Under the PBT provider that `BinaryTree` actually runs, deleting
    the account pops its storage outright, so `account_has_storage`
    reads false afterward and this CREATE2 is allowed to proceed. This
    is a known open consensus question recorded in the PR, not a bug
    in either provider — this test pins BinaryTree's CURRENT behavior;
    it does not bless that behavior as correct.

    The clearing step is a zero-balance SELFDESTRUCT that names
    `target` as beneficiary, rather than a zero-value CALL to it: this
    fork's `modify_state` (`state_tracker.py`) re-checks "exists and
    is empty, so destroy" after EVERY write it mediates — balance,
    nonce, or code alike — but a zero-value CALL to a plain account
    never reaches `modify_state` for the recipient at all: the
    value-transfer step that would (`move_ether`) only runs when
    `message.should_transfer_value and message.value != 0`, and there
    is no code to execute that could mediate any other write.
    `SELFDESTRUCT` always writes the beneficiary's balance via
    `move_ether` unconditionally, even to add zero, so it reaches
    `modify_state`, and therefore the destroy check, regardless.
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
            factory: Account(nonce=2),
        },
    )


@pytest.mark.pre_alloc_mutable()
def test_create2_into_storage_holding_codeless_address_without_clearing(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Pin the result of the straight EIP-7610 shape, with NO prior
    clearing: CREATE2 targets an address that, from genesis, already
    holds storage but no code/nonce.

    Unlike the clear-then-recreate scenario above, MPT and PBT do NOT
    diverge here — the storage was never deleted/orphaned, so both
    providers agree the target's `account_has_storage` is true, and
    CREATE2 is rejected as a collision on BOTH. This test only pins
    BinaryTree's (PBT's) side, which is ordinary, unsurprising
    EIP-7610 behavior with no open question attached.
    """
    old_slot, old_value = 7, 0xFEED
    new_slot, new_value = 8, 0x1234
    salt = 0x51DF

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

    tx = Transaction(sender=pre.fund_eoa(), to=factory)

    state_test(
        pre=pre,
        post={
            target: Account(nonce=0, code=b"", storage={old_slot: old_value}),
            factory: Account(nonce=2),
        },
        tx=tx,
    )
