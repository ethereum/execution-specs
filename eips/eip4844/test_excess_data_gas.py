"""
Test EIP-4844: Shard Blob Transactions (Excess Data Tests)
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""
import itertools
from typing import Iterator, List, Mapping, Optional, Tuple

import pytest

from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Environment,
    Header,
    TestAddress,
    Transaction,
    add_kzg_version,
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
)

# * Adding a new test *
# Add a function that is named `test_<test_name>` and takes the following
# arguments:
#   - blockchain_test
#   - env
#   - pre
#   - blocks
#   - post
#   - correct_excess_data_gas
#
# The following arguments *need* to be parametrized or the test will not be
# generated:
# - new_blobs
#
# All other `pytest.fixture` fixtures can be parametrized to generate new
# combinations and test cases.


REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"

# All tests run from Cancun fork
pytestmark = pytest.mark.valid_from("Cancun")


@pytest.fixture
def parent_excess_blobs() -> int:  # noqa: D103
    """
    By default we start with an intermediate value between the target and max.
    """
    return (MAX_BLOBS_PER_BLOCK + TARGET_BLOBS_PER_BLOCK) // 2 + 1


@pytest.fixture
def parent_excess_data_gas(parent_excess_blobs: int) -> int:  # noqa: D103
    return parent_excess_blobs * DATA_GAS_PER_BLOB


@pytest.fixture
def correct_excess_data_gas(  # noqa: D103
    parent_excess_data_gas: int,
    parent_blobs: int,
) -> int:
    return calc_excess_data_gas(
        parent_excess_data_gas=parent_excess_data_gas,
        parent_blobs=parent_blobs,
    )


@pytest.fixture
def header_excess_blobs_delta() -> Optional[int]:  # noqa: D103
    return None


@pytest.fixture
def header_excess_data_gas_delta() -> Optional[int]:  # noqa: D103
    return None


@pytest.fixture
def header_excess_data_gas(  # noqa: D103
    correct_excess_data_gas: int,
    header_excess_blobs_delta: Optional[int],
    header_excess_data_gas_delta: Optional[int],
) -> Optional[int]:
    if header_excess_blobs_delta is not None:
        return correct_excess_data_gas + (header_excess_blobs_delta * DATA_GAS_PER_BLOB)
    if header_excess_data_gas_delta is not None:
        return correct_excess_data_gas + header_excess_data_gas_delta
    return None


@pytest.fixture
def fee_per_data_gas(  # noqa: D103
    correct_excess_data_gas: int,
) -> int:
    return get_data_gasprice(excess_data_gas=correct_excess_data_gas)


@pytest.fixture
def tx_max_fee_per_data_gas(  # noqa: D103
    fee_per_data_gas: int,
) -> int:
    return fee_per_data_gas


@pytest.fixture
def block_base_fee() -> int:  # noqa: D103
    return 7


@pytest.fixture
def env(  # noqa: D103
    parent_excess_data_gas: int,
    parent_blobs: int,
    block_base_fee: int,
) -> Environment:
    return Environment(
        excess_data_gas=parent_excess_data_gas,
        data_gas_used=parent_blobs * DATA_GAS_PER_BLOB,
        base_fee=block_base_fee,
    )


@pytest.fixture
def tx_max_fee(  # noqa: D103
    block_base_fee: int,
) -> int:
    return block_base_fee


@pytest.fixture
def tx_data_cost(  # noqa: D103
    fee_per_data_gas: int,
    new_blobs: int,
) -> int:
    return fee_per_data_gas * DATA_GAS_PER_BLOB * new_blobs


@pytest.fixture
def tx_value() -> int:  # noqa: D103
    return 1


@pytest.fixture
def tx_exact_cost(tx_value: int, tx_max_fee: int, tx_data_cost: int) -> int:  # noqa: D103
    tx_gas = 21000
    return (tx_gas * tx_max_fee) + tx_value + tx_data_cost


@pytest.fixture
def pre(tx_exact_cost: int) -> Mapping[str, Account]:  # noqa: D103
    return {
        TestAddress: Account(balance=tx_exact_cost),
    }


@pytest.fixture
def destination_account() -> str:  # noqa: D103
    return to_address(0x100)


@pytest.fixture
def post(destination_account: str, tx_value: int) -> Mapping[str, Account]:  # noqa: D103
    return {
        destination_account: Account(balance=tx_value),
    }


@pytest.fixture
def tx(  # noqa: D103
    new_blobs: int,
    tx_max_fee: int,
    tx_data_cost: int,
    destination_account: str,
):
    if new_blobs == 0:
        # Send a normal type two tx instead
        return Transaction(
            ty=2,
            nonce=0,
            to=destination_account,
            value=1,
            gas_limit=21000,
            max_fee_per_gas=tx_max_fee,
            max_priority_fee_per_gas=0,
            access_list=[],
        )
    else:
        return Transaction(
            ty=3,
            nonce=0,
            to=destination_account,
            value=1,
            gas_limit=21000,
            max_fee_per_gas=tx_max_fee,
            max_priority_fee_per_gas=0,
            max_fee_per_data_gas=tx_data_cost,
            access_list=[],
            blob_versioned_hashes=add_kzg_version(
                [to_hash_bytes(x) for x in range(new_blobs)],
                BLOB_COMMITMENT_VERSION_KZG,
            ),
        )


@pytest.fixture
def header_data_gas_used() -> Optional[int]:  # noqa: D103
    return None


@pytest.fixture
def blocks(  # noqa: D103
    tx: Transaction,
    header_excess_data_gas: Optional[int],
    header_data_gas_used: Optional[int],
):
    if header_excess_data_gas is not None:
        return [
            Block(
                txs=[tx],
                rlp_modifier=Header(
                    excess_data_gas=header_excess_data_gas,
                ),
                exception="invalid excess data gas",
            )
        ]
    if header_data_gas_used is not None:
        return [
            Block(
                txs=[tx],
                rlp_modifier=Header(
                    data_gas_used=header_data_gas_used,
                ),
                exception="invalid data gas used",
            )
        ]
    return [Block(txs=[tx])]


@pytest.mark.parametrize("parent_blobs", range(0, MAX_BLOBS_PER_BLOCK + 1))
@pytest.mark.parametrize("parent_excess_blobs", range(0, TARGET_BLOBS_PER_BLOCK + 1))
@pytest.mark.parametrize("new_blobs", [1])
def test_correct_excess_data_gas_calculation(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    post: Mapping[str, Account],
    correct_excess_data_gas: int,
):
    """
    Test calculation of the excess_data_gas increase/decrease across
    multiple blocks with and without blobs.
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_data_gas:{hex(correct_excess_data_gas)}",
    )


