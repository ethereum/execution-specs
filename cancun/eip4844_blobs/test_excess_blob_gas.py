"""
abstract: Tests `excessBlobGas` and `blobGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test `excessBlobGas` and `blobGasUsed` block fields for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

note: Adding a new test
    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test
    - env
    - pre
    - blocks
    - post
    - correct_excess_blob_gas

    The following arguments *need* to be parametrized or the test will not be generated:

    - new_blobs

    All other `pytest.fixture` fixtures can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501

import itertools
from typing import Dict, Iterator, List, Mapping, Optional, Tuple

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Hash,
    Header,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import TestAddress, TestAddress2, Transaction, add_kzg_version

from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

# All tests run from Cancun fork
pytestmark = pytest.mark.valid_from("Cancun")


@pytest.fixture
def parent_excess_blobs() -> int:  # noqa: D103
    """
    By default we start with an intermediate value between the target and max.
    """
    return (SpecHelpers.max_blobs_per_block() + SpecHelpers.target_blobs_per_block()) // 2 + 1


@pytest.fixture
def parent_excess_blob_gas(parent_excess_blobs: int) -> int:  # noqa: D103
    return parent_excess_blobs * Spec.GAS_PER_BLOB


@pytest.fixture
def correct_excess_blob_gas(  # noqa: D103
    parent_excess_blob_gas: int,
    parent_blobs: int,
) -> int:
    return SpecHelpers.calc_excess_blob_gas_from_blob_count(
        parent_excess_blob_gas=parent_excess_blob_gas,
        parent_blob_count=parent_blobs,
    )


@pytest.fixture
def header_excess_blobs_delta() -> Optional[int]:  # noqa: D103
    return None


@pytest.fixture
def header_excess_blob_gas_delta() -> Optional[int]:  # noqa: D103
    return None


@pytest.fixture
def header_excess_blob_gas(  # noqa: D103
    correct_excess_blob_gas: int,
    header_excess_blobs_delta: Optional[int],
    header_excess_blob_gas_delta: Optional[int],
) -> Optional[int]:
    if header_excess_blobs_delta is not None:
        modified_excess_blob_gas = correct_excess_blob_gas + (
            header_excess_blobs_delta * Spec.GAS_PER_BLOB
        )
        if modified_excess_blob_gas < 0:
            modified_excess_blob_gas = 2**64 + (modified_excess_blob_gas)
        return modified_excess_blob_gas
    if header_excess_blob_gas_delta is not None:
        return correct_excess_blob_gas + header_excess_blob_gas_delta
    return None


@pytest.fixture
def block_fee_per_blob_gas(  # noqa: D103
    correct_excess_blob_gas: int,
) -> int:
    return Spec.get_blob_gasprice(excess_blob_gas=correct_excess_blob_gas)


@pytest.fixture
def block_base_fee() -> int:  # noqa: D103
    return 7


@pytest.fixture
def env(  # noqa: D103
    parent_excess_blob_gas: int,
    block_base_fee: int,
    parent_blobs: int,
) -> Environment:
    return Environment(
        excess_blob_gas=(
            parent_excess_blob_gas
            if parent_blobs == 0
            else parent_excess_blob_gas + Spec.TARGET_BLOB_GAS_PER_BLOCK
        ),
        base_fee_per_gas=block_base_fee,
    )


@pytest.fixture
def tx_max_fee_per_gas(  # noqa: D103
    block_base_fee: int,
) -> int:
    return block_base_fee


@pytest.fixture
def tx_max_fee_per_blob_gas(  # noqa: D103
    block_fee_per_blob_gas: int,
) -> int:
    return block_fee_per_blob_gas


@pytest.fixture
def tx_data_cost(  # noqa: D103
    tx_max_fee_per_blob_gas: int,
    new_blobs: int,
) -> int:
    return tx_max_fee_per_blob_gas * Spec.GAS_PER_BLOB * new_blobs


@pytest.fixture
def tx_value() -> int:  # noqa: D103
    return 1


@pytest.fixture
def tx_gas_limit() -> int:  # noqa: D103
    return 45000


@pytest.fixture
def tx_exact_cost(  # noqa: D103
    tx_value: int, tx_max_fee_per_gas: int, tx_data_cost: int, tx_gas_limit: int
) -> int:
    return (tx_gas_limit * tx_max_fee_per_gas) + tx_value + tx_data_cost


@pytest.fixture
def destination_account_bytecode() -> bytes:  # noqa: D103
    # Verify that the BLOBBASEFEE opcode reflects the current blob gas cost
    return Op.SSTORE(0, Op.BLOBBASEFEE)


@pytest.fixture
def destination_account() -> Address:  # noqa: D103
    return Address(0x100)


@pytest.fixture
def pre(  # noqa: D103
    destination_account: Address, destination_account_bytecode: bytes, tx_exact_cost: int
) -> Mapping[Address, Account]:
    return {
        TestAddress: Account(balance=tx_exact_cost),
        TestAddress2: Account(balance=10**40),
        destination_account: Account(balance=0, code=destination_account_bytecode),
    }


@pytest.fixture
def post(  # noqa: D103
    destination_account: Address, tx_value: int, block_fee_per_blob_gas: int
) -> Mapping[Address, Account]:
    return {
        destination_account: Account(
            storage={0: block_fee_per_blob_gas},
            balance=tx_value,
        ),
    }


@pytest.fixture
def tx(  # noqa: D103
    new_blobs: int,
    tx_max_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    tx_gas_limit: int,
    destination_account: Address,
):
    if new_blobs == 0:
        # Send a normal type two tx instead
        return Transaction(
            ty=2,
            nonce=0,
            to=destination_account,
            value=1,
            gas_limit=tx_gas_limit,
            max_fee_per_gas=tx_max_fee_per_gas,
            max_priority_fee_per_gas=0,
            access_list=[],
        )
    else:
        return Transaction(
            ty=Spec.BLOB_TX_TYPE,
            nonce=0,
            to=destination_account,
            value=1,
            gas_limit=tx_gas_limit,
            max_fee_per_gas=tx_max_fee_per_gas,
            max_priority_fee_per_gas=0,
            max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
            access_list=[],
            blob_versioned_hashes=add_kzg_version(
                [Hash(x) for x in range(new_blobs)],
                Spec.BLOB_COMMITMENT_VERSION_KZG,
            ),
        )


@pytest.fixture
def header_blob_gas_used() -> Optional[int]:  # noqa: D103
    return None


@pytest.fixture
def correct_blob_gas_used(  # noqa: D103
    tx: Transaction,
) -> int:
    return Spec.get_total_blob_gas(tx)


@pytest.fixture
def blocks(  # noqa: D103
    tx: Transaction,
    header_excess_blob_gas: Optional[int],
    header_blob_gas_used: Optional[int],
    correct_excess_blob_gas: int,
    correct_blob_gas_used: int,
    non_zero_blob_gas_used_genesis_block: Block,
):
    blocks = (
        []
        if non_zero_blob_gas_used_genesis_block is None
        else [non_zero_blob_gas_used_genesis_block]
    )

    def add_block(
        header_modifier: Optional[Dict] = None,
        exception_message: Optional[BlockException | List[BlockException]] = None,
    ):
        """
        Utility function to add a block to the blocks list.
        """
        blocks.append(
            Block(
                txs=[tx],
                rlp_modifier=Header(**header_modifier) if header_modifier else None,
                header_verify=Header(
                    excess_blob_gas=correct_excess_blob_gas,
                    blob_gas_used=correct_blob_gas_used,
                ),
                exception=exception_message,
            )
        )

    if header_excess_blob_gas is not None:
        add_block(
            header_modifier={"excess_blob_gas": header_excess_blob_gas},
            exception_message=BlockException.INCORRECT_EXCESS_BLOB_GAS,
        )
    elif header_blob_gas_used is not None:
        if header_blob_gas_used > Spec.MAX_BLOB_GAS_PER_BLOCK:
            add_block(
                header_modifier={"blob_gas_used": header_blob_gas_used},
                exception_message=[
                    BlockException.BLOB_GAS_USED_ABOVE_LIMIT,
                    BlockException.INCORRECT_BLOB_GAS_USED,
                ],
            )
        else:
            add_block(
                header_modifier={"blob_gas_used": header_blob_gas_used},
                exception_message=BlockException.INCORRECT_BLOB_GAS_USED,
            )
    else:
        add_block()

    return blocks


@pytest.mark.parametrize("parent_blobs", range(0, SpecHelpers.max_blobs_per_block() + 1))
@pytest.mark.parametrize("parent_excess_blobs", range(0, SpecHelpers.target_blobs_per_block() + 1))
@pytest.mark.parametrize("new_blobs", [1])
def test_correct_excess_blob_gas_calculation(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    post: Mapping[Address, Account],
    correct_excess_blob_gas: int,
):
    """
    Test calculation of the `excessBlobGas` increase/decrease across
    multiple blocks with and without blobs:

    - With parent block containing `[0, MAX_BLOBS_PER_BLOCK]` blobs
    - With parent block containing `[0, TARGET_BLOBS_PER_BLOCK]` equivalent value of excess blob gas
    """  # noqa: E501
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_blob_gas:{hex(correct_excess_blob_gas)}",
    )


BLOB_GAS_COST_INCREASES = [
    SpecHelpers.get_min_excess_blobs_for_blob_gas_price(i)
    for i in [
        2,  # First blob gas cost increase
        2**32 // Spec.GAS_PER_BLOB,  # Data tx wei cost 2^32
        2**32,  # blob gas cost 2^32
        2**64 // Spec.GAS_PER_BLOB,  # Data tx wei cost 2^64
        2**64,  # blob gas cost 2^64
        (
            120_000_000 * (10**18) // Spec.GAS_PER_BLOB
        ),  # Data tx wei is current total Ether supply
    ]
]


@pytest.mark.parametrize(
    "parent_excess_blobs",
    [g - 1 for g in BLOB_GAS_COST_INCREASES],
)
@pytest.mark.parametrize("parent_blobs", [SpecHelpers.target_blobs_per_block() + 1])
@pytest.mark.parametrize("new_blobs", [1])
def test_correct_increasing_blob_gas_costs(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    post: Mapping[Address, Account],
    correct_excess_blob_gas: int,
):
    """
    Test calculation of the `excessBlobGas` and blob gas tx costs at
    value points where the cost increases to interesting amounts:

    - At the first blob gas cost increase (1 to 2)
    - At total transaction data cost increase to `> 2^32`
    - At blob gas wei cost increase to `> 2^32`
    - At total transaction data cost increase to `> 2^64`
    - At blob gas wei cost increase to `> 2^64`
    - At blob gas wei cost increase of around current total Ether supply
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_blob_gas:{hex(correct_excess_blob_gas)}",
    )


