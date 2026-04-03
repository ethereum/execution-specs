"""
Multi-block tests for EIP-8037 state gas receipt accounting and
coinbase fee accumulation.

Verify that `receipt_gas_used` is computed correctly across multiple
blocks under two-dimensional gas accounting. These tests exercise:

- Receipt gas accounting over multi-block sequences with diverse
  state gas paths (reservoir, spill+revert, spill+halt)
- Observable coinbase balance between state-creating transactions

Any disagreement in `receipt_gas_used` between clients causes the
coinbase balance to diverge, producing a different state root.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Op,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("Amsterdam")
def test_exact_coinbase_fee_simple_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Assert exact coinbase balance from a single SSTORE transaction.

    Compute `tx_gas_used` from first principles and verify the
    reporter contract reads exactly `tx_gas_used` as the coinbase
    balance (priority fee is 1 wei). Any error in `state_gas_left` or
    `refund_counter` will produce a different coinbase balance,
    causing the state root to diverge.

    Motivated by BAL devnet-3 ethrex/besu coinbase balance mismatch
    where clients diverged on cumulative `receipt_gas_used`.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    # Gas breakdown for tx 1 (SSTORE zero-to-nonzero, no calldata):
    # PUSH1(1) + PUSH1(0) + SSTORE(cold, zero-to-nonzero) + STOP
    intrinsic_regular = gas_costs.GAS_TX_BASE
    evm_regular = (
        2 * gas_costs.GAS_VERY_LOW  # PUSH1 + PUSH1
        + gas_costs.GAS_COLD_STORAGE_WRITE  # SSTORE cold zero-to-nonzero
    )
    tx1_gas_used = intrinsic_regular + evm_regular + sstore_state_gas
    expected_coinbase = tx1_gas_used

    # Tx 1: single SSTORE zero-to-nonzero
    sstore_storage = Storage()
    sstore_contract = pre.deploy_contract(
        code=(Op.SSTORE(sstore_storage.store_next(1), 1)),
    )

    # Tx 2: reporter reads BALANCE(COINBASE) into slot 0
    reporter = pre.deploy_contract(
        code=(Op.SSTORE(0, Op.BALANCE(Op.COINBASE)) + Op.SSTORE(1, 1)),
    )

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=sstore_contract,
                    gas_limit=(gas_limit_cap + sstore_state_gas),
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter,
                    gas_limit=gas_limit_cap,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
    ]

    post = {
        sstore_contract: Account(storage=sstore_storage),
        reporter: Account(storage={0: expected_coinbase, 1: 1}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.valid_from("Amsterdam")
def test_multi_block_mixed_state_operations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify coinbase fee across blocks with diverse state operations.

    Block 1: Simple SSTORE transactions (state gas from reservoir).
    Block 2: Child spill + revert transactions (reservoir recovery).
    Block 3: Child spill + halt transactions (halt recovery).

    This mixed scenario tests that `receipt_gas_used` is consistent
    across different state gas paths within a multi-block chain.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    reverting_child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)),
    )
    halting_child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.INVALID),
    )

    all_contracts = []
    all_storages = []

    # Simple SSTOREs from reservoir
    block1_txs = []
    for _ in range(2):
        storage = Storage()
        contract = pre.deploy_contract(
            code=(Op.SSTORE(storage.store_next(1), 1)),
        )
        all_contracts.append(contract)
        all_storages.append(storage)
        block1_txs.append(
            Transaction(
                to=contract,
                gas_limit=(gas_limit_cap + sstore_state_gas),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
                sender=pre.fund_eoa(),
            )
        )

    # Child spill + revert
    block2_txs = []
    for _ in range(2):
        storage = Storage()
        parent = pre.deploy_contract(
            code=(
                Op.POP(
                    Op.CALL(
                        gas=500_000,
                        address=reverting_child,
                    )
                )
                + Op.SSTORE(storage.store_next(1), 1)
            ),
        )
        all_contracts.append(parent)
        all_storages.append(storage)
        block2_txs.append(
            Transaction(
                to=parent,
                gas_limit=(gas_limit_cap + sstore_state_gas),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
                sender=pre.fund_eoa(),
            )
        )

    # Child spill + exceptional halt
    block3_txs = []
    for _ in range(2):
        storage = Storage()
        parent = pre.deploy_contract(
            code=(
                Op.POP(
                    Op.CALL(
                        gas=500_000,
                        address=halting_child,
                    )
                )
                + Op.SSTORE(storage.store_next(1), 1)
            ),
        )
        all_contracts.append(parent)
        all_storages.append(storage)
        block3_txs.append(
            Transaction(
                to=parent,
                gas_limit=(gas_limit_cap + sstore_state_gas),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
                sender=pre.fund_eoa(),
            )
        )

    blocks = [
        Block(txs=block1_txs),
        Block(txs=block2_txs),
        Block(txs=block3_txs),
    ]
    post = {
        c: Account(storage=s)
        for c, s in zip(all_contracts, all_storages, strict=False)
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.valid_from("Amsterdam")
def test_multi_block_observed_coinbase_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Observe coinbase balance between state-creating transactions.

    A reporter contract reads `BALANCE(COINBASE)` and stores it.
    This makes `receipt_gas_used` directly observable: if a client
    computes a different `receipt_gas_used` for prior transactions,
    the stored balance will differ and the state root will not match.

    Block 1:
      Tx 1: SSTORE zero-to-nonzero (coinbase earns fee).
      Tx 2: Store `BALANCE(COINBASE)` in slot 0.

    Block 2:
      Tx 3: Child spills state gas then reverts; parent SSTOREs
      (coinbase earns fee through different code path).
      Tx 4: Store `BALANCE(COINBASE)` in slot 0.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    reporter1 = pre.deploy_contract(
        code=(Op.SSTORE(0, Op.BALANCE(Op.COINBASE))),
    )
    reporter2 = pre.deploy_contract(
        code=(Op.SSTORE(0, Op.BALANCE(Op.COINBASE))),
    )

    # Block 1 tx 1: simple SSTORE
    sstore_storage = Storage()
    sstore_contract = pre.deploy_contract(
        code=(Op.SSTORE(sstore_storage.store_next(1), 1)),
    )

    # Block 2 tx 3: child spill + revert, parent SSTORE
    reverting_child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)),
    )
    spill_storage = Storage()
    spill_parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=500_000, address=reverting_child))
            + Op.SSTORE(spill_storage.store_next(1), 1)
        ),
    )

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=sstore_contract,
                    gas_limit=(gas_limit_cap + sstore_state_gas),
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter1,
                    gas_limit=gas_limit_cap,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
        Block(
            txs=[
                Transaction(
                    to=spill_parent,
                    gas_limit=(gas_limit_cap + sstore_state_gas),
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter2,
                    gas_limit=gas_limit_cap,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
    ]

    post = {
        sstore_contract: Account(storage=sstore_storage),
        spill_parent: Account(storage=spill_storage),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
