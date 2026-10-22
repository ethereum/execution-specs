"""
Exercise the Merkle Patricia Trie via account addresses.

The account trie adds bookkeeping to the node operations the storage
tests cover: accounts are deleted and re-created, each leaf value carries
a storage root, and every block touches accounts the test does not
choose (sender, coinbase, system contracts). The tests use mined
addresses (`*_ADDRS_*` in `constants.py`).

Because of those accounts, shape assertions run over `pre`, which holds
the whole genesis of the fixture being filled (plus the coinbase after
the block), and pin only the nodes around the mined group; an
uncontrolled account sharing the group's prefix fails the fill.

A committed account leaf can only be deleted by a contract created in the
same transaction (EIP-6780). The deletion tests fund a mined address at
genesis and CREATE2 onto it through the deterministic factory with init
code that self-destructs at once: creation at a balance-only address is
legal, and the contract counts as created in the transaction. The init
code sends the balance to the sender, because from EIP-8246 a
self-destructed account keeps its balance and is removed only when that
balance is zero (EIP-161). From EIP-4758 no account can be deleted, so
the deletion tests run only before it.

Not expressible: emptying a committed storage trie in one step while its
account survives, and clearing a committed empty account (the filler
emits no empty genesis accounts). CREATE2 onto an address that holds
storage is out of scope.
"""

from typing import Iterable, List, Tuple

import pytest
from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    Withdrawal,
    compute_create2_address,
)
from execution_testing.base_types import StorageRootType

from .constants import (
    ADDR_EXT_MERGE_TRIO,
    COLLAPSE_SALT,
    DELETE_INITCODE,
    EXT_MERGE_SALT,
    GWEI,
    SHARE2_SALT,
    SHARE3_SALT,
    SINGLE_SLOT,
    SIXTEEN_ADDRS_BRANCH4,
    SIXTEEN_SALTS_BRANCH4,
    SLOT_WRITER,
    SURVIVOR_SALT,
    TWO_ADDRS_EXT4,
    TWO_ADDRS_EXT4_SIBLING_DEPTH1,
    TWO_ADDRS_EXT4_SIBLING_DEPTH3,
)
from .trie_shape import account_shape, covering, node_at

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.valid_from("Osaka"),
    pytest.mark.pre_alloc_group(
        "separate", reason="Asserts the shape of the whole account trie."
    ),
]

FUNDING = 10**18


def _create2_address(salt: int, initcode: bytes = DELETE_INITCODE) -> Address:
    """Return the address the factory creates for `initcode` under `salt`."""
    return compute_create2_address(
        DETERMINISTIC_FACTORY_ADDRESS, salt, initcode
    )


def _ensure_factory(pre: Alloc) -> None:
    """
    Put the deterministic factory into the genesis state.

    Forks with EIP-7997 allocate it at genesis; on the others the filler
    adds it with the first `deterministic_deploy_contract`, so deploy a
    trivial contract through it.
    """
    if DETERMINISTIC_FACTORY_ADDRESS not in pre:
        pre.deterministic_deploy_contract(deploy_code=Op.STOP)


def _delete_tx(sender: EOA, salt: int) -> Transaction:
    """Return a factory call that deploys `DELETE_INITCODE` under `salt`."""
    return Transaction(
        sender=sender,
        to=DETERMINISTIC_FACTORY_ADDRESS,
        data=Hash(salt) + DELETE_INITCODE,
    )


def _after_block(
    genesis: Iterable[Address], *removed: Address
) -> List[Address]:
    """Return `genesis` after a block: `removed` gone, the coinbase added."""
    return [a for a in genesis if a not in removed] + [
        Environment().fee_recipient
    ]


