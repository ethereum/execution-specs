"""
Exercise the Merkle Patricia Trie via account addresses.

The account trie runs the same node code as a storage trie in every
surveyed client; what differs is the bookkeeping around it: account
destruction and resurrection, the storage root carried inside the leaf
value, and the accounts every block touches (sender, coinbase, system
contracts). The tests here target that bookkeeping on mined addresses
(`*_ADDRS_*` in `constants.py`).

The account trie also holds accounts the test does not control, so shape
assertions are computed over the full genesis set (pre-alloc plus the
fork's system contracts, plus the coinbase after the block) and pin the
node kind around the mined group rather than the whole path; an
uncontrolled account sharing the group's prefix would fail the fill.

Deleting a committed account leaf on these forks is only possible for a
contract created in the same transaction (EIP-6780). The deletion tests
fund a mined address at genesis and CREATE2 onto it through the
deterministic factory with init code that immediately self-destructs:
creation at a balance-only address is legal, the contract counts as
created in the transaction, and the pre-existing leaf is removed. Not
expressible: wiping a committed storage trie in one step while its
account survives; EIP-161 clearing of a committed empty account (the
filler does not emit empty genesis accounts); and, excluded on purpose,
CREATE2 onto an address with pre-existing storage, where this
specification and geth currently disagree.
"""

from typing import Iterable, List

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
    Fork,
    Hash,
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
    EXT_MERGE_SALT,
    SHARE2_SALT,
    SHARE3_SALT,
    SINGLE_SLOT,
    SIXTEEN_ADDRS_BRANCH4,
    SIXTEEN_SALTS_BRANCH4,
    SURVIVOR_SALT,
    TWO_ADDRS_EXT4,
    TWO_ADDRS_EXT4_SIBLING_DEPTH1,
    TWO_ADDRS_EXT4_SIBLING_DEPTH3,
)
from .trie_shape import Shape, account_shape, covering, node_at

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")

FUNDING = 10**18
SLOT_WRITER = Op.SSTORE(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)) + Op.STOP

# The salts in `constants.py` were mined against exactly these bytes and
# this factory address; either changing would silently move every doomed
# address.
DELETE_INITCODE = bytes(Op.SELFDESTRUCT(Op.ORIGIN))
assert DELETE_INITCODE == bytes.fromhex("32ff")
assert DETERMINISTIC_FACTORY_ADDRESS == Address(
    0x4E59B44847B379578588920CA78FBF26C0B4956C
)


def create2_preimage(salt: int) -> bytes:
    """Address the deterministic factory creates for `salt`."""
    return bytes(
        compute_create2_address(
            DETERMINISTIC_FACTORY_ADDRESS, salt, DELETE_INITCODE
        )
    )


def _ensure_factory(pre: Alloc) -> None:
    """
    Bring the deterministic factory into the pre-alloc.

    The filler only injects it on first use of
    `deterministic_deploy_contract`, so deploy a trivial contract through
    it.
    """
    pre.deterministic_deploy_contract(deploy_code=Op.STOP)
    assert DETERMINISTIC_FACTORY_ADDRESS in pre


def _delete_tx(sender: EOA, salt: int) -> Transaction:
    """CREATE2 `DELETE_INITCODE` with `salt`; it self-destructs at once."""
    return Transaction(
        sender=sender,
        to=DETERMINISTIC_FACTORY_ADDRESS,
        data=Hash(salt) + DELETE_INITCODE,
    )


def _genesis(pre: Alloc, fork: Fork) -> List[Address]:
    """Every address in the genesis trie: pre-alloc and system contracts."""
    return [*pre, *(Address(a) for a in fork.pre_allocation_blockchain())]


def _after_block(
    genesis: Iterable[Address], *removed: Address
) -> List[Address]:
    """Addresses after a block: `removed` gone, the coinbase credited."""
    return [a for a in genesis if a not in removed] + [
        Environment().fee_recipient
    ]


def _shape(addresses: Iterable[Address], target: Address) -> Shape:
    return account_shape(addresses, target)


