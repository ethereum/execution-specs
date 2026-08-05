"""
Account lifecycle tests for the EIP-8297 partitioned binary tree:
creation, mutation, destruction, and non-creation, under the
`BinaryTree` fork. No tree stem is observable here; cross-fork
equivalence with Amsterdam is guaranteed structurally by
`test_fork_parity.py`'s byte-for-byte pin, not by running these same
tests on both forks and comparing.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .helpers import FACTORY_CANARY_SLOT, create_contract_via_factory
from .spec import Spec, ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")

# 31 * 128: the last byte of code that still fits the account header.
HEADER_CODE_BYTES = Spec.CODE_CHUNK_SIZE * (
    Spec.STEM_SUBTREE_WIDTH - Spec.CODE_OFFSET
)


def test_fund_fresh_eoa_via_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Fund a never-seen EOA through a plain value transfer.

    The recipient materializes holding exactly the transferred balance
    with nonce zero; the sender's nonce increments for having sent the
    transaction.
    """
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()
    value = 10**9

    tx = Transaction(sender=sender, to=recipient, value=value)

    post = {
        recipient: Account(balance=value, nonce=0, code=b"", storage={}),
        sender: Account(nonce=1),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(Op.CREATE2, id="CREATE2"),
    ],
)
def test_create_deploys_code_and_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Verify a CREATE/CREATE2-deployed contract lands at its
    deterministic address (computed with the framework helper) holding
    its deployed code and constructor-written storage, and that the
    creator's nonce bumps.
    """
    deploy_code = Op.STOP
    slot, value = 0, 1
    initcode = Initcode(
        deploy_code=deploy_code, initcode_prefix=Op.SSTORE(slot, value)
    )

    factory, created = create_contract_via_factory(
        pre, initcode, opcode=opcode, salt=0x5A17
    )

    tx = Transaction(sender=pre.fund_eoa(), to=factory)

    post = {
        factory: Account(nonce=2, storage={FACTORY_CANARY_SLOT: 1}),
        created: Account(nonce=1, code=deploy_code, storage={slot: value}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_contract_creating_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a contract-creating transaction (`to=None`) deploys the new
    contract with its constructor-written storage, bumping the
    sender's nonce.
    """
    deploy_code = Op.STOP
    slot, value = 0, 1
    initcode = Initcode(
        deploy_code=deploy_code, initcode_prefix=Op.SSTORE(slot, value)
    )

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=None, data=initcode)
    created = tx.created_contract

    post = {
        created: Account(nonce=1, code=deploy_code, storage={slot: value}),
        sender: Account(nonce=1),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_selfdestruct_same_transaction_leaves_no_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify EIP-6780: a contract created and destroyed in the SAME
    transaction leaves no trace in the post state, including any
    storage it wrote before self-destructing.
    """
    beneficiary = pre.nonexistent_account()
    value = 1000
    initcode = Op.SSTORE(0, 1) + Op.SELFDESTRUCT(beneficiary)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=None, data=initcode, value=value)
    created = tx.created_contract

    post = {
        created: Account.NONEXISTENT,
        beneficiary: Account(balance=value, nonce=0, code=b"", storage={}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "beneficiary_pre_exists",
    [
        pytest.param(True, id="aged_beneficiary_sweeps_balance"),
        pytest.param(False, id="fresh_beneficiary_materializes"),
    ],
)
def test_selfdestruct_survives_and_sweeps_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    beneficiary_pre_exists: bool,
) -> None:
    """
    Verify a post-6780 SELFDESTRUCT on a contract that existed before
    the transaction leaves it alive with its code and storage intact,
    sweeping its balance to the beneficiary -- whether the beneficiary
    already existed (gaining the swept balance on top of its own
    pre-existing balance) or is fresh (materializing for the first
    time holding exactly the swept balance).
    """
    initial_balance = 1000
    pre_existing_beneficiary_balance = 500
    beneficiary = (
        pre.fund_eoa(amount=pre_existing_beneficiary_balance)
        if beneficiary_pre_exists
        else pre.nonexistent_account()
    )
    victim_code = Op.SELFDESTRUCT(beneficiary)
    victim = pre.deploy_contract(
        code=victim_code, balance=initial_balance, storage={0: 42}
    )

    tx = Transaction(sender=pre.fund_eoa(), to=victim)

    expected_beneficiary = (
        Account(balance=pre_existing_beneficiary_balance + initial_balance)
        if beneficiary_pre_exists
        else Account(balance=initial_balance, nonce=0, code=b"", storage={})
    )
    post = {
        victim: Account(balance=0, code=victim_code, storage={0: 42}),
        beneficiary: expected_beneficiary,
    }
    state_test(pre=pre, post=post, tx=tx)


def test_create_then_revert_leaves_child_nonexistent(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a contract that creates a child and then reverts leaves the
    child address nonexistent and its own storage exactly as before
    the call.

    `parent`'s own REVERT wipes out everything in its frame, so an
    unconditional canary cannot live there; an outer `caller` writes
    one instead, right after popping `parent`'s (always-failing) CALL
    result, to distinguish the CREATE succeeding and then correctly
    rolling back from the CREATE running out of gas before ever
    reaching the REVERT.
    """
    child_deploy_code = Op.STOP
    child_initcode = Initcode(
        deploy_code=child_deploy_code, initcode_prefix=Op.SSTORE(0, 1)
    )
    template = pre.deploy_contract(code=child_initcode)

    existing_slot, existing_value = 5, 0xAAAA
    parent_code = (
        Op.EXTCODECOPY(template, 0, 0, len(child_initcode))
        + Op.POP(Op.CREATE(value=0, offset=0, size=len(child_initcode)))
        + Op.SSTORE(existing_slot, 0xBBBB)
        + Op.REVERT(0, 0)
    )
    parent = pre.deploy_contract(
        code=parent_code, storage={existing_slot: existing_value}
    )
    child = compute_create_address(address=parent, nonce=1)

    canary_slot = 0
    caller = pre.deploy_contract(
        code=Op.POP(Op.CALL(address=parent))
        + Op.SSTORE(canary_slot, 1)
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        parent: Account(nonce=1, storage={existing_slot: existing_value}),
        child: Account.NONEXISTENT,
        caller: Account(storage={canary_slot: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_empty_account_touch_not_materialized(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify EIP-161: touching a never-seen, empty account with a
    zero-value CALL does not materialize it in the post state.

    An unconditional canary slot written right after the (POP'd) CALL
    proves the caller's frame actually continued, distinguishing this
    from the frame never running at all.
    """
    canary_slot = 1
    touched = pre.nonexistent_account()
    contract = pre.deploy_contract(
        code=Op.POP(Op.CALL(address=touched, value=0))
        + Op.SSTORE(canary_slot, 1)
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {
        touched: Account.NONEXISTENT,
        contract: Account(storage={canary_slot: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value_call_only"),
        pytest.param(100, id="zero_value_call_then_value_transfer"),
    ],
)
def test_precompile_touch_and_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
) -> None:
    """
    Verify a zero-value CALL to a precompile does not materialize an
    account for it, while a subsequent value transfer does.

    An unconditional canary slot written right after both (POP'd)
    CALLs proves the caller's frame actually continued, at least for
    the `value == 0` case.
    """
    sha256_address = Address(0x02)
    canary_slot = 1

    code = Op.POP(Op.CALL(address=sha256_address, value=0))
    if value:
        code += Op.POP(Op.CALL(address=sha256_address, value=value))
    code += Op.SSTORE(canary_slot, 1) + Op.STOP

    contract = pre.deploy_contract(code=code, balance=value)

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {
        sha256_address: (
            Account.NONEXISTENT
            if value == 0
            else Account(balance=value, nonce=0, code=b"", storage={})
        ),
        contract: Account(storage={canary_slot: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_removal_keeps_overflow_code_a_survivor_shares(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Destroy an account whose bytecode overflows into the code zone while
    another account still runs that same bytecode.

    An account owns its header stem and its storage prefix, and removing
    it removes those two subtrees. Its overflow code chunks are not in
    either: they are content-addressed, so byte-identical contracts share
    one set of leaves, and those leaves outlive any single account
    referencing them. Dropping them along with the account would leave
    the survivor's code half-committed and move the state root.

    The victim is created and destroyed inside one transaction, which
    post-EIP-6780 is the only way an account with code and storage is
    removed at all. It writes storage on both sides of the header
    boundary first, so the removal has to reach the storage zone as well
    as the header.
    """
    beneficiary = pre.fund_eoa(amount=0)
    header_slot, zone_slot = 5, 300

    # Long enough to reach the code zone, and self-destructing so the
    # victim can be destroyed by a call rather than from its own
    # constructor -- it has to hold code and storage when it goes.
    shared_code = Op.SELFDESTRUCT(beneficiary)
    shared_code += Op.INVALID * (HEADER_CODE_BYTES + 1 - len(shared_code))
    assert len(shared_code) == HEADER_CODE_BYTES + 1

    # Deployed before the transaction, so EIP-6780 leaves it in place: a
    # call would only sweep its balance. It is the reference holder of
    # the shared overflow chunks.
    survivor = pre.deploy_contract(code=shared_code)

    initcode = Initcode(
        deploy_code=shared_code,
        initcode_prefix=Op.SSTORE(header_slot, 1) + Op.SSTORE(zone_slot, 2),
    )
    template = pre.deploy_contract(code=initcode)
    factory = pre.deploy_contract(
        code=Op.EXTCODECOPY(template, 0, 0, len(initcode))
        + Op.MSTORE(32, Op.CREATE(offset=0, size=len(initcode)))
        + Op.POP(Op.CALL(address=Op.MLOAD(32)))
        + Op.SSTORE(FACTORY_CANARY_SLOT, 1)
        + Op.STOP
    )
    victim = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=pre.fund_eoa(), to=factory, gas_limit=10_000_000)

    post = {
        victim: Account.NONEXISTENT,
        survivor: Account(code=shared_code),
        factory: Account(storage={FACTORY_CANARY_SLOT: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)