def _fund_collapse_pair(pre: Alloc) -> Tuple[Address, Address, EOA]:
    """
    Fund a survivor and a deletable sibling that share four nibbles.

    Return both and a funded sender; the pair sits under one 2-child
    branch at depth 4.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = _create2_address(COLLAPSE_SALT)
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    assert node_at(account_shape(pre, survivor), 4) == ("branch", 2)
    return survivor, doomed, sender


# --- shapes present at genesis ------------------------------------------


def test_genesis_extension_and_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Two funded addresses sharing four nibbles sit under one branch.

    pre:  .. -> branch@4 -> {leaf, leaf}
    post: unchanged (an unrelated transfer)
    """
    a, b = (Address(x) for x in TWO_ADDRS_EXT4)
    pre.fund_address(a, amount=1)
    pre.fund_address(b, amount=2)
    sender, recipient = pre.fund_eoa(), pre.fund_eoa(amount=1)
    assert node_at(account_shape(pre, a), 4) == ("branch", 2)

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=recipient),
        post={a: Account(balance=1), b: Account(balance=2)},
    )


def test_genesis_full_branch_arity_sixteen(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Sixteen funded addresses sharing four nibbles fill one branch.

    pre:  .. -> branch@4 -> {16 x leaf}
    post: unchanged (an unrelated transfer)
    """
    addresses = [Address(x) for x in SIXTEEN_ADDRS_BRANCH4]
    for i, address in enumerate(addresses):
        pre.fund_address(address, amount=i + 1)
    sender, recipient = pre.fund_eoa(), pre.fund_eoa(amount=1)
    assert node_at(account_shape(pre, addresses[0]), 4) == ("branch", 16)

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=recipient),
        post={a: Account(balance=i + 1) for i, a in enumerate(addresses)},
    )


# --- inserts during execution -----------------------------------------


def _pay_each(addresses: List[Address]) -> Bytecode:
    """Return code that sends 1 wei to each address in turn."""
    code = Bytecode()
    for address in addresses:
        code += Op.POP(Op.CALL(gas=Op.GAS, address=address, value=1))
    return code + Op.STOP


def test_insert_full_branch_during_execution(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    A contract pays sixteen mined addresses, creating their leaves.

    pre:  no branch at depth 4 on the group's path
    post: .. -> branch@4 -> {16 x leaf}
    """
    addresses = [Address(x) for x in SIXTEEN_ADDRS_BRANCH4]
    payer = pre.deploy_contract(code=_pay_each(addresses), balance=16)
    sender = pre.fund_eoa()
    assert covering(account_shape(pre, addresses[0]), 4)[1] != "branch"
    after = _after_block(pre) + addresses
    assert node_at(account_shape(after, addresses[0]), 4) == ("branch", 16)

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=payer),
        post={
            payer: Account(balance=0),
            **{a: Account(balance=1) for a in addresses},
        },
    )


