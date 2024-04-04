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

import itertools
from typing import Dict, List, Optional, Tuple

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    AccessList,
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    BlockException,
    EngineAPIError,
    Environment,
    Hash,
    Header,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    Removable,
    StateTestFiller,
    Storage,
    TestAddress,
    TestAddress2,
    Transaction,
    TransactionException,
    add_kzg_version,
    eip_2028_transaction_data_cost,
)

from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

TestPreFundingKey = "0x0b2986cc45bd8a8d028c3fcf6f7a11a52f1df61f3ea5d63f05ca109dd73a3fa0"
TestPreFundingAddress = "0x97a7cb1de3cc7d556d0aa32433b035067709e1fc"


@pytest.fixture
def destination_account() -> Address:
    """Default destination account for the blob transactions."""
    return Address(0x100)


@pytest.fixture
def tx_value() -> int:
    """
    Default value contained by the transactions sent during test.

    Can be overloaded by a test case to provide a custom transaction value.
    """
    return 1


@pytest.fixture
def tx_gas(
    tx_calldata: bytes,
    tx_access_list: List[AccessList],
) -> int:
    """Default gas allocated to transactions sent during test."""
    access_list_gas = 0
    if tx_access_list:
        ACCESS_LIST_ADDRESS_COST = 2400
        ACCESS_LIST_STORAGE_KEY_COST = 1900

        for address in tx_access_list:
            access_list_gas += ACCESS_LIST_ADDRESS_COST
            access_list_gas += len(address.storage_keys) * ACCESS_LIST_STORAGE_KEY_COST

    return 21000 + eip_2028_transaction_data_cost(tx_calldata) + access_list_gas


@pytest.fixture
def tx_calldata() -> bytes:
    """Default calldata in transactions sent during test."""
    return b""


@pytest.fixture
def block_fee_per_gas() -> int:
    """Default max fee per gas for transactions sent during test."""
    return 7


@pytest.fixture(autouse=True)
def parent_excess_blobs() -> Optional[int]:
    """
    Default excess blobs of the parent block.

    Can be overloaded by a test case to provide a custom parent excess blob
    count.
    """
    return 10  # Defaults to a blob gas price of 1.


@pytest.fixture(autouse=True)
def parent_blobs() -> Optional[int]:
    """
    Default data blobs of the parent blob.

    Can be overloaded by a test case to provide a custom parent blob count.
    """
    return 0


@pytest.fixture
def parent_excess_blob_gas(
    parent_excess_blobs: Optional[int],
) -> Optional[int]:
    """
    Calculates the excess blob gas of the parent block from the excess blobs.
    """
    if parent_excess_blobs is None:
        return None
    return parent_excess_blobs * Spec.GAS_PER_BLOB


@pytest.fixture
def blob_gasprice(
    parent_excess_blob_gas: Optional[int],
    parent_blobs: Optional[int],
) -> Optional[int]:
    """
    Blob gas price for the block of the test.
    """
    if parent_excess_blob_gas is None or parent_blobs is None:
        return None

    return Spec.get_blob_gasprice(
        excess_blob_gas=SpecHelpers.calc_excess_blob_gas_from_blob_count(
            parent_excess_blob_gas=parent_excess_blob_gas,
            parent_blob_count=parent_blobs,
        ),
    )


@pytest.fixture
def tx_max_priority_fee_per_gas() -> int:
    """
    Default max priority fee per gas for transactions sent during test.

    Can be overloaded by a test case to provide a custom max priority fee per
    gas.
    """
    return 0


@pytest.fixture
def blobs_per_tx() -> List[int]:
    """
    Returns a list of integers that each represent the number of blobs in each
    transaction in the block of the test.

    Used to automatically generate a list of correctly versioned blob hashes.

    Default is to have one transaction with one blob.

    Can be overloaded by a test case to provide a custom list of blob counts.
    """
    return [1]


