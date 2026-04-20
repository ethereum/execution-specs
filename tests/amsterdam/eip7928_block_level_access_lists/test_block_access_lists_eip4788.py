"""Tests for the effects of EIP-4788 beacon roots on EIP-7928."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Hash,
    Op,
    Transaction,
)

from tests.cancun.eip4788_beacon_root.spec import Spec, SpecHelpers

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

BEACON_ROOTS_ADDRESS = Address(Spec.BEACON_ROOTS_ADDRESS)
SYSTEM_ADDRESS = Address(Spec.SYSTEM_ADDRESS)


def get_beacon_root_slots(timestamp: int) -> tuple:
    """
    Return (timestamp_slot, root_slot) for beacon root ring buffer.

    The beacon root contract uses two ring buffers:
    - timestamp_slot = timestamp % 8191
    - root_slot = (timestamp % 8191) + 8191
    """
    helpers = SpecHelpers()
    return (
        helpers.timestamp_index(timestamp),
        helpers.root_index(timestamp),
    )


def beacon_root_system_call_expectations(
    timestamp: int,
    beacon_root: Hash,
) -> dict:
    """
    Build BAL expectations for beacon root pre-execution system call.

    Returns account expectations for BEACON_ROOTS_ADDRESS and
    SYSTEM_ADDRESS at block_access_index=0.
    """
    timestamp_slot, root_slot = get_beacon_root_slots(timestamp)

    return {
        BEACON_ROOTS_ADDRESS: BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=timestamp_slot,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=0, post_value=timestamp
                        )
                    ],
                ),
                BalStorageSlot(
                    slot=root_slot,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=0, post_value=beacon_root
                        )
                    ],
                ),
            ],
        ),
        # System address MUST NOT be included
        SYSTEM_ADDRESS: None,
    }


def build_beacon_root_setup_block(
    timestamp: int,
    beacon_root: Hash,
) -> Block:
    """
    Build a block that stores beacon root via pre-execution system call.

    This is used as the first block in tests that query beacon roots.
    Returns an empty block (no transactions) that only performs the
    system call to store the beacon root.
    """
    account_expectations = beacon_root_system_call_expectations(
        timestamp, beacon_root
    )

    return Block(
        txs=[],
        parent_beacon_block_root=beacon_root,
        timestamp=timestamp,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )


def test_bal_4788_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure BAL captures beacon root storage writes during pre-execution
    system call.

    Block with 2 normal user transactions: Alice sends 10 wei to Charlie,
    Bob sends 10 wei to Charlie. At block start (pre-execution),
    SYSTEM_ADDRESS calls BEACON_ROOTS_ADDRESS to store parent beacon root.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa(amount=0)

    block_timestamp = 12
    beacon_root = Hash(0xABCDEF)

    transfer_value = 10

    tx1 = Transaction(
        sender=alice,
        to=charlie,
        value=transfer_value,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    tx2 = Transaction(
        sender=bob,
        to=charlie,
        value=transfer_value,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # Build BAL expectations starting with system call
    account_expectations = beacon_root_system_call_expectations(
        block_timestamp, beacon_root
    )

    # Add transaction-specific expectations
    account_expectations[alice] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )
    account_expectations[bob] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=2, post_nonce=1)],
    )
    account_expectations[charlie] = BalAccountExpectation(
        balance_changes=[
            BalBalanceChange(
                block_access_index=1, post_balance=transfer_value
            ),
            BalBalanceChange(
                block_access_index=2, post_balance=transfer_value * 2
            ),
        ],
    )

    block = Block(
        txs=[tx1, tx2],
        parent_beacon_block_root=beacon_root,
        timestamp=block_timestamp,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            charlie: Account(balance=transfer_value * 2),
        },
    )


def test_bal_4788_empty_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures beacon root storage writes in empty block.

    Block with no transactions. At block start (pre-execution),
    SYSTEM_ADDRESS calls BEACON_ROOTS_ADDRESS to store parent beacon root.
    """
    block_timestamp = 12
    beacon_root = Hash(0xABCDEF)

    # Build BAL expectations (only system call, no transactions)
    account_expectations = beacon_root_system_call_expectations(
        block_timestamp, beacon_root
    )

    block = Block(
        txs=[],
        parent_beacon_block_root=beacon_root,
        timestamp=block_timestamp,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={},
    )


