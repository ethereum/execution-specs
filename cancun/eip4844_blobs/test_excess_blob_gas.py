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
from typing import Callable, Dict, Iterator, List, Mapping, Optional, Tuple

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Environment,
    Hash,
    Header,
    Transaction,
    add_kzg_version,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, SpecHelpers, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

# All tests run from Cancun fork
pytestmark = pytest.mark.valid_from("Cancun")


@pytest.fixture
def parent_excess_blobs(fork: Fork) -> int:  # noqa: D103
    """By default we start with an intermediate value between the target and max."""
    return (fork.max_blobs_per_block() + fork.target_blobs_per_block()) // 2 + 1


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
    blob_gas_per_blob: int,
) -> Optional[int]:
    if header_excess_blobs_delta is not None:
        modified_excess_blob_gas = correct_excess_blob_gas + (
            header_excess_blobs_delta * blob_gas_per_blob
        )
        if modified_excess_blob_gas < 0:
            modified_excess_blob_gas = 2**64 + (modified_excess_blob_gas)
        return modified_excess_blob_gas
    if header_excess_blob_gas_delta is not None:
        return correct_excess_blob_gas + header_excess_blob_gas_delta
    return None


@pytest.fixture
def tx_blob_data_cost(  # noqa: D103
    tx_max_fee_per_blob_gas: int,
    new_blobs: int,
    blob_gas_per_blob: int,
) -> int:
    return tx_max_fee_per_blob_gas * blob_gas_per_blob * new_blobs


@pytest.fixture
def tx_gas_limit() -> int:  # noqa: D103
    return 45000


@pytest.fixture
def tx_exact_cost(  # noqa: D103
    tx_value: int, tx_max_fee_per_gas: int, tx_blob_data_cost: int, tx_gas_limit: int
) -> int:
    return (tx_gas_limit * tx_max_fee_per_gas) + tx_value + tx_blob_data_cost


@pytest.fixture
def destination_account_bytecode() -> Bytecode:  # noqa: D103
    # Verify that the BLOBBASEFEE opcode reflects the current blob gas cost
    return Op.SSTORE(0, Op.BLOBBASEFEE)


@pytest.fixture
def destination_account(  # noqa: D103
    pre: Alloc,
    destination_account_bytecode: Bytecode,
) -> Address:
    return pre.deploy_contract(destination_account_bytecode)


@pytest.fixture
def sender(pre: Alloc, tx_exact_cost: int) -> Address:  # noqa: D103
    return pre.fund_eoa(tx_exact_cost)


@pytest.fixture
def post(  # noqa: D103
    destination_account: Address, tx_value: int, blob_gas_price: int
) -> Mapping[Address, Account]:
    return {
        destination_account: Account(
            storage={0: blob_gas_price},
            balance=tx_value,
        ),
    }


@pytest.fixture
def tx(  # noqa: D103
    sender: EOA,
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
            sender=sender,
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
            sender=sender,
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
    blob_gas_per_blob: int,
) -> int:
    return Spec.get_total_blob_gas(tx=tx, blob_gas_per_blob=blob_gas_per_blob)


@pytest.fixture
def blocks(  # noqa: D103
    tx: Transaction,
    header_excess_blob_gas: Optional[int],
    header_blob_gas_used: Optional[int],
    correct_excess_blob_gas: int,
    correct_blob_gas_used: int,
    non_zero_blob_gas_used_genesis_block: Block,
    max_blobs_per_block: int,
    blob_gas_per_blob: int,
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
        """Add a block to the blocks list."""
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
        if header_blob_gas_used > (max_blobs_per_block * blob_gas_per_blob):
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


@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: range(0, fork.max_blobs_per_block() + 1),
)
@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs",
    lambda fork: range(0, fork.target_blobs_per_block() + 1),
)
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
    multiple blocks with and without blobs.

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


def generate_blob_gas_cost_increases_tests(delta: int) -> Callable[[Fork], List[int]]:
    """
    Generate a list of block excess blob gas values where the blob gas price increases
    based on fork properties.
    """

    def generator_function(fork: Fork) -> List[int]:
        gas_per_blob = fork.blob_gas_per_blob()
        return [
            SpecHelpers.get_min_excess_blobs_for_blob_gas_price(
                fork=fork, blob_gas_price=blob_gas_price
            )
            + delta
            for blob_gas_price in [
                2,  # First blob gas cost increase
                2**32 // gas_per_blob,  # Data tx wei cost 2^32
                2**32,  # blob gas cost 2^32
                2**64 // gas_per_blob,  # Data tx wei cost 2^64
                2**64,  # blob gas cost 2^64
                (
                    120_000_000 * (10**18) // gas_per_blob
                ),  # Data tx wei is current total Ether supply
            ]
        ]

    return generator_function


