"""
abstract: Tests `excessDataGas` and `dataGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)

    Test `excessDataGas` and `dataGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

note: Adding a new test

    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test
    - env
    - pre
    - blocks
    - post
    - correct_excess_data_gas

    The following arguments *need* to be parametrized or the test will not be generated:

     - new_blobs

    All other `pytest.fixture` fixtures can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501
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
    TestAddress2,
    Transaction,
    add_kzg_version,
    to_address,
    to_hash_bytes,
)

from .common import (
    BLOB_COMMITMENT_VERSION_KZG,
    DATA_GAS_PER_BLOB,
    MAX_BLOBS_PER_BLOCK,
    REF_SPEC_4844_GIT_PATH,
    REF_SPEC_4844_VERSION,
    TARGET_BLOBS_PER_BLOCK,
    TARGET_DATA_GAS_PER_BLOCK,
    calc_excess_data_gas,
    get_data_gasprice,
    get_min_excess_data_blobs_for_data_gas_price,
)

REFERENCE_SPEC_GIT_PATH = REF_SPEC_4844_GIT_PATH
REFERENCE_SPEC_VERSION = REF_SPEC_4844_VERSION

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
        modified_excess_data_gas = correct_excess_data_gas + (
            header_excess_blobs_delta * DATA_GAS_PER_BLOB
        )
        if modified_excess_data_gas < 0:
            modified_excess_data_gas = 2**64 + (modified_excess_data_gas)
        return modified_excess_data_gas
    if header_excess_data_gas_delta is not None:
        return correct_excess_data_gas + header_excess_data_gas_delta
    return None


@pytest.fixture
def block_fee_per_data_gas(  # noqa: D103
    correct_excess_data_gas: int,
) -> int:
    return get_data_gasprice(excess_data_gas=correct_excess_data_gas)


@pytest.fixture
def block_base_fee() -> int:  # noqa: D103
    return 7


@pytest.fixture
def env(  # noqa: D103
    parent_excess_data_gas: int,
    block_base_fee: int,
    parent_blobs: int,
) -> Environment:
    return Environment(
        excess_data_gas=parent_excess_data_gas
        if parent_blobs == 0
        else parent_excess_data_gas + TARGET_DATA_GAS_PER_BLOCK,
        base_fee=block_base_fee,
    )


@pytest.fixture
def tx_max_fee_per_gas(  # noqa: D103
    block_base_fee: int,
) -> int:
    return block_base_fee


@pytest.fixture
def tx_max_fee_per_data_gas(  # noqa: D103
    block_fee_per_data_gas: int,
) -> int:
    return block_fee_per_data_gas


@pytest.fixture
def tx_data_cost(  # noqa: D103
    tx_max_fee_per_data_gas: int,
    new_blobs: int,
) -> int:
    return tx_max_fee_per_data_gas * DATA_GAS_PER_BLOB * new_blobs


@pytest.fixture
def tx_value() -> int:  # noqa: D103
    return 1


@pytest.fixture
def tx_exact_cost(tx_value: int, tx_max_fee_per_gas: int, tx_data_cost: int) -> int:  # noqa: D103
    tx_gas = 21000
    return (tx_gas * tx_max_fee_per_gas) + tx_value + tx_data_cost


@pytest.fixture
def pre(tx_exact_cost: int) -> Mapping[str, Account]:  # noqa: D103
    return {
        TestAddress: Account(balance=tx_exact_cost),
        TestAddress2: Account(balance=10**40),
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
    tx_max_fee_per_gas: int,
    tx_max_fee_per_data_gas: int,
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
            max_fee_per_gas=tx_max_fee_per_gas,
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
            max_fee_per_gas=tx_max_fee_per_gas,
            max_priority_fee_per_gas=0,
            max_fee_per_data_gas=tx_max_fee_per_data_gas,
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
    block_intermediate: Block,
):
    blocks = [] if block_intermediate is None else [block_intermediate]
    if header_excess_data_gas is not None:
        blocks.append(
            Block(
                txs=[tx],
                rlp_modifier=Header(
                    excess_data_gas=header_excess_data_gas,
                ),
                exception="invalid excess data gas",
            ),
        )
    elif header_data_gas_used is not None:
        blocks.append(
            Block(
                txs=[tx],
                rlp_modifier=Header(
                    data_gas_used=header_data_gas_used,
                ),
                exception="invalid data gas used",
            ),
        )
    else:
        blocks.append(Block(txs=[tx]))
    return blocks


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
    Test calculation of the `excessDataGas` increase/decrease across
    multiple blocks with and without blobs:

    - With parent block containing `[0, MAX_BLOBS_PER_BLOCK]` blobs
    - With parent block containing `[0, TARGET_BLOBS_PER_BLOCK]` equivalent value of excess data gas
    """  # noqa: E501
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_data_gas:{hex(correct_excess_data_gas)}",
    )


