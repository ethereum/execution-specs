"""
Tests for the write operation of
[EIP-8272: Recent Roots for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8272).

A call to the recent root contract with 64 bytes of calldata publishes a
root for the caller's source under the current slot; the root becomes
referenceable from the next slot on. Publishing is ordinary execution:
value reverts, a static context fails, and delegated code writes the
delegating account's storage instead.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Environment,
    Fork,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import (
    default_frame,
    sender_frame,
    verify_frame,
)
from ..eip8141_frame_transactions.spec import Spec as FrameSpec
from .helpers import (
    WRITE_STATE_GAS,
    recent_root_frame,
    validation_gas,
    write_frame,
)
from .spec import (
    Spec,
    entry_hash,
    ref_spec_8272,
    source_id,
    storage_key,
    validation_tuple,
    write_calldata,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_8272.git_path
REFERENCE_SPEC_VERSION = ref_spec_8272.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

WRITE_SLOT = 100
"""Slot in which roots are published."""

SALT = (0x5A17).to_bytes(32, "big")
"""Salt of the root sources in these tests."""

OTHER_SALT = (0x5A18).to_bytes(32, "big")
"""Second salt, giving the same address a second root source."""

ROOT_A = (0xA1).to_bytes(32, "big")
ROOT_B = (0xB2).to_bytes(32, "big")


def entry_value(source: bytes, slot: int, root: bytes) -> int:
    """Return the stored entry hash as a storage value."""
    return int.from_bytes(entry_hash(source, slot, root), "big")


def relay_contract(pre: Alloc, opcode: Op) -> Address:
    """
    Deploy a contract forwarding its calldata to the recent root contract
    with `opcode` (`CALL`, `DELEGATECALL` or `CALLCODE`), recording the
    call's success at `SLOT_EXECUTED`.
    """
    call = (
        opcode(
            gas=Op.GAS,
            address=Spec.RECENT_ROOT_ADDRESS,
            args_offset=0,
            args_size=Op.CALLDATASIZE,
            ret_offset=0,
            ret_size=0,
        )
        if opcode == Op.DELEGATECALL
        else opcode(
            gas=Op.GAS,
            address=Spec.RECENT_ROOT_ADDRESS,
            value=0,
            args_offset=0,
            args_size=Op.CALLDATASIZE,
            ret_offset=0,
            ret_size=0,
        )
    )
    return pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(SLOT_EXECUTED, call)
        + Op.STOP
    )


@pytest.mark.parametrize("write_slot", [WRITE_SLOT, 8192, 2**64 - 2])
def test_publish_then_verify(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    write_slot: int,
) -> None:
    """
    Publish a root from a sender frame in one slot and verify it from the
    next slot on.

    The write appears in the first block's access list as a storage
    change at the recent root contract; the verification appears in the
    second block's as a storage read of the same key.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source = source_id(sender, SALT)
    key = storage_key(source, write_slot)
    value = entry_value(source, write_slot, ROOT_A)

    publish = Transaction(
        sender=sender,
        frames=[verify_frame(), write_frame(SALT, ROOT_A)],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
            ],
        ),
    )
    verify = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(validation_tuple(source, write_slot, ROOT_A)),
            verify_frame(),
            sender_frame(target=target),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=FrameSpec.STATUS_SUCCESS,
                    gas_used=validation_gas(fork, tuples=1, cold_keys=1),
                    state_gas_used=0,
                ),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
            ],
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                slot_number=write_slot,
                txs=[publish],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        Spec.RECENT_ROOT_ADDRESS: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=key,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=value,
                                        )
                                    ],
                                )
                            ],
                        ),
                    }
                ),
            ),
            Block(
                slot_number=write_slot + 1,
                txs=[verify],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        Spec.RECENT_ROOT_ADDRESS: BalAccountExpectation(
                            storage_changes=[],
                            storage_reads=[key],
                        ),
                    }
                ),
            ),
        ],
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                nonce=Spec.RECENT_ROOT_NONCE,
                code=Spec.RECENT_ROOT_CODE,
                storage={key: value},
            ),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.parametrize(
    "separate_transactions",
    [False, True],
    ids=["one_transaction", "two_transactions"],
)
def test_last_write_in_slot_wins(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    separate_transactions: bool,
) -> None:
    """
    Two writes by the same source in one slot target the same storage
    key: the later one overwrites the earlier, within one transaction or
    across two, and only its root verifies in the next slot.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source = source_id(sender, SALT)
    key = storage_key(source, WRITE_SLOT)

    writes = [write_frame(SALT, ROOT_A), write_frame(SALT, ROOT_B)]
    if separate_transactions:
        publish = [
            Transaction(sender=sender, frames=[verify_frame(), write])
            for write in writes
        ]
    else:
        publish = [
            Transaction(sender=sender, frames=[verify_frame(), *writes])
        ]
    verify_last = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(validation_tuple(source, WRITE_SLOT, ROOT_B)),
            verify_frame(),
            sender_frame(target=target),
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(slot_number=WRITE_SLOT, txs=publish),
            Block(slot_number=WRITE_SLOT + 1, txs=[verify_last]),
        ],
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                storage={key: entry_value(source, WRITE_SLOT, ROOT_B)},
            ),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


def test_ring_overwrite(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A write `RECENT_ROOT_LENGTH` slots after an earlier one lands on the
    same ring buffer key and replaces the earlier entry; the new root
    verifies in the following slot and the old root does not.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source = source_id(sender, SALT)
    later_slot = WRITE_SLOT + Spec.RECENT_ROOT_LENGTH
    key = storage_key(source, WRITE_SLOT)
    assert key == storage_key(source, later_slot)

    # Transactions are built in execution order: the sender's nonce is
    # assigned at construction.
    publish_first = Transaction(
        sender=sender,
        frames=[verify_frame(), write_frame(SALT, ROOT_A)],
    )
    publish_again = Transaction(
        sender=sender,
        frames=[verify_frame(), write_frame(SALT, ROOT_B)],
    )
    verify_new = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(validation_tuple(source, later_slot, ROOT_B)),
            verify_frame(),
            sender_frame(target=target),
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(slot_number=WRITE_SLOT, txs=[publish_first]),
            Block(slot_number=later_slot, txs=[publish_again]),
            Block(slot_number=later_slot + 1, txs=[verify_new]),
        ],
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                storage={key: entry_value(source, later_slot, ROOT_B)},
            ),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


def test_publish_from_contract(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A contract calling the recent root contract is the root source: the
    entry is keyed by the contract's address, not by the transaction
    sender's, and a reference naming the contract verifies.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    relay = relay_contract(pre, Op.CALL)
    source = source_id(relay, SALT)
    key = storage_key(source, WRITE_SLOT)

    publish = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                target=relay,
                data=write_calldata(SALT, ROOT_A),
                state_gas_limit=WRITE_STATE_GAS,
            ),
        ],
    )
    verify = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(validation_tuple(source, WRITE_SLOT, ROOT_A)),
            verify_frame(),
            sender_frame(target=target),
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(slot_number=WRITE_SLOT, txs=[publish]),
            Block(slot_number=WRITE_SLOT + 1, txs=[verify]),
        ],
        post={
            relay: Account(storage={SLOT_EXECUTED: 1}),
            Spec.RECENT_ROOT_ADDRESS: Account(
                storage={key: entry_value(source, WRITE_SLOT, ROOT_A)},
            ),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
        pytest.param(Op.CALLCODE, id="callcode"),
    ],
)
def test_delegated_write_uses_calling_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
) -> None:
    """
    Running the recent root code in another account's storage context
    writes that account's storage, not the recent root contract's.

    Under `DELEGATECALL` the source is the relay's caller, the sender;
    under `CALLCODE` it is the relay itself. Either way the entry lands
    in the relay's storage and the recent root contract's stays empty.
    """
    sender = pre.fund_eoa()
    relay = relay_contract(pre, opcode)
    writer = sender if opcode == Op.DELEGATECALL else relay
    source = source_id(writer, SALT)
    key = storage_key(source, WRITE_SLOT)

    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                sender_frame(
                    target=relay,
                    data=write_calldata(SALT, ROOT_A),
                    state_gas_limit=WRITE_STATE_GAS,
                ),
            ],
        ),
        post={
            relay: Account(
                storage={
                    SLOT_EXECUTED: 1,
                    key: entry_value(source, WRITE_SLOT, ROOT_A),
                }
            ),
            Spec.RECENT_ROOT_ADDRESS: Account(
                nonce=Spec.RECENT_ROOT_NONCE,
                code=Spec.RECENT_ROOT_CODE,
                storage={key: 0},
            ),
        },
    )


def test_write_with_value_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A write call carrying value reverts and stores nothing; the sender
    frame fails without invalidating the transaction.
    """
    sender = pre.fund_eoa()
    source = source_id(sender, SALT)
    key = storage_key(source, WRITE_SLOT)

    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[verify_frame(), write_frame(SALT, ROOT_A, value=1)],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(status=FrameSpec.STATUS_FAILURE),
                ],
            ),
        ),
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                nonce=Spec.RECENT_ROOT_NONCE,
                code=Spec.RECENT_ROOT_CODE,
                balance=0,
                storage={key: 0},
            ),
        },
    )


