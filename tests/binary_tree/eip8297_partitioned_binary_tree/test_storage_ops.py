"""
Storage operation tests for the EIP-8297 partitioned binary tree,
covering the account-header and overflow-zone boundaries the tree
embedding cares about.

EIP-8297's "Zero values and deletion" section is normative today:
"a zero-valued leaf is distinct from an absent key, committing to a
different root," and "removing entries is reserved for a future
state-expiry mechanism." `src/ethereum/state_pbt.py` does the
opposite -- a zero write deletes the slot -- so every zero-write test
below pins this provider's current behavior, not EIP-8297
conformance; their post states would need regenerating if the
provider were ever made conformant.
`tests/binary_trie/test_trie.py::test_zero_value_is_not_absence` is
the one conformant test in the tree: the raw trie does keep a
zero-valued leaf; only the provider layer removes it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import sstore_from_calldata_contract
from .spec import Spec, ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


@pytest.mark.parametrize(
    "slot",
    [
        pytest.param(0, id="header_slot_0"),
        pytest.param(1, id="header_slot_1"),
        pytest.param(
            Spec.CODE_OFFSET - Spec.HEADER_STORAGE_OFFSET - 1,
            id="header_last_63",
        ),
        pytest.param(
            Spec.CODE_OFFSET - Spec.HEADER_STORAGE_OFFSET,
            id="overflow_first_64",
        ),
        pytest.param(
            Spec.STEM_SUBTREE_WIDTH - 1, id="storage_group_0_last_255"
        ),
        pytest.param(Spec.STEM_SUBTREE_WIDTH, id="storage_group_1_first_256"),
        pytest.param(2**256 - 1, id="max_slot"),
    ],
)
def test_sstore_sload_round_trip(
    state_test: StateTestFiller,
    pre: Alloc,
    slot: int,
) -> None:
    """
    Verify SSTORE followed by SLOAD round-trips a value into another
    slot within the same transaction, over slots spanning the account
    header and every storage-group boundary the tree embedding cares
    about.
    """
    value = 0xC0FFEE
    # Distinct from every parametrized slot above (including
    # 2**256 - 1), so it can never collide with the slot under test.
    readback_slot = 2**128

    contract = pre.deploy_contract(
        code=Op.SSTORE(slot, value)
        + Op.SSTORE(readback_slot, Op.SLOAD(slot))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {
        contract: Account(storage={slot: value, readback_slot: value}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_sstore_zero_after_nonzero_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify writing a nonzero value and then zeroing the same slot
    within one transaction leaves the slot absent from the post state.

    `src/ethereum/state_pbt.py` treats a zero-valued storage slot as
    equivalent to an absent one, so the expected post storage below
    is simply empty. Not EIP-8297-conformant (see the module
    docstring): this pins current provider behavior.
    """
    slot = 7
    contract = pre.deploy_contract(
        code=Op.SSTORE(slot, 0xFF) + Op.SSTORE(slot, 0) + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "same_block",
    [
        pytest.param(True, id="across_transactions_same_block"),
        pytest.param(False, id="across_blocks"),
    ],
)
def test_sstore_zero_across_transactions_or_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    same_block: bool,
) -> None:
    """
    Verify a slot written by one transaction and zeroed by a second
    ends up absent from the post state, whether the two land in the
    SAME block (as two transactions) or in two consecutive blocks.

    Not EIP-8297-conformant (see the module docstring): the absent
    slot pins current provider behavior.
    """
    slot = 7
    contract = sstore_from_calldata_contract(pre, slot=slot)
    sender = pre.fund_eoa()

    write_tx = Transaction(sender=sender, to=contract, data=Hash(0xFF))
    zero_tx = Transaction(sender=sender, to=contract, data=Hash(0))

    blocks = (
        [Block(txs=[write_tx, zero_tx])]
        if same_block
        else [Block(txs=[write_tx]), Block(txs=[zero_tx])]
    )

    post = {contract: Account(storage={})}
    blockchain_test(pre=pre, post=post, blocks=blocks)


