"""
Tests that pin `eth_createAccessList` against a spec-derived expectation.

The one method in the suite where a derived expectation clearly beats a
recorded one. execution-apis carries four `eth_createAccessList` tests
and marks every one `speconly` — asserting that the response has the
right *shape* and nothing at all about its value — because the recording
client's answer was not treated as authoritative. What a message touches
is not a matter of opinion, though: it follows from executing the
message, so the specification can state it exactly, and these tests do.

Two things are asserted. The `accessList` is the set of entries a list
would have to declare to make the message's cold accesses warm, which is
what `declarable_access_list` derives from the EVM's own warm sets. The
`gasUsed` is what the message costs *with that list attached*, which is
not what the plain call costs — attaching a list charges for it up front
— and so comes from a re-run carrying it.

Every shape here is chosen to stay clear of the one place the
specification and go-ethereum answer differently: a frame that reverted
below the top level, documented at `declarable_access_list`. What is
left is the ordinary case, and the ordinary case is where clients
actually disagree.

The two creation tests are the exception, and they assert different
amounts on purpose. Clients split over whether a created address belongs
in the list at all, so the case where it carries nothing is stored as a
shape; the case where it carries a slot is stored as a value, because
every client puts it there.

Derivation replays the first transaction of each block, so most of these
tests need only produce a block whose opening transaction has the shape
wanted, and write no call at all.

The suite starts at Prague rather than at the current fork. Nothing here
is fork-specific — an access list has meant the same thing since Berlin —
and Prague is the most recent fork at which a block containing a cold
`SLOAD` is accepted by go-ethereum, so it is the most recent fork at
which these expectations can actually be replayed. See the fill-time
notes for the Amsterdam storage-access disagreement that makes the later
forks unreplayable today.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Transaction,
)
from execution_testing.specs.blockchain import RPCExpectation

pytestmark = [pytest.mark.valid_from("Prague"), pytest.mark.rpc]


def test_access_list_of_a_transfer(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A plain value transfer, which touches nothing worth declaring.

    The empty list is the assertion, and it is a stronger one than it
    looks. Both parties to a transfer *are* touched — they are warm from
    the moment the message starts — and neither belongs in a list,
    because declaring an address that is already warm by rule costs gas
    and buys nothing. A client reporting the sender or the recipient here
    would be reporting a list that makes the message more expensive.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=recipient, value=1)])
        ],
        post={},
    )


def test_access_list_of_a_storage_read(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract reading one of its own slots.

    The recipient is warm by rule and its *slots* are not, so the entry
    the list needs names an address that is itself excluded. A client
    deriving the list by excluding the recipient outright — rather than
    excluding only the bare address — drops the one entry that matters
    here, and the message it proposes saves nothing.
    """
    probe = pre.deploy_contract(
        Op.MSTORE(0, Op.SLOAD(0x2A)) + Op.RETURN(0, 32),
        storage={0x2A: 0x99},
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=probe)])],
        post={},
    )


def test_access_list_of_several_accounts(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract reading the balance of three unrelated accounts.

    Three entries, each carrying no storage keys, which is the shape a
    client gets wrong by omitting `storageKeys` rather than sending it
    empty. The order is asserted as a set rather than as a sequence; see
    `canonical_result`.
    """
    first = pre.fund_eoa(amount=11)
    second = pre.fund_eoa(amount=22)
    third = pre.deploy_contract(Op.STOP, balance=33)
    probe = pre.deploy_contract(
        Op.POP(Op.BALANCE(first))
        + Op.POP(Op.BALANCE(second))
        + Op.POP(Op.BALANCE(third))
        + Op.STOP
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=probe)])],
        post={},
    )


def test_access_list_across_a_call(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract calling another, which reads two of its own slots.

    The entries come from two different frames, so a client collecting
    only what the top-level frame touched reports the callee's address
    and neither of its slots. Both slots belong to the callee rather than
    to the recipient, which is what distinguishes this from the
    single-contract case: the address of an entry is the account whose
    storage was read, not the account whose code read it.
    """
    callee = pre.deploy_contract(
        Op.POP(Op.SLOAD(1)) + Op.POP(Op.SLOAD(2)) + Op.STOP,
        storage={1: 0xAA, 2: 0xBB},
    )
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(Op.GAS, callee, 0, 0, 0, 0, 0)) + Op.STOP
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=caller)])],
        post={},
    )


