"""
Exercise the Merkle Patricia Trie as a data structure via account addresses.

The account trie has the same mechanics as the storage trie (both key on
keccak256 of the preimage), but most clients implement it as a separate
code path (reth's account vs storage walkers, Besu's Bonsai account
accumulator, erigon's unified `HexPatriciaHashed` keying), so the same
shapes are exercised here over addresses (`*_ADDRS_*` constants).

Address control uses `pre.fund_address()` (public API, no
`pre_alloc_mutable`, execute-mode aware). The account trie also holds
uncontrolled accounts -- sender, fee recipient, the deterministic factory
-- so shape assertions are *local*: they check the node at the mined
group's shared depth, which uncontrolled accounts can only perturb if one
shares that prefix, which the fill-time assertion would then report.

Deleting a committed account leaf on a post-Cancun fork is only possible
for a contract created in the same transaction (EIP-6780). The deletion
tests therefore fund a mined address at genesis and, in a later
transaction, CREATE2 onto it via the deterministic factory with init code
that immediately `SELFDESTRUCT`s: creation at a balance-only address is
legal (no nonce or code), the contract counts as created in the
transaction, and its pre-existing leaf is removed. Clearing a committed
*storage* trie while its account survives is not expressible on these
forks (EIP-6780 removes the whole account) and stays out of scope.

Pinned to the latest deployed fork so every client consumes one identical
fixture set; MPT rules are fork-invariant.
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
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)

from .constants import (
    ADDR_EXT_MERGE_TRIO,
    COLLAPSE_SALT,
    EXT_MERGE_SALT,
    SIXTEEN_ADDRS_BRANCH4,
    TWO_ADDRS_EXT4,
)
from .trie_shape import Shape, node_at, path_shape

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")

FUNDING = 10**18

# Beneficiary is ORIGIN so the init code, and therefore every CREATE2
# address derived from it, does not depend on any per-test address. The
# salts in `constants.py` were mined against these exact bytes.
DELETE_INITCODE = bytes(Op.SELFDESTRUCT(Op.ORIGIN))
assert DELETE_INITCODE == bytes.fromhex("32ff")


def create2_preimage(salt: int) -> bytes:
    """Address the deterministic factory creates for `salt`."""
    return bytes(
        compute_create2_address(
            DETERMINISTIC_FACTORY_ADDRESS, salt, DELETE_INITCODE
        )
    )


def _shape(accounts: Iterable[Address], target: Address) -> Shape:
    return path_shape([bytes(a) for a in accounts], bytes(target))


def _ensure_factory(pre: Alloc) -> None:
    """
    Bring the deterministic factory into the pre-alloc. The filler only
    injects it on first use of `deterministic_deploy_contract`, so deploy a
    trivial contract through it; the mined salts assume the factory sits at
    `DETERMINISTIC_FACTORY_ADDRESS`.
    """
    pre.deterministic_deploy_contract(deploy_code=Op.STOP)
    assert DETERMINISTIC_FACTORY_ADDRESS in pre


def _delete_tx(sender: EOA, salt: int) -> Transaction:
    """
    Ask the deterministic factory to CREATE2 `DELETE_INITCODE` with `salt`;
    the created contract self-destructs to ORIGIN in the same transaction.
    """
    return Transaction(
        sender=sender,
        to=DETERMINISTIC_FACTORY_ADDRESS,
        data=Hash(salt) + DELETE_INITCODE,
    )


# --- inserts at genesis -----------------------------------------------


def test_insert_splits_into_extension_and_branch(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Two addresses sharing 4 nibbles meet in a 2-child branch at depth 4."""
    a, b = (Address(x) for x in TWO_ADDRS_EXT4)
    pre.fund_address(a, amount=1)
    pre.fund_address(b, amount=2)
    assert node_at(_shape(pre, a), 4) == ("branch", 2)

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=pre.fund_eoa(amount=1)),
        post={a: Account(balance=1), b: Account(balance=2)},
    )


