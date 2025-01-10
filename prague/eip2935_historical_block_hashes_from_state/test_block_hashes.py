"""
abstract: Tests [EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935)
    Test [EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935).
"""  # noqa: E501

from typing import Dict, List

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Storage,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, ref_spec_2935

REFERENCE_SPEC_GIT_PATH = ref_spec_2935.git_path
REFERENCE_SPEC_VERSION = ref_spec_2935.version


def generate_block_check_code(
    check_block_number: int,
    current_block_number: int,
    fork_block_number: int,
    storage: Storage,
    check_contract_first: bool = False,
) -> Bytecode:
    """
    Generate EVM code to check that the block hashes are correctly stored in the state.

    Args:
        check_block_number (int): The block number to check.
        current_block_number (int): The current block number where the check is taking place.
        fork_block_number (int): The block number of the fork transition.
        storage (Storage): The storage object to use.
        check_contract_first (bool): Whether to check the contract first, for slot warming checks.

    """
    if check_block_number < 0:
        # Block number outside of range, nothing to check
        return Bytecode()

    populated_blockhash = (
        current_block_number - check_block_number <= Spec.BLOCKHASH_OLD_WINDOW
        and check_block_number < current_block_number
    )
    populated_history_storage_contract = (
        check_block_number >= fork_block_number - 1
        and current_block_number - check_block_number <= Spec.HISTORY_SERVE_WINDOW
        and check_block_number < current_block_number
    )

    blockhash_key = storage.store_next(not populated_blockhash)
    contract_key = storage.store_next(not populated_history_storage_contract)

    check_blockhash = Op.SSTORE(blockhash_key, Op.ISZERO(Op.BLOCKHASH(check_block_number)))
    check_contract = (
        Op.MSTORE(0, check_block_number)
        + Op.POP(Op.CALL(Op.GAS, Spec.HISTORY_STORAGE_ADDRESS, 0, 0, 32, 0, 32))
        + Op.SSTORE(contract_key, Op.ISZERO(Op.MLOAD(0)))
    )

    if check_contract_first:
        code = check_contract + check_blockhash
    else:
        code = check_blockhash + check_contract

    if populated_history_storage_contract and populated_blockhash:
        # Both values must be equal
        store_equal_key = storage.store_next(True)
        code += Op.SSTORE(store_equal_key, Op.EQ(Op.MLOAD(0), Op.BLOCKHASH(check_block_number)))

    return code


# TODO: Test at transition: `BLOCKHASH_OLD_WINDOW + 1` blocks before transition
# TODO: Test post fork: `HISTORY_SERVE_WINDOW` + 1 blocks after transition


