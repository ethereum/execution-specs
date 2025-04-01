"""
abstract: Tests blob type transactions for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test blob type transactions for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).


note: Adding a new test
    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test or state_test
    - pre
    - env
    - block or txs

    All other `pytest.fixture` fixtures can be parametrized to generate new combinations and test cases.

"""  # noqa: E501

from typing import List, Optional, Tuple

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    EngineAPIError,
    Environment,
    Hash,
    Header,
    Removable,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version


@pytest.fixture
def destination_account_code() -> Bytecode | None:
    """Code in the destination account for the blob transactions."""
    return None


@pytest.fixture
def destination_account_balance() -> int:
    """Balance in the destination account for the blob transactions."""
    return 0


@pytest.fixture
def destination_account(
    pre: Alloc, destination_account_code: Bytecode | None, destination_account_balance: int
) -> Address:
    """Destination account for the blob transactions."""
    if destination_account_code is not None:
        return pre.deploy_contract(
            code=destination_account_code,
            balance=destination_account_balance,
        )
    return pre.fund_eoa(destination_account_balance)


@pytest.fixture
def tx_gas(
    fork: Fork,
    tx_calldata: bytes,
    tx_access_list: List[AccessList],
) -> int:
    """Gas allocated to transactions sent during test."""
    tx_intrinsic_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    return tx_intrinsic_cost_calculator(calldata=tx_calldata, access_list=tx_access_list)


@pytest.fixture
def blobs_per_tx() -> List[int]:
    """
    Return list of integers that each represent the number of blobs in each
    transaction in the block of the test.

    Used to automatically generate a list of correctly versioned blob hashes.

    Default is to have one transaction with one blob.

    Can be overloaded by a test case to provide a custom list of blob counts.
    """
    return [1]


@pytest.fixture
def blob_hashes_per_tx(blobs_per_tx: List[int]) -> List[List[Hash]]:
    """
    Produce the list of blob hashes that are sent during the test.

    Can be overloaded by a test case to provide a custom list of blob hashes.
    """
    return [
        add_kzg_version(
            [Hash(x) for x in range(blob_count)],
            Spec.BLOB_COMMITMENT_VERSION_KZG,
        )
        for blob_count in blobs_per_tx
    ]


@pytest.fixture
def total_account_minimum_balance(  # noqa: D103
    blob_gas_per_blob: int,
    tx_gas: int,
    tx_value: int,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    blob_hashes_per_tx: List[List[bytes]],
) -> int:
    """
    Calculate minimum balance required for the account to be able to send
    the transactions in the block of the test.
    """
    minimum_cost = 0
    for tx_blob_count in [len(x) for x in blob_hashes_per_tx]:
        blob_cost = tx_max_fee_per_blob_gas * blob_gas_per_blob * tx_blob_count
        minimum_cost += (tx_gas * tx_max_fee_per_gas) + tx_value + blob_cost
    return minimum_cost


@pytest.fixture
def total_account_transactions_fee(  # noqa: D103
    tx_gas: int,
    tx_value: int,
    blob_gas_price: int,
    block_base_fee_per_gas: int,
    blob_gas_per_blob: int,
    tx_max_fee_per_gas: int,
    tx_max_priority_fee_per_gas: int,
    blob_hashes_per_tx: List[List[bytes]],
) -> int:
    """Calculate actual fee for the blob transactions in the block of the test."""
    total_cost = 0
    for tx_blob_count in [len(x) for x in blob_hashes_per_tx]:
        blob_cost = blob_gas_price * blob_gas_per_blob * tx_blob_count
        block_producer_fee = (
            tx_max_fee_per_gas - block_base_fee_per_gas if tx_max_priority_fee_per_gas else 0
        )
        total_cost += (
            (tx_gas * (block_base_fee_per_gas + block_producer_fee)) + tx_value + blob_cost
        )
    return total_cost


@pytest.fixture
def tx_access_list() -> List[AccessList]:
    """
    Access list for transactions sent during test.

    Can be overloaded by a test case to provide a custom access list.
    """
    return []


@pytest.fixture
def tx_error() -> Optional[TransactionException]:
    """
    Error produced by the block transactions (no error).

    Can be overloaded on test cases where the transactions are expected
    to fail.
    """
    return None