def test_insert_full_branch_arity_sixteen(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """Sixteen addresses sharing 4 nibbles fill every child of one branch."""
    addresses = [Address(x) for x in SIXTEEN_ADDRS_BRANCH4]
    for i, address in enumerate(addresses):
        pre.fund_address(address, amount=i + 1)
    assert node_at(_shape(pre, addresses[0]), 4) == ("branch", 16)

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=pre.fund_eoa(amount=1)),
        post={a: Account(balance=i + 1) for i, a in enumerate(addresses)},
    )


# --- inserts during execution -----------------------------------------


def _pay_each(addresses: List[Address]) -> Bytecode:
    code = Bytecode()
    for address in addresses:
        code += Op.POP(Op.CALL(Op.GAS, address, 1, 0, 0, 0, 0))
    return code + Op.STOP


def test_insert_full_branch_during_execution(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    A contract pays 1 wei to each of sixteen mined addresses, creating
    the 16-way branch against the committed genesis trie rather than in
    the genesis allocation.
    """
    addresses = [Address(x) for x in SIXTEEN_ADDRS_BRANCH4]
    payer = pre.deploy_contract(code=_pay_each(addresses), balance=16)
    assert node_at(_shape([*pre, *addresses], addresses[0]), 4) == (
        "branch",
        16,
    )

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=payer),
        post={
            payer: Account(balance=0),
            **{a: Account(balance=1) for a in addresses},
        },
    )


def test_touched_empty_account_never_persists(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    A zero-value call to a never-seen address creates a transiently empty
    account that EIP-161 state clearing prunes before the state root is
    computed; it must not appear in the trie.
    """
    target = pre.fund_eoa(amount=0)

    state_test(
        pre=pre,
        tx=Transaction(sender=pre.fund_eoa(), to=target, value=0),
        post={target: Account.NONEXISTENT},
    )


# --- deletes of committed leaves ----------------------------------------


def test_delete_collapses_branch_into_leaf(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Two funded accounts share 4 nibbles (ext -> branch -> 2 leaves). The
    same-transaction CREATE2 + SELFDESTRUCT deletes one; the branch
    collapses onto the survivor.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    assert node_at(_shape(pre, survivor), 4) == ("branch", 2)
    after = [a for a in pre if a != doomed]
    assert all(
        kind != "branch" for d, kind, _ in _shape(after, survivor) if d == 4
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
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    ext(2) -> branch -> {doomed leaf, ext(2) -> branch -> 2 leaves}:
    deleting the doomed leaf merges the two extensions into ext(5).
    """
    l1, l2 = (Address(x) for x in ADDR_EXT_MERGE_TRIO[:2])
    doomed = Address(create2_preimage(EXT_MERGE_SALT))
    pre.fund_address(l1, amount=1)
    pre.fund_address(l2, amount=2)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    assert node_at(_shape(pre, l1), 2) == ("branch", 2)
    assert node_at(_shape(pre, l1), 5) == ("branch", 2)
    after = [a for a in pre if a != doomed]
    assert node_at(_shape(after, l1), 5) == ("branch", 2)
    assert all(kind != "branch" for d, kind, _ in _shape(after, l1) if d == 2)

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
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Pre: two funded accounts sharing 4 nibbles (ext -> branch@4 -> 2
    leaves), one of them the CREATE2 target `doomed`.
    Op: in one block, tx1 CREATE2s onto `doomed` and SELFDESTRUCTs in the
    same transaction (leaf deleted, branch@4 would collapse), tx2 sends
    1 wei to the same address.
    Post: `doomed` exists again as a balance-only leaf (nonce 0, no code,
    no storage) and branch@4 has two children: the pre shape with one
    changed leaf value.
    Exercises: account resurrection inside one block diff. Clients that
    record per-block destructions (geth `stateObjectsDestruct`, erigon
    incarnations, reth destroyed-account status) must let the later write
    re-create the leaf instead of keeping it deleted.
    """
    survivor = Address(TWO_ADDRS_EXT4[0])
    doomed = Address(create2_preimage(COLLAPSE_SALT))
    pre.fund_address(survivor, amount=1)
    pre.fund_address(doomed, amount=FUNDING)
    _ensure_factory(pre)
    sender = pre.fund_eoa()
    assert node_at(_shape(pre, survivor), 4) == ("branch", 2)
    without = [a for a in pre if a != doomed]
    assert all(
        kind != "branch" for d, kind, _ in _shape(without, survivor) if d == 4
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
