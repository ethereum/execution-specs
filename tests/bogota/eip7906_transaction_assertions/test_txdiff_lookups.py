"""
`TXDIFF` keyed lookups (EIP-7906): slots, balances and code hashes
before and after the transaction, read by key from the transaction
prestate and the live state, for keys the transaction wrote, keys it
never wrote and accounts that never existed.
"""

from typing import Callable, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
    keccak256,
)

from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

from .helpers import (
    BOB_FUNDS,
    CAROL_FUNDS,
    DEPLOYED_RUNTIME,
    FUNDS,
    INITCODE_DEPLOYING,
    KEY_A,
    KEY_B,
    KEY_C,
    KEY_U,
    NEVER_EXISTED,
    VALUE,
    WRITER_CODE,
    MixedBody,
    as_int,
    assertion_transaction,
    body_frame,
    creation_state_gas,
    expect_eq,
    initcode_word,
    mixed_body,
    success_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

# TODO: Contract creation over a zero-nonce account that holds storage
# stays undefined for clients until EIP-8253 (Hegota) bumps the nonce of
# the mainnet accounts of that shape. Revisit the storage-only tests once
# EIP-8253 ships: unskip them or drop them. See PR #3508.
STORAGE_ONLY_ACCOUNT_SKIP = pytest.mark.skip(
    reason="Undefined until EIP-8253 (Hegota), see PR #3508"
)


def code_hash(code: bytes | Bytecode) -> int:
    """Return the hash of `code` as the integer the opcodes push."""
    return int.from_bytes(keccak256(bytes(code)), "big")


@pytest.mark.parametrize(
    "key,before,after",
    [
        pytest.param(KEY_A, 0, 1, id="set_slot"),
        pytest.param(KEY_B, 5, 7, id="updated_slot"),
        pytest.param(KEY_C, 0, 0, id="restored_slot"),
        pytest.param(KEY_U, 3, 3, id="unwritten_slot"),
    ],
)
def test_slot_lookup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    key: int,
    before: int,
    after: int,
) -> None:
    """
    Look up a slot before and after the transaction by key, a slot the
    transaction never wrote reading its live value for both.
    """
    body = mixed_body(pre, fork)
    assertion = pre.deploy_contract(
        code=expect_eq(
            Op.TXDIFF(Spec.TXDIFF_SLOT_BEFORE, body.writer, key), before
        )
        + expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, body.writer, key), after)
        + Op.STOP
    )
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


AccountLookup = Callable[
    [MixedBody], Tuple[Address, int | Bytecode, int | Bytecode]
]
"""Pick an account of the body with its expected before and after values."""


@pytest.mark.parametrize(
    "lookup",
    [
        pytest.param(
            lambda body: (body.sender, FUNDS, Op.BALANCE(body.sender)),
            id="payer",
        ),
        pytest.param(
            lambda body: (body.recipient, BOB_FUNDS, BOB_FUNDS + VALUE),
            id="recipient",
        ),
        pytest.param(
            lambda body: (body.untouched, CAROL_FUNDS, CAROL_FUNDS),
            id="untouched",
        ),
    ],
)
def test_balance_lookup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    lookup: AccountLookup,
) -> None:
    """
    Look up an account's balance before and after the transaction, the
    payer's after value being its live balance before settlement.
    """
    body = mixed_body(pre, fork)
    account, before, after = lookup(body)
    assertion = pre.deploy_contract(
        code=expect_eq(
            Op.TXDIFF(Spec.TXDIFF_BALANCE_BEFORE, account, 0), before
        )
        + expect_eq(Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, account, 0), after)
        + Op.STOP
    )
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