@pytest.fixture
def sender_initial_balance(  # noqa: D103
    total_account_minimum_balance: int, account_balance_modifier: int
) -> int:
    return total_account_minimum_balance + account_balance_modifier


@pytest.fixture
def sender(pre: Alloc, sender_initial_balance: int) -> Address:  # noqa: D103
    return pre.fund_eoa(sender_initial_balance)


@pytest.fixture
def txs(  # noqa: D103
    sender: EOA,
    destination_account: Optional[Address],
    tx_gas: int,
    tx_value: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_access_list: List[AccessList],
    blob_hashes_per_tx: List[List[bytes]],
    tx_error: Optional[TransactionException],
) -> List[Transaction]:
    """Prepare the list of transactions that are sent during the test."""
    return [
        Transaction(
            ty=Spec.BLOB_TX_TYPE,
            sender=sender,
            to=destination_account,
            value=tx_value,
            gas_limit=tx_gas,
            data=tx_calldata,
            max_fee_per_gas=tx_max_fee_per_gas,
            max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
            max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
            access_list=tx_access_list,
            blob_versioned_hashes=blob_hashes,
            error=tx_error if tx_i == (len(blob_hashes_per_tx) - 1) else None,
        )
        for tx_i, blob_hashes in enumerate(blob_hashes_per_tx)
    ]


@pytest.fixture
def account_balance_modifier() -> int:
    """
    Account balance modifier for the source account of all tests.
    See `pre` fixture.
    """
    return 0


@pytest.fixture
def state_env(
    excess_blob_gas: Optional[int],
) -> Environment:
    """
    Prepare the environment for all state test cases.

    Main difference is that the excess blob gas is not increased by the target, as
    there is no genesis block -> block 1 transition, and therefore the excess blob gas
    is not decreased by the target.
    """
    return Environment(
        excess_blob_gas=excess_blob_gas if excess_blob_gas else 0,
    )


@pytest.fixture
def engine_api_error_code() -> Optional[EngineAPIError]:
    """
    Engine API error code to be returned by the client on consumption
    of the erroneous block in hive.
    """
    return None


@pytest.fixture
def block_error(
    tx_error: Optional[TransactionException],
) -> Optional[TransactionException | BlockException]:
    """
    Error produced by the block transactions (no error).

    Can be overloaded on test cases where the transactions are expected
    to fail.
    """
    return tx_error


@pytest.fixture
def block_number() -> int:
    """First block number."""
    return 1


@pytest.fixture
def block_timestamp() -> int:
    """Timestamp of the first block."""
    return 1


@pytest.fixture
def expected_blob_gas_used(
    fork: Fork,
    txs: List[Transaction],
    block_number: int,
    block_timestamp: int,
) -> Optional[int | Removable]:
    """Calculate blob gas used by the test block."""
    if not fork.header_blob_gas_used_required(
        block_number=block_number, timestamp=block_timestamp
    ):
        return Header.EMPTY_FIELD
    blob_gas_per_blob = fork.blob_gas_per_blob(
        block_number=block_number,
        timestamp=block_timestamp,
    )
    return sum([Spec.get_total_blob_gas(tx=tx, blob_gas_per_blob=blob_gas_per_blob) for tx in txs])


@pytest.fixture
def expected_excess_blob_gas(
    fork: Fork,
    parent_excess_blobs: Optional[int],
    parent_blobs: Optional[int],
    block_number: int,
    block_timestamp: int,
) -> Optional[int | Removable]:
    """Calculate blob gas used by the test block."""
    if not fork.header_excess_blob_gas_required(
        block_number=block_number, timestamp=block_timestamp
    ):
        return Header.EMPTY_FIELD
    excess_blob_gas = fork.excess_blob_gas_calculator()
    return excess_blob_gas(
        parent_excess_blobs=parent_excess_blobs if parent_excess_blobs else 0,
        parent_blob_count=parent_blobs if parent_blobs else 0,
    )