@pytest.mark.parametrize(
    "parent_excess_blobs",
    [
        # Data gas cost increase to 2
        11,
        # Data tx wei cost increase to 2^32
        176,
        # Data gas cost increase to 2^32
        376,
        # Data tx wei cost increase to 2^64
        553,
        # Data gas cost increase to 2^64
        753,
        # Data tx wei cost increase to main net current total Ether supply
        820,
    ],
)
@pytest.mark.parametrize("parent_blobs", [TARGET_BLOBS_PER_BLOCK + 1])
@pytest.mark.parametrize("new_blobs", [1])
def test_correct_increasing_data_gas_costs(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    post: Mapping[str, Account],
    correct_excess_data_gas: int,
):
    """
    Test calculation of the excess_data_gas and data gas tx costs at
    value points where the cost increases to interesting amounts.
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_data_gas:{hex(correct_excess_data_gas)}",
    )


@pytest.mark.parametrize(
    "parent_excess_blobs",
    [
        # Data gas cost decrease to 1
        12,
        # Data tx wei cost decrease from 2^32
        177,
        # Data gas cost decrease from 2^32
        377,
        # Data tx wei cost decrease from 2^64
        554,
        # Data gas cost decrease from 2^64
        754,
    ],
)
@pytest.mark.parametrize("parent_blobs", [TARGET_BLOBS_PER_BLOCK - 1])
@pytest.mark.parametrize("new_blobs", [1])
def test_correct_decreasing_data_gas_costs(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    post: Mapping[str, Account],
    correct_excess_data_gas: int,
):
    """
    Test calculation of the excess_data_gas and data gas tx costs at
    value points where the cost decreases to interesting amounts.
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_data_gas:{hex(correct_excess_data_gas)}",
    )


@pytest.mark.parametrize("header_excess_data_gas", [0])
@pytest.mark.parametrize("new_blobs", [0, 1])
@pytest.mark.parametrize("parent_blobs", range(0, MAX_BLOBS_PER_BLOCK + 1))
def test_invalid_zero_excess_data_gas_in_header(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas in the header drops to
    zero in a block with or without data blobs, but the parent_excess_blobs is
    greater than target in the previous block.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )


def all_invalid_data_gas_used_combinations() -> Iterator[Tuple[int, int]]:
    """
    Returns all invalid data gas used combinations.
    """
    for new_blobs in range(0, MAX_BLOBS_PER_BLOCK + 1):
        for header_data_gas_used in range(0, MAX_BLOBS_PER_BLOCK + 1):
            if new_blobs != header_data_gas_used:
                yield (new_blobs, header_data_gas_used * DATA_GAS_PER_BLOB)


