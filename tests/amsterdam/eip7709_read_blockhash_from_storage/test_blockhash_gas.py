"""
Tests [EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).

Test the gas cost changes for the BLOCKHASH opcode: the base opcode cost
is always charged, and valid in-range accesses additionally charge cold
or warm history-slot access gas.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    CodeGasMeasure,
    Fork,
    Op,
    Transaction,
)

from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def blockhash_cost(fork: Fork, access_cost: int = 0) -> int:
    """Return the expected BLOCKHASH gas cost for the current fork."""
    return Op.BLOCKHASH.gas_cost(fork) + access_cost


def test_blockhash_cold_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that the first valid in-range BLOCKHASH access charges the base
    opcode cost plus the cold history-slot access cost.
    """
    code = CodeGasMeasure(
        code=Op.BLOCKHASH(0),
        extra_stack_items=1,
        overhead_cost=Op.PUSH1.gas_cost(fork),
        sstore_key=0,
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [
        Block(),
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        ),
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(
            storage={
                0: blockhash_cost(
                    fork,
                    Spec.GAS_COLD_STORAGE_ACCESS,
                )
            }
        ),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_warm_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a repeated BLOCKHASH for the same valid block number
    charges the base opcode cost plus the warm access cost.
    """
    code = Op.POP(Op.BLOCKHASH(0)) + CodeGasMeasure(
        code=Op.BLOCKHASH(0),
        extra_stack_items=1,
        overhead_cost=Op.PUSH1.gas_cost(fork),
        sstore_key=0,
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [
        Block(),
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        ),
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(
            storage={
                0: blockhash_cost(
                    fork,
                    Spec.GAS_WARM_ACCESS,
                )
            }
        ),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_different_blocks_both_cold(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a prior BLOCKHASH(0) does not warm the history slot used
    by BLOCKHASH(1), so the measured BLOCKHASH(1) access pays the cold
    access cost.
    """
    code = Op.POP(Op.BLOCKHASH(0)) + CodeGasMeasure(
        code=Op.BLOCKHASH(1),
        extra_stack_items=1,
        overhead_cost=Op.PUSH1.gas_cost(fork),
        sstore_key=0,
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [
        Block(),
        Block(),
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        ),
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(
            storage={
                0: blockhash_cost(
                    fork,
                    Spec.GAS_COLD_STORAGE_ACCESS,
                )
            }
        ),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_out_of_range_charges_base_only(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a future out-of-range BLOCKHASH charges only the base
    opcode cost and does not charge any history-slot access gas.
    """
    code = CodeGasMeasure(
        code=Op.BLOCKHASH(0xFFFFFF),
        extra_stack_items=1,
        overhead_cost=Op.PUSH1.gas_cost(fork),
        sstore_key=0,
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        ),
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(storage={0: blockhash_cost(fork)}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.slow()
def test_blockhash_too_old_but_available_in_history_charges_base_only(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a BLOCKHASH query older than 256 blocks charges only the
    base opcode cost, even when EIP-2935 still serves the hash.
    """
    query_block = 1

    code = CodeGasMeasure(
        code=Op.BLOCKHASH(query_block),
        extra_stack_items=1,
        overhead_cost=Op.PUSH1.gas_cost(fork),
        sstore_key=0,
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [Block() for _ in range(Spec.BLOCKHASH_SERVE_WINDOW + 1)]
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        )
    )

    post: Dict[Address, Account] = {
        contract_address: Account(storage={0: blockhash_cost(fork)}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_warm_via_prior_history_call(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a prior STATICCALL to the history storage contract warms
    the storage slot, making a subsequent BLOCKHASH for the same block
    number charge the warm access cost instead of the cold one.
    """
    query_block = 1

    code = (
        Op.MSTORE(0, query_block)
        + Op.POP(
            Op.STATICCALL(
                Op.GAS,
                Spec.HISTORY_STORAGE_ADDRESS,
                0,
                32,
                32,
                32,
            )
        )
        + CodeGasMeasure(
            code=Op.BLOCKHASH(query_block),
            extra_stack_items=1,
            overhead_cost=Op.PUSH1.gas_cost(fork),
            sstore_key=0,
        )
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [
        Block(),
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        ),
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(
            storage={
                0: blockhash_cost(
                    fork,
                    Spec.GAS_WARM_ACCESS,
                )
            }
        ),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_out_of_range_does_not_warm_aliased_slot(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a future out-of-range BLOCKHASH does not warm the aliased
    history slot for a later valid query.
    """
    # 8192 and 1 alias to the same history slot because 8192 % 8191 == 1.
    code = Op.POP(Op.BLOCKHASH(8192)) + CodeGasMeasure(
        code=Op.BLOCKHASH(1),
        extra_stack_items=1,
        overhead_cost=Op.PUSH1.gas_cost(fork),
        sstore_key=0,
    )

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [
        Block(),
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        ),
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(
            storage={
                0: blockhash_cost(
                    fork,
                    Spec.GAS_COLD_STORAGE_ACCESS,
                )
            }
        ),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