@pytest.mark.parametrize(
    "lookup",
    [
        pytest.param(
            lambda body: (
                body.deployed,
                Spec.EMPTY_CODE_HASH,
                code_hash(DEPLOYED_RUNTIME),
            ),
            id="deployed_contract",
        ),
        pytest.param(
            lambda body: (
                body.writer,
                code_hash(WRITER_CODE),
                code_hash(WRITER_CODE),
            ),
            id="existing_contract",
        ),
        pytest.param(
            lambda body: (
                body.recipient,
                Spec.EMPTY_CODE_HASH,
                Spec.EMPTY_CODE_HASH,
            ),
            id="eoa",
        ),
    ],
)
def test_codehash_lookup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    lookup: AccountLookup,
) -> None:
    """Look up an account's code hash before and after the transaction."""
    body = mixed_body(pre, fork)
    account, before, after = lookup(body)
    assertion = pre.deploy_contract(
        code=expect_eq(
            Op.TXDIFF(Spec.TXDIFF_CODEHASH_BEFORE, account, 0), before
        )
        + expect_eq(Op.TXDIFF(Spec.TXDIFF_CODEHASH_AFTER, account, 0), after)
        + Op.STOP
    )
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


def test_codehash_lookup_of_delegated_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Look up a delegated account's code hash as the hash of its
    delegation indicator, without following the delegation.
    """
    body = mixed_body(pre, fork)
    delegated = pre.fund_eoa(amount=CAROL_FUNDS, delegation=body.writer)
    indicator = code_hash(Spec7702.delegation_designation(body.writer))
    assertion = pre.deploy_contract(
        code=expect_eq(
            Op.TXDIFF(Spec.TXDIFF_CODEHASH_BEFORE, delegated, 0), indicator
        )
        + expect_eq(
            Op.TXDIFF(Spec.TXDIFF_CODEHASH_AFTER, delegated, 0), indicator
        )
        + Op.STOP
    )
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


@pytest.mark.parametrize(
    "param,expected",
    [
        pytest.param(Spec.TXDIFF_SLOT_BEFORE, 0, id="slot_before"),
        pytest.param(Spec.TXDIFF_SLOT_AFTER, 0, id="slot_after"),
        pytest.param(Spec.TXDIFF_BALANCE_BEFORE, 0, id="balance_before"),
        pytest.param(Spec.TXDIFF_BALANCE_AFTER, 0, id="balance_after"),
        pytest.param(
            Spec.TXDIFF_CODEHASH_BEFORE,
            Spec.EMPTY_CODE_HASH,
            id="codehash_before",
        ),
        pytest.param(
            Spec.TXDIFF_CODEHASH_AFTER,
            Spec.EMPTY_CODE_HASH,
            id="codehash_after",
        ),
    ],
)
def test_never_existing_account_lookup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
    expected: int,
) -> None:
    """
    Look up an account that exists neither before nor after the
    transaction as an empty account.
    """
    body = mixed_body(pre, fork)
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXDIFF(param, NEVER_EXISTED, 0), expected) + Op.STOP
    )
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


PrestateChecks = Callable[[Address, Address, Address], Bytecode]
"""
Build an assertion's checks from the counter, the transfer recipient
and the contract the earlier transactions wrote, paid and created.
"""


@pytest.mark.parametrize(
    "checks",
    [
        pytest.param(
            lambda counter, *_: expect_eq(
                Op.TXDIFF(Spec.TXDIFF_SLOT_BEFORE, counter, KEY_A), 1
            ),
            id="txdiff_slot_before",
        ),
        pytest.param(
            lambda *_: expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOT_BEFORE, 0), 1),
            id="txtrace_slot_before",
        ),
        pytest.param(
            lambda _, recipient, __: expect_eq(
                Op.TXDIFF(Spec.TXDIFF_BALANCE_BEFORE, recipient, 0),
                BOB_FUNDS + VALUE,
            ),
            id="txdiff_balance_before",
        ),
        pytest.param(
            lambda *_: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), 1
            ),
            id="txtrace_balances_exclude_earlier_transfer",
        ),
        pytest.param(
            lambda *accounts: expect_eq(
                Op.TXDIFF(Spec.TXDIFF_CODEHASH_BEFORE, accounts[2], 0),
                code_hash(DEPLOYED_RUNTIME),
            ),
            id="txdiff_codehash_before",
        ),
    ],
)
def test_prestate_after_earlier_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    checks: PrestateChecks,
) -> None:
    """
    Take the before values from the transaction prestate, which includes
    the writes, transfers and deployments of earlier transactions in
    the same block.
    """
    alice = pre.fund_eoa()
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=BOB_FUNDS)
    counter = pre.deploy_contract(
        code=Op.SSTORE(KEY_A, Op.ADD(Op.SLOAD(KEY_A), 1)) + Op.STOP
    )
    created = compute_create_address(address=alice, nonce=2)
    assertion = pre.deploy_contract(
        code=checks(counter, recipient, created) + Op.STOP
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(sender=alice, to=counter),
                    Transaction(
                        sender=alice, to=recipient, value=VALUE, nonce=1
                    ),
                    Transaction(
                        sender=alice,
                        to=None,
                        data=INITCODE_DEPLOYING,
                        nonce=2,
                    ),
                    assertion_transaction(
                        fork,
                        sender,
                        body=[body_frame(fork, target=counter)],
                        assertion=assertion,
                        frame_receipts=success_receipts(3),
                    ),
                ]
            )
        ],
        post={
            sender: Account(nonce=1),
            counter: Account(storage={KEY_A: 2}),
            recipient: Account(balance=BOB_FUNDS + VALUE),
            created: Account(code=DEPLOYED_RUNTIME),
        },
    )


@STORAGE_ONLY_ACCOUNT_SKIP
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("creation_reverts", [False, True])
def test_storage_before_creation_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    creation_reverts: bool,
) -> None:
    """
    Read the true transaction prestate after creation at a storage-only
    address, including when the creation is reverted.
    """
    sender = pre.fund_eoa()
    initcode = Op.SSTORE(KEY_A, 7) + (
        Op.REVERT(0, 0) if creation_reverts else Op.STOP
    )
    factory = pre.deploy_contract(
        code=Op.MSTORE(
            0, int.from_bytes(bytes(initcode).ljust(32, b"\x00"), "big")
        )
        + Op.POP(Op.CREATE(0, 0, len(initcode)))
        + Op.STOP
    )
    created = compute_create_address(address=factory, nonce=1)
    pre.deploy_contract(
        address=created, code=b"", nonce=0, storage={KEY_A: 5}, balance=1
    )
    checks = expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_BEFORE, created, KEY_A), 5)
    checks += expect_eq(
        Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, created, KEY_A),
        5 if creation_reverts else 7,
    )
    checks += expect_eq(
        Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0),
        0 if creation_reverts else 1,
    )
    if not creation_reverts:
        checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOT_BEFORE, 0), 5)
        checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOT_AFTER, 0), 7)
    assertion = pre.deploy_contract(code=checks + Op.STOP)
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork,
                    target=factory,
                    state_gas_limit=creation_state_gas(fork, creations=1),
                )
            ],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=2),
            created: Account(
                nonce=0 if creation_reverts else 1,
                storage={KEY_A: 5 if creation_reverts else 7},
            ),
        },
    )


@STORAGE_ONLY_ACCOUNT_SKIP
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "initcode_writes",
    [
        pytest.param(False, id="wipe_only"),
        pytest.param(True, id="wipe_beside_write"),
    ],
)
def test_storage_wipe_of_unwritten_slot(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_writes: bool,
) -> None:
    """
    Leave a slot that creation at a storage-only address wipes without
    writing out of `slots_changed`, the per-address slot view and the
    storage flag, while the keyed lookups read its value before and
    after.
    """
    sender = pre.fund_eoa()
    initcode = Bytecode()
    if initcode_writes:
        initcode += Op.SSTORE(KEY_A, 7, original_value=0, new_value=7)
    initcode += Op.STOP
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, initcode_word(initcode))
        + Op.POP(Op.CREATE(0, 0, len(initcode)))
        + Op.STOP
    )
    created = compute_create_address(address=factory, nonce=1)
    pre.deploy_contract(
        address=created, code=b"", nonce=0, storage={KEY_B: 9}, balance=1
    )
    written = 1 if initcode_writes else 0
    flags = Spec.CHANGE_FLAG_NONCE
    if initcode_writes:
        flags |= Spec.CHANGE_FLAG_STORAGE

    checks = expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_BEFORE, created, KEY_B), 9)
    checks += expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, created, KEY_B), 0)
    checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), written)
    checks += expect_eq(
        Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOTS_COUNT, created, 0), written
    )
    if initcode_writes:
        checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOT_KEY, 0), KEY_A)
    checks += expect_eq(
        Op.TXDIFF(Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, created, 0), flags
    )
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork,
                    target=factory,
                    state_gas_limit=creation_state_gas(fork, creations=1)
                    + initcode.state_cost(fork),
                )
            ],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=2),
            created: Account(
                nonce=1, storage={KEY_A: 7 if initcode_writes else 0, KEY_B: 0}
            ),
        },
    )


ADDRESS_HIGH_BITS = (2**256 - 1) ^ (2**160 - 1)
"""Every bit of a stack word above the 20 address bytes."""

MASKED_WRITER_CODE = Op.SSTORE(KEY_A, 1) + Op.LOG0(0, 0) + Op.STOP
"""Update a slot and emit one event."""


@pytest.mark.parametrize(
    "param,index,expected",
    [
        pytest.param(Spec.TXDIFF_SLOT_BEFORE, KEY_A, 5, id="slot_before"),
        pytest.param(Spec.TXDIFF_SLOT_AFTER, KEY_A, 1, id="slot_after"),
        pytest.param(
            Spec.TXDIFF_BALANCE_BEFORE, 0, BOB_FUNDS, id="balance_before"
        ),
        pytest.param(
            Spec.TXDIFF_BALANCE_AFTER, 0, BOB_FUNDS, id="balance_after"
        ),
        pytest.param(
            Spec.TXDIFF_CODEHASH_BEFORE,
            0,
            code_hash(MASKED_WRITER_CODE),
            id="codehash_before",
        ),
        pytest.param(
            Spec.TXDIFF_CODEHASH_AFTER,
            0,
            code_hash(MASKED_WRITER_CODE),
            id="codehash_after",
        ),
        pytest.param(
            Spec.TXDIFF_ADDRESS_SLOTS_COUNT, 0, 1, id="address_slots_count"
        ),
        pytest.param(
            Spec.TXDIFF_ADDRESS_SLOT_INDEX, 0, 0, id="address_slot_index"
        ),
        pytest.param(
            Spec.TXDIFF_ADDRESS_EVENTS_COUNT, 0, 1, id="address_events_count"
        ),
        pytest.param(
            Spec.TXDIFF_ADDRESS_EVENT_INDEX, 0, 0, id="address_event_index"
        ),
        pytest.param(
            Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS,
            0,
            Spec.CHANGE_FLAG_STORAGE,
            id="account_change_flags",
        ),
    ],
)
def test_txdiff_masks_address_high_bits(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
    index: int,
    expected: int,
) -> None:
    """
    Read an address-keyed `TXDIFF` parameter for an address operand
    whose high bits are set as for its low 20 bytes, as `BALANCE` masks
    its operand.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(
        code=MASKED_WRITER_CODE, storage={KEY_A: 5}, balance=BOB_FUNDS
    )
    dirty = as_int(writer) | ADDRESS_HIGH_BITS
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXDIFF(param, dirty, index), expected) + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={sender: Account(nonce=1), writer: Account(storage={KEY_A: 1})},
    )