@pytest.mark.parametrize(
    "timestamp,beacon_root,query_timestamp,expected_result,is_valid",
    [
        pytest.param(
            12, Hash(0xABCDEF), 12, Hash(0xABCDEF), True, id="valid_timestamp"
        ),
        pytest.param(12, Hash(0xABCDEF), 42, 0, False, id="invalid_timestamp"),
        pytest.param(12, Hash(0xABCDEF), 0, 0, False, id="zero_timestamp"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="no_value"),
        pytest.param(100, id="with_value"),
    ],
)
def test_bal_4788_query(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    timestamp: int,
    beacon_root: Hash,
    query_timestamp: int,
    expected_result: int | Hash,
    is_valid: bool,
    value: int,
) -> None:
    """
    Ensure BAL captures storage reads when querying beacon root.

    Test scenarios:
    1. Valid query (timestamp=12, matches stored timestamp): Beacon root
       contract reads both timestamp and root slots, query contract writes
       returned value
    2. Invalid query with non-zero timestamp (timestamp=42, no match):
       Beacon root contract reads only timestamp slot then reverts, query
       contract has implicit read recorded
    3. Invalid query with zero timestamp (timestamp=0): Beacon root
       contract reverts immediately before any storage access, query
       contract has implicit read recorded
    4. With value transfer: BAL captures balance changes in addition
       to storage operations (only when query is valid)
    """
    # Block 1: Store beacon root
    block1 = build_beacon_root_setup_block(timestamp, beacon_root)

    # Block 2: Alice queries the beacon root
    alice = pre.fund_eoa()

    # Contract that calls beacon root contract with timestamp from calldata
    # and stores returned beacon root in slot 0, forwarding any value sent
    query_code = (
        Op.CALLDATACOPY(0, 0, 32)
        + Op.CALL(
            Spec.BEACON_ROOTS_CALL_GAS,
            BEACON_ROOTS_ADDRESS,
            Op.CALLVALUE,  # forward value to beacon root contract
            0,  # args offset
            32,  # args size (timestamp)
            32,  # return offset
            32,  # return size (beacon root)
        )
        + Op.SSTORE(0, Op.MLOAD(32))
    )
    query_contract = pre.deploy_contract(query_code)

    tx = Transaction(
        sender=alice,
        to=query_contract,
        data=Hash(query_timestamp),
        value=value,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # Build BAL expectations for block 2
    block2_timestamp = timestamp + 1
    block2_beacon_root = Hash(0xDEADBEEF)

    account_expectations = beacon_root_system_call_expectations(
        block2_timestamp, block2_beacon_root
    )

    # Add storage reads for the query
    timestamp_slot, root_slot = get_beacon_root_slots(query_timestamp)

    # Storage access depends on query validity:
    # - Zero timestamp: reverts immediately (no storage access)
    # - Valid timestamp: reads both timestamp and root slots
    # - Invalid non-zero timestamp: reads only timestamp slot before reverting
    account_expectations[BEACON_ROOTS_ADDRESS].storage_reads = (
        []
        if query_timestamp == 0  # Reverts early if timestamp is zero
        else [timestamp_slot, root_slot]
        if is_valid
        else [timestamp_slot]
    )

    # Balance changes for callee: credited if valid, must be empty if invalid
    if value > 0:
        account_expectations[BEACON_ROOTS_ADDRESS].balance_changes = (
            [BalBalanceChange(block_access_index=1, post_balance=value)]
            if is_valid
            else []
        )

    # Add transaction-specific expectations
    account_expectations[alice] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )

    account_expectations[query_contract] = BalAccountExpectation(
        # If the call to beacon root contract reverts
        # a no-op write happens and an implicit read is
        # recorded.
        storage_reads=[] if is_valid else [0],
        # Write reverts if invalid
        storage_changes=[
            BalStorageSlot(
                slot=0,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=1, post_value=expected_result
                    )
                ],
            ),
        ]
        if is_valid
        else [],
        # if value > 0 and invalid, no balance is sent to beacon root so
        # is kept in the query contract
        balance_changes=[
            BalBalanceChange(
                block_access_index=1,
                post_balance=value,
            )
        ]
        if not is_valid and value > 0
        else [],
    )

    block2 = Block(
        txs=[tx],
        parent_beacon_block_root=block2_beacon_root,
        timestamp=block2_timestamp,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post_state = {
        alice: Account(nonce=1),
        query_contract: Account(storage={0: expected_result}),
    }

    if value > 0 and is_valid:
        post_state[BEACON_ROOTS_ADDRESS] = Account(balance=value)

    blockchain_test(
        pre=pre,
        blocks=[block1, block2],
        post=post_state,
    )


@pytest.mark.parametrize(
    "calldata_size",
    [
        pytest.param(0, id="empty_calldata"),
        pytest.param(31, id="calldata_too_short"),
        pytest.param(33, id="calldata_too_long"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="no_value"),
        pytest.param(100, id="with_value"),
    ],
)
def test_bal_4788_invalid_calldata_size(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    calldata_size: int,
    value: int,
) -> None:
    """
    Ensure BAL correctly handles EIP-4788 queries with invalid calldata size.

    EIP-4788 requires exactly 32 bytes of calldata (a timestamp). Any other
    size causes immediate revert before any storage access occurs.

    Test scenarios with and without value transfer:
    1. Empty calldata (0 bytes): Reverts immediately
    2. Too short (31 bytes): Reverts before storage access
    3. Too long (33 bytes): Reverts before storage access
    """
    alice = pre.fund_eoa()

    block_timestamp = 12
    beacon_root = Hash(0xABCDEF)

    # Contract that calls beacon roots contract with variable-size calldata
    # and stores returned beacon root in slot 0
    query_code = (
        Op.CALLDATACOPY(0, 0, calldata_size)
        + Op.CALL(
            Spec.BEACON_ROOTS_CALL_GAS,
            BEACON_ROOTS_ADDRESS,
            Op.CALLVALUE,
            0,
            calldata_size,
            32,
            32,
        )
        + Op.SSTORE(0, Op.MLOAD(32))
    )
    query_contract = pre.deploy_contract(query_code)

    # Pad calldata to requested size
    calldata = b"\x00" * calldata_size

    tx = Transaction(
        sender=alice,
        to=query_contract,
        data=calldata,
        value=value,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    account_expectations = beacon_root_system_call_expectations(
        block_timestamp, beacon_root
    )
    # Beacon roots contract reverts before any storage access
    account_expectations[BEACON_ROOTS_ADDRESS].storage_reads = []
    if value > 0:
        account_expectations[BEACON_ROOTS_ADDRESS].balance_changes = []

    account_expectations[alice] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )

    account_expectations[query_contract] = BalAccountExpectation(
        # SSTORE(0, 0) is a no-op write, becomes implicit read
        storage_reads=[0],
        storage_changes=[],
        # Value stays in query contract when call reverts
        balance_changes=[
            BalBalanceChange(block_access_index=1, post_balance=value)
        ]
        if value > 0
        else [],
    )

    block = Block(
        txs=[tx],
        parent_beacon_block_root=beacon_root,
        timestamp=block_timestamp,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post_state: dict[Address, Account] = {
        alice: Account(nonce=1),
        query_contract: Account(storage={0: 0}),
    }

    if value > 0:
        post_state[query_contract] = Account(storage={0: 0}, balance=value)

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post_state,
    )


def test_bal_4788_selfdestruct_to_beacon_root(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure BAL captures SELFDESTRUCT to beacon root address alongside
    system call storage writes.

    Single block with pre-execution system call writing beacon root to
    storage, followed by transaction where contract selfdestructs sending
    funds to BEACON_ROOTS_ADDRESS. Tests that same address can appear in
    BAL with different change types (storage_changes and balance_changes)
    at different transaction indices.
    """
    alice = pre.fund_eoa()

    block_timestamp = 12
    beacon_root = Hash(0xABCDEF)
    contract_balance = 100

    # Contract that selfdestructs to beacon root address
    selfdestruct_code = Op.SELFDESTRUCT(BEACON_ROOTS_ADDRESS)
    selfdestruct_contract = pre.deploy_contract(
        code=selfdestruct_code,
        balance=contract_balance,
    )

    tx = Transaction(
        sender=alice,
        to=selfdestruct_contract,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # Build BAL expectations starting with system call
    account_expectations = beacon_root_system_call_expectations(
        block_timestamp, beacon_root
    )

    # Add balance change from selfdestruct to beacon root address
    account_expectations[BEACON_ROOTS_ADDRESS].balance_changes = [
        BalBalanceChange(block_access_index=1, post_balance=contract_balance)
    ]

    # Add transaction-specific expectations
    account_expectations[alice] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )
    account_expectations[selfdestruct_contract] = BalAccountExpectation(
        balance_changes=[
            BalBalanceChange(block_access_index=1, post_balance=0)
        ],
    )

    block = Block(
        txs=[tx],
        parent_beacon_block_root=beacon_root,
        timestamp=block_timestamp,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            BEACON_ROOTS_ADDRESS: Account(balance=contract_balance),
        },
    )
