"""
System-contract storage tests for the EIP-8297 partitioned binary
tree.

Amsterdam-era system contracts write storage on EVERY block, which
under EIP-8297 means their storage churns constantly. The EIP-4788
beacon-root ring buffer is the one whose slot numbers reach far past
the 64-slot account header into overflow storage groups (see the slot
arithmetic in each test's docstring below); EIP-2935's block-hash ring
buffer and EIP-7002's withdrawal-request queue both stay entirely
inside the header for realistic block counts, so they carry no
PBT-specific property beyond what the upstream
`tests/prague/eip2935_historical_block_hashes_from_state` and
`tests/prague/eip7002_el_triggerable_withdrawals` suites already cover
under `BinaryTree` by inheritance (both are `valid_from` a fork at or
before Prague, and `BinaryTree` subclasses Amsterdam).
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

    Storage groups (`Spec.storage_group_index`; group 0 is the header
    plus overflow slots 64-255, group >= 1 is HIGH, i.e. slot > 255):
    timestamp=12 keeps its own timestamp slot (12) in the account
    HEADER, but its root slot (8203) already lands in group 32.
    timestamp=300 pushes even the timestamp slot itself into group 1
    (HIGH) without needing the root slot's fixed +8191 offset; its
    root slot (8491) is group 33. timestamp=8000 puts the timestamp
    slot in group 31 and the root slot (16191) in group 63. This
    grouping is why these three timestamps were chosen for coverage;
    it is not itself verified below, which checks only slot/value
    pairs on the account, not which tree group a key lands in.
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