# --- shapes present at genesis ------------------------------------------


def test_genesis_extension_and_branch(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
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
    assert node_at(_shape(_genesis(pre, fork), a), 4) == ("branch", 2)

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=recipient),
        post={a: Account(balance=1), b: Account(balance=2)},
    )


def test_genesis_full_branch_arity_sixteen(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
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
    assert node_at(_shape(_genesis(pre, fork), addresses[0]), 4) == (
        "branch",
        16,
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=recipient),
        post={a: Account(balance=i + 1) for i, a in enumerate(addresses)},
    )


# --- inserts during execution -----------------------------------------


def _pay_each(addresses: List[Address]) -> Bytecode:
    code = Bytecode()
    for address in addresses:
        code += Op.POP(Op.CALL(Op.GAS, address, 1, 0, 0, 0, 0))
    return code + Op.STOP


def test_insert_full_branch_during_execution(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    A contract pays sixteen mined addresses, creating their leaves.

    pre:  no node at depth 4 on the group's path
    post: .. -> branch@4 -> {16 x leaf}
    """
    addresses = [Address(x) for x in SIXTEEN_ADDRS_BRANCH4]
    payer = pre.deploy_contract(code=_pay_each(addresses), balance=16)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    assert covering(_shape(genesis, addresses[0]), 4)[1] != "branch"
    after = _after_block(genesis) + addresses
    assert node_at(_shape(after, addresses[0]), 4) == ("branch", 16)

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
    A zero-value call to a never-seen address creates nothing.

    pre:  no leaf for the target
    post: still none
    Control: EIP-161 clears the transiently empty account before the root
    is computed.
    """
    target = pre.fund_eoa(amount=0)
    assert target not in pre

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=target, value=0),
        post={target: Account.NONEXISTENT},
    )


# --- deletes of committed leaves ----------------------------------------


