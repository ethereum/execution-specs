"""
Fork-transition tests for
[EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    CodeGasMeasure,
    EIPChecklist,
    Fork,
    Op,
    Transaction,
)

from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_at_transition_to("EIP7709")

BEFORE_TS = Spec.FORK_TIMESTAMP - 1
AFTER_TS = Spec.FORK_TIMESTAMP


def _measure_blockhash_for_regime(
    arg: int,
    regime: Fork,
    *,
    sstore_key: int,
) -> CodeGasMeasure:
    """
    Build a ``CodeGasMeasure`` around ``Op.BLOCKHASH(arg)`` whose stored
    result at ``sstore_key`` is the bare ``BLOCKHASH`` opcode cost under
    ``regime``.
    """
    measured = Op.BLOCKHASH(arg)
    overhead = measured.gas_cost(regime) - Op.BLOCKHASH(
        key_warm=False,
        in_bounds=True,
    ).gas_cost(regime)
    return CodeGasMeasure(
        code=measured,
        overhead_cost=overhead,
        extra_stack_items=1,
        sstore_key=sstore_key,
    )


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@EIPChecklist.Opcode.Test.ForkTransition.At()
def test_blockhash_gas_and_resolution_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify ``BLOCKHASH`` gas cost and hash resolution across the EIP-7709
    fork activation boundary.

    * Block 1 (``timestamp = 14_999``, pre-fork Amsterdam):
      - First ``BLOCKHASH(0)`` costs flat ``20`` gas.
      - Second ``BLOCKHASH(0)`` also costs flat ``20`` gas.
      - Out-of-bounds ``BLOCKHASH(999)`` costs ``20`` gas.
    * Block 2 (``timestamp = 15_000``, at-fork Bogota):
      - First ``BLOCKHASH(0)`` is cold and costs ``2120`` gas.
      - Second ``BLOCKHASH(0)`` is warm and costs ``120`` gas.
      - Out-of-bounds ``BLOCKHASH(999)`` costs ``20`` gas.
      - Both pre-fork Block 0 (genesis) and Block 1 hashes resolve to
        non-zero values from ``HISTORY_STORAGE_ADDRESS``.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    cold_before = Op.BLOCKHASH(key_warm=False, in_bounds=True).gas_cost(before)
    warm_before = Op.BLOCKHASH(key_warm=True, in_bounds=True).gas_cost(before)
    oob_before = Op.BLOCKHASH(in_bounds=False).gas_cost(before)

    cold_after = Op.BLOCKHASH(key_warm=False, in_bounds=True).gas_cost(after)
    warm_after = Op.BLOCKHASH(key_warm=True, in_bounds=True).gas_cost(after)
    oob_after = Op.BLOCKHASH(in_bounds=False).gas_cost(after)

    assert cold_before == warm_before == oob_before
    assert cold_after > warm_after > oob_after

    contract_before = pre.deploy_contract(
        code=(
            _measure_blockhash_for_regime(0, before, sstore_key=0)
            + _measure_blockhash_for_regime(0, before, sstore_key=1)
            + _measure_blockhash_for_regime(999, before, sstore_key=2)
            + Op.SSTORE(3, Op.ISZERO(Op.BLOCKHASH(0)))
        ),
        storage={3: 0xDEAD},
    )
    contract_after = pre.deploy_contract(
        code=(
            _measure_blockhash_for_regime(0, after, sstore_key=0)
            + _measure_blockhash_for_regime(0, after, sstore_key=1)
            + _measure_blockhash_for_regime(999, after, sstore_key=2)
            + Op.SSTORE(3, Op.ISZERO(Op.BLOCKHASH(0)))
            + Op.SSTORE(4, Op.ISZERO(Op.BLOCKHASH(1)))
        ),
        storage={3: 0xDEAD, 4: 0xDEAD},
    )

    sender = pre.fund_eoa()
    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[Transaction(sender=sender, to=contract_before)],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[Transaction(sender=sender, to=contract_after)],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            contract_before: Account(
                storage={
                    0: cold_before,
                    1: warm_before,
                    2: oob_before,
                    3: 0,
                }
            ),
            contract_after: Account(
                storage={
                    0: cold_after,
                    1: warm_after,
                    2: oob_after,
                    3: 0,
                    4: 0,
                }
            ),
        },
    )


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@EIPChecklist.Opcode.Test.ForkTransition.At()
def test_blockhash_bal_storage_reads_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify that ``BLOCKHASH(0)`` on a non-parent block does NOT record a
    storage read in ``HISTORY_STORAGE_ADDRESS``'s Block Access List before
    the fork, and DOES record slot ``0`` in ``storage_reads`` at and after
    the fork transition.
    """
    sender = pre.fund_eoa()
    reader = pre.deploy_contract(
        code=Op.SSTORE(Op.NUMBER, Op.ISZERO(Op.BLOCKHASH(0))),
        storage={2: 0xDEAD, 3: 0xDEAD},
    )

    blocks = [
        # Block 1 (pre-fork): advances chain so Block 0 is no longer the
        # parent block in Block 2.
        Block(timestamp=BEFORE_TS - 1, txs=[]),
        # Block 2 (pre-fork): BLOCKHASH(0) resolves from client header
        # history without reading HISTORY_STORAGE_ADDRESS storage.
        Block(
            timestamp=BEFORE_TS,
            txs=[Transaction(sender=sender, to=reader)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    Spec.HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                        storage_reads=[],
                    ),
                }
            ),
        ),
        # Block 3 (at-fork): BLOCKHASH(0) reads slot 0 from
        # HISTORY_STORAGE_ADDRESS storage, which appears in storage_reads.
        Block(
            timestamp=AFTER_TS,
            txs=[Transaction(sender=sender, to=reader)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    Spec.HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                        storage_reads=[0],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={reader: Account(storage={2: 0, 3: 0})},
    )
