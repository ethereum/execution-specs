"""Tests for the effects of EIP-2935 historical block hashes on EIP-7928."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Hash,
    Op,
    Transaction,
)

from tests.cancun.eip4788_beacon_root.spec import Spec as Spec4788
from tests.prague.eip2935_historical_block_hashes_from_state.spec import Spec

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

HISTORY_STORAGE_ADDRESS = Address(Spec.HISTORY_STORAGE_ADDRESS)
SYSTEM_ADDRESS = Address(Spec4788.SYSTEM_ADDRESS)


def get_history_storage_slot(block_number: int) -> int:
    """
    Return the ring buffer slot for a given block number.

    The history storage contract uses a ring buffer:
    slot = block_number % HISTORY_SERVE_WINDOW
    """
    return block_number % Spec.HISTORY_SERVE_WINDOW


def test_bal_2935_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure BAL captures history storage writes during system call.

    Block with 2 normal user transactions: Alice sends 10 wei to Charlie,
    Bob sends 10 wei to Charlie. At block start (pre-execution),
    SYSTEM_ADDRESS calls HISTORY_STORAGE_ADDRESS to store parent block hash.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa(amount=0)

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

    block = Block(
        txs=[tx1, tx2],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=get_history_storage_slot(0),
                            validate_any_change=True,
                        ),
                    ],
                ),
                # System address MUST NOT be included
                SYSTEM_ADDRESS: None,
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=2, post_nonce=1)
                    ],
                ),
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=transfer_value
                        ),
                        BalBalanceChange(
                            block_access_index=2,
                            post_balance=transfer_value * 2,
                        ),
                    ],
                ),
            }
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


def test_bal_2935_empty_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures history storage writes in empty block.

    Block with no transactions. At block start (pre-execution),
    SYSTEM_ADDRESS calls HISTORY_STORAGE_ADDRESS to store parent block hash.
    """
    block = Block(
        txs=[],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=get_history_storage_slot(0),
                            validate_any_change=True,
                        ),
                    ],
                ),
                SYSTEM_ADDRESS: None,
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={},
    )


@pytest.mark.parametrize(
    "query_block_number,is_valid",
    [
        pytest.param(0, True, id="valid_block_number"),
        pytest.param(1042, False, id="block_number_out_of_range"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="no_value"),
        pytest.param(100, id="with_value"),
    ],
)
def test_bal_2935_query(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    query_block_number: int,
    is_valid: bool,
    value: int,
) -> None:
    """
    Ensure BAL captures storage reads when querying historical block hashes.

    Test scenarios:
    1. Valid query (block_number=0, genesis hash): History storage contract
       reads the genesis hash slot, query contract writes returned value
    2. Invalid query (block_number=1042, out of range): History storage
       contract reverts before any storage access, query contract has
       implicit read recorded
    3. With value transfer: BAL captures balance changes in addition
       to storage operations (only when query is valid)
    """
    alice = pre.fund_eoa()

    # Contract that calls history storage contract with block number from
    # calldata and stores returned block hash in slot 0,
    # forwarding any value sent
    query_code = (
        Op.CALLDATACOPY(0, 0, 32)
        + Op.CALL(
            Op.GAS,
            HISTORY_STORAGE_ADDRESS,
            Op.CALLVALUE,
            0,
            32,
            32,
            32,
        )
        + Op.SSTORE(0, Op.MLOAD(32))
    )
    oracle = pre.deploy_contract(query_code)

    tx = Transaction(
        sender=alice,
        to=oracle,
        data=Hash(query_block_number),
        value=value,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # A setup up block that writes genesis block-hash
    # to history storage contract so that it can be
    # queried later.
    block_1 = Block()

    block_hash_slot = get_history_storage_slot(query_block_number)
    # Storage reads for the query:
    # - Valid query (block 0): reads `block_hash_slot`
    # - Invalid query (out-of-range block): reverts before SLOAD
    account_expectations = {}
    account_expectations[HISTORY_STORAGE_ADDRESS] = BalAccountExpectation(
        # Read only occurs for valid query
        storage_reads=[block_hash_slot] if is_valid else []
    )

    # Add balance changes if value is transferred and query is valid
    if value > 0 and is_valid:
        account_expectations[HISTORY_STORAGE_ADDRESS].balance_changes = [
            BalBalanceChange(block_access_index=1, post_balance=value)
        ]

    account_expectations[alice] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )

    account_expectations[oracle] = BalAccountExpectation(
        # Valid: write the returned hash (value is framework-computed)
        # Invalid: no-op SSTORE(0, 0) becomes implicit read
        storage_reads=[] if is_valid else [0],
        storage_changes=[
            BalStorageSlot(
                slot=0,
                validate_any_change=True,
            ),
        ]
        if is_valid
        else [],
        # if value > 0 and invalid, value stays in query contract
        balance_changes=[
            BalBalanceChange(
                block_access_index=1,
                post_balance=value,
            )
        ]
        if not is_valid and value > 0
        else [],
    )

    block_2 = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post_state = {
        alice: Account(nonce=1),
    }

    if is_valid:
        post_state[oracle] = Account()
    else:
        # Invalid query: zero stored
        post_state[oracle] = Account(storage={0: 0})

    if value > 0 and is_valid:
        post_state[HISTORY_STORAGE_ADDRESS] = Account(balance=value)

    blockchain_test(
        pre=pre,
        blocks=[block_1, block_2],
        post=post_state,
    )


def test_bal_2935_selfdestruct_to_history_storage(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure BAL captures SELFDESTRUCT to history storage address alongside
    system call storage writes.

    Single block with pre-execution system call writing parent hash to
    storage, followed by transaction where contract selfdestructs sending
    funds to HISTORY_STORAGE_ADDRESS. Tests that same address can appear in
    BAL with different change types (storage_changes and balance_changes)
    at different transaction indices.
    """
    alice = pre.fund_eoa()

    contract_balance = 100

    # Contract that selfdestructs to history storage address
    selfdestruct_code = Op.SELFDESTRUCT(HISTORY_STORAGE_ADDRESS)
    selfdestruct_contract = pre.deploy_contract(
        code=selfdestruct_code,
        balance=contract_balance,
    )

    tx = Transaction(
        sender=alice,
        to=selfdestruct_contract,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    account_expectations = {}

    # Add balance change from selfdestruct to history storage address
    account_expectations[HISTORY_STORAGE_ADDRESS] = BalAccountExpectation(
        balance_changes=[
            BalBalanceChange(
                block_access_index=1, post_balance=contract_balance
            )
        ]
    )

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
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            HISTORY_STORAGE_ADDRESS: Account(balance=contract_balance),
        },
    )