def test_access_list_of_a_reverting_call(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract that touches a slot and then reverts.

    A revert is not an error here, which is the difference from
    `eth_call`: a client answers with a perfectly good access list and
    reports the halt as a free-text `error` beside it. The list and the
    gas are therefore still asserted, and only the wording is left alone
    — which is what drops this one expectation to the `partial` tier.

    The revert is at the top level on purpose. A frame that reverts below
    the top has its warm sets discarded by the specification and kept by
    go-ethereum, and this suite does not pretend to settle that.
    """
    probe = pre.deploy_contract(
        Op.POP(Op.SLOAD(3)) + Op.REVERT(0, 0),
        storage={3: 0xCC},
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=probe)])],
        post={},
    )


def _factory_deploying(initcode: Bytecode) -> Bytecode:
    """
    Return code that writes `initcode` to memory and creates from it.

    Right-aligned in the first word, which is what makes a short
    init code expressible as a single `PUSH32` and keeps the factory
    itself from touching anything the list would have to declare.
    """
    length = len(initcode)
    return (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).rjust(32, b"\x00")))
        + Op.CREATE(0, 32 - length, length)
        + Op.STOP
    )


def test_access_list_of_a_creation_that_stores_nothing(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A factory deploying a contract that touches no storage.

    The created address is warm the moment it is created — EIP-2929 adds
    it to `accessed_addresses` "immediately (ie. before checks are done
    to determine whether or not the address is unclaimed)" — so
    declaring it would buy a caller nothing and cost them
    `ACCESS_LIST_ADDRESS_COST`. The list here leaves it out for that
    reason.

    Nothing asserts that, though, and the expectation this test files is
    a shape and no value. go-ethereum and reth agree with the omission
    but only by accident, their lists being built by watching opcodes
    that never name a created address; Nethermind and Erigon read the
    EVM's warm set directly and declare it. Nothing in EIP-2930 or in
    execution-apis decides between them — EIP-2930 raises "the tx
    sender/recipient/newly created contract" only to decline to police
    duplicates — so what is pinned here is that the suite declines to
    decide too.
    """
    factory = pre.deploy_contract(_factory_deploying(Op.STOP))
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=factory)])],
        post={},
    )


def test_access_list_of_a_creation_that_stores(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A factory whose init code writes one slot before returning.

    The created address is back in the list, and this one *is* asserted.
    A created account's address is warm but its storage is not, and a
    slot cannot be declared without naming the account that holds it, so
    the entry is worth its price and every client produces it — the two
    that watch opcodes see the `SSTORE` and attribute it to the frame
    that ran it, and the two that read the warm set find the slot there.

    The contrast with the preceding test is the point. "Leave a created
    address out" is not the rule; the rule is that a *bare* created
    address is not worth declaring, which is the same rule the recipient
    is subject to.
    """
    factory = pre.deploy_contract(
        _factory_deploying(Op.SSTORE(7, 0x11) + Op.STOP)
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=factory)])],
        post={},
    )


def test_access_list_of_a_top_level_creation(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A message with no recipient, which deploys and stores nothing.

    The address this creates is left out of the list, and unlike the
    nested case that omission is not contested by anybody: it is the
    message's own recipient, warmed at the start of the transaction by
    the same EIP-2929 rule that warms an ordinary callee, and every
    client excludes it by name. go-ethereum computes it as
    `crypto.CreateAddress(args.from(), *args.Nonce)` for exactly this
    purpose. So this expectation is a value rather than a shape.
    """
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=None, data=Op.STOP)])
        ],
        post={},
    )


def test_declared_access_list_at_historical_states(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    One declared message, asked of two states that answer differently.

    Derivation replays a message the chain contained; asking the *same*
    message of several states has to be declared. That is what makes this
    the case for historical state — the probe reads whichever slot the
    recipient's balance names, and the chain moves that balance between
    the two blocks, so the same message declares a different slot at each
    of them. A client resolving every block to its head reports the later
    list for the earlier block and is caught by the first assertion.
    """
    recipient = pre.fund_eoa(amount=0)
    probe = pre.deploy_contract(
        Op.POP(Op.SLOAD(Op.BALANCE(recipient))) + Op.STOP
    )
    sender = pre.fund_eoa()
    message = {"from": sender, "to": probe}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=recipient, value=5)])
        ],
        post={},
        rpc_checks=[
            RPCExpectation(
                method="eth_createAccessList",
                params=[message, "0x0"],
                derive_result=True,
            ),
            RPCExpectation(
                method="eth_createAccessList",
                params=[message, "latest"],
                derive_result=True,
            ),
        ],
    )