@pytest.mark.parametrize(
    "data_length",
    [
        pytest.param(Spec.RECENT_ROOT_WRITE_BYTES - 1, id="63_bytes"),
        pytest.param(Spec.RECENT_ROOT_WRITE_BYTES + 1, id="65_bytes"),
    ],
)
def test_write_with_wrong_length_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    data_length: int,
) -> None:
    """
    Calldata one byte shorter or longer than the write encoding is
    neither a write nor a whole number of validation tuples: the call
    reverts and stores nothing.
    """
    sender = pre.fund_eoa()
    source = source_id(sender, SALT)
    key = storage_key(source, WRITE_SLOT)
    data = (write_calldata(SALT, ROOT_A) + b"\x00")[:data_length]

    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[verify_frame(), write_frame(SALT, ROOT_A, data=data)],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(status=FrameSpec.STATUS_FAILURE),
                ],
            ),
        ),
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                nonce=Spec.RECENT_ROOT_NONCE,
                code=Spec.RECENT_ROOT_CODE,
                storage={key: 0},
            ),
        },
    )


@pytest.mark.exception_test
def test_static_write_fails(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A `VERIFY` frame carrying the 64-byte write encoding runs the write
    in a static context: the store fails, the frame halts, and the
    transaction is invalid with storage unchanged.
    """
    sender = pre.fund_eoa()
    source = source_id(sender, SALT)
    key = storage_key(source, WRITE_SLOT)

    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                recent_root_frame(write_calldata(SALT, ROOT_A)),
                verify_frame(),
            ],
            error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
        ),
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                nonce=Spec.RECENT_ROOT_NONCE,
                code=Spec.RECENT_ROOT_CODE,
                storage={key: 0},
            ),
        },
    )


def test_delegated_eoa_write_uses_authority_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Keep an EIP-7702 delegated write in the authority's storage."""
    sender = pre.fund_eoa()
    authority = pre.fund_eoa(delegation=Spec.RECENT_ROOT_ADDRESS)
    source = source_id(sender, SALT)
    key = storage_key(source, WRITE_SLOT)
    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                sender_frame(
                    target=authority,
                    data=write_calldata(SALT, ROOT_A),
                    state_gas_limit=WRITE_STATE_GAS,
                ),
            ],
            expected_receipt=TransactionReceipt(
                frame_receipts=[
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                ],
            ),
        ),
        post={
            authority: Account(
                storage={key: entry_value(source, WRITE_SLOT, ROOT_A)}
            ),
            Spec.RECENT_ROOT_ADDRESS: Account(storage={key: 0}),
        },
    )