@pytest.fixture
def header_verify(
    txs: List[Transaction],
    expected_blob_gas_used: Optional[int | Removable],
    expected_excess_blob_gas: Optional[int | Removable],
) -> Header:
    """Header fields to verify from the transition tool."""
    header_verify = Header(
        blob_gas_used=expected_blob_gas_used,
        excess_blob_gas=expected_excess_blob_gas,
        gas_used=0 if len([tx for tx in txs if not tx.error]) == 0 else None,
    )
    return header_verify


@pytest.fixture
def rlp_modifier(
    expected_blob_gas_used: Optional[int | Removable],
) -> Optional[Header]:
    """Header fields to modify on the output block in the BlockchainTest."""
    if expected_blob_gas_used == Header.EMPTY_FIELD:
        return None
    return Header(
        blob_gas_used=expected_blob_gas_used,
    )


@pytest.fixture
def block(
    txs: List[Transaction],
    block_error: Optional[TransactionException | BlockException],
    engine_api_error_code: Optional[EngineAPIError],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
) -> Block:
    """Test block for all blockchain test cases."""
    return Block(
        txs=txs,
        exception=block_error,
        engine_api_error_code=engine_api_error_code,
        header_verify=header_verify,
        rlp_modifier=rlp_modifier,
    )


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx",
    SpecHelpers.all_valid_blob_combinations,
)
@pytest.mark.valid_from("Cancun")
def test_valid_blob_tx_combinations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    block: Block,
):
    """
    Test all valid blob combinations in a single block, assuming a given value of
    `MAX_BLOBS_PER_BLOCK`.

    This assumes a block can include from 1 and up to `MAX_BLOBS_PER_BLOCK` transactions where all
    transactions contain at least 1 blob, and the sum of all blobs in a block is at
    most `MAX_BLOBS_PER_BLOCK`.

    This test is parametrized with all valid blob transaction combinations for a given block, and
    therefore if value of `MAX_BLOBS_PER_BLOCK` changes, this test is automatically updated.
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=[block],
        genesis_environment=env,
    )


def generate_invalid_tx_max_fee_per_blob_gas_tests(
    fork: Fork,
) -> List:
    """
    Return a list of tests for invalid blob transactions due to insufficient max fee per blob gas
    parametrized for each different fork.
    """
    min_base_fee_per_blob_gas = fork.min_base_fee_per_blob_gas()
    minimum_excess_blobs_for_first_increment = SpecHelpers.get_min_excess_blobs_for_blob_gas_price(
        fork=fork,
        blob_gas_price=min_base_fee_per_blob_gas + 1,
    )
    next_base_fee_per_blob_gas = fork.blob_gas_price_calculator()(
        excess_blob_gas=minimum_excess_blobs_for_first_increment,
    )

    tests = []
    tests.append(
        pytest.param(
            minimum_excess_blobs_for_first_increment - 1,  # blob gas price is 1
            fork.target_blobs_per_block() + 1,  # blob gas cost increases to above the minimum
            min_base_fee_per_blob_gas,  # tx max_blob_gas_cost is the minimum
            TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
            id="insufficient_max_fee_per_blob_gas",
        )
    )
    if (next_base_fee_per_blob_gas - min_base_fee_per_blob_gas) > 1:
        tests.append(
            pytest.param(
                minimum_excess_blobs_for_first_increment
                - 1,  # blob gas price is one less than the minimum
                fork.target_blobs_per_block() + 1,  # blob gas cost increases to above the minimum
                next_base_fee_per_blob_gas
                - 1,  # tx max_blob_gas_cost is one less than the minimum
                TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
                id="insufficient_max_fee_per_blob_gas_one_less_than_next",
            )
        )
    if min_base_fee_per_blob_gas > 1:
        tests.append(
            pytest.param(
                0,  # blob gas price is the minimum
                0,  # blob gas cost stays put at 1
                min_base_fee_per_blob_gas - 1,  # tx max_blob_gas_cost is one less than the minimum
                TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
                id="insufficient_max_fee_per_blob_gas_one_less_than_min",
            )
        )

    tests.append(
        pytest.param(
            0,  # blob gas price is the minimum
            0,  # blob gas cost stays put at 1
            0,  # tx max_blob_gas_cost is 0
            TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
            id="invalid_max_fee_per_blob_gas",
        )
    )
    return tests


@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs,parent_blobs,tx_max_fee_per_blob_gas,tx_error",
    generate_invalid_tx_max_fee_per_blob_gas_tests,
)
@pytest.mark.parametrize(
    "account_balance_modifier",
    [1_000_000_000],
)  # Extra balance to cover block blob gas cost
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_max_fee_per_blob_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    block: Block,
    non_zero_blob_gas_used_genesis_block: Optional[Block],
):
    """
    Reject blocks with invalid blob txs.

    - tx max_fee_per_blob_gas is barely not enough
    - tx max_fee_per_blob_gas is zero
    """
    if non_zero_blob_gas_used_genesis_block is not None:
        blocks = [non_zero_blob_gas_used_genesis_block, block]
    else:
        blocks = [block]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs,parent_blobs,tx_max_fee_per_blob_gas,tx_error",
    generate_invalid_tx_max_fee_per_blob_gas_tests,
)
@pytest.mark.state_test_only
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_max_fee_per_blob_gas_state(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    txs: List[Transaction],
):
    """
    Reject an invalid blob transaction.

    - tx max_fee_per_blob_gas is barely not enough
    - tx max_fee_per_blob_gas is zero
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize(
    "tx_max_fee_per_gas,tx_error",
    [
        # max blob gas is ok, but max fee per gas is less than base fee per gas
        (
            6,
            TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
        ),
    ],
    ids=["insufficient_max_fee_per_gas"],
)
@pytest.mark.valid_from("Cancun")
def test_invalid_normal_gas(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    txs: List[Transaction],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
):
    """
    Reject an invalid blob transaction.

    - Sufficient max fee per blob gas, but insufficient max fee per gas
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=state_env,
        blockchain_test_header_verify=header_verify,
        blockchain_test_rlp_modifier=rlp_modifier,
    )


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx",
    SpecHelpers.invalid_blob_combinations,
)
@pytest.mark.parametrize(
    "tx_error", [TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED], ids=[""]
)
@pytest.mark.valid_from("Cancun")
def test_invalid_block_blob_count(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    block: Block,
):
    """
    Test all invalid blob combinations in a single block, where the sum of all blobs in a block is
    at `MAX_BLOBS_PER_BLOCK + 1`.

    This test is parametrized with all blob transaction combinations exceeding
    `MAX_BLOBS_PER_BLOCK` by one for a given block, and
    therefore if value of `MAX_BLOBS_PER_BLOCK` changes, this test is automatically updated.
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=[block],
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "tx_access_list",
    [[], [AccessList(address=100, storage_keys=[100, 200])]],
    ids=["no_access_list", "access_list"],
)
@pytest.mark.parametrize("tx_max_fee_per_gas", [7, 14])
@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 7])
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.parametrize(
    "tx_calldata",
    [b"", b"\x00", b"\x01"],
    ids=["no_calldata", "single_zero_calldata", "single_one_calldata"],
)
@pytest.mark.parametrize("tx_max_fee_per_blob_gas_multiplier", [1, 100, 10000])
@pytest.mark.parametrize("account_balance_modifier", [-1], ids=["exact_balance_minus_1"])
@pytest.mark.parametrize("tx_error", [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_insufficient_balance_blob_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    txs: List[Transaction],
):
    """
    Reject blocks where user cannot afford the blob gas specified (but
    max_fee_per_gas would be enough for current block).

    - Transactions with max fee equal or higher than current block base fee
    - Transactions with and without priority fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per blob gas lower or higher than the priority fee
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx",
    lambda fork: [
        pytest.param([1], id="single_blob"),
        pytest.param([fork.max_blobs_per_block()], id="max_blobs"),
    ],
)
@pytest.mark.parametrize(
    "tx_access_list",
    [[], [AccessList(address=100, storage_keys=[100, 200])]],
    ids=["no_access_list", "access_list"],
)
@pytest.mark.parametrize("tx_max_fee_per_gas", [7, 14])
@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 7])
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.parametrize(
    "tx_calldata",
    [b"", b"\x00", b"\x01"],
    ids=["no_calldata", "single_zero_calldata", "single_one_calldata"],
)
@pytest.mark.parametrize("tx_max_fee_per_blob_gas_multiplier", [1, 100, 10000])
@pytest.mark.valid_from("Cancun")
def test_sufficient_balance_blob_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    txs: List[Transaction],
):
    """
    Check that transaction is accepted when user can exactly afford the blob gas specified (and
    max_fee_per_gas would be enough for current block).

    - Transactions with max fee equal or higher than current block base fee
    - Transactions with and without priority fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per blob gas lower or higher than the priority fee
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx",
    lambda fork: [
        pytest.param([1], id="single_blob"),
        pytest.param([fork.max_blobs_per_block()], id="max_blobs"),
    ],
)
@pytest.mark.parametrize(
    "tx_access_list",
    [[], [AccessList(address=100, storage_keys=[100, 200])]],
    ids=["no_access_list", "access_list"],
)
@pytest.mark.parametrize("tx_max_fee_per_gas", [7, 14])
@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 7])
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.parametrize(
    "tx_calldata",
    [b"", b"\x00", b"\x01"],
    ids=["no_calldata", "single_zero_calldata", "single_one_calldata"],
)
@pytest.mark.parametrize("tx_max_fee_per_blob_gas_multiplier", [1, 100, 10000])
@pytest.mark.parametrize("sender_initial_balance", [0])
@pytest.mark.valid_from("Cancun")
def test_sufficient_balance_blob_tx_pre_fund_tx(
    blockchain_test: BlockchainTestFiller,
    total_account_minimum_balance: int,
    sender: EOA,
    env: Environment,
    pre: Alloc,
    txs: List[Transaction],
    header_verify: Optional[Header],
):
    """
    Check that transaction is accepted when user can exactly afford the blob gas specified (and
    max_fee_per_gas would be enough for current block) because a funding transaction is
    prepended in the same block.

    - Transactions with max fee equal or higher than current block base fee
    - Transactions with and without priority fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per blob gas lower or higher than the priority fee
    """
    pre_funding_sender = pre.fund_eoa(amount=(21_000 * 100) + total_account_minimum_balance)
    txs = [
        Transaction(
            sender=pre_funding_sender,
            to=sender,
            value=total_account_minimum_balance,
            gas_limit=21_000,
        )
    ] + txs
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=txs,
                header_verify=header_verify,
            )
        ],
        genesis_environment=env,
    )


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx",
    lambda fork: [
        pytest.param([1], id="single_blob"),
        pytest.param([fork.max_blobs_per_block()], id="max_blobs"),
    ],
)
@pytest.mark.parametrize(
    "tx_access_list",
    [[], [AccessList(address=100, storage_keys=[100, 200])]],
    ids=["no_access_list", "access_list"],
)
@pytest.mark.parametrize("tx_max_fee_per_gas", [7, 14])
@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 7])
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.parametrize(
    "tx_calldata",
    [b"", b"\x01"],
    ids=["no_calldata", "single_non_zero_byte_calldata"],
)
@pytest.mark.parametrize("tx_max_fee_per_blob_gas_multiplier", [1, 100])
@pytest.mark.parametrize(
    "tx_gas", [500_000], ids=[""]
)  # Increase gas to account for contract code
@pytest.mark.parametrize(
    "destination_account_balance", [100], ids=["100_wei_mid_execution"]
)  # Amount sent by the contract to the sender mid execution
@pytest.mark.parametrize(
    "destination_account_code",
    [
        Op.SSTORE(0, Op.BALANCE(Op.ORIGIN))
        + Op.CALL(Op.GAS, Op.ORIGIN, Op.SUB(Op.SELFBALANCE, Op.CALLVALUE), 0, 0, 0, 0)
        + Op.SSTORE(1, Op.BALANCE(Op.ORIGIN))
    ],
    ids=[""],
)  # Amount sent by the contract to the sender mid execution
@pytest.mark.valid_from("Cancun")
def test_blob_gas_subtraction_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    sender_initial_balance: int,
    txs: List[Transaction],
    destination_account: Address,
    destination_account_balance: int,
    total_account_transactions_fee: int,
):
    """
    Check that the blob gas fee for a transaction is subtracted from the sender balance before the
    transaction is executed.

    - Transactions with max fee equal or higher than current block base fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per blob gas lower or higher than the priority fee
    - Transactions where an externally owned account sends funds to the sender mid execution
    """
    assert len(txs) == 1
    post = {
        destination_account: Account(
            storage={
                0: sender_initial_balance - total_account_transactions_fee,
                1: sender_initial_balance
                - total_account_transactions_fee
                + destination_account_balance,
            }
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx",
    SpecHelpers.all_valid_blob_combinations,
)
@pytest.mark.parametrize("account_balance_modifier", [-1], ids=["exact_balance_minus_1"])
@pytest.mark.parametrize("tx_error", [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_insufficient_balance_blob_tx_combinations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    block: Block,
):
    """
    Reject all valid blob transaction combinations in a block, but block is invalid.

    - The amount of blobs is correct but the user cannot afford the
            transaction total cost
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=[block],
        genesis_environment=env,
    )


def generate_invalid_tx_blob_count_tests(
    fork: Fork,
) -> List:
    """Return a list of tests for invalid blob transactions due to invalid blob counts."""
    return [
        pytest.param(
            [0],
            TransactionException.TYPE_3_TX_ZERO_BLOBS,
            id="too_few_blobs",
        ),
        pytest.param(
            [fork.max_blobs_per_block() + 1],
            TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
            id="too_many_blobs",
        ),
    ]


@pytest.mark.parametrize_by_fork(
    "blobs_per_tx,tx_error",
    generate_invalid_tx_blob_count_tests,
)
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_blob_count(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    txs: List[Transaction],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
):
    """
    Reject blocks that include blob transactions with invalid blob counts.

    - `blob count == 0` in type 3 transaction
    - `blob count > MAX_BLOBS_PER_BLOCK` in type 3 transaction
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=state_env,
        blockchain_test_header_verify=header_verify,
        blockchain_test_rlp_modifier=rlp_modifier,
    )


@pytest.mark.parametrize(
    "blob_hashes_per_tx",
    [
        [[Hash(1)]],
        [[Hash(x) for x in range(2)]],
        [add_kzg_version([Hash(1)], Spec.BLOB_COMMITMENT_VERSION_KZG) + [Hash(2)]],
        [[Hash(1)] + add_kzg_version([Hash(2)], Spec.BLOB_COMMITMENT_VERSION_KZG)],
    ],
    ids=[
        "single_blob",
        "multiple_blobs",
        "multiple_blobs_single_bad_hash_1",
        "multiple_blobs_single_bad_hash_2",
    ],
)
@pytest.mark.parametrize(
    "tx_error", [TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH], ids=[""]
)
@pytest.mark.valid_from("Cancun")
def test_invalid_blob_hash_versioning_single_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Alloc,
    txs: List[Transaction],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
):
    """
    Reject blob transactions with invalid blob hash version.

    - Transaction with single blob with invalid version
    - Transaction with multiple blobs all with invalid version
    - Transaction with multiple blobs either with invalid version
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=state_env,
        blockchain_test_header_verify=header_verify,
        blockchain_test_rlp_modifier=rlp_modifier,
    )


@pytest.mark.parametrize(
    "blob_hashes_per_tx",
    [
        [
            add_kzg_version([Hash(1)], Spec.BLOB_COMMITMENT_VERSION_KZG),
            [Hash(2)],
        ],
        [
            add_kzg_version([Hash(1)], Spec.BLOB_COMMITMENT_VERSION_KZG),
            [Hash(x) for x in range(1, 3)],
        ],
        [
            add_kzg_version([Hash(1)], Spec.BLOB_COMMITMENT_VERSION_KZG),
            [Hash(2)] + add_kzg_version([Hash(3)], Spec.BLOB_COMMITMENT_VERSION_KZG),
        ],
        [
            add_kzg_version([Hash(1)], Spec.BLOB_COMMITMENT_VERSION_KZG),
            add_kzg_version([Hash(2)], Spec.BLOB_COMMITMENT_VERSION_KZG),
            [Hash(3)],
        ],
    ],
    ids=[
        "single_blob",
        "multiple_blobs",
        "multiple_blobs_single_bad_hash_1",
        "multiple_blobs_single_bad_hash_2",
    ],
)
@pytest.mark.parametrize(
    "tx_error", [TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH], ids=[""]
)
@pytest.mark.valid_from("Cancun")
def test_invalid_blob_hash_versioning_multiple_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    block: Block,
):
    """
    Reject blocks that include blob transactions with invalid blob hash
    version.

    - Multiple blob transactions with single blob all with invalid version
    - Multiple blob transactions with multiple blobs all with invalid version
    - Multiple blob transactions with multiple blobs only one with invalid version
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=[block],
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "tx_gas", [500_000], ids=[""]
)  # Increase gas to account for contract creation
@pytest.mark.valid_from("Cancun")
def test_invalid_blob_tx_contract_creation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    txs: List[Transaction],
    header_verify: Optional[Header],
):
    """Reject blocks that include blob transactions that have nil to value (contract creating)."""
    assert len(txs) == 1
    assert txs[0].blob_versioned_hashes is not None and len(txs[0].blob_versioned_hashes) == 1
    # Replace the transaction with a contract creating one, only in the RLP version
    contract_creating_tx = txs[0].copy(to=None).with_signature_and_sender()
    txs[0].rlp_override = contract_creating_tx.rlp()
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=txs,
                exception=[
                    BlockException.RLP_STRUCTURES_ENCODING,
                    TransactionException.TYPE_3_TX_CONTRACT_CREATION,
                ],
                header_verify=header_verify,
            )
        ],
        genesis_environment=env,
    )