def test_delete_collapses_branch_into_leaf(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete one of two funded accounts sharing four nibbles.

    pre:  .. -> ext -> branch@4 -> {survivor, doomed}
    post: .. -> leaf   (the survivor absorbs the nibble and the extension)
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    before = _shape(genesis, survivor)
    assert node_at(before, 4) == ("branch", 2)
    assert before[before.index((4, "branch", 2)) - 1][1] == "ext"
    assert covering(_shape(_after_block(genesis, doomed), survivor), 4)[1] == (
        "leaf"
    )

    state_test(
        pre=pre,
        tx=_delete_tx(sender, COLLAPSE_SALT),
        post={
            survivor: Account(balance=1),
            doomed: Account.NONEXISTENT,
        },
    )


def test_delete_merges_adjacent_extensions(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete the shallow sibling of a nested extension.

    pre:  .. -> ext -> branch@2 -> {doomed, ext(2) -> branch@5 -> {l1, l2}}
    post: .. -> ext -> branch@5 -> {l1, l2}   (one extension ends at 5)
    """
    l1, l2 = (Address(x) for x in ADDR_EXT_MERGE_TRIO[:2])
    doomed = Address(create2_preimage(EXT_MERGE_SALT))
    pre.fund_address(l1, amount=1)
    pre.fund_address(l2, amount=2)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    before = _shape(genesis, l1)
    assert node_at(before, 2) == ("branch", 2)
    assert before[before.index((2, "branch", 2)) - 1][1] == "ext"
    assert node_at(before, 3) == ("ext", 2)
    assert node_at(before, 5) == ("branch", 2)
    after = _shape(_after_block(genesis, doomed), l1)
    depth, kind, size = covering(after, 2)
    assert kind == "ext" and depth + size == 5
    assert node_at(after, 5) == ("branch", 2)

    state_test(
        pre=pre,
        tx=_delete_tx(sender, EXT_MERGE_SALT),
        post={
            l1: Account(balance=1),
            l2: Account(balance=2),
            doomed: Account.NONEXISTENT,
        },
    )


# --- delete and re-create inside one block ------------------------------


def test_account_deleted_and_recreated_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete a leaf and re-create it by a value transfer in the same block.

    pre:  .. -> branch@4 -> {survivor, doomed}
    post: the same shape; doomed is a balance-only leaf again
    A per-block destruction record must not shadow the later write.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    assert node_at(_shape(genesis, survivor), 4) == ("branch", 2)
    assert node_at(_shape(_after_block(genesis), survivor), 4) == (
        "branch",
        2,
    )

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
def test_storage_root_flip_with_account_shape_change(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    pre_storage: StorageRootType,
    value: int,
) -> None:
    """
    The collapse survivor is a contract whose storage root flips.

    pre:  .. -> ext -> branch@4 -> {survivor contract, doomed}
    post: .. -> leaf whose value carries the flipped storage root
    Storage root and account re-pathing change in one block diff. The
    survivor is created through the factory with a salt mined so that its
    address shares four nibbles with the doomed one.
    """
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    survivor = pre.deterministic_deploy_contract(
        deploy_code=SLOT_WRITER, salt=SURVIVOR_SALT, storage=pre_storage
    )
    pre.fund_address(doomed, amount=FUNDING)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    assert node_at(_shape(genesis, survivor), 4) == ("branch", 2)
    assert covering(_shape(_after_block(genesis, doomed), survivor), 4)[1] == (
        "leaf"
    )
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


def test_delete_and_update_survivor_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete one sibling and credit the other within one block.

    pre:  .. -> branch@4 -> {survivor = 1 wei, doomed}
    post: .. -> leaf survivor = 2 wei
    The collapsed leaf must carry the survivor's updated balance.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    assert node_at(_shape(genesis, survivor), 4) == ("branch", 2)
    assert covering(_shape(_after_block(genesis, doomed), survivor), 4)[1] == (
        "leaf"
    )

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


def test_delete_resurrect_delete_across_blocks(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete a leaf, re-create it by a transfer, delete it again.

    pre:  .. -> branch@4 -> {survivor, doomed}
    post: block 1: leaf survivor; block 2: the pre shape; block 3: leaf
    The resurrected balance-only account is deployable again, so the
    same CREATE2 deletes it a second time from persisted nodes.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    assert node_at(_shape(genesis, survivor), 4) == ("branch", 2)
    assert covering(_shape(_after_block(genesis, doomed), survivor), 4)[1] == (
        "leaf"
    )

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
def test_resurrection_via_withdrawal(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork, amount: int
) -> None:
    """
    Delete a leaf, then a withdrawal targets its address in the same block.

    pre:  .. -> branch@4 -> {survivor, doomed}
    post: the pre shape with doomed re-created by the withdrawal credit,
          or the collapsed leaf when the withdrawal carries 0 Gwei
    Withdrawals are applied after the transactions; a zero one must not
    leave an empty account behind.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    assert node_at(_shape(genesis, survivor), 4) == ("branch", 2)
    resurrected = (
        Account(balance=amount * 10**9) if amount else Account.NONEXISTENT
    )

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


# --- collapse cells with a controlled parent -----------------------------


def _cell(
    pre: Alloc,
    fork: Fork,
    funded: List[Address],
    salt: int,
    target: Address,
    depth: int,
    parent_kind: str,
    survivor_kind: str,
) -> Address:
    """
    Fund `funded` and the address created by `salt`; pin the collapse cell.

    Asserts that `target`'s path holds a 2-child branch at `depth` whose
    parent is `parent_kind`, and that after the block the node covering
    `depth` is `survivor_kind`.
    """
    doomed = Address(create2_preimage(salt))
    for address in funded:
        pre.fund_address(address, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    genesis = _genesis(pre, fork)
    before = _shape(genesis, target)
    assert node_at(before, depth) == ("branch", 2)
    assert before[before.index((depth, "branch", 2)) - 1][1] == parent_kind
    after = _shape(_after_block(genesis, doomed), target)
    assert covering(after, depth)[1] == survivor_kind
    return doomed


@pytest.mark.parametrize(
    "funded,salt,depth,parent_kind,survivor_kind",
    [
        pytest.param(
            [TWO_ADDRS_EXT4[0], TWO_ADDRS_EXT4_SIBLING_DEPTH3],
            COLLAPSE_SALT,
            4,
            "branch",
            "leaf",
            id="leaf_under_branch",
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
            [
                TWO_ADDRS_EXT4[0],
                TWO_ADDRS_EXT4_SIBLING_DEPTH3,
                TWO_ADDRS_EXT4_SIBLING_DEPTH1,
            ],
            SHARE2_SALT,
            2,
            "branch",
            "ext",
            id="branch_under_branch",
        ),
        pytest.param(
            [*TWO_ADDRS_EXT4, TWO_ADDRS_EXT4_SIBLING_DEPTH1],
            SHARE3_SALT,
            3,
            "ext",
            "ext",
            id="branch_under_ext",
        ),
    ],
)
def test_delete_collapse_cells(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    funded: List[int],
    salt: int,
    depth: int,
    parent_kind: str,
    survivor_kind: str,
) -> None:
    """
    Account-trie collapses whose parent node is controlled.

    pre:  branch@3 -> {d3, branch@4 -> {p, doomed}}         leaf_under_branch
          branch@1 -> {d1, branch@2 -> {doomed, ext(1) ..}} ext_under_branch
          branch@1 -> {d1, branch@2 -> {doomed, branch@3}}  branch_under_branch
          branch@1 -> {d1, ext(1) -> branch@3 -> {doomed, branch@4}} under_ext
    post: leaf under branch@3; ext(2) under branch@1; ext(1) -> branch@3
          under branch@1; ext(2) -> branch@4 under branch@1
    Mined siblings at depths 1 and 3 make the parent kind independent of
    the uncontrolled accounts, up to a 16^-2 collision the assert reports.
    """
    addresses = [Address(x) for x in funded]
    doomed = _cell(
        pre,
        fork,
        addresses,
        salt,
        addresses[0],
        depth,
        parent_kind,
        survivor_kind,
    )

    state_test(
        pre=pre,
        tx=_delete_tx(pre.fund_eoa(), salt),
        post={
            **{a: Account(balance=1) for a in addresses},
            doomed: Account.NONEXISTENT,
        },
    )


def test_delete_from_three_child_branch(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete one of three accounts under one branch.

    pre:  .. -> branch@4 -> {p, q, doomed}
    post: .. -> branch@4 -> {p, q}
    """
    p, q = (Address(x) for x in TWO_ADDRS_EXT4)
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(p, amount=1)
    pre.fund_address(q, amount=2)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    genesis = _genesis(pre, fork)
    assert node_at(_shape(genesis, p), 4) == ("branch", 3)
    assert node_at(_shape(_after_block(genesis, doomed), p), 4) == (
        "branch",
        2,
    )

    state_test(
        pre=pre,
        tx=_delete_tx(pre.fund_eoa(), COLLAPSE_SALT),
        post={
            p: Account(balance=1),
            q: Account(balance=2),
            doomed: Account.NONEXISTENT,
        },
    )


def test_mass_delete_sixteen_to_one(
    blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Delete fifteen of sixteen accounts under one branch in one block.

    pre:  .. -> ext -> branch@4 -> {survivor, 15 x doomed}
    post: .. -> leaf survivor
    Fifteen CREATE2 deletions in one block collapse the branch onto the
    survivor and merge it into the extension above.
    """
    survivor = Address(SIXTEEN_ADDRS_BRANCH4[0])
    doomed = [Address(create2_preimage(s)) for s in SIXTEEN_SALTS_BRANCH4]
    pre.fund_address(survivor, amount=1)
    for address in doomed:
        pre.fund_address(address, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    genesis = _genesis(pre, fork)
    before = _shape(genesis, survivor)
    assert node_at(before, 4) == ("branch", 16)
    assert before[before.index((4, "branch", 16)) - 1][1] == "ext"
    assert covering(_shape(_after_block(genesis, *doomed), survivor), 4)[
        1
    ] == ("leaf")

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