@pytest.fixture
def blob_hashes_per_tx(blobs_per_tx: List[int]) -> List[List[bytes]]:
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
    tx_gas: int,
    tx_value: int,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    blob_hashes_per_tx: List[List[bytes]],
) -> int:
    """
    Calculates the minimum balance required for the account to be able to send
    the transactions in the block of the test.
    """
    minimum_cost = 0
    for tx_blob_count in [len(x) for x in blob_hashes_per_tx]:
        blob_cost = tx_max_fee_per_blob_gas * Spec.GAS_PER_BLOB * tx_blob_count
        minimum_cost += (tx_gas * tx_max_fee_per_gas) + tx_value + blob_cost
    return minimum_cost


@pytest.fixture
def total_account_transactions_fee(  # noqa: D103
    tx_gas: int,
    tx_value: int,
    blob_gasprice: int,
    block_fee_per_gas: int,
    tx_max_fee_per_gas: int,
    tx_max_priority_fee_per_gas: int,
    blob_hashes_per_tx: List[List[bytes]],
) -> int:
    """
    Calculates the actual fee for the blob transactions in the block of the test.
    """
    total_cost = 0
    for tx_blob_count in [len(x) for x in blob_hashes_per_tx]:
        blob_cost = blob_gasprice * Spec.GAS_PER_BLOB * tx_blob_count
        block_producer_fee = (
            tx_max_fee_per_gas - block_fee_per_gas if tx_max_priority_fee_per_gas else 0
        )
        total_cost += (tx_gas * (block_fee_per_gas + block_producer_fee)) + tx_value + blob_cost
    return total_cost


@pytest.fixture(autouse=True)
def tx_max_fee_per_gas(
    block_fee_per_gas: int,
) -> int:
    """
    Max fee per gas value used by all transactions sent during test.

    By default the max fee per gas is the same as the block fee per gas.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per gas is insufficient.
    """
    return block_fee_per_gas


@pytest.fixture
def tx_max_fee_per_blob_gas(  # noqa: D103
    blob_gasprice: Optional[int],
) -> int:
    """
    Default max fee per blob gas for transactions sent during test.

    By default, it is set to the blob gas price of the block.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per blob gas is insufficient.
    """
    if blob_gasprice is None:
        # When fork transitioning, the default blob gas price is 1.
        return 1
    return blob_gasprice


@pytest.fixture
def tx_access_list() -> List[AccessList]:
    """
    Default access list for transactions sent during test.

    Can be overloaded by a test case to provide a custom access list.
    """
    return []


@pytest.fixture
def tx_error() -> Optional[TransactionException]:
    """
    Default expected error produced by the block transactions (no error).

    Can be overloaded on test cases where the transactions are expected
    to fail.
    """
    return None