# # ----------------------------------------
# # Opcode Tests in Blob Transaction Context
# # ----------------------------------------


@pytest.fixture
def opcode(
    request,
    sender: EOA,
    tx_calldata: bytes,
    block_base_fee_per_gas: int,
    tx_max_fee_per_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_value: int,
) -> Tuple[Bytecode, Storage.StorageDictType]:
    """Build bytecode and post to test each opcode that accesses transaction information."""
    if request.param == Op.ORIGIN:
        return (
            Op.SSTORE(0, Op.ORIGIN),
            {0: sender},
        )
    elif request.param == Op.CALLER:
        return (
            Op.SSTORE(0, Op.CALLER),
            {0: sender},
        )
    elif request.param == Op.CALLVALUE:
        return (
            Op.SSTORE(0, Op.CALLVALUE),
            {0: tx_value},
        )
    elif request.param == Op.CALLDATALOAD:
        return (
            Op.SSTORE(0, Op.CALLDATALOAD(0)),
            {0: tx_calldata.ljust(32, b"\x00")},
        )
    elif request.param == Op.CALLDATASIZE:
        return (
            Op.SSTORE(0, Op.CALLDATASIZE),
            {0: len(tx_calldata)},
        )
    elif request.param == Op.CALLDATACOPY:
        return (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(0, Op.MLOAD(0)),
            {0: tx_calldata.ljust(32, b"\x00")},
        )
    elif request.param == Op.GASPRICE:
        assert tx_max_fee_per_gas >= block_base_fee_per_gas
        return (
            Op.SSTORE(0, Op.GASPRICE),
            {
                0: min(tx_max_priority_fee_per_gas, tx_max_fee_per_gas - block_base_fee_per_gas)
                + block_base_fee_per_gas
            },
        )
    raise Exception("Unknown opcode")