def test_sources_by_salt(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    One address publishing under two salts in the same slot owns two
    root sources, and both roots verify together in the next slot.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    published = [
        (source_id(sender, SALT), ROOT_A),
        (source_id(sender, OTHER_SALT), ROOT_B),
    ]

    publish = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            write_frame(SALT, ROOT_A),
            write_frame(OTHER_SALT, ROOT_B),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS, logs=[]),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS, logs=[]),
            ],
        ),
    )
    verify = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(
                [
                    validation_tuple(source, WRITE_SLOT, root)
                    for source, root in published
                ]
            ),
            verify_frame(),
            sender_frame(target=target),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=FrameSpec.STATUS_SUCCESS,
                    gas_used=validation_gas(fork, tuples=2, cold_keys=2),
                    state_gas_used=0,
                ),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
            ],
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(slot_number=WRITE_SLOT, txs=[publish]),
            Block(slot_number=WRITE_SLOT + 1, txs=[verify]),
        ],
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                storage={
                    storage_key(source, WRITE_SLOT): entry_value(
                        source, WRITE_SLOT, root
                    )
                    for source, root in published
                },
            ),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


def test_default_frame_write_uses_entry_point_source(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A `DEFAULT` frame calls as the frame entry point, so its write lands
    under the entry point's source rather than the sender's.
    """
    sender = pre.fund_eoa()
    entry_point_source = source_id(FrameSpec.ENTRY_POINT, SALT)

    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                default_frame(
                    target=Spec.RECENT_ROOT_ADDRESS,
                    data=write_calldata(SALT, ROOT_A),
                    state_gas_limit=WRITE_STATE_GAS,
                ),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS, logs=[]),
                ],
            ),
        ),
        post={
            Spec.RECENT_ROOT_ADDRESS: Account(
                storage={
                    storage_key(entry_point_source, WRITE_SLOT): entry_value(
                        entry_point_source, WRITE_SLOT, ROOT_A
                    ),
                    storage_key(source_id(sender, SALT), WRITE_SLOT): 0,
                },
            ),
        },
    )


def test_static_call_write_fails(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A write reached through `STATICCALL` fails and stores nothing, while
    the calling frame carries on and the transaction stays valid.
    """
    sender = pre.fund_eoa()
    relay = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=Spec.RECENT_ROOT_ADDRESS,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=0,
            )
        )
        + Op.STOP
    )
    key = storage_key(source_id(relay, SALT), WRITE_SLOT)

    state_test(
        env=Environment(slot_number=WRITE_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                sender_frame(
                    target=relay,
                    data=write_calldata(SALT, ROOT_A),
                    state_gas_limit=WRITE_STATE_GAS,
                ),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                ],
            ),
        ),
        post={Spec.RECENT_ROOT_ADDRESS: Account(storage={key: 0})},
    )