@pytest.mark.parametrize(
    "blocks_before_fork, blocks_after_fork",
    [
        [1, 2],
        [Spec.BLOCKHASH_OLD_WINDOW + 1, 10],
        [1, Spec.BLOCKHASH_OLD_WINDOW + 1],
    ],
)
@pytest.mark.valid_at_transition_to("Prague")
def test_block_hashes_history_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks_before_fork: int,
    blocks_after_fork: int,
):
    """
    Tests that block hashes are stored correctly at the system contract address after the fork
    transition. Block hashes are stored incrementally at the transition until the
    `HISTORY_SERVE_WINDOW` ring buffer is full. Afterwards the oldest block hash is replaced by the
    new one.

    Note: The block hashes before the fork are no longer stored in the contract at the moment of
    the transition.
    """
    blocks: List[Block] = []
    assert blocks_before_fork >= 1 and blocks_before_fork < Spec.FORK_TIMESTAMP

    sender = pre.fund_eoa(10_000_000_000)
    post: Dict[Address, Account] = {}
    current_block_number = 1
    fork_block_number = current_block_number + blocks_before_fork

    for i in range(blocks_before_fork):
        txs: List[Transaction] = []
        if i == blocks_before_fork - 1:
            # On the last block before the fork, `BLOCKHASH` must return values for the last 256
            # blocks but not for the blocks before that.
            # And `HISTORY_STORAGE_ADDRESS` should be empty.
            code = Bytecode()
            storage = Storage()

            # Check the last block before blockhash the window
            code += generate_block_check_code(
                check_block_number=current_block_number - Spec.BLOCKHASH_OLD_WINDOW - 1,
                current_block_number=current_block_number,
                fork_block_number=fork_block_number,
                storage=storage,
            )

            # Check the first block inside blockhash the window
            code += generate_block_check_code(
                check_block_number=(
                    current_block_number - Spec.BLOCKHASH_OLD_WINDOW
                    if current_block_number > Spec.BLOCKHASH_OLD_WINDOW
                    else 0  # Entire chain is inside the window, check genesis
                ),
                current_block_number=current_block_number,
                fork_block_number=fork_block_number,
                storage=storage,
            )

            check_blocks_before_fork_address = pre.deploy_contract(code)
            txs.append(
                Transaction(
                    to=check_blocks_before_fork_address,
                    gas_limit=10_000_000,
                    sender=sender,
                )
            )
            post[check_blocks_before_fork_address] = Account(storage=storage)
        blocks.append(Block(timestamp=current_block_number, txs=txs))
        current_block_number += 1

    # Add blocks after the fork transition to gradually fill up the `HISTORY_SERVE_WINDOW`
    for i in range(blocks_after_fork):
        txs = []
        # On these blocks, `BLOCKHASH` will still return values for the last 256 blocks, and
        # `HISTORY_STORAGE_ADDRESS` should now serve values for the previous blocks in the new
        # fork.
        code = Bytecode()
        storage = Storage()

        # Check that each block can return previous blockhashes if `BLOCKHASH_OLD_WINDOW` and or
        # `HISTORY_SERVE_WINDOW`.
        for j in range(current_block_number):
            code += generate_block_check_code(
                check_block_number=j,
                current_block_number=current_block_number,
                fork_block_number=fork_block_number,
                storage=storage,
            )

        check_blocks_after_fork_address = pre.deploy_contract(code)
        txs.append(
            Transaction(
                to=check_blocks_after_fork_address,
                gas_limit=10_000_000,
                sender=sender,
            )
        )
        post[check_blocks_after_fork_address] = Account(storage=storage)

        blocks.append(Block(timestamp=Spec.FORK_TIMESTAMP + i, txs=txs))
        current_block_number += 1

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )


@pytest.mark.parametrize(
    "block_count,check_contract_first",
    [
        pytest.param(1, False, id="single_block_check_blockhash_first"),
        pytest.param(1, True, id="single_block_check_contract_first"),
        pytest.param(2, False, id="two_blocks_check_blockhash_first"),
        pytest.param(2, True, id="two_blocks_check_contract_first"),
        pytest.param(
            Spec.HISTORY_SERVE_WINDOW + 1,
            False,
            marks=pytest.mark.slow,
            id="full_history_plus_one_check_blockhash_first",
        ),
    ],
)
@pytest.mark.valid_from("Prague")
def test_block_hashes_history(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_count: int,
    check_contract_first: bool,
):
    """
    Tests that block hashes are stored correctly at the system contract address after the fork
    transition. Block hashes are stored incrementally at the transition until the
    `HISTORY_SERVE_WINDOW` ring buffer is full. Afterwards the oldest block hash is replaced by the
    new one.
    """
    blocks: List[Block] = []

    sender = pre.fund_eoa(10_000_000_000)
    post: Dict[Address, Account] = {}
    current_block_number = 1
    fork_block_number = 0  # We fork at genesis

    for _ in range(block_count - 1):
        # Generate empty blocks after the fork.
        blocks.append(Block())
        current_block_number += 1

    txs = []
    # On these blocks, `BLOCKHASH` will still return values for the last 256 blocks, and
    # `HISTORY_STORAGE_ADDRESS` should now serve values for the previous blocks in the new
    # fork.
    code = Bytecode()
    storage = Storage()

    # Check the first block outside of the window if any
    code += generate_block_check_code(
        check_block_number=current_block_number - Spec.HISTORY_SERVE_WINDOW - 1,
        current_block_number=current_block_number,
        fork_block_number=fork_block_number,
        storage=storage,
        check_contract_first=check_contract_first,
    )

    # Check the first block inside the window
    code += generate_block_check_code(
        check_block_number=current_block_number - Spec.HISTORY_SERVE_WINDOW,
        current_block_number=current_block_number,
        fork_block_number=fork_block_number,
        storage=storage,
        check_contract_first=check_contract_first,
    )

    # Check the first block outside the BLOCKHASH window
    code += generate_block_check_code(
        check_block_number=current_block_number - Spec.BLOCKHASH_OLD_WINDOW - 1,
        current_block_number=current_block_number,
        fork_block_number=fork_block_number,
        storage=storage,
        check_contract_first=check_contract_first,
    )

    # Check the first block inside the BLOCKHASH window
    code += generate_block_check_code(
        check_block_number=current_block_number - Spec.BLOCKHASH_OLD_WINDOW,
        current_block_number=current_block_number,
        fork_block_number=fork_block_number,
        storage=storage,
        check_contract_first=check_contract_first,
    )

    # Check the previous block
    code += generate_block_check_code(
        check_block_number=current_block_number - 1,
        current_block_number=current_block_number,
        fork_block_number=fork_block_number,
        storage=storage,
        check_contract_first=check_contract_first,
    )

    check_blocks_after_fork_address = pre.deploy_contract(code)
    txs.append(
        Transaction(
            to=check_blocks_after_fork_address,
            gas_limit=10_000_000,
            sender=sender,
        )
    )
    post[check_blocks_after_fork_address] = Account(storage=storage)

    blocks.append(Block(txs=txs))
    current_block_number += 1

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )


@pytest.mark.parametrize(
    "block_number,reverts",
    [
        pytest.param(1, True, id="current_block"),
        pytest.param(2, True, id="future_block"),
        pytest.param(2**64 - 1, True, id="2**64-1"),
        pytest.param(2**64, True, id="2**64"),
    ],
)
@pytest.mark.valid_from("Prague")
def test_invalid_history_contract_calls(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_number: int,
    reverts: bool,
):
    """
    Test calling the history contract with invalid block numbers, such as blocks from the future
    or overflowing block numbers.

    Also test the BLOCKHASH opcode with the same block numbers, which should not affect the
    behavior of the opcode, even after verkle.
    """
    storage = Storage()

    return_code_slot = storage.store_next(not reverts)
    returned_block_hash_slot = storage.store_next(0)
    block_hash_opcode_slot = storage.store_next(0)

    return_offset = 64
    return_size = 32
    args_size = 32

    # Check the first block outside of the window if any
    code = (
        Op.MSTORE(0, block_number)
        + Op.SSTORE(
            return_code_slot,
            Op.CALL(
                address=Spec.HISTORY_STORAGE_ADDRESS,
                args_offset=0,
                args_size=args_size,
                ret_offset=return_offset,
                ret_size=return_size,
            ),
        )
        + Op.SSTORE(returned_block_hash_slot, Op.MLOAD(return_offset))
        + Op.SSTORE(block_hash_opcode_slot, Op.BLOCKHASH(block_number))
    )
    check_contract_address = pre.deploy_contract(code, storage=storage.canary())

    txs = [
        Transaction(
            to=check_contract_address,
            gas_limit=10_000_000,
            sender=pre.fund_eoa(),
        )
    ]
    post = {check_contract_address: Account(storage=storage)}

    blocks = [Block(txs=txs)]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
        reverts=reverts,
    )


@pytest.mark.parametrize(
    "args_size,reverts",
    [
        pytest.param(0, True, id="zero_size"),
        pytest.param(33, True, id="too_large"),
        pytest.param(31, True, id="too_small"),
    ],
)
@pytest.mark.valid_from("Prague")
def test_invalid_history_contract_calls_input_size(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    reverts: bool,
    args_size: int,
):
    """Test calling the history contract with invalid input sizes."""
    storage = Storage()

    return_code_slot = storage.store_next(not reverts, "history storage call result")
    returned_block_hash_slot = storage.store_next(0)

    return_offset = 64
    return_size = 32
    block_number = 0

    # Check the first block outside of the window if any
    code = (
        Op.MSTORE(0, block_number)
        + Op.SSTORE(
            return_code_slot,
            Op.CALL(
                address=Spec.HISTORY_STORAGE_ADDRESS,
                args_offset=0,
                args_size=args_size,
                ret_offset=return_offset,
                ret_size=return_size,
            ),
        )
        + Op.SSTORE(returned_block_hash_slot, Op.MLOAD(return_offset))
    )
    check_contract_address = pre.deploy_contract(code, storage=storage.canary())

    txs = [
        Transaction(
            to=check_contract_address,
            gas_limit=10_000_000,
            sender=pre.fund_eoa(),
        )
    ]
    post = {check_contract_address: Account(storage=storage)}

    blocks = [Block(txs=txs)]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
        reverts=reverts,
    )