DATA_GAS_COST_INCREASES = [
    get_min_excess_data_blobs_for_data_gas_price(i)
    for i in [
        2,  # First data gas cost increase
        2**32 // DATA_GAS_PER_BLOB,  # Data tx wei cost 2^32
        2**32,  # Data gas cost 2^32
        2**64 // DATA_GAS_PER_BLOB,  # Data tx wei cost 2^64
        2**64,  # Data gas cost 2^64
        (
            120_000_000 * (10**18) // DATA_GAS_PER_BLOB
        ),  # Data tx wei is current total Ether supply
    ]
]


@pytest.mark.parametrize(
    "parent_excess_blobs",
    [g - 1 for g in DATA_GAS_COST_INCREASES],
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
    Test calculation of the `excessDataGas` and data gas tx costs at
    value points where the cost increases to interesting amounts:

    - At the first data gas cost increase (1 to 2)
    - At total transaction data cost increase to `> 2^32`
    - At data gas wei cost increase to `> 2^32`
    - At total transaction data cost increase to `> 2^64`
    - At data gas wei cost increase to `> 2^64`
    - At data gas wei cost increase of around current total Ether supply
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
    [g for g in DATA_GAS_COST_INCREASES],
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
    Test calculation of the `excessDataGas` and data gas tx costs at
    value points where the cost decreases to interesting amounts.

    See test_correct_increasing_data_gas_costs.
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
    Test rejection of blocks where the `excessDataGas` in the header drops to
    zero in a block with or without data blobs, but the excess blobs in the parent are
    greater than target.
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
        yield (new_blobs, 2**64 - 1)


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
    Test rejection of blocks where the `dataGasUsed` in the header is invalid:

    - `dataGasUsed` is not equal to the number of data blobs in the block
    - `dataGasUsed` is the max uint64 value
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
    [
        (-1, 0),
        (+1, MAX_BLOBS_PER_BLOCK),
    ],
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
    Test rejection of blocks where the `excessDataGas`

    - decreases more than `TARGET_DATA_GAS_PER_BLOCK` in a single block with zero blobs
    - increases more than `TARGET_DATA_GAS_PER_BLOCK` in a single block with max blobs
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
    Test rejection of blocks where the `excessDataGas` remains unchanged
    but the parent blobs included are not `TARGET_BLOBS_PER_BLOCK`.

    Test is parametrized to `MAX_BLOBS_PER_BLOCK` and `TARGET_BLOBS_PER_BLOCK`.
    """
    blocks[-1].rlp_modifier = Header(excess_data_gas=parent_excess_data_gas)
    blocks[-1].exception = "invalid excessDataGas"
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
    Test rejection of blocks where the `excessDataGas` increases from zero,
    even when the included blobs are on or below target.

    Test is parametrized according to `[0, TARGET_BLOBS_PER_BLOCK]` new blobs.
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
    Test rejection of blocks where the `excessDataGas` does not increase from
    zero, even when the included blobs is above target.

    Test is parametrized to `[TARGET_BLOBS_PER_BLOCK+1, MAX_BLOBS_PER_BLOCK]` new blobs.
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
    Test rejection of blocks where the `excessDataGas` changes to an invalid
    value.

    Given a parent block containing `[0, MAX_BLOBS_PER_BLOCK]` blobs, test an invalid
    `excessDataGas` value by changing it by `[-TARGET_BLOBS_PER_BLOCK, TARGET_BLOBS_PER_BLOCK]`
    from the correct value.
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
    Test rejection of blocks where the `excessDataGas` changes to the two's
    complement equivalent of the negative value after subtracting target blobs.

    Reasoning is that the `excessDataGas` is a `uint64`, so it cannot be negative, and
    we test for a potential underflow here.
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
    Test rejection of blocks where the `excessDataGas` changes to a value that
    is not a multiple of `DATA_GAS_PER_BLOB`:

    - Parent block contains `TARGET_BLOBS_PER_BLOCK + 1` blobs, but `excessDataGas` is off by +/-1
    - Parent block contains `TARGET_BLOBS_PER_BLOCK - 1` blobs, but `excessDataGas` is off by +/-1
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
