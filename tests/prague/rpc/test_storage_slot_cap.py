"""
Tests that drive the cap on how many storage slots an expectation names.

Every state read and every account proof this suite derives is bounded by
`MAX_STORAGE_SLOTS_PER_ACCOUNT`, so that one storage-heavy account cannot
decide the cost of a whole run. Until these tests the bound was reached
only by unit tests holding a post-state written by hand: no marked test in
the corpus had a touched account with more than a single slot, so the
branch that drops slots had never once run against a chain a transition
tool produced. A truncation nothing real reaches is a truncation nobody
has checked.

Two accounts, one on either side of the bound, because a single account
past it would exercise the branch without saying where it starts. The
account at the cap has every slot asked about and the account one past it
has exactly one dropped, which together place the bound: the first says
the cap is the last count asserted in full, the second that the next
count is not.

Which slot is dropped is the second thing pinned here, and the reason the
writes run downwards. Truncation keeps whichever slots come first, so the
fixture is reproducible only if that order is a property of the chain
rather than of the run — and the alternative spelling, reading the keys
out of a set, would satisfy the cap while producing a different fixture
each time. Descending writes separate the two: the chain hands back the
highest slot first and a set of small integers hands back the lowest, so
a reordering shows up as a different set of slots surviving rather than
as the same set in a different sequence.

Each slot stores the position at which it was written, which puts that
order in the fixture where a reader can see it: the slots the cap keeps
are exactly the ones whose value is no greater than the cap.

Nothing here is fork-specific — a storage slot has read back the same way
since Frontier — so the suite starts where its neighbours do, at the most
recent fork whose blocks go-ethereum has long been able to consume.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Transaction,
)
from execution_testing.rpc.serialization import MAX_STORAGE_SLOTS_PER_ACCOUNT

pytestmark = [pytest.mark.valid_from("Prague"), pytest.mark.rpc]


@pytest.mark.parametrize(
    "slots",
    [
        pytest.param(MAX_STORAGE_SLOTS_PER_ACCOUNT, id="at_the_cap"),
        pytest.param(MAX_STORAGE_SLOTS_PER_ACCOUNT + 1, id="one_past_the_cap"),
    ],
)
def test_storage_heavy_account(
    blockchain_test: BlockchainTestFiller, pre: Alloc, slots: int
) -> None:
    """
    A contract filling enough slots to reach the cap, and one past it.

    The count is taken from the cap rather than written down, so that
    moving the bound moves the pair with it instead of leaving two
    fixtures that no longer straddle anything.
    """
    # Descending, so that the order the chain wrote the slots in is not
    # also the order they sort in; see the module docstring.
    writes = [(slots - position, position + 1) for position in range(slots)]

    code = Bytecode()
    for slot, position in writes:
        code += Op.SSTORE(slot, position)
    contract = pre.deploy_contract(code + Op.STOP)

    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=contract)])],
        post={contract: Account(storage=dict(writes))},
    )