def test_sstore_overwrite_nonzero_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify overwriting a slot with a different nonzero value replaces
    it.

    A same-value no-op write is deliberately not covered as a second
    case here: with the write's target value equal to both the
    pre-alloc value and the expected post value, that scenario's
    post-state assertion cannot fail whether the SSTORE actually ran
    or the whole call did nothing -- state_pbt.py's storage_changes
    application has no code path specific to "write the value already
    there" separate from an ordinary nonzero write, so this directed,
    distinguishable overwrite is what exercises that path.
    """
    slot = 9
    contract = pre.deploy_contract(
        code=Op.SSTORE(slot, 0x1111) + Op.STOP, storage={slot: 0x9999}
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={slot: 0x1111})}
    state_test(pre=pre, post=post, tx=tx)


def test_sload_never_written_slot_returns_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify SLOAD of a never-written slot returns zero and never
    creates a storage entry in the post state.

    The read value is then SSTORE'd back into slot 0, so the absent
    slot 0 below also relies on the zero-write-deletes-the-slot
    behavior disclosed in the module docstring, not just on the
    never-written slot's read.
    """
    never_written_slot = 999
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SLOAD(never_written_slot)) + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    # A correct zero read makes this an SSTORE-to-zero, i.e. an absent
    # slot; a buggy nonzero read would surface as slot 0 holding that
    # value. `Storage.must_be_equal` (composite_types.py:317-338)
    # only raises for an unexpected key when its value is nonzero, so
    # zero and absent are indistinguishable here -- this still catches
    # a nonzero misread, just not a wrong-but-zero one.
    post = {contract: Account(storage={})}
    state_test(pre=pre, post=post, tx=tx)


def test_storage_coexists_with_sizeable_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Pin that storage writes and sizeable code (spanning multiple code
    chunks) coexist for one account.

    The `JUMPDEST` padding pushes the code comfortably past one
    `CODE_CHUNK_SIZE`-byte chunk, so the account actually carries
    several code chunks alongside its storage -- chosen for coverage
    (per the `code_chunk_count` assert below), not verified by the
    account-level post state, which checks only code bytes and
    storage values, not how many tree chunks they occupy.
    """
    slot, value = 10, 0xFEED
    code = Op.JUMPDEST * 200 + Op.SSTORE(slot, value) + Op.STOP
    assert Spec.code_chunk_count(len(code)) > 1, "code must span > 1 chunk"

    contract = pre.deploy_contract(code=code)

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(code=code, storage={slot: value})}
    state_test(pre=pre, post=post, tx=tx)


def test_transient_storage_round_trip(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify TSTORE/TLOAD (EIP-1153) round-trip within the transaction
    but leave no trace in the persistent storage post state.
    """
    transient_slot, value, marker_slot = 7, 0xABCD, 0
    contract = pre.deploy_contract(
        code=Op.TSTORE(transient_slot, value)
        + Op.SSTORE(marker_slot, Op.TLOAD(transient_slot))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={marker_slot: value})}
    state_test(pre=pre, post=post, tx=tx)


def test_storage_under_7702_delegation_lands_on_authority(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify storage written while executing under an EIP-7702
    delegation lands on the AUTHORITY's account, never the delegate's.
    """
    slot, value = 3, 0xC0FFEE
    delegate_code = Op.SSTORE(slot, value) + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)
    authority = pre.fund_eoa(delegation=delegate)

    tx = Transaction(sender=pre.fund_eoa(), to=authority)

    post = {
        authority: Account(storage={slot: value}),
        delegate: Account(storage={}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_two_accounts_same_slot_independent(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify two accounts writing the same slot number keep independent
    logical storage.

    Account-by-account post-state verification cannot observe tree
    keys directly, so this does not prove the accounts' tree stems
    avoid colliding (a real collision would surface as a wrong state
    root, not necessarily a wrong value here); that pinning belongs to
    the `tests/binary_trie/` unit suites.
    """
    slot = 42
    value_a, value_b = 0x1111, 0x2222
    contract_a = pre.deploy_contract(code=Op.SSTORE(slot, value_a) + Op.STOP)
    contract_b = pre.deploy_contract(code=Op.SSTORE(slot, value_b) + Op.STOP)
    driver = pre.deploy_contract(
        code=Op.POP(Op.CALL(address=contract_a))
        + Op.POP(Op.CALL(address=contract_b))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=driver)

    post = {
        contract_a: Account(storage={slot: value_a}),
        contract_b: Account(storage={slot: value_b}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_sstore_many_slots_header_and_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a single transaction writing many slots across both the
    account header and overflow storage ranges leaves all of them
    present.
    """
    slots = [0, 63, 64, 300, 512]
    code = Bytecode()
    for index, slot in enumerate(slots):
        code += Op.SSTORE(slot, index + 1)
    code += Op.STOP

    contract = pre.deploy_contract(code=code)

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {
        contract: Account(
            storage={slot: index + 1 for index, slot in enumerate(slots)}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)