@pytest.fixture(autouse=True)
def txs(  # noqa: D103
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
    """
    Prepare the list of transactions that are sent during the test.
    """
    return [
        Transaction(
            ty=Spec.BLOB_TX_TYPE,
            nonce=tx_i,
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
    Default modifier for the balance of the source account of all test.
    See `pre` fixture.
    """
    return 0


@pytest.fixture
def pre(  # noqa: D103
    total_account_minimum_balance: int,
    account_balance_modifier: int,
) -> Dict:
    """
    Prepares the pre state of all test cases, by setting the balance of the
    source account of all test transactions.

    The `account_balance_modifier` can be overloaded by a test case and alter
    the balance of the account from the minimum expected, to produce invalid
    blocks.
    """
    return {
        TestAddress: Account(balance=total_account_minimum_balance + account_balance_modifier),
    }


@pytest.fixture
def env(
    parent_excess_blob_gas: Optional[int],
    parent_blobs: int,
) -> Environment:
    """
    Prepare the environment of the genesis block for all blockchain tests.
    """
    excess_blob_gas = parent_excess_blob_gas if parent_excess_blob_gas else 0
    if parent_blobs:
        # We increase the excess blob gas of the genesis because
        # we cannot include blobs in the genesis, so the
        # test blobs are actually in block 1.
        excess_blob_gas += Spec.TARGET_BLOB_GAS_PER_BLOCK
    return Environment(
        excess_blob_gas=excess_blob_gas,
        blob_gas_used=0,
    )


@pytest.fixture
def state_env(
    parent_excess_blob_gas: Optional[int],
    parent_blobs: int,
) -> Environment:
    """
    Prepare the environment for all state test cases.

    Main difference is that the excess blob gas is not increased by the target, as
    there is no genesis block -> block 1 transition, and therefore the excess blob gas
    is not decreased by the target.
    """
    return Environment(
        excess_blob_gas=SpecHelpers.calc_excess_blob_gas_from_blob_count(
            parent_excess_blob_gas=parent_excess_blob_gas if parent_excess_blob_gas else 0,
            parent_blob_count=parent_blobs,
        ),
    )


@pytest.fixture
def engine_api_error_code() -> Optional[EngineAPIError]:
    """
    Expected Engine API error code to be returned by the client on consumption
    of the erroneous block in hive.
    """
    return None


@pytest.fixture
def block_error(
    tx_error: Optional[TransactionException],
) -> Optional[TransactionException | BlockException]:
    """
    Default expected error produced by the block transactions (no error).

    Can be overloaded on test cases where the transactions are expected
    to fail.
    """
    return tx_error


@pytest.fixture
def block_number() -> int:
    """
    Default number of the first block.
    """
    return 1


@pytest.fixture
def block_timestamp() -> int:
    """
    Default timestamp of the first block.
    """
    return 1


@pytest.fixture
def expected_blob_gas_used(
    fork: Fork,
    txs: List[Transaction],
    block_number: int,
    block_timestamp: int,
) -> Optional[int | Removable]:
    """
    Calculates the blob gas used by the test block.
    """
    if not fork.header_blob_gas_used_required(
        block_number=block_number, timestamp=block_timestamp
    ):
        return Header.EMPTY_FIELD
    return sum([Spec.get_total_blob_gas(tx) for tx in txs])


@pytest.fixture
def expected_excess_blob_gas(
    fork: Fork,
    parent_excess_blob_gas: Optional[int],
    parent_blobs: Optional[int],
    block_number: int,
    block_timestamp: int,
) -> Optional[int | Removable]:
    """
    Calculates the blob gas used by the test block.
    """
    if not fork.header_excess_blob_gas_required(
        block_number=block_number, timestamp=block_timestamp
    ):
        return Header.EMPTY_FIELD
    return SpecHelpers.calc_excess_blob_gas_from_blob_count(
        parent_excess_blob_gas=parent_excess_blob_gas if parent_excess_blob_gas else 0,
        parent_blob_count=parent_blobs if parent_blobs else 0,
    )


@pytest.fixture
def header_verify(
    txs: List[Transaction],
    expected_blob_gas_used: Optional[int | Removable],
    expected_excess_blob_gas: Optional[int | Removable],
) -> Header:
    """
    Header fields to verify from the transition tool.
    """
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
    """
    Header fields to modify on the output block in the BlockchainTest.
    """
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
    """
    Test block for all blockchain test cases.
    """
    return Block(
        txs=txs,
        exception=block_error,
        engine_api_error_code=engine_api_error_code,
        header_verify=header_verify,
        rlp_modifier=rlp_modifier,
    )


def all_valid_blob_combinations() -> List[Tuple[int, ...]]:
    """
    Returns all valid blob tx combinations for a given block,
    assuming the given MAX_BLOBS_PER_BLOCK
    """
    all = [
        seq
        for i in range(
            SpecHelpers.max_blobs_per_block(), 0, -1
        )  # We can have from 1 to at most MAX_BLOBS_PER_BLOCK blobs per block
        for seq in itertools.combinations_with_replacement(
            range(1, SpecHelpers.max_blobs_per_block() + 1), i
        )  # We iterate through all possible combinations
        if sum(seq)
        <= SpecHelpers.max_blobs_per_block()  # And we only keep the ones that are valid
    ]
    # We also add the reversed version of each combination, only if it's not
    # already in the list. E.g. (2, 1, 1) is added from (1, 1, 2) but not
    # (1, 1, 1) because its reversed version is identical.
    all += [tuple(reversed(x)) for x in all if tuple(reversed(x)) not in all]
    return all


def invalid_blob_combinations() -> List[Tuple[int, ...]]:
    """
    Returns invalid blob tx combinations for a given block that use up to
    MAX_BLOBS_PER_BLOCK+1 blobs
    """
    all = [
        seq
        for i in range(
            SpecHelpers.max_blobs_per_block() + 1, 0, -1
        )  # We can have from 1 to at most MAX_BLOBS_PER_BLOCK blobs per block
        for seq in itertools.combinations_with_replacement(
            range(1, SpecHelpers.max_blobs_per_block() + 2), i
        )  # We iterate through all possible combinations
        if sum(seq)
        == SpecHelpers.max_blobs_per_block() + 1  # And we only keep the ones that match the
        # expected invalid blob count
    ]
    # We also add the reversed version of each combination, only if it's not
    # already in the list. E.g. (4, 1) is added from (1, 4) but not
    # (1, 1, 1, 1, 1) because its reversed version is identical.
    all += [tuple(reversed(x)) for x in all if tuple(reversed(x)) not in all]
    return all


@pytest.mark.parametrize(
    "blobs_per_tx",
    all_valid_blob_combinations(),
)
@pytest.mark.valid_from("Cancun")
def test_valid_blob_tx_combinations(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
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


@pytest.mark.parametrize(
    "parent_excess_blobs,parent_blobs,tx_max_fee_per_blob_gas,tx_error",
    [
        # tx max_blob_gas_cost of the transaction is not enough
        pytest.param(
            SpecHelpers.get_min_excess_blobs_for_blob_gas_price(2) - 1,  # blob gas price is 1
            SpecHelpers.target_blobs_per_block() + 1,  # blob gas cost increases to 2
            1,  # tx max_blob_gas_cost is 1
            TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
            id="insufficient_max_fee_per_blob_gas",
        ),
        # tx max_blob_gas_cost of the transaction is zero, which is invalid
        pytest.param(
            0,  # blob gas price is 1
            0,  # blob gas cost stays put at 1
            0,  # tx max_blob_gas_cost is 0
            TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
            id="invalid_max_fee_per_blob_gas",
        ),
    ],
)
@pytest.mark.parametrize(
    "account_balance_modifier",
    [1_000_000_000],
)  # Extra balance to cover block blob gas cost
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_max_fee_per_blob_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    block: Block,
    non_zero_blob_gas_used_genesis_block: Optional[Block],
):
    """
    Reject blocks with invalid blob txs due to:

    - tx max_fee_per_blob_gas is barely not enough
    - tx max_fee_per_blob_gas is zero
    """
    blocks = [block]
    if non_zero_blob_gas_used_genesis_block is not None:
        pre[TestAddress2] = Account(balance=10**9)
        blocks = [non_zero_blob_gas_used_genesis_block, block]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "parent_excess_blobs,parent_blobs,tx_max_fee_per_blob_gas,tx_error",
    [
        # tx max_blob_gas_cost of the transaction is not enough
        pytest.param(
            SpecHelpers.get_min_excess_blobs_for_blob_gas_price(2) - 1,  # blob gas price is 1
            SpecHelpers.target_blobs_per_block() + 1,  # blob gas cost increases to 2
            1,  # tx max_blob_gas_cost is 1
            TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
            id="insufficient_max_fee_per_blob_gas",
        ),
        # tx max_blob_gas_cost of the transaction is zero, which is invalid
        pytest.param(
            0,  # blob gas price is 1
            0,  # blob gas cost stays put at 1
            0,  # tx max_blob_gas_cost is 0
            TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
            id="invalid_max_fee_per_blob_gas",
        ),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_max_fee_per_blob_gas_state(
    state_test_only: StateTestFiller,
    state_env: Environment,
    pre: Dict,
    txs: List[Transaction],
):
    """
    Reject an invalid blob transaction due to:

    - tx max_fee_per_blob_gas is barely not enough
    - tx max_fee_per_blob_gas is zero
    """
    assert len(txs) == 1
    state_test_only(
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
    pre: Dict,
    txs: List[Transaction],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
):
    """
    Reject an invalid blob transaction due to:

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


@pytest.mark.parametrize(
    "blobs_per_tx",
    invalid_blob_combinations(),
)
@pytest.mark.parametrize(
    "tx_error", [TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED], ids=[""]
)
@pytest.mark.valid_from("Cancun")
def test_invalid_block_blob_count(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
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
@pytest.mark.parametrize("tx_max_fee_per_blob_gas", [1, 100, 10000])
@pytest.mark.parametrize("account_balance_modifier", [-1], ids=["exact_balance_minus_1"])
@pytest.mark.parametrize("tx_error", [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_insufficient_balance_blob_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Dict,
    txs: List[Transaction],
):
    """
    Reject blocks where user cannot afford the blob gas specified (but
    max_fee_per_gas would be enough for current block), including:

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
@pytest.mark.parametrize("tx_max_fee_per_blob_gas", [1, 100, 10000])
@pytest.mark.valid_from("Cancun")
def test_sufficient_balance_blob_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Dict,
    txs: List[Transaction],
):
    """
    Check that transaction is accepted when user can exactly afford the blob gas specified (and
    max_fee_per_gas would be enough for current block), including:

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
@pytest.mark.parametrize("tx_max_fee_per_blob_gas", [1, 100, 10000])
@pytest.mark.valid_from("Cancun")
def test_sufficient_balance_blob_tx_pre_fund_tx(
    blockchain_test: BlockchainTestFiller,
    total_account_minimum_balance: int,
    env: Environment,
    pre: Dict,
    txs: List[Transaction],
    header_verify: Optional[Header],
):
    """
    Check that transaction is accepted when user can exactly afford the blob gas specified (and
    max_fee_per_gas would be enough for current block) because a funding transaction is
    prepended in the same block, including:

    - Transactions with max fee equal or higher than current block base fee
    - Transactions with and without priority fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per blob gas lower or higher than the priority fee
    """
    pre = {
        TestPreFundingAddress: Account(balance=(21_000 * 100) + total_account_minimum_balance),
    }
    txs = [
        Transaction(
            ty=2,
            nonce=0,
            to=TestAddress,
            value=total_account_minimum_balance,
            gas_limit=21_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=0,
            access_list=[],
            secret_key=TestPreFundingKey,
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
@pytest.mark.parametrize("tx_max_fee_per_blob_gas", [1, 100])
@pytest.mark.parametrize(
    "tx_gas", [500_000], ids=[""]
)  # Increase gas to account for contract code
@pytest.mark.parametrize(
    "mid_tx_send_amount", [100]
)  # Amount sent by the contract to the sender mid execution
@pytest.mark.valid_from("Cancun")
def test_blob_gas_subtraction_tx(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Dict,
    txs: List[Transaction],
    destination_account: Address,
    mid_tx_send_amount: int,
    total_account_transactions_fee: int,
):
    """
    Check that the blob gas fee for a transaction is subtracted from the sender balance before the
    transaction is executed, including:

    - Transactions with max fee equal or higher than current block base fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per blob gas lower or higher than the priority fee
    - Transactions where an externally owned account sends funds to the sender mid execution
    """
    assert len(txs) == 1
    pre[destination_account] = Account(
        balance=mid_tx_send_amount,
        code=Op.SSTORE(0, Op.BALANCE(Op.ORIGIN))
        + Op.CALL(Op.GAS, Op.ORIGIN, mid_tx_send_amount, 0, 0, 0, 0)
        + Op.SSTORE(1, Op.BALANCE(Op.ORIGIN)),
    )
    post = {
        destination_account: Account(
            storage={
                0: pre[TestAddress].balance - total_account_transactions_fee,
                1: pre[TestAddress].balance - total_account_transactions_fee + mid_tx_send_amount,
            }
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize(
    "blobs_per_tx",
    all_valid_blob_combinations(),
)
@pytest.mark.parametrize("account_balance_modifier", [-1], ids=["exact_balance_minus_1"])
@pytest.mark.parametrize("tx_error", [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_insufficient_balance_blob_tx_combinations(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    block: Block,
):
    """
    Reject all valid blob transaction combinations in a block, but block is invalid due to:

    - The amount of blobs is correct but the user cannot afford the
            transaction total cost
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=[block],
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "blobs_per_tx,tx_error",
    [
        ([0], TransactionException.TYPE_3_TX_ZERO_BLOBS),
        (
            [SpecHelpers.max_blobs_per_block() + 1],
            TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
        ),
    ],
    ids=["too_few_blobs", "too_many_blobs"],
)
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_blob_count(
    state_test: StateTestFiller,
    state_env: Environment,
    pre: Dict,
    txs: List[Transaction],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
):
    """
    Reject blocks that include blob transactions with invalid blob counts:

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
    pre: Dict,
    txs: List[Transaction],
    header_verify: Optional[Header],
    rlp_modifier: Optional[Header],
):
    """
    Reject blob transactions with invalid blob hash version, including:

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
    pre: Dict,
    env: Environment,
    block: Block,
):
    """
    Reject blocks that include blob transactions with invalid blob hash
    version, including:

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
    pre: Dict,
    env: Environment,
    txs: List[Transaction],
    header_verify: Optional[Header],
):
    """
    Reject blocks that include blob transactions that have nil to value (contract creating).
    """
    assert len(txs) == 1
    assert txs[0].blob_versioned_hashes is not None and len(txs[0].blob_versioned_hashes) == 1
    # Replace the transaction with a contract creating one, only in the RLP version
    contract_creating_tx = txs[0].copy(to=None).with_signature_and_sender()
    txs[0].rlp_override = contract_creating_tx.rlp
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


# ----------------------------------------
# Opcode Tests in Blob Transaction Context
# ----------------------------------------


@pytest.fixture
def opcode(
    request,
    tx_calldata: bytes,
    block_fee_per_gas: int,
    tx_max_fee_per_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_value: int,
) -> Tuple[bytes, Storage.StorageDictType]:
    """
    Build bytecode and post to test each opcode that accesses transaction information.
    """
    if request.param == Op.ORIGIN:
        return (
            Op.SSTORE(0, Op.ORIGIN),
            {0: TestAddress},
        )
    elif request.param == Op.CALLER:
        return (
            Op.SSTORE(0, Op.CALLER),
            {0: TestAddress},
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
        assert tx_max_fee_per_gas >= block_fee_per_gas
        return (
            Op.SSTORE(0, Op.GASPRICE),
            {
                0: min(tx_max_priority_fee_per_gas, tx_max_fee_per_gas - block_fee_per_gas)
                + block_fee_per_gas
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
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    state_env: Environment,
    txs: List[Transaction],
    destination_account: Address,
):
    """
    Test opcodes that read transaction attributes work properly for blob type transactions:

    - ORIGIN
    - CALLER
    """
    assert len(txs) == 1
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize("opcode", [Op.CALLVALUE], indirect=["opcode"])
@pytest.mark.parametrize("tx_value", [0, 1, int(1e18)])
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_value_opcode(
    state_test: StateTestFiller,
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    state_env: Environment,
    txs: List[Transaction],
    tx_value: int,
    destination_account: Address,
):
    """
    Test the VALUE opcode with different blob type transaction value amounts.
    """
    assert len(txs) == 1
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
            balance=tx_value,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=txs[0],
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
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    state_env: Environment,
    txs: List[Transaction],
    destination_account: Address,
):
    """
    Test calldata related opcodes to verify their behavior is not affected by blobs:

    - CALLDATALOAD
    - CALLDATASIZE
    - CALLDATACOPY
    """
    assert len(txs) == 1
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=txs[0],
        env=state_env,
    )


@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 2])  # always below data fee
@pytest.mark.parametrize("tx_max_fee_per_blob_gas", [1, 3])  # normal and above priority fee
@pytest.mark.parametrize("tx_max_fee_per_gas", [100])  # always above priority fee
@pytest.mark.parametrize("opcode", [Op.GASPRICE], indirect=True)
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_gasprice_opcode(
    state_test: StateTestFiller,
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    state_env: Environment,
    txs: List[Transaction],
    destination_account: Address,
):
    """
    Test GASPRICE opcode to sanity check that the blob gas fee does not affect
    its calculation:

    - No priority fee
    - Priority fee below data fee
    - Priority fee above data fee
    """
    assert len(txs) == 1
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    state_test(
        pre=pre,
        post=post,
        tx=txs[0],
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
    pre: Dict,
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