@pytest.mark.parametrize(
    "opcode",
    [Op.ORIGIN, Op.CALLER],
    indirect=["opcode"],
)
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    tx_gas: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_access_list: List[AccessList],
    blob_hashes_per_tx: List[List[bytes]],
    opcode: Tuple[Bytecode, Storage.StorageDictType],
    state_env: Environment,
):
    """
    Test opcodes that read transaction attributes work properly for blob type transactions.

    - ORIGIN
    - CALLER
    """
    code, storage = opcode
    destination_account = pre.deploy_contract(code=code)
    tx = Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=sender,
        to=destination_account,
        value=tx_value,
        gas_limit=tx_gas,
        data=tx_calldata,
        max_fee_per_gas=tx_max_fee_per_gas,
        max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
        max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
        access_list=tx_access_list,
        blob_versioned_hashes=blob_hashes_per_tx[0],
    )
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        env=state_env,
    )


@pytest.mark.parametrize("opcode", [Op.CALLVALUE], indirect=["opcode"])
@pytest.mark.parametrize("tx_value", [0, 1, int(1e18)])
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_value_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    tx_gas: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_access_list: List[AccessList],
    blob_hashes_per_tx: List[List[bytes]],
    opcode: Tuple[Bytecode, Storage.StorageDictType],
    state_env: Environment,
):
    """Test the VALUE opcode with different blob type transaction value amounts."""
    code, storage = opcode
    destination_account = pre.deploy_contract(code=code)
    tx = Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=sender,
        to=destination_account,
        value=tx_value,
        gas_limit=tx_gas,
        data=tx_calldata,
        max_fee_per_gas=tx_max_fee_per_gas,
        max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
        max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
        access_list=tx_access_list,
        blob_versioned_hashes=blob_hashes_per_tx[0],
    )
    post = {
        destination_account: Account(
            storage=storage,
            balance=tx_value,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        env=state_env,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALLDATALOAD,
        Op.CALLDATASIZE,
        Op.CALLDATACOPY,
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "tx_calldata",
    [
        b"",
        b"\x01",
        b"\x00\x01" * 16,
    ],
    ids=["empty", "single_byte", "word"],
)
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_calldata_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    tx_gas: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_access_list: List[AccessList],
    blob_hashes_per_tx: List[List[bytes]],
    opcode: Tuple[Bytecode, Storage.StorageDictType],
    state_env: Environment,
):
    """
    Test calldata related opcodes to verify their behavior is not affected by blobs.

    - CALLDATALOAD
    - CALLDATASIZE
    - CALLDATACOPY
    """
    code, storage = opcode
    destination_account = pre.deploy_contract(code=code)
    tx = Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=sender,
        to=destination_account,
        value=tx_value,
        gas_limit=tx_gas,
        data=tx_calldata,
        max_fee_per_gas=tx_max_fee_per_gas,
        max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
        max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
        access_list=tx_access_list,
        blob_versioned_hashes=blob_hashes_per_tx[0],
    )
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        env=state_env,
    )