@pytest.mark.parametrize(
    "new_blobs,header_data_gas_used",
    all_invalid_data_gas_used_combinations(),
)
@pytest.mark.parametrize("parent_blobs", [0])
def test_invalid_data_gas_used_in_header(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    new_blobs: int,
    header_data_gas_used: Optional[int],
):
    """
    Test rejection of blocks where the data_gas_used in the header is zero in
    a block with data blobs.
    """
    if header_data_gas_used is None:
        raise Exception("test case is badly formatted")
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(new_blobs * DATA_GAS_PER_BLOB)}",
                f"header:{hex(header_data_gas_used)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "header_excess_blobs_delta,parent_blobs",
    [(-1, 0), (1, MAX_BLOBS_PER_BLOCK)],
    ids=["zero_blobs_decrease_more_than_expected", "max_blobs_increase_more_than_expected"],
)
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_excess_data_gas_above_target_change(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas decreases or increases
    more than TARGET_DATA_GAS_PER_BLOCK in a single block.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "parent_blobs",
    [b for b in range(0, MAX_BLOBS_PER_BLOCK + 1) if b != TARGET_BLOBS_PER_BLOCK],
)
@pytest.mark.parametrize("parent_excess_blobs", [1, TARGET_BLOBS_PER_BLOCK])
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_static_excess_data_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    parent_excess_data_gas: int,
):
    """
    Test rejection of blocks where the excess_data_gas remains unchanged
    but the parent blobs included are not TARGET_BLOBS_PER_BLOCK.
    """
    blocks[0].rlp_modifier = Header(excess_data_gas=parent_excess_data_gas)
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(parent_excess_data_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize("header_excess_blobs_delta", range(1, MAX_BLOBS_PER_BLOCK))
@pytest.mark.parametrize("parent_blobs", range(0, TARGET_BLOBS_PER_BLOCK + 1))
@pytest.mark.parametrize("parent_excess_blobs", [0])  # Start at 0
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_excess_data_gas_target_blobs_increase_from_zero(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas increases from zero,
    even when the included blobs are on or below target.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize("header_excess_data_gas", [0])
@pytest.mark.parametrize(
    "parent_blobs", range(TARGET_BLOBS_PER_BLOCK + 1, MAX_BLOBS_PER_BLOCK + 1)
)
@pytest.mark.parametrize("parent_excess_blobs", [0])  # Start at 0
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_static_excess_data_gas_from_zero_on_blobs_above_target(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas does not increase from
    zero, even when the included blobs is above target.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "parent_blobs,header_excess_blobs_delta",
    itertools.product(
        # parent_blobs
        range(0, MAX_BLOBS_PER_BLOCK + 1),
        # header_excess_blobs_delta (from correct value)
        [x for x in range(-TARGET_BLOBS_PER_BLOCK, TARGET_BLOBS_PER_BLOCK + 1) if x != 0],
    ),
)
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_excess_data_gas_change(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas changes to an invalid
    value.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "header_excess_data_gas",
    [(2**64 + (x * DATA_GAS_PER_BLOB)) for x in range(-TARGET_BLOBS_PER_BLOCK, 0)],
)
@pytest.mark.parametrize("parent_blobs", range(TARGET_BLOBS_PER_BLOCK))
@pytest.mark.parametrize("new_blobs", [1])
@pytest.mark.parametrize("parent_excess_blobs", range(TARGET_BLOBS_PER_BLOCK))
def test_invalid_negative_excess_data_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas changes to the two's
    complement equivalent of the negative value after subtracting target blobs.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "parent_blobs,header_excess_data_gas_delta",
    [
        (TARGET_BLOBS_PER_BLOCK + 1, 1),
        (TARGET_BLOBS_PER_BLOCK + 1, DATA_GAS_PER_BLOB - 1),
        (TARGET_BLOBS_PER_BLOCK - 1, -1),
        (TARGET_BLOBS_PER_BLOCK - 1, -(DATA_GAS_PER_BLOB - 1)),
    ],
)
@pytest.mark.parametrize("new_blobs", [1])
@pytest.mark.parametrize("parent_excess_blobs", [TARGET_BLOBS_PER_BLOCK + 1])
def test_invalid_non_multiple_excess_data_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    blocks: List[Block],
    correct_excess_data_gas: int,
    header_excess_data_gas: Optional[int],
):
    """
    Test rejection of blocks where the excess_data_gas changes to a value that
    is not a multiple of DATA_GAS_PER_BLOB.
    """
    if header_excess_data_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_data_gas == correct_excess_data_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_data_gas)}",
                f"header:{hex(header_excess_data_gas)}",
            ]
        ),
    )