@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs",
    generate_blob_gas_cost_increases_tests(-1),
)
@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: [fork.target_blobs_per_block() + 1],
)
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
    value points where the cost increases to interesting amounts.

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


@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs",
    generate_blob_gas_cost_increases_tests(0),
)
@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: [fork.target_blobs_per_block() - 1],
)
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
@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: range(0, fork.max_blobs_per_block() + 1),
)
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


def all_invalid_blob_gas_used_combinations(fork: Fork) -> Iterator[Tuple[int, int]]:
    """Return all invalid blob gas used combinations."""
    gas_per_blob = fork.blob_gas_per_blob()
    for new_blobs in range(0, fork.max_blobs_per_block() + 1):
        for header_blob_gas_used in range(0, fork.max_blobs_per_block() + 1):
            if new_blobs != header_blob_gas_used:
                yield (new_blobs, header_blob_gas_used * gas_per_blob)
        yield (new_blobs, 2**64 - 1)


@pytest.mark.parametrize_by_fork(
    "new_blobs,header_blob_gas_used",
    all_invalid_blob_gas_used_combinations,
)
@pytest.mark.parametrize("parent_blobs", [0])
def test_invalid_blob_gas_used_in_header(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Mapping[Address, Account],
    blocks: List[Block],
    new_blobs: int,
    header_blob_gas_used: Optional[int],
    blob_gas_per_blob: int,
):
    """
    Test rejection of blocks where the `blobGasUsed` in the header is invalid.

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
                f"correct:{hex(new_blobs * blob_gas_per_blob)}",
                f"header:{hex(header_blob_gas_used)}",
            ]
        ),
    )


def generate_invalid_excess_blob_gas_above_target_change_tests(fork: Fork) -> List:
    """Return all invalid excess blob gas above target change tests."""
    return [
        pytest.param(-1, 0, id="zero_blobs_decrease_more_than_expected"),
        pytest.param(+1, fork.max_blobs_per_block(), id="max_blobs_increase_more_than_expected"),
    ]


@pytest.mark.parametrize_by_fork(
    "header_excess_blobs_delta,parent_blobs",
    generate_invalid_excess_blob_gas_above_target_change_tests,
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
    Test rejection of blocks where the `excessBlobGas`.

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


@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: [
        b for b in range(0, fork.max_blobs_per_block() + 1) if b != fork.target_blobs_per_block()
    ],
)
@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs", lambda fork: [1, fork.target_blobs_per_block()]
)
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


@pytest.mark.parametrize_by_fork(
    "header_excess_blobs_delta",
    lambda fork: range(1, fork.max_blobs_per_block()),
)
@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: range(0, fork.target_blobs_per_block() + 1),
)
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
@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: range(fork.target_blobs_per_block() + 1, fork.max_blobs_per_block() + 1),
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


@pytest.mark.parametrize_by_fork(
    "parent_blobs,header_excess_blobs_delta",
    lambda fork: itertools.product(
        # parent_blobs
        range(0, fork.max_blobs_per_block() + 1),
        # header_excess_blobs_delta (from correct value)
        [
            x
            for x in range(-fork.target_blobs_per_block(), fork.target_blobs_per_block() + 1)
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


@pytest.mark.parametrize_by_fork(
    "header_excess_blob_gas",
    lambda fork: [
        (2**64 + (x * fork.blob_gas_per_blob())) for x in range(-fork.target_blobs_per_block(), 0)
    ],
)
@pytest.mark.parametrize_by_fork(
    "parent_blobs",
    lambda fork: range(fork.target_blobs_per_block()),
)
@pytest.mark.parametrize("new_blobs", [1])
@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs",
    lambda fork: range(fork.target_blobs_per_block()),
)
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


@pytest.mark.parametrize_by_fork(
    "parent_blobs,header_excess_blob_gas_delta",
    lambda fork: [
        (fork.target_blobs_per_block() + 1, 1),
        (fork.target_blobs_per_block() + 1, fork.blob_gas_per_blob() - 1),
        (fork.target_blobs_per_block() - 1, -1),
        (fork.target_blobs_per_block() - 1, -(fork.blob_gas_per_blob() - 1)),
    ],
)
@pytest.mark.parametrize("new_blobs", [1])
@pytest.mark.parametrize_by_fork(
    "parent_excess_blobs",
    lambda fork: [fork.target_blobs_per_block() + 1],
)
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
    is not a multiple of Spec.GAS_PER_BLOB`.

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