@pytest.mark.parametrize(
    "parent_excess_blobs",
    [g for g in BLOB_GAS_COST_INCREASES],
)
@pytest.mark.parametrize("parent_blobs", [SpecHelpers.target_blobs_per_block() - 1])
@pytest.mark.parametrize("new_blobs", [1])
def test_correct_decreasing_blob_gas_costs(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    post: Mapping[Address, Account],
    correct_excess_blob_gas: int,
):
    """
    Test calculation of the `excessBlobGas` and blob gas tx costs at
    value points where the cost decreases to interesting amounts.

    See test_correct_increasing_blob_gas_costs.
    """
    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=env,
        tag=f"expected_excess_blob_gas:{hex(correct_excess_blob_gas)}",
    )


@pytest.mark.parametrize("header_excess_blob_gas", [0])
@pytest.mark.parametrize("new_blobs", [0, 1])
@pytest.mark.parametrize("parent_blobs", range(0, SpecHelpers.max_blobs_per_block() + 1))
def test_invalid_zero_excess_blob_gas_in_header(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas` in the header drops to
    zero in a block with or without data blobs, but the excess blobs in the parent are
    greater than target.
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )


def all_invalid_blob_gas_used_combinations() -> Iterator[Tuple[int, int]]:
    """
    Returns all invalid blob gas used combinations.
    """
    for new_blobs in range(0, SpecHelpers.max_blobs_per_block() + 1):
        for header_blob_gas_used in range(0, SpecHelpers.max_blobs_per_block() + 1):
            if new_blobs != header_blob_gas_used:
                yield (new_blobs, header_blob_gas_used * Spec.GAS_PER_BLOB)
        yield (new_blobs, 2**64 - 1)


@pytest.mark.parametrize(
    "new_blobs,header_blob_gas_used",
    all_invalid_blob_gas_used_combinations(),
)
@pytest.mark.parametrize("parent_blobs", [0])
def test_invalid_blob_gas_used_in_header(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    new_blobs: int,
    header_blob_gas_used: Optional[int],
):
    """
    Test rejection of blocks where the `blobGasUsed` in the header is invalid:

    - `blobGasUsed` is not equal to the number of data blobs in the block
    - `blobGasUsed` is the max uint64 value
    """
    if header_blob_gas_used is None:
        raise Exception("test case is badly formatted")
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(new_blobs * Spec.GAS_PER_BLOB)}",
                f"header:{hex(header_blob_gas_used)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "header_excess_blobs_delta,parent_blobs",
    [
        (-1, 0),
        (+1, SpecHelpers.max_blobs_per_block()),
    ],
    ids=["zero_blobs_decrease_more_than_expected", "max_blobs_increase_more_than_expected"],
)
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_excess_blob_gas_above_target_change(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas`

    - decreases more than `TARGET_BLOB_GAS_PER_BLOCK` in a single block with zero blobs
    - increases more than `TARGET_BLOB_GAS_PER_BLOCK` in a single block with max blobs
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "parent_blobs",
    [
        b
        for b in range(0, SpecHelpers.max_blobs_per_block() + 1)
        if b != SpecHelpers.target_blobs_per_block()
    ],
)
@pytest.mark.parametrize("parent_excess_blobs", [1, SpecHelpers.target_blobs_per_block()])
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_static_excess_blob_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    parent_excess_blob_gas: int,
):
    """
    Test rejection of blocks where the `excessBlobGas` remains unchanged
    but the parent blobs included are not `TARGET_BLOBS_PER_BLOCK`.

    Test is parametrized to `MAX_BLOBS_PER_BLOCK` and `TARGET_BLOBS_PER_BLOCK`.
    """
    blocks[-1].rlp_modifier = Header(excess_blob_gas=parent_excess_blob_gas)
    blocks[-1].header_verify = None
    blocks[-1].exception = BlockException.INCORRECT_EXCESS_BLOB_GAS
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(parent_excess_blob_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize("header_excess_blobs_delta", range(1, SpecHelpers.max_blobs_per_block()))
@pytest.mark.parametrize("parent_blobs", range(0, SpecHelpers.target_blobs_per_block() + 1))
@pytest.mark.parametrize("parent_excess_blobs", [0])  # Start at 0
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_excess_blob_gas_target_blobs_increase_from_zero(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas` increases from zero,
    even when the included blobs are on or below target.

    Test is parametrized according to `[0, TARGET_BLOBS_PER_BLOCK` new blobs.
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize("header_excess_blob_gas", [0])
@pytest.mark.parametrize(
    "parent_blobs",
    range(SpecHelpers.target_blobs_per_block() + 1, SpecHelpers.max_blobs_per_block() + 1),
)
@pytest.mark.parametrize("parent_excess_blobs", [0])  # Start at 0
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_static_excess_blob_gas_from_zero_on_blobs_above_target(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas` does not increase from
    zero, even when the included blobs is above target.

    Test is parametrized to `[TARGET_BLOBS_PER_BLOCK+1, MAX_BLOBS_PER_BLOCK]` new blobs.
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "parent_blobs,header_excess_blobs_delta",
    itertools.product(
        # parent_blobs
        range(0, SpecHelpers.max_blobs_per_block() + 1),
        # header_excess_blobs_delta (from correct value)
        [
            x
            for x in range(
                -SpecHelpers.target_blobs_per_block(), SpecHelpers.target_blobs_per_block() + 1
            )
            if x != 0
        ],
    ),
)
@pytest.mark.parametrize("new_blobs", [1])
def test_invalid_excess_blob_gas_change(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas` changes to an invalid
    value.

    Given a parent block containing `[0, MAX_BLOBS_PER_BLOCK]` blobs, test an invalid
    `excessBlobGas` value by changing it by `[-TARGET_BLOBS_PER_BLOCK, TARGET_BLOBS_PER_BLOCK]`
    from the correct value.
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "header_excess_blob_gas",
    [(2**64 + (x * Spec.GAS_PER_BLOB)) for x in range(-SpecHelpers.target_blobs_per_block(), 0)],
)
@pytest.mark.parametrize("parent_blobs", range(SpecHelpers.target_blobs_per_block()))
@pytest.mark.parametrize("new_blobs", [1])
@pytest.mark.parametrize("parent_excess_blobs", range(SpecHelpers.target_blobs_per_block()))
def test_invalid_negative_excess_blob_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas` changes to the two's
    complement equivalent of the negative value after subtracting target blobs.

    Reasoning is that the `excessBlobGas` is a `uint64`, so it cannot be negative, and
    we test for a potential underflow here.
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )


@pytest.mark.parametrize(
    "parent_blobs,header_excess_blob_gas_delta",
    [
        (SpecHelpers.target_blobs_per_block() + 1, 1),
        (SpecHelpers.target_blobs_per_block() + 1, Spec.GAS_PER_BLOB - 1),
        (SpecHelpers.target_blobs_per_block() - 1, -1),
        (SpecHelpers.target_blobs_per_block() - 1, -(Spec.GAS_PER_BLOB - 1)),
    ],
)
@pytest.mark.parametrize("new_blobs", [1])
@pytest.mark.parametrize("parent_excess_blobs", [SpecHelpers.target_blobs_per_block() + 1])
def test_invalid_non_multiple_excess_blob_gas(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    correct_excess_blob_gas: int,
    header_excess_blob_gas: Optional[int],
):
    """
    Test rejection of blocks where the `excessBlobGas` changes to a value that
    is not a multiple of Spec.GAS_PER_BLOB`:

    - Parent block contains `TARGET_BLOBS_PER_BLOCK + 1` blobs, but `excessBlobGas` is off by +/-1
    - Parent block contains `TARGET_BLOBS_PER_BLOCK - 1` blobs, but `excessBlobGas` is off by +/-1
    """
    if header_excess_blob_gas is None:
        raise Exception("test case is badly formatted")

    if header_excess_blob_gas == correct_excess_blob_gas:
        raise Exception("invalid test case")

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=env,
        tag="-".join(
            [
                f"correct:{hex(correct_excess_blob_gas)}",
                f"header:{hex(header_excess_blob_gas)}",
            ]
        ),
    )