def test_touched_empty_account_never_persists(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    A zero-value call to a never-seen address creates no leaf.

    pre:  no leaf for the target
    post: none; EIP-161 removes the touched empty account
    """
    target = pre.fund_eoa(amount=0)
    assert target not in pre

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=target, value=0),
        post={target: Account.NONEXISTENT},
    )


# --- delete and re-create inside one block ------------------------------


@pytest.mark.valid_before("EIP4758")
def test_account_deleted_and_recreated_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Delete a leaf and re-create it by a value transfer in the same block.

    pre:  .. -> branch@4 -> {survivor, doomed}
    post: the same shape; doomed is a balance-only leaf again
    The value transfer wins over the deletion earlier in the block.
    """
    survivor, doomed, sender = _fund_collapse_pair(pre)
    after = account_shape(_after_block(pre), survivor)
    assert node_at(after, 4) == ("branch", 2)

    blockchain_test(
        pre=pre,
        post={
            survivor: Account(balance=1),
            doomed: Account(balance=1, nonce=0, code=b"", storage={}),
        },
        blocks=[
            Block(
                txs=[
                    _delete_tx(sender, COLLAPSE_SALT),
                    Transaction(sender=sender, to=doomed, value=1),
                ]
            )
        ],
    )


@pytest.mark.parametrize(
    "pre_storage,value",
    [
        pytest.param({}, 1, id="empty_to_hash"),
        pytest.param({SINGLE_SLOT: 1}, 0, id="hash_to_empty"),
    ],
)
@pytest.mark.valid_before("EIP4758")
def test_storage_root_flip_with_account_shape_change(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_storage: StorageRootType,
    value: int,
) -> None:
    """
    The collapse survivor is a contract whose storage root flips.

    pre:  .. -> ext -> branch@4 -> {survivor contract, doomed}
    post: .. -> leaf whose value carries the flipped storage root
    The survivor's storage root and its path change in the same block.
    """
    doomed = _create2_address(COLLAPSE_SALT)
    survivor = pre.deterministic_deploy_contract(
        deploy_code=SLOT_WRITER, salt=SURVIVOR_SALT, storage=pre_storage
    )
    pre.fund_address(doomed, amount=FUNDING)
    sender = pre.fund_eoa()
    before = account_shape(pre, survivor)
    assert node_at(before, 4) == ("branch", 2)
    assert before[before.index((4, "branch", 2)) - 1][1] == "ext"
    after = account_shape(_after_block(pre, doomed), survivor)
    assert covering(after, 4)[1] == "leaf"
    post_storage = {SINGLE_SLOT: value} if value else {}

    blockchain_test(
        pre=pre,
        post={
            survivor: Account(storage=post_storage),
            doomed: Account.NONEXISTENT,
        },
        blocks=[
            Block(
                txs=[
                    _delete_tx(sender, COLLAPSE_SALT),
                    Transaction(
                        sender=sender,
                        to=survivor,
                        data=Hash(SINGLE_SLOT) + Hash(value),
                    ),
                ]
            )
        ],
    )


@pytest.mark.valid_before("EIP4758")
def test_code_hash_flip_with_account_shape_change(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Code is deployed onto the collapse survivor, a balance-only account.

    pre:  .. -> ext -> branch@4 -> {survivor, doomed}
    post: .. -> leaf whose value carries the survivor's new code hash
    The survivor's code hash and its path change in the same block.
    """
    initcode = bytes(Initcode(deploy_code=SLOT_WRITER))
    survivor = _create2_address(SURVIVOR_SALT, initcode)
    sender = pre.fund_eoa()
    doomed = _fund_collapse(pre, [survivor], COLLAPSE_SALT, 4, "ext", "leaf")

    blockchain_test(
        pre=pre,
        post={
            survivor: Account(nonce=1, balance=1, code=SLOT_WRITER),
            doomed: Account.NONEXISTENT,
        },
        blocks=[
            Block(
                txs=[
                    _delete_tx(sender, COLLAPSE_SALT),
                    Transaction(
                        sender=sender,
                        to=DETERMINISTIC_FACTORY_ADDRESS,
                        data=Hash(SURVIVOR_SALT) + initcode,
                    ),
                ]
            )
        ],
    )


@pytest.mark.valid_before("EIP4758")
def test_delete_and_update_survivor_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Delete one sibling and credit the other within one block.

    pre:  .. -> branch@4 -> {survivor = 1 wei, doomed}
    post: .. -> leaf survivor = 2 wei
    The collapsed leaf carries the survivor's new balance.
    """
    survivor, doomed, sender = _fund_collapse_pair(pre)
    after = account_shape(_after_block(pre, doomed), survivor)
    assert covering(after, 4)[1] == "leaf"

    blockchain_test(
        pre=pre,
        post={survivor: Account(balance=2), doomed: Account.NONEXISTENT},
        blocks=[
            Block(
                txs=[
                    _delete_tx(sender, COLLAPSE_SALT),
                    Transaction(sender=sender, to=survivor, value=1),
                ]
            )
        ],
    )


@pytest.mark.valid_before("EIP4758")
def test_delete_resurrect_delete_across_blocks(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Delete a leaf, re-create it by a transfer, delete it again.

    pre:  .. -> branch@4 -> {survivor, doomed}
    post: block 1: leaf survivor; block 2: the pre shape; block 3: leaf
    The resurrected balance-only account is deployable again, so the
    same CREATE2 deletes it a second time from persisted nodes.
    """
    survivor, doomed, sender = _fund_collapse_pair(pre)
    after = account_shape(_after_block(pre, doomed), survivor)
    assert covering(after, 4)[1] == "leaf"

    blockchain_test(
        pre=pre,
        post={survivor: Account(balance=1), doomed: Account.NONEXISTENT},
        blocks=[
            Block(
                txs=[_delete_tx(sender, COLLAPSE_SALT)],
                expected_post_state={doomed: Account.NONEXISTENT},
            ),
            Block(
                txs=[Transaction(sender=sender, to=doomed, value=1)],
                expected_post_state={doomed: Account(balance=1)},
            ),
            Block(txs=[_delete_tx(sender, COLLAPSE_SALT)]),
        ],
    )


@pytest.mark.parametrize("amount", [1, 0], ids=["credited", "zero_amount"])
@pytest.mark.valid_before("EIP4758")
def test_resurrection_via_withdrawal(
    blockchain_test: BlockchainTestFiller, pre: Alloc, amount: int
) -> None:
    """
    Delete a leaf, then a withdrawal targets its address in the same block.

    pre:  .. -> branch@4 -> {survivor, doomed}
    post: the pre shape when the withdrawal credits the address, the
          collapsed leaf when it credits 0 Gwei
    Withdrawals apply after the transactions; a zero-amount one leaves no
    empty account behind.
    """
    survivor, doomed, sender = _fund_collapse_pair(pre)
    resurrected: Account | None
    if amount:
        resurrected = Account(balance=amount * GWEI)
        after = account_shape(_after_block(pre), survivor)
        assert node_at(after, 4) == ("branch", 2)
    else:
        resurrected = Account.NONEXISTENT
        after = account_shape(_after_block(pre, doomed), survivor)
        assert covering(after, 4)[1] == "leaf"

    blockchain_test(
        pre=pre,
        post={survivor: Account(balance=1), doomed: resurrected},
        blocks=[
            Block(
                txs=[_delete_tx(sender, COLLAPSE_SALT)],
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=0,
                        address=doomed,
                        amount=amount,
                    )
                ],
            )
        ],
    )


# --- collapses under a controlled parent ---------------------------------


def _fund_collapse(
    pre: Alloc,
    funded: List[Address],
    salt: int,
    depth: int,
    parent_kind: str,
    survivor_kind: str,
) -> Address:
    """
    Fund `funded` and the address `salt` creates; return the latter.

    Assert that the path of `funded[0]` holds a 2-child branch at `depth`
    below a `parent_kind` node and above a `survivor_kind` node, and how
    deleting the created account collapses it. Every other account must
    already be in `pre`.
    """
    doomed = _create2_address(salt)
    for address in funded:
        pre.fund_address(address, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    before = account_shape(pre, funded[0])
    assert node_at(before, depth) == ("branch", 2)
    assert before[before.index((depth, "branch", 2)) - 1][1] == parent_kind
    assert node_at(before, depth + 1)[0] == survivor_kind
    after = account_shape(_after_block(pre, doomed), funded[0])
    start, kind, size = covering(after, depth)
    if survivor_kind == "leaf":
        assert kind == "leaf"
    else:
        # The branch nibble, the survivor and an extension parent merge
        # into one extension that ends at the survivor's branch.
        below = [d for d, k, _ in before if d > depth and k == "branch"]
        assert kind == "ext" and start + size == below[0]
    return doomed


@pytest.mark.parametrize(
    "funded,salt,depth,parent_kind,survivor_kind",
    [
        pytest.param(
            [TWO_ADDRS_EXT4[0]],
            COLLAPSE_SALT,
            4,
            "ext",
            "leaf",
            id="leaf_under_ext",
        ),
        pytest.param(
            [TWO_ADDRS_EXT4[0], TWO_ADDRS_EXT4_SIBLING_DEPTH3],
            COLLAPSE_SALT,
            4,
            "branch",
            "leaf",
            id="leaf_under_branch",
        ),
        pytest.param(
            [*ADDR_EXT_MERGE_TRIO[:2]],
            EXT_MERGE_SALT,
            2,
            "ext",
            "ext",
            id="ext_under_ext",
        ),
        pytest.param(
            [*TWO_ADDRS_EXT4, TWO_ADDRS_EXT4_SIBLING_DEPTH1],
            SHARE2_SALT,
            2,
            "branch",
            "ext",
            id="ext_under_branch",
        ),
        pytest.param(
            [*TWO_ADDRS_EXT4, TWO_ADDRS_EXT4_SIBLING_DEPTH1],
            SHARE3_SALT,
            3,
            "ext",
            "branch",
            id="branch_under_ext",
        ),
        pytest.param(
            [
                TWO_ADDRS_EXT4[0],
                TWO_ADDRS_EXT4_SIBLING_DEPTH3,
                TWO_ADDRS_EXT4_SIBLING_DEPTH1,
            ],
            SHARE2_SALT,
            2,
            "branch",
            "branch",
            id="branch_under_branch",
        ),
    ],
)
@pytest.mark.valid_before("EIP4758")
def test_delete_collapses_under_controlled_parent(
    state_test: StateTestFiller,
    pre: Alloc,
    funded: List[int],
    salt: int,
    depth: int,
    parent_kind: str,
    survivor_kind: str,
) -> None:
    """
    Delete one child of a 2-child branch below a mined parent node.

    pre:  .. -> parent -> branch@d -> {doomed, survivor}
    post: .. -> parent -> survivor, extended by the branch nibble; under
          an extension parent the two merge into one node
    Mined siblings at depths 1 and 3 fix the parent kind whatever the
    uncontrolled accounts are; a collision fails the shape assert.
    """
    addresses = [Address(x) for x in funded]
    sender = pre.fund_eoa()
    doomed = _fund_collapse(
        pre, addresses, salt, depth, parent_kind, survivor_kind
    )

    state_test(
        pre=pre,
        tx=_delete_tx(sender, salt),
        post={
            **{a: Account(balance=1) for a in addresses},
            doomed: Account.NONEXISTENT,
        },
    )


@pytest.mark.valid_before("EIP4758")
def test_delete_from_three_child_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Delete one of three accounts under one branch.

    pre:  .. -> branch@4 -> {p, q, doomed}
    post: .. -> branch@4 -> {p, q}
    """
    p, q = (Address(x) for x in TWO_ADDRS_EXT4)
    doomed = _create2_address(COLLAPSE_SALT)
    pre.fund_address(p, amount=1)
    pre.fund_address(q, amount=2)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    assert node_at(account_shape(pre, p), 4) == ("branch", 3)
    after = account_shape(_after_block(pre, doomed), p)
    assert node_at(after, 4) == ("branch", 2)

    state_test(
        pre=pre,
        tx=_delete_tx(sender, COLLAPSE_SALT),
        post={
            p: Account(balance=1),
            q: Account(balance=2),
            doomed: Account.NONEXISTENT,
        },
    )


@pytest.mark.valid_before("EIP4758")
def test_mass_delete_sixteen_to_one(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Delete fifteen of sixteen accounts under one branch in one block.

    pre:  .. -> ext -> branch@4 -> {survivor, 15 x doomed}
    post: .. -> leaf survivor
    The branch collapses onto the survivor, which merges with the
    extension above.
    """
    survivor = Address(SIXTEEN_ADDRS_BRANCH4[0])
    doomed = [_create2_address(s) for s in SIXTEEN_SALTS_BRANCH4]
    pre.fund_address(survivor, amount=1)
    for address in doomed:
        pre.fund_address(address, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    before = account_shape(pre, survivor)
    assert node_at(before, 4) == ("branch", 16)
    assert before[before.index((4, "branch", 16)) - 1][1] == "ext"
    after = account_shape(_after_block(pre, *doomed), survivor)
    assert covering(after, 4)[1] == "leaf"

    blockchain_test(
        pre=pre,
        post={
            survivor: Account(balance=1),
            **dict.fromkeys(doomed, Account.NONEXISTENT),
        },
        blocks=[
            Block(txs=[_delete_tx(sender, s) for s in SIXTEEN_SALTS_BRANCH4])
        ],
    )
