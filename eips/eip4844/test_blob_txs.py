"""
abstract: Tests blob type transactions for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)

    Test blob type transactions for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).


note: Adding a new test

    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test
    - pre
    - env
    - blocks

    All other `pytest.fixture` fixtures can be parametrized to generate new combinations and test cases.

"""  # noqa: E501
import itertools
from typing import Dict, List, Optional, Tuple

import pytest

from ethereum_test_tools import Account, Block, BlockchainTestFiller, Environment, Header
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    Storage,
    TestAddress,
    Transaction,
    add_kzg_version,
    eip_2028_transaction_data_cost,
    to_address,
    to_hash_bytes,
)

from .utils import (
    BLOB_COMMITMENT_VERSION_KZG,
    DATA_GAS_PER_BLOB,
    MAX_BLOBS_PER_BLOCK,
    TARGET_BLOBS_PER_BLOCK,
    calc_excess_data_gas,
    get_data_gasprice,
    get_min_excess_data_blobs_for_data_gas_price,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "b33e063530f0a114635dd4f89d3cca90f8cac28f"


@pytest.fixture
def destination_account() -> str:
    """Default destination account for the blob transactions."""
    return to_address(0x100)


@pytest.fixture
def tx_value() -> int:
    """
    Default value contained by the transactions sent during test.

    Can be overloaded by a test case to provide a custom transaction value.
    """
    return 1


@pytest.fixture
def tx_gas() -> int:
    """Default gas allocated to transactions sent during test."""
    return 21000


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
    return 10  # Defaults to a data gas price of 1.


@pytest.fixture(autouse=True)
def parent_blobs() -> Optional[int]:
    """
    Default data blobs of the parent blob.

    Can be overloaded by a test case to provide a custom parent blob count.
    """
    return 0


@pytest.fixture
def parent_excess_data_gas(
    parent_excess_blobs: Optional[int],
) -> Optional[int]:
    """
    Calculates the excess data gas of the paraent block from the excess blobs.
    """
    if parent_excess_blobs is None:
        return None
    return parent_excess_blobs * DATA_GAS_PER_BLOB


@pytest.fixture
def data_gasprice(
    parent_excess_data_gas: Optional[int],
    parent_blobs: Optional[int],
) -> Optional[int]:
    """
    Data gas price for the block of the test.
    """
    if parent_excess_data_gas is None or parent_blobs is None:
        return None

    return get_data_gasprice(
        excess_data_gas=calc_excess_data_gas(
            parent_excess_data_gas=parent_excess_data_gas,
            parent_blobs=parent_blobs,
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
            [to_hash_bytes(x) for x in range(blob_count)],
            BLOB_COMMITMENT_VERSION_KZG,
        )
        for blob_count in blobs_per_tx
    ]


@pytest.fixture
def total_account_minimum_balance(  # noqa: D103
    tx_gas: int,
    tx_value: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_priority_fee_per_gas: int,
    tx_max_fee_per_data_gas: int,
    blob_hashes_per_tx: List[List[bytes]],
) -> int:
    """
    Calculates the minimum balance required for the account to be able to send
    the transactions in the block of the test.
    """
    total_cost = 0
    for tx_blob_count in [len(x) for x in blob_hashes_per_tx]:
        data_cost = tx_max_fee_per_data_gas * DATA_GAS_PER_BLOB * tx_blob_count
        total_cost += (
            (tx_gas * (tx_max_fee_per_gas + tx_max_priority_fee_per_gas))
            + tx_value
            + eip_2028_transaction_data_cost(tx_calldata)
            + data_cost
        )
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
def tx_max_fee_per_data_gas(  # noqa: D103
    data_gasprice: Optional[int],
) -> int:
    """
    Default max fee per data gas for transactions sent during test.

    By default, it is set to the data gas price of the block.

    Can be overloaded by a test case to test rejection of transactions where
    the max fee per data gas is insufficient.
    """
    if data_gasprice is None:
        # When fork transitioning, the default data gas price is 1.
        return 1
    return data_gasprice


@pytest.fixture
def tx_error() -> Optional[str]:
    """
    Default expected error produced by the block transactions (no error).

    Can be overloaded on test cases where the transactions are expected
    to fail.
    """
    return None


@pytest.fixture(autouse=True)
def txs(  # noqa: D103
    destination_account: Optional[str],
    tx_gas: int,
    tx_value: int,
    tx_calldata: bytes,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_data_gas: int,
    tx_max_priority_fee_per_gas: int,
    blob_hashes_per_tx: List[List[bytes]],
    tx_error: Optional[str],
) -> List[Transaction]:
    """
    Prepare the list of transactions that are sent during the test.
    """
    return [
        Transaction(
            ty=3,
            nonce=tx_i,
            to=destination_account,
            value=tx_value,
            gas_limit=tx_gas,
            data=tx_calldata,
            max_fee_per_gas=tx_max_fee_per_gas,
            max_priority_fee_per_gas=tx_max_priority_fee_per_gas,
            max_fee_per_data_gas=tx_max_fee_per_data_gas,
            access_list=[],
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
    parent_excess_data_gas: Optional[int],
    parent_blobs: Optional[int],
) -> Environment:
    """
    Prepare the environment for all test cases.
    """
    if parent_blobs is None:
        parent_blobs = 0
    return Environment(
        excess_data_gas=parent_excess_data_gas, data_gas_used=parent_blobs * DATA_GAS_PER_BLOB
    )


@pytest.fixture
def blocks(
    txs: List[Transaction],
    tx_error: Optional[str],
) -> List[Block]:
    """
    Prepare the list of blocks for all test cases.
    """
    header_data_gas_used = 0
    if len(txs) > 0:
        header_data_gas_used = (
            sum(
                [
                    len(tx.blob_versioned_hashes)
                    for tx in txs
                    if tx.blob_versioned_hashes is not None
                ]
            )
            * DATA_GAS_PER_BLOB
        )
    return [
        Block(txs=txs, exception=tx_error, rlp_modifier=Header(data_gas_used=header_data_gas_used))
    ]


def all_valid_blob_combinations() -> List[Tuple[int, ...]]:
    """
    Returns all valid blob tx combinations for a given block,
    assuming the given MAX_BLOBS_PER_BLOCK
    """
    all = [
        seq
        for i in range(
            MAX_BLOBS_PER_BLOCK, 0, -1
        )  # We can have from 1 to at most MAX_BLOBS_PER_BLOCK blobs per block
        for seq in itertools.combinations_with_replacement(
            range(1, MAX_BLOBS_PER_BLOCK + 1), i
        )  # We iterate through all possible combinations
        if sum(seq) <= MAX_BLOBS_PER_BLOCK  # And we only keep the ones that are valid
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
            MAX_BLOBS_PER_BLOCK + 1, 0, -1
        )  # We can have from 1 to at most MAX_BLOBS_PER_BLOCK blobs per block
        for seq in itertools.combinations_with_replacement(
            range(1, MAX_BLOBS_PER_BLOCK + 2), i
        )  # We iterate through all possible combinations
        if sum(seq) == MAX_BLOBS_PER_BLOCK + 1  # And we only keep the ones that match the
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
    blocks: List[Block],
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
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "parent_excess_blobs,parent_blobs,tx_max_fee_per_data_gas,tx_error",
    [
        # tx max_data_gas_cost of the transaction is not enough
        (
            get_min_excess_data_blobs_for_data_gas_price(2) - 1,  # data gas price is 1
            TARGET_BLOBS_PER_BLOCK + 1,  # data gas cost increases to 2
            1,  # tx max_data_gas_cost is 1
            "insufficient max fee per data gas",
        ),
        # tx max_data_gas_cost of the transaction is zero, which is invalid
        (
            0,  # data gas price is 1
            0,  # data gas cost stays put at 1
            0,  # tx max_data_gas_cost is 0
            "invalid max fee per data gas",
        ),
    ],
    ids=["insufficient_max_fee_per_data_gas", "invalid_max_fee_per_data_gas"],
)
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_max_fee_per_data_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks with invalid blob txs due to:

    - tx max_fee_per_data_gas is barely not enough
    - tx max_fee_per_data_gas is zero
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "tx_max_fee_per_gas,tx_error",
    [
        # max data gas is ok, but max fee per gas is less than base fee per gas
        (
            6,
            "insufficient max fee per gas",
        ),
    ],
    ids=["insufficient_max_fee_per_gas"],
)
@pytest.mark.valid_from("Cancun")
def test_invalid_normal_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks with invalid blob txs due to:

    - Sufficient max fee per data gas, but insufficient max fee per gas
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "blobs_per_tx",
    invalid_blob_combinations(),
)
@pytest.mark.parametrize("tx_error", ["invalid_blob_count"])
@pytest.mark.valid_from("Cancun")
def test_invalid_block_blob_count(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
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
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 8])
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.parametrize(
    "tx_calldata",
    [b"", b"\x00", b"\x01"],
    ids=["no_calldata", "single_zero_calldata", "single_one_calldata"],
)
@pytest.mark.parametrize("tx_max_fee_per_data_gas", [1, 100, 10000])
@pytest.mark.parametrize("account_balance_modifier", [-1], ids=["exact_balance_minus_1"])
@pytest.mark.parametrize("tx_error", ["insufficient_account_balance"], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_insufficient_balance_blob_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks where user cannot afford the data gas specified (but
    max_fee_per_gas would be enough for current block), including:

    - Transactions with and without priority fee
    - Transactions with and without value
    - Transactions with and without calldata
    - Transactions with max fee per data gas lower or higher than the priority fee
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "blobs_per_tx",
    all_valid_blob_combinations(),
)
@pytest.mark.parametrize("account_balance_modifier", [-1], ids=["exact_balance_minus_1"])
@pytest.mark.parametrize("tx_error", ["insufficient_account_balance"], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_insufficient_balance_blob_tx_combinations(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject all valid blob transaction combinations in a block, but block is invalid due to:

    - The amount of blobs is correct but the user cannot afford the
            transaction total cost
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "blobs_per_tx,tx_error",
    [
        ([0], "zero_blob_tx"),
        ([MAX_BLOBS_PER_BLOCK + 1], "too_many_blobs_tx"),
    ],
    ids=["too_few_blobs", "too_many_blobs"],
)
@pytest.mark.valid_from("Cancun")
def test_invalid_tx_blob_count(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks that include blob transactions with invalid blob counts:

    - `blob count == 0` in type 3 transaction
    - `blob count > MAX_BLOBS_PER_BLOCK` in type 3 transaction
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "blob_hashes_per_tx",
    [
        [[to_hash_bytes(1)]],
        [[to_hash_bytes(x) for x in range(2)]],
        [add_kzg_version([to_hash_bytes(1)], BLOB_COMMITMENT_VERSION_KZG) + [to_hash_bytes(2)]],
        [[to_hash_bytes(1)] + add_kzg_version([to_hash_bytes(2)], BLOB_COMMITMENT_VERSION_KZG)],
        [
            add_kzg_version([to_hash_bytes(1)], BLOB_COMMITMENT_VERSION_KZG),
            [to_hash_bytes(2)],
        ],
        [
            add_kzg_version([to_hash_bytes(1)], BLOB_COMMITMENT_VERSION_KZG),
            [to_hash_bytes(x) for x in range(1, 3)],
        ],
        [
            add_kzg_version([to_hash_bytes(1)], BLOB_COMMITMENT_VERSION_KZG),
            [to_hash_bytes(2)] + add_kzg_version([to_hash_bytes(3)], BLOB_COMMITMENT_VERSION_KZG),
        ],
        [
            add_kzg_version([to_hash_bytes(1)], BLOB_COMMITMENT_VERSION_KZG),
            add_kzg_version([to_hash_bytes(2)], BLOB_COMMITMENT_VERSION_KZG),
            [to_hash_bytes(3)],
        ],
    ],
    ids=[
        "single_tx_single_blob",
        "single_tx_multiple_blobs",
        "single_tx_multiple_blobs_single_bad_hash_1",
        "single_tx_multiple_blobs_single_bad_hash_2",
        "multiple_txs_single_blob",
        "multiple_txs_multiple_blobs",
        "multiple_txs_multiple_blobs_single_bad_hash_1",
        "multiple_txs_multiple_blobs_single_bad_hash_2",
    ],
)
@pytest.mark.parametrize("tx_error", ["invalid_versioned_hash"], ids=[""])
@pytest.mark.valid_from("Cancun")
def test_invalid_blob_hash_versioning(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks that include blob transactions with invalid blob hash
    version, including:

    - Single blob transaction with single blob with invalid version
    - Single blob transaction with multiple blobs all with invalid version
    - Single blob transaction with multiple blobs either with invalid version
    - Multiple blob transactions with single blob all with invalid version
    - Multiple blob transactions with multiple blobs all with invalid version
    - Multiple blob transactions with multiple blobs only one with invalid version
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    "destination_account,tx_error", [(None, "no_contract_creating_blob_txs")], ids=[""]
)
@pytest.mark.valid_from("Cancun")
def test_invalid_blob_tx_contract_creation(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks that include blob transactions that have nil to value (contract creating).
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
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
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    env: Environment,
    blocks: List[Block],
    destination_account: str,
):
    """
    Test opcodes that read transaction attributes work properly for blob type transactions:

    - ORIGIN
    - CALLER
    """
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize("opcode", [Op.CALLVALUE], indirect=["opcode"])
@pytest.mark.parametrize("tx_value", [0, 1, int(1e18)])
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_value_opcode(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    env: Environment,
    blocks: List[Block],
    tx_value: int,
    destination_account: str,
):
    """
    Test the VALUE opcode with different blob type transaction value amounts.
    """
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
            balance=tx_value,
        )
    }
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
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
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    env: Environment,
    blocks: List[Block],
    destination_account: str,
):
    """
    Test calldata related opcodes to verify their behavior is not affected by blobs:

    - CALLDATALOAD
    - CALLDATASIZE
    - CALLDATACOPY
    """
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize("tx_max_priority_fee_per_gas", [0, 2])  # always below data fee
@pytest.mark.parametrize("tx_max_fee_per_data_gas", [1, 3])  # normal and above priority fee
@pytest.mark.parametrize("tx_max_fee_per_gas", [100])  # always above priority fee
@pytest.mark.parametrize("opcode", [Op.GASPRICE], indirect=True)
@pytest.mark.parametrize("tx_gas", [500_000])
@pytest.mark.valid_from("Cancun")
def test_blob_tx_attribute_gasprice_opcode(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    opcode: Tuple[bytes, Storage.StorageDictType],
    env: Environment,
    blocks: List[Block],
    destination_account: str,
):
    """
    Test GASPRICE opcode to sanity check that the data fee per gas does not affect
    its calculation:

    - No priority fee
    - Priority fee below data fee
    - Priority fee above data fee
    """
    code, storage = opcode
    pre[destination_account] = Account(code=code)
    post = {
        destination_account: Account(
            storage=storage,
        )
    }
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
    )


@pytest.mark.parametrize(
    [
        "blobs_per_tx",
        "parent_excess_blobs",
        "tx_max_fee_per_data_gas",
        "tx_error",
    ],
    [
        ([0], None, 1, "tx_type_3_not_allowed_yet"),
        ([1], None, 1, "tx_type_3_not_allowed_yet"),
    ],
    ids=["no_blob_tx", "one_blob_tx"],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_blob_type_tx_pre_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    blocks: List[Block],
):
    """
    Reject blocks with blob type transactions before Cancun fork
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=Environment(),  # `env` fixture has blob fields
    )
