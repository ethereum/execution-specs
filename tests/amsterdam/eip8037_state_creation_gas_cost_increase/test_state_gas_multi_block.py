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
    Environment,
    Fork,
    Op,
    Storage,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
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
    # Tx 1: single SSTORE zero-to-nonzero
    sstore_storage = Storage()
    sstore_code = Op.SSTORE(sstore_storage.store_next(1), 1, new_value=1)
    sstore_state_gas = sstore_code.state_cost(fork)
    sstore_contract = pre.deploy_contract(code=sstore_code)

    # tx 1 gas used: the intrinsic (TX_BASE plus the EIP-2780
    # recipient-access charge) plus the SSTORE code's own execution and
    # state cost.
    tx1_gas_used = (
        fork.transaction_intrinsic_cost_calculator()()
        + sstore_code.gas_cost(fork)
    )
    expected_coinbase = tx1_gas_used

    # Tx 2: reporter reads BALANCE(COINBASE) into slot 0
    reporter = pre.deploy_contract(
        code=(Op.SSTORE(0, Op.BALANCE(Op.COINBASE)) + Op.SSTORE(1, 1)),
    )

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=sstore_contract,
                    state_gas_reservoir=sstore_state_gas,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter,
                    state_gas_reservoir=0,
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


@pytest.mark.valid_from("EIP8037")
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
    Every receipt pins its cumulative gas, so a mis-credited spill
    on any path breaks the fill.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    priority_fee = 1
    child_gas = 500_000

    reverting_child_code = Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)
    reverting_child = pre.deploy_contract(code=reverting_child_code)

    halting_child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.INVALID),
    )
    # Every transaction spends its whole bill on gas, and the coinbase
    # takes `priority_fee` per unit of it.
    block_gas_used = [0, 0, 0]

    all_contracts = []
    all_storages = []

    # Simple SSTOREs from reservoir
    block1_txs = []
    for i in range(2):
        storage = Storage()
        contract_code = Op.SSTORE(storage.store_next(1), 1)
        contract = pre.deploy_contract(code=contract_code)
        tx_gas_used = intrinsic_gas + contract_code.gas_cost(fork)
        block_gas_used[0] += tx_gas_used
        all_contracts.append(contract)
        all_storages.append(storage)
        block1_txs.append(
            Transaction(
                to=contract,
                state_gas_reservoir=contract_code.state_cost(fork),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
                sender=pre.fund_eoa(),
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=(i + 1) * tx_gas_used,
                ),
            )
        )

    # Child spill + revert
    block2_txs = []
    for i in range(2):
        storage = Storage()
        parent_code = Op.POP(
            Op.CALL(gas=child_gas, address=reverting_child)
        ) + Op.SSTORE(storage.store_next(1), 1)
        parent = pre.deploy_contract(code=parent_code)
        # The reverted child refunds its state gas and returns its
        # unspent budget, so only its execution gas is consumed.
        tx_gas_used = (
            intrinsic_gas
            + parent_code.gas_cost(fork)
            + reverting_child_code.execution_cost(fork)
        )
        block_gas_used[1] += tx_gas_used
        all_contracts.append(parent)
        all_storages.append(storage)
        block2_txs.append(
            Transaction(
                to=parent,
                state_gas_reservoir=parent_code.state_cost(fork),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
                sender=pre.fund_eoa(),
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=(i + 1) * tx_gas_used,
                ),
            )
        )

    # Child spill + exceptional halt
    block3_txs = []
    for i in range(2):
        storage = Storage()
        parent_code = Op.POP(
            Op.CALL(gas=child_gas, address=halting_child)
        ) + Op.SSTORE(storage.store_next(1), 1)
        parent = pre.deploy_contract(code=parent_code)
        # The halted child burns its whole budget, spill included.
        tx_gas_used = intrinsic_gas + parent_code.gas_cost(fork) + child_gas
        block_gas_used[2] += tx_gas_used
        all_contracts.append(parent)
        all_storages.append(storage)
        block3_txs.append(
            Transaction(
                to=parent,
                state_gas_reservoir=sstore_state_gas,
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
                sender=pre.fund_eoa(),
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=(i + 1) * tx_gas_used,
                ),
            )
        )

    blocks = [
        Block(txs=block1_txs),
        Block(txs=block2_txs),
        Block(txs=block3_txs),
    ]
    post: dict = {
        c: Account(storage=s)
        for c, s in zip(all_contracts, all_storages, strict=False)
    }
    fee_recipient = Environment().fee_recipient
    post[fee_recipient] = Account(balance=sum(block_gas_used) * priority_fee)
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    priority_fee = 1
    child_gas = 500_000

    reporter_code = Op.SSTORE(0, Op.BALANCE(Op.COINBASE, address_warm=True))
    reporter1 = pre.deploy_contract(code=reporter_code)
    reporter2 = pre.deploy_contract(code=reporter_code)
    reporter_gas = intrinsic_gas + reporter_code.gas_cost(fork)

    # Block 1 tx 1: simple SSTORE
    sstore_storage = Storage()
    sstore_code = Op.SSTORE(sstore_storage.store_next(1), 1)
    sstore_contract = pre.deploy_contract(code=sstore_code)
    sstore_tx_gas = (
        intrinsic_gas + sstore_code.execution_cost(fork) + sstore_state_gas
    )

    # Block 2 tx 3: child spill + revert, parent SSTORE
    reverting_child_code = Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)
    reverting_child = pre.deploy_contract(code=reverting_child_code)
    spill_storage = Storage()
    spill_code = Op.POP(
        Op.CALL(gas=child_gas, address=reverting_child)
    ) + Op.SSTORE(spill_storage.store_next(1), 1)
    spill_parent = pre.deploy_contract(code=spill_code)

    spill_tx_gas = (
        intrinsic_gas
        + spill_code.gas_cost(fork)
        + reverting_child_code.execution_cost(fork)
    )

    reporter1_observes = sstore_tx_gas * priority_fee
    reporter2_observes = (
        sstore_tx_gas + reporter_gas + spill_tx_gas
    ) * priority_fee

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=sstore_contract,
                    state_gas_reservoir=sstore_state_gas,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter1,
                    state_gas_reservoir=0,
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
                    state_gas_reservoir=sstore_state_gas,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter2,
                    state_gas_reservoir=0,
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
        reporter1: Account(storage={0: reporter1_observes}),
        reporter2: Account(storage={0: reporter2_observes}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
