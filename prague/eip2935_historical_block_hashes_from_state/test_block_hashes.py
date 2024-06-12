"""
abstract: Tests [EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935)
    Test [EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935)
"""  # noqa: E501

from typing import Dict, List

import pytest

from ethereum_test_tools import Account, Address, Alloc, Block, BlockchainTestFiller, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import Storage, Transaction

from .spec import Spec, ref_spec_2935

REFERENCE_SPEC_GIT_PATH = ref_spec_2935.git_path
REFERENCE_SPEC_VERSION = ref_spec_2935.version

FORK_TIMESTAMP = 15_000


def generate_block_check_code(
    block_number: int | None,
    populated_blockhash: bool,
    populated_contract: bool,
    storage: Storage,
    check_contract_first: bool = False,
) -> bytes:
    """
    Generate EVM code to check that the blockhashes are correctly stored in the state.

    Args:
        block_number (int | None): The block number to check (or None to return empty code).
        populated_blockhash (bool): Whether the blockhash should be populated.
        populated_contract (bool): Whether the contract should be populated.
        storage (Storage): The storage object to use.
        check_contract_first (bool): Whether to check the contract first, for slot warming checks.
    """
    if block_number is None:
        # No block number to check
        return b""

    blockhash_key = storage.store_next(not populated_blockhash)
    contract_key = storage.store_next(not populated_contract)

    check_blockhash = Op.SSTORE(blockhash_key, Op.ISZERO(Op.BLOCKHASH(block_number)))
    check_contract = (
        Op.MSTORE(0, block_number)
        + Op.POP(Op.CALL(Op.GAS, Spec.HISTORY_STORAGE_ADDRESS, 0, 0, 32, 0, 32))
        + Op.SSTORE(contract_key, Op.ISZERO(Op.MLOAD(0)))
    )

    if check_contract_first:
        code = check_contract + check_blockhash
    else:
        code = check_blockhash + check_contract

    if populated_contract and populated_blockhash:
        # Both values must be equal
        code += Op.SSTORE(storage.store_next(True), Op.EQ(Op.MLOAD(0), Op.BLOCKHASH(block_number)))

    return code


@pytest.mark.parametrize(
    "blocks_before_fork",
    [
        pytest.param(1, id="fork_at_1"),
        pytest.param(Spec.BLOCKHASH_OLD_WINDOW, id="fork_at_BLOCKHASH_OLD_WINDOW"),
        pytest.param(
            Spec.BLOCKHASH_OLD_WINDOW + 1,
            id="fork_at_BLOCKHASH_OLD_WINDOW_plus_1",
        ),
        pytest.param(
            Spec.BLOCKHASH_OLD_WINDOW + 2,
            id="fork_at_BLOCKHASH_OLD_WINDOW_plus_2",
        ),
        pytest.param(
            Spec.HISTORY_SERVE_WINDOW + 1,
            id="fork_at_HISTORY_SERVE_WINDOW_plus_1",
            marks=pytest.mark.skip("To be re-evaluated when updating the tests for new spec"),
        ),
    ],
)
@pytest.mark.valid_at_transition_to("Prague")
def test_block_hashes_history_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks_before_fork: int,
):
    """
    Test the fork transition and that the block hashes of previous blocks, even blocks
    before the fork, are included in the state at the moment of the transition.
    """
    # Fork happens at timestamp 15_000, and genesis counts as a block before fork.
    blocks: List[Block] = []
    assert blocks_before_fork >= 1 and blocks_before_fork < FORK_TIMESTAMP

    sender = pre.fund_eoa(10_000_000_000)
    post: Dict[Address, Account] = {}

    for i in range(1, blocks_before_fork):
        txs: List[Transaction] = []
        if i == blocks_before_fork - 1:
            # On the last block before the fork, BLOCKHASH must return values for the last 256
            # blocks but not for the blocks before that.
            # And HISTORY_STORAGE_ADDRESS should be empty.
            code = b""
            storage = Storage()

            # Check the last block before the window
            code += generate_block_check_code(
                block_number=(
                    i - Spec.BLOCKHASH_OLD_WINDOW - 1
                    if i > Spec.BLOCKHASH_OLD_WINDOW
                    else None  # Chain not long enough, no block to check
                ),
                populated_blockhash=False,
                populated_contract=False,
                storage=storage,
            )

            # Check the first block inside the window
            code += generate_block_check_code(
                block_number=(
                    i - Spec.BLOCKHASH_OLD_WINDOW
                    if i > Spec.BLOCKHASH_OLD_WINDOW
                    else 0  # Entire chain is inside the window, check genesis
                ),
                populated_blockhash=True,
                populated_contract=False,
                storage=storage,
            )

            code_address = pre.deploy_contract(code)
            txs.append(
                Transaction(
                    to=code_address,
                    gas_limit=10_000_000,
                    sender=sender,
                )
            )
            post[code_address] = Account(storage=storage)
        blocks.append(Block(timestamp=i, txs=txs))

    # Add the fork block
    current_block_number = len(blocks) + 1
    txs = []
    # On the block after the fork, BLOCKHASH must return values for the last
    # Spec.HISTORY_SERVE_WINDOW blocks.
    # And HISTORY_STORAGE_ADDRESS should be also serve the same values.
    code = b""
    storage = Storage()

    # Check the last block before the window
    code += generate_block_check_code(
        block_number=(
            current_block_number - Spec.HISTORY_SERVE_WINDOW - 1
            if current_block_number > Spec.HISTORY_SERVE_WINDOW
            else None  # Chain not long enough, no block to check
        ),
        populated_blockhash=False,
        populated_contract=False,
        storage=storage,
    )

    # Check the first block inside the window
    code += generate_block_check_code(
        block_number=(
            current_block_number - Spec.HISTORY_SERVE_WINDOW
            if current_block_number > Spec.HISTORY_SERVE_WINDOW
            else 0  # Entire chain is inside the window, check genesis
        ),
        populated_blockhash=True,
        populated_contract=True,
        storage=storage,
    )

    code_address = pre.deploy_contract(code)
    txs.append(
        Transaction(
            to=code_address,
            gas_limit=10_000_000,
            sender=sender,
        )
    )
    post[code_address] = Account(storage=storage)

    blocks.append(Block(timestamp=FORK_TIMESTAMP, txs=txs))

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        blocks=blocks,
        post=post,
    )
