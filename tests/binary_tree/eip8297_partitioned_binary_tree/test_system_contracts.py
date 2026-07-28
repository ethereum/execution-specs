"""
System-contract storage tests for the EIP-8297 partitioned binary
tree.

Amsterdam-era system contracts (EIP-4788, EIP-2935, EIP-7002) write
storage on EVERY block, which under EIP-8297 means their storage
churns constantly, including ring buffers whose slot numbers reach far
past the 64-slot header range into many overflow storage groups.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Hash,
    Op,
    Transaction,
)

from ...cancun.eip4788_beacon_root.spec import Spec as Spec4788
from ...cancun.eip4788_beacon_root.spec import SpecHelpers
from ...prague.eip2935_historical_block_hashes_from_state.spec import (
    Spec as Spec2935,
)
from ...prague.eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
)
from ...prague.eip7002_el_triggerable_withdrawals.spec import Spec as Spec7002
from .spec import Spec, ref_spec_8297

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
    slot in group 31 and the root slot (16191) in group 63.
    """
    helpers = SpecHelpers()
    beacon_roots_address = Address(Spec4788.BEACON_ROOTS_ADDRESS)

    entries = [
        (12, Hash(0xAAAA)),
        (300, Hash(0xBBBB)),
        (8000, Hash(0xCCCC)),
    ]
    assert Spec.storage_group_index(300) == 1, (
        "timestamp slot 300 must reach a HIGH group on its own"
    )

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
    assert helpers.timestamp_index(first_timestamp) == helpers.timestamp_index(
        second_timestamp
    ), "timestamps must collide in the ring buffer"

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


def test_block_hash_history_ring_buffer_across_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the EIP-2935 block-hash history ring buffer serves the
    correct parent hash, at slot `block_number % HISTORY_SERVE_WINDOW`,
    for each of several recent blocks.

    A literal expected hash cannot be written ahead of fill time (a
    block's hash depends on a state root the t8n computes), so,
    following the idiom already established in
    `tests/prague/eip2935_historical_block_hashes_from_state`, a
    checker contract stores 1 only when the history contract's
    returned hash for a given block number agrees with the legacy
    `BLOCKHASH` opcode for that same number (valid here since every
    checked block is comfortably within `BLOCKHASH`'s last-256-block
    window regardless of EIP-2935).
    """
    history_address = Address(Spec2935.HISTORY_STORAGE_ADDRESS)
    sender = pre.fund_eoa()

    empty_block_count = 4
    blocks: list[Block] = [Block() for _ in range(empty_block_count)]

    check_return_offset = 32
    code = Bytecode()
    expected_storage: dict[int, int] = {}
    for i, block_number in enumerate(range(0, empty_block_count + 1)):
        code += (
            Op.MSTORE(0, block_number)
            + Op.POP(
                Op.CALL(
                    Op.GAS,
                    history_address,
                    0,
                    0,
                    32,
                    check_return_offset,
                    32,
                )
            )
            + Op.SSTORE(
                i,
                Op.EQ(
                    Op.MLOAD(check_return_offset),
                    Op.BLOCKHASH(block_number),
                ),
            )
        )
        expected_storage[i] = 1
    code += Op.STOP

    checker = pre.deploy_contract(code)
    blocks.append(Block(txs=[Transaction(sender=sender, to=checker)]))

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={checker: Account(storage=expected_storage)},
    )


def test_withdrawal_request_queue_storage_and_block_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a single EIP-7002 withdrawal request mutates exactly the
    queue-storage slots the EIP defines, and that the block's EIP-7685
    requests field still carries the request correctly: the commitment
    swap only changes how storage is committed, not what
    execution-layer requests a block produces.
    """
    sender = pre.fund_eoa()
    predeploy = Address(Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS)

    pubkey = b"\xab" * 48
    amount = 64_000_000_000
    request = WithdrawalRequest(
        validator_pubkey=pubkey, amount=amount, fee=Spec7002.get_fee(0)
    ).with_source_address(sender)

    tx = Transaction(
        sender=sender,
        to=predeploy,
        value=request.fee,
        data=request.calldata,
    )

    base_slot = Spec7002.WITHDRAWAL_REQUEST_QUEUE_STORAGE_OFFSET
    pubkey_first_word = int.from_bytes(pubkey[:32], byteorder="big")
    pubkey_amount_word = int.from_bytes(
        pubkey[-16:] + amount.to_bytes(8, byteorder="big") + b"\x00" * 8,
        byteorder="big",
    )
    # EXCESS/COUNT/HEAD/TAIL (slots 0-3) all churn mid-block but, for a
    # single request under TARGET_WITHDRAWAL_REQUESTS_PER_BLOCK, this
    # is a "clean sweep": all four are back at their genesis value of
    # zero by the end of the block, so they are omitted below (an
    # omitted slot is equivalent to an explicit zero in this
    # framework).
    expected_queue_storage = {
        base_slot: sender,
        base_slot + 1: pubkey_first_word,
        base_slot + 2: pubkey_amount_word,
    }

    block = Block(txs=[tx], requests=[request])

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender: Account(nonce=1),
            predeploy: Account(
                balance=request.fee, storage=expected_queue_storage
            ),
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