@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 2])  # always below data fee
@pytest.mark.parametrize("tx_max_fee_per_blob_gas_delta", [0, 1])  # normal and above priority fee
@pytest.mark.parametrize("tx_max_fee_per_gas", [100])  # always above priority fee (FOR CANCUN)
@pytest.mark.parametrize("opcode", [Op.GASPRICE], indirect=True)
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_gasprice_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    tx_gas: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_access_list: List[AccessList],
    blob_hashes_per_tx: List[List[bytes]],
    opcode: Tuple[Bytecode, Storage.StorageDictType],
    state_env: Environment,
):
    """
    Test GASPRICE opcode to sanity check that the blob gas fee does not affect its calculation.

    - No priority fee
    - Priority fee below data fee
    - Priority fee above data fee
    """
    code, storage = opcode
    destination_account = pre.deploy_contract(code=code)
    tx = Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=sender,
        to=destination_account,
        value=tx_value,
        gas_limit=tx_gas,
        data=tx_calldata,
        max_fee_per_gas=tx_max_fee_per_gas,
        max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
        max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
        access_list=tx_access_list,
        blob_versioned_hashes=blob_hashes_per_tx[0],
    )
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        env=state_env,
    )


@pytest.mark.parametrize(
    [
        "blobs_per_tx",
        "parent_excess_blobs",
        "tx_max_fee_per_blob_gas",
        "tx_error",
    ],
    [
        (
            [0],
            None,
            1,
            [TransactionException.TYPE_3_TX_PRE_FORK, TransactionException.TYPE_3_TX_ZERO_BLOBS],
        ),
        ([1], None, 1, TransactionException.TYPE_3_TX_PRE_FORK),
    ],
    ids=["no_blob_tx", "one_blob_tx"],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_blob_type_tx_pre_fork(
    state_test: StateTestFiller,
    pre: Alloc,
    txs: List[Transaction],
):
    """
    Reject blocks with blob type transactions before Cancun fork.

    Blocks sent by NewPayloadV2 (Shanghai) that contain blob type transactions, furthermore blobs
    field within NewPayloadV2 method must be computed as INVALID, due to an invalid block hash.
    """
    assert len(txs) == 1
    state_test(
        pre=pre,
        post={},
        tx=txs[0],
        env=Environment(),  # `env` fixture has blob fields
    )
