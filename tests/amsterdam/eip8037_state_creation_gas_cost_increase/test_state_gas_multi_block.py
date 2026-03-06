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
    Op,
    Storage,
    Transaction,
)

from .spec import Spec, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

# Non-zero priority fee so coinbase balance depends on
# receipt_gas_used. Default base_fee_per_gas is 7.
PRIORITY_FEE = 2
MAX_FEE = 9  # base_fee(7) + PRIORITY_FEE(2)


@pytest.mark.valid_from("Amsterdam")
def test_exact_coinbase_fee_simple_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Assert exact coinbase balance from a single SSTORE transaction.

    Compute ``tx_gas_used`` from first principles and verify the
    reporter contract reads exactly ``tx_gas_used * priority_fee``
    as the coinbase balance. Any error in ``state_gas_left`` or
    ``refund_counter`` will produce a different coinbase balance,
    causing the state root to diverge.

    Gas breakdown for tx 1 (SSTORE zero-to-nonzero, no calldata)::

        intrinsic_regular = 21000  (GAS_TX_BASE)
        evm_regular       =  5006  (PUSH1 + PUSH1 + SSTORE_cold)
        state_gas         = 32 * cost_per_state_byte  (from reservoir)
        refund            = 0
        tx_gas_used       = 21000 + 5006 + state_gas = 26006 + state_gas

    Motivated by BAL devnet-3 ethrex/besu coinbase balance mismatch
    where clients diverged on cumulative ``receipt_gas_used``.
    """
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

    # Exact gas breakdown for tx 1:
    # PUSH1(1) + PUSH1(0) + SSTORE(cold, zero-to-nonzero) + STOP
    # Regular: 3 + 3 + (2100 cold + 2900 update) + 0 = 5006
    intrinsic_regular = 21000
    evm_regular = 5006
    tx1_gas_used = intrinsic_regular + evm_regular + sstore_state_gas
    expected_coinbase = tx1_gas_used * PRIORITY_FEE

    # Tx 1: single SSTORE zero-to-nonzero
    sstore_storage = Storage()
    sstore_contract = pre.deploy_contract(
        code=(
            Op.SSTORE(sstore_storage.store_next(1), 1)
            + Op.STOP
        ),
    )

    # Tx 2: reporter reads BALANCE(COINBASE) into slot 0
    reporter = pre.deploy_contract(
        code=(
            Op.SSTORE(0, Op.BALANCE(Op.COINBASE))
            + Op.SSTORE(1, 1)
            + Op.STOP
        ),
    )

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=sstore_contract,
                    gas_limit=(
                        Spec.TX_MAX_GAS_LIMIT
                        + sstore_state_gas
                    ),
                    max_priority_fee_per_gas=PRIORITY_FEE,
                    max_fee_per_gas=MAX_FEE,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter,
                    gas_limit=Spec.TX_MAX_GAS_LIMIT,
                    max_priority_fee_per_gas=PRIORITY_FEE,
                    max_fee_per_gas=MAX_FEE,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
    ]

    post = {
        sstore_contract: Account(storage=sstore_storage),
        reporter: Account(
            storage={0: expected_coinbase, 1: 1}
        ),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.valid_from("Amsterdam")
def test_multi_block_mixed_state_operations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify coinbase fee across blocks with diverse state operations.

    Block 1: Simple SSTORE transactions (state gas from reservoir).
    Block 2: Child spill + revert transactions (reservoir recovery).
    Block 3: Child spill + halt transactions (halt recovery).

    This mixed scenario tests that ``receipt_gas_used`` is consistent
    across different state gas paths within a multi-block chain.
    """
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

    reverting_child = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.SSTORE(1, 1)
            + Op.REVERT(0, 0)
        ),
    )
    halting_child = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.SSTORE(1, 1)
            + Op.INVALID
        ),
    )

    all_contracts = []
    all_storages = []

    # --- Block 1: simple SSTOREs from reservoir ---
    block1_txs = []
    for _ in range(2):
        storage = Storage()
        contract = pre.deploy_contract(
            code=(
                Op.SSTORE(storage.store_next(1), 1)
                + Op.STOP
            ),
        )
        all_contracts.append(contract)
        all_storages.append(storage)
        block1_txs.append(
            Transaction(
                to=contract,
                gas_limit=(
                    Spec.TX_MAX_GAS_LIMIT
                    + sstore_state_gas
                ),
                max_priority_fee_per_gas=PRIORITY_FEE,
                max_fee_per_gas=MAX_FEE,
                sender=pre.fund_eoa(),
            )
        )

    # --- Block 2: child spill + revert ---
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
                + Op.STOP
            ),
        )
        all_contracts.append(parent)
        all_storages.append(storage)
        block2_txs.append(
            Transaction(
                to=parent,
                gas_limit=(
                    Spec.TX_MAX_GAS_LIMIT
                    + sstore_state_gas
                ),
                max_priority_fee_per_gas=PRIORITY_FEE,
                max_fee_per_gas=MAX_FEE,
                sender=pre.fund_eoa(),
            )
        )

    # --- Block 3: child spill + exceptional halt ---
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
                + Op.STOP
            ),
        )
        all_contracts.append(parent)
        all_storages.append(storage)
        block3_txs.append(
            Transaction(
                to=parent,
                gas_limit=(
                    Spec.TX_MAX_GAS_LIMIT
                    + sstore_state_gas
                ),
                max_priority_fee_per_gas=PRIORITY_FEE,
                max_fee_per_gas=MAX_FEE,
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
        for c, s in zip(all_contracts, all_storages)
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.valid_from("Amsterdam")
def test_multi_block_observed_coinbase_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Observe coinbase balance between state-creating transactions.

    A reporter contract reads ``BALANCE(COINBASE)`` and stores a flag
    indicating whether the coinbase has received fees. This makes
    ``receipt_gas_used`` directly observable: if a client computes a
    different ``receipt_gas_used`` for prior transactions, the stored
    balance observation will differ and the state root will not match.

    Block 1:
      Tx 1 -- SSTORE zero-to-nonzero (coinbase earns fee).
      Tx 2 -- Store ``BALANCE(COINBASE)`` in slot 0; store 1 in
      slot 1 as success marker.

    Block 2:
      Tx 3 -- Child spills state gas then reverts; parent SSTOREs
      (coinbase earns fee through different code path).
      Tx 4 -- Store ``BALANCE(COINBASE)`` in slot 0; store 1 in
      slot 1 as success marker.
    """
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

    # Reporters store BALANCE(COINBASE) in slot 0 and a marker
    # in slot 1. The exact slot 0 value is validated by the state
    # root; the marker confirms execution completed.
    reporter1 = pre.deploy_contract(
        code=(
            Op.SSTORE(0, Op.BALANCE(Op.COINBASE))
            + Op.SSTORE(1, 1)
            + Op.STOP
        ),
    )
    reporter2 = pre.deploy_contract(
        code=(
            Op.SSTORE(0, Op.BALANCE(Op.COINBASE))
            + Op.SSTORE(1, 1)
            + Op.STOP
        ),
    )

    # Block 1 tx 1: simple SSTORE
    sstore_storage = Storage()
    sstore_contract = pre.deploy_contract(
        code=(
            Op.SSTORE(sstore_storage.store_next(1), 1)
            + Op.STOP
        ),
    )

    # Block 2 tx 3: child spill + revert, parent SSTORE
    reverting_child = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.SSTORE(1, 1)
            + Op.REVERT(0, 0)
        ),
    )
    spill_storage = Storage()
    spill_parent = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=500_000, address=reverting_child
                )
            )
            + Op.SSTORE(spill_storage.store_next(1), 1)
            + Op.STOP
        ),
    )

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=sstore_contract,
                    gas_limit=(
                        Spec.TX_MAX_GAS_LIMIT
                        + sstore_state_gas
                    ),
                    max_priority_fee_per_gas=PRIORITY_FEE,
                    max_fee_per_gas=MAX_FEE,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter1,
                    gas_limit=Spec.TX_MAX_GAS_LIMIT,
                    max_priority_fee_per_gas=PRIORITY_FEE,
                    max_fee_per_gas=MAX_FEE,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
        Block(
            txs=[
                Transaction(
                    to=spill_parent,
                    gas_limit=(
                        Spec.TX_MAX_GAS_LIMIT
                        + sstore_state_gas
                    ),
                    max_priority_fee_per_gas=PRIORITY_FEE,
                    max_fee_per_gas=MAX_FEE,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter2,
                    gas_limit=Spec.TX_MAX_GAS_LIMIT,
                    max_priority_fee_per_gas=PRIORITY_FEE,
                    max_fee_per_gas=MAX_FEE,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
    ]

    post = {
        sstore_contract: Account(storage=sstore_storage),
        spill_parent: Account(storage=spill_storage),
        # Only check the success marker. Slot 0 (coinbase
        # balance) is validated by the state root.
        reporter1: Account(storage={1: 1}),
        reporter2: Account(storage={1: 1}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
