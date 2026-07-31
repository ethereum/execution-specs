"""
System-contract storage tests for the EIP-8297 partitioned binary
tree.

Amsterdam-era system contracts write storage on EVERY block, which
under EIP-8297 means their storage churns constantly. The EIP-4788
beacon-root ring buffer is the one exercised below whose slot numbers
reach far past the 64-slot account header into overflow storage
groups (see the slot arithmetic in each test's docstring below).

EIP-2935's block-hash ring buffer and EIP-7002's withdrawal-request
queue are NOT bounded to the header either, but the upstream suites
this module inherits (unmodified, running under `BinaryTree` via
`valid_from` inheritance) never drive them that far: EIP-2935's
`HISTORY_SERVE_WINDOW` is 8191 slots, and EIP-7002 stores each queued
request at `WITHDRAWAL_REQUEST_QUEUE_STORAGE_OFFSET + 3 *
queue_index`, so ~21 requests in one block already exceed slot 64 --
neither upstream suite reaches those counts, which is a property of
their inputs, not a bound on either buffer. A high genesis block
number (EIP-2935) or 21+ queued withdrawal requests (EIP-7002) would
drive these into overflow storage groups; not covered here yet.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
    Op,
    Transaction,
)

from ...cancun.eip4788_beacon_root.spec import Spec as Spec4788
from ...cancun.eip4788_beacon_root.spec import SpecHelpers
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


def test_beacon_root_ring_buffer_across_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the EIP-4788 beacon-root ring buffer lands its timestamp and
    root slots correctly across three blocks with distinct timestamps.

    Chosen for storage-group coverage (group 0 is the header plus
    overflow slots 64-255, group >= 1 is HIGH): timestamp=12 keeps its
    timestamp slot in the header but its root slot (8203) is already
    group 32; timestamp=300 pushes even the timestamp slot itself into
    group 1; timestamp=8000 puts the timestamp slot in group 31 and
    the root slot in group 63. This grouping is not itself verified
    below, which checks only slot/value pairs, not tree group.
    """
    helpers = SpecHelpers()
    beacon_roots_address = Address(Spec4788.BEACON_ROOTS_ADDRESS)

    entries = [
        (12, Hash(0xAAAA)),
        (300, Hash(0xBBBB)),
        (8000, Hash(0xCCCC)),
    ]

    blocks = [
        Block(txs=[], parent_beacon_block_root=root, timestamp=ts)
        for ts, root in entries
    ]

    expected_storage: dict[int, int | Hash] = {}
    for ts, root in entries:
        expected_storage[helpers.timestamp_index(ts)] = ts
        expected_storage[helpers.root_index(ts)] = root

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={beacon_roots_address: Account(storage=expected_storage)},
    )


def test_beacon_root_ring_buffer_collision_later_overwrites(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify two blocks whose timestamps collide in the EIP-4788 ring
    buffer (same `timestamp % HISTORY_BUFFER_LENGTH`) end with the
    LATER block's timestamp and root values in both ring-buffer slots.
    """
    helpers = SpecHelpers()
    beacon_roots_address = Address(Spec4788.BEACON_ROOTS_ADDRESS)

    first_timestamp = 100
    second_timestamp = first_timestamp + Spec4788.HISTORY_BUFFER_LENGTH

    first_root = Hash(0x1111)
    second_root = Hash(0x2222)

    blocks = [
        Block(
            txs=[],
            parent_beacon_block_root=first_root,
            timestamp=first_timestamp,
        ),
        Block(
            txs=[],
            parent_beacon_block_root=second_root,
            timestamp=second_timestamp,
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            beacon_roots_address: Account(
                storage={
                    helpers.timestamp_index(second_timestamp): (
                        second_timestamp
                    ),
                    helpers.root_index(second_timestamp): second_root,
                }
            )
        },
    )


def test_system_contract_and_user_contract_writes_coexist(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a block where the EIP-4788 beacon-root system call and a
    user transaction's contract storage write both land in the post
    state: the commitment swap must not let one clobber or drop the
    other, even though the two writes live in totally different
    accounts (a predeploy vs. a freshly deployed user contract).
    """
    helpers = SpecHelpers()
    beacon_roots_address = Address(Spec4788.BEACON_ROOTS_ADDRESS)

    timestamp = 4200
    beacon_root = Hash(0xFEEDFACE)

    slot, value = 5, 0xC0FFEE
    user_contract = pre.deploy_contract(code=Op.SSTORE(slot, value) + Op.STOP)

    tx = Transaction(sender=pre.fund_eoa(), to=user_contract)

    block = Block(
        txs=[tx],
        parent_beacon_block_root=beacon_root,
        timestamp=timestamp,
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            beacon_roots_address: Account(
                storage={
                    helpers.timestamp_index(timestamp): timestamp,
                    helpers.root_index(timestamp): beacon_root,
                }
            ),
            user_contract: Account(storage={slot: value}),
        },
    )
