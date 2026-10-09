"""Tests for the activation of EIP-7999 at the fork transition."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Header,
    RecipientType,
    Transaction,
)

from .spec import Spec, ref_spec_7999

REFERENCE_SPEC_GIT_PATH = ref_spec_7999.git_path
REFERENCE_SPEC_VERSION = ref_spec_7999.version


def transfer_gas(fork: Fork) -> int:
    """Return the gas a value transfer to an existing EOA uses at `fork`."""
    return fork.transaction_intrinsic_cost_calculator()(
        sends_value=True, recipient_type=RecipientType.EOA
    )


@pytest.mark.valid_at_transition_to("EIP7999")
def test_transition_prices_from_parent_scalars(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: Address,
    recipient: Address,
) -> None:
    """
    The first block after the fork derives its excess gas from the
    parent's scalar base fee and excess blob gas, so the EVM base fee
    carries across the fork instead of resetting.
    """
    before = fork.transitions_from()
    after = fork.transitions_to()
    genesis_base_fee = 1000
    env = Environment(base_fee_per_gas=genesis_base_fee)
    gas_limit = int(env.gas_limit)

    # The last block before the fork, with one transfer.
    block_1_gas_used = transfer_gas(before)
    block_1_base_fee = before.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=genesis_base_fee,
        parent_gas_used=0,
        parent_gas_limit=gas_limit,
    )
    block_1_excess_blob_gas = before.excess_blob_gas_calculator()(
        parent_excess_blob_gas=0,
        parent_blob_gas_used=0,
        parent_base_fee_per_gas=genesis_base_fee,
    )

    # The first block after the fork lifts the parent's scalars.
    gas_limits = after.block_gas_limits_calculator()(gas_limit=gas_limit)
    parent_excess_gas = after.initial_excess_gas_calculator()(
        base_fee_per_gas=block_1_base_fee,
        excess_blob_gas=block_1_excess_blob_gas,
    )
    block_2_excess_gas = after.excess_gas_calculator()(
        parent_excess_gas=parent_excess_gas,
        parent_gas_used=[block_1_gas_used, 0, 0],
        parent_gas_limits=gas_limits,
    )
    block_2_base_fees = after.base_fees_calculator()(
        excess_gas=block_2_excess_gas
    )
    block_2_gas_used = transfer_gas(after)

    def transfer(gas: int) -> Transaction:
        return Transaction(
            sender=sender,
            to=recipient,
            value=1,
            gas_limit=gas,
            max_fee_per_gas=2 * genesis_base_fee,
            max_priority_fee_per_gas=0,
        )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={recipient: Account(balance=3)},
        blocks=[
            Block(
                timestamp=14_999,
                txs=[transfer(block_1_gas_used)],
                header_verify=Header(base_fee_per_gas=block_1_base_fee),
            ),
            Block(
                timestamp=15_000,
                txs=[transfer(block_2_gas_used)],
                header_verify=Header(
                    gas_limits=gas_limits,
                    gas_used_vector=[block_2_gas_used, 0, 0],
                    excess_gas=block_2_excess_gas,
                    base_fee_per_gas=block_2_base_fees[Spec.EVM_GAS],
                ),
            ),
        ],
    )
