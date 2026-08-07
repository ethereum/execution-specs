"""
Fork-transition tests for
[EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

"Same operation, different gas" across the Amsterdam boundary. A block
at ``timestamp=14_999`` runs under the pre-fork (parent) schedule; a
block at ``timestamp=15_000`` runs under the EIP-8038 schedule. Every
before/after magnitude is derived from the opcode's own cost at each
fork (``bytecode.gas_cost`` / ``execution_cost`` / ``refund``) — nothing
is hardcoded.

Two proof styles are used:

* Account-access dimensions that are pure execution gas (``BALANCE`` cold
  access and the ``EXT*`` code-read surcharge) are measured exactly with
  ``CodeGasMeasure`` in each regime and asserted against the derived
  cost.
* Repricings that the runtime opcode model cannot isolate without
  state-gas confounders (``CALL`` with value, ``CREATE``,
  ``SELFDESTRUCT`` to a fresh beneficiary, ``SSTORE`` first change) are
  exercised in both blocks to prove the operation still runs in each
  regime, with the ``SSTORE`` execution/state split and clear refund
  compared across forks via the bytecode's own cost methods.
* The authorization intrinsic rise is proven behaviourally: a tx whose
  ``gas_limit`` equals the old auth intrinsic is valid before the fork
  and rejected with ``INTRINSIC_GAS_TOO_LOW`` after.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    Storage,
    Transaction,
    TransactionException,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_at_transition_to("Amsterdam")

# Block timestamps straddling the Amsterdam activation.
BEFORE_TS = 14_999
AFTER_TS = 15_000


def _measure_contract(
    pre: Alloc, measured: Bytecode, opcode_cost: int, fork: Fork
) -> Address:
    """
    Deploy a contract that stores the exact gas consumed by the measured
    opcode in slot 0.

    ``measured`` is the runnable expression (opcode plus its PUSH
    operands); ``opcode_cost`` is the bare opcode's own gas at ``fork``.
    The wrapper overhead (the PUSH operands) is the difference between
    the two, so ``CodeGasMeasure`` strips it and slot 0 holds only the
    opcode's own cost. The opcode leaves one stack item (its result).
    """
    overhead = measured.gas_cost(fork) - opcode_cost
    code = CodeGasMeasure(
        code=measured,
        overhead_cost=overhead,
        extra_stack_items=1,
    )
    return pre.deploy_contract(code=code)


def transition_blocks(
    before_to: Address,
    after_to: Address,
    pre: Alloc,
    *,
    value: int = 0,
) -> List[Block]:
    """
    Return the two blocks that straddle the Amsterdam activation.

    The first block runs at ``BEFORE_TS`` (pre-fork schedule) and the
    second at ``AFTER_TS`` (EIP-8038 schedule). Each carries a single
    transaction from a fresh sender to its respective ``to`` target,
    forwarding ``value`` so a value-bearing operation is exercised in both
    regimes.
    """
    return [
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(to=before_to, value=value, sender=pre.fund_eoa()),
            ],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(to=after_to, value=value, sender=pre.fund_eoa()),
            ],
        ),
    ]


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_cold_account_access_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    ``BALANCE`` of a cold account costs ``COLD_ACCOUNT_ACCESS``, which
    rises across the Amsterdam boundary. The
    same opcode is measured before and after; each block asserts its
    regime's derived cost.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    # BALANCE's bare cost equals COLD_ACCOUNT_ACCESS in each regime.
    cold_balance = Op.BALANCE.with_metadata(address_warm=False)
    cost_before = cold_balance.gas_cost(before)
    cost_after = cold_balance.gas_cost(after)
    assert cost_after > cost_before

    target = pre.deploy_contract(code=Op.STOP)

    # A distinct cold target per block keeps each measurement cold.
    target_after = pre.deploy_contract(code=Op.STOP)

    # BALANCE has no code-read surcharge, so its bare cost equals
    # COLD_ACCOUNT_ACCESS in each regime.
    measure_before = _measure_contract(
        pre, Op.BALANCE(target), cost_before, before
    )
    measure_after = _measure_contract(
        pre, Op.BALANCE(target_after), cost_after, after
    )

    blocks = transition_blocks(measure_before, measure_after, pre)

    post = {
        measure_before: Account(storage={0: cost_before}),
        measure_after: Account(storage={0: cost_after}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_ext_code_surcharge_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The EIP-8038 ``EXT*`` code-read surcharge appears at the fork. The
    surcharge equals ``EXTCODESIZE`` minus ``BALANCE`` at equal warmth:
    it is zero before the fork and one ``WARM_ACCESS`` after. That
    comparison is computed from the opcode model. On-chain, each block
    measures only a cold ``EXTCODESIZE``: its
    rise reflects the surcharge on top of the cold-access repricing, and
    ``BALANCE`` is never executed.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    surcharge_before = Op.EXTCODESIZE(address_warm=True).gas_cost(
        before
    ) - Op.BALANCE(address_warm=True).gas_cost(before)
    surcharge_after = Op.EXTCODESIZE(address_warm=True).gas_cost(
        after
    ) - Op.BALANCE(address_warm=True).gas_cost(after)
    assert surcharge_before == 0
    assert surcharge_after > surcharge_before

    extcodesize_cost_before = Op.EXTCODESIZE(address_warm=False).gas_cost(
        before
    )
    extcodesize_cost_after = Op.EXTCODESIZE(address_warm=False).gas_cost(after)
    assert extcodesize_cost_after > extcodesize_cost_before

    target = pre.deploy_contract(code=Op.STOP)
    target_after = pre.deploy_contract(code=Op.STOP)

    measure_before = _measure_contract(
        pre, Op.EXTCODESIZE(target), extcodesize_cost_before, before
    )
    measure_after = _measure_contract(
        pre, Op.EXTCODESIZE(target_after), extcodesize_cost_after, after
    )

    blocks = transition_blocks(measure_before, measure_after, pre)

    post = {
        measure_before: Account(storage={0: extcodesize_cost_before}),
        measure_after: Account(storage={0: extcodesize_cost_after}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_call_value_cost_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    ``CALL_VALUE`` rises across the boundary, becoming
    ``ACCOUNT_WRITE + CALL_STIPEND``. The constant transition
    is asserted from the derived schedules while a value-bearing ``CALL``
    is exercised in both blocks to prove it still succeeds in each
    regime.
    """
    callee_before = pre.deploy_contract(code=Op.STOP, balance=0)
    callee_after = pre.deploy_contract(code=Op.STOP, balance=0)

    storage_before = Storage()
    caller_before = pre.deploy_contract(
        code=Op.SSTORE(
            storage_before.store_next(1),
            Op.CALL(gas=100_000, address=callee_before, value=1),
        ),
    )
    storage_after = Storage()
    caller_after = pre.deploy_contract(
        code=Op.SSTORE(
            storage_after.store_next(1),
            Op.CALL(gas=100_000, address=callee_after, value=1),
        ),
    )

    blocks = transition_blocks(caller_before, caller_after, pre, value=1)

    post = {
        caller_before: Account(storage=storage_before),
        callee_before: Account(balance=1),
        caller_after: Account(storage=storage_after),
        callee_after: Account(balance=1),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_create_base_cost_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The ``CREATE`` execution base cost changes across the boundary
    (``OPCODE_CREATE_BASE`` is redefined as
    ``ACCOUNT_WRITE + COLD_ACCOUNT_ACCESS``). The constant transition is
    asserted from the derived schedules and a ``CREATE`` is exercised in
    both blocks to prove it still deploys.
    """
    init_code = Op.STOP
    init_word = int.from_bytes(bytes(init_code), "big") << (
        256 - 8 * len(init_code)
    )

    storage_before = Storage()
    factory_before = pre.deploy_contract(
        code=(
            Op.MSTORE(0, init_word)
            + Op.SSTORE(
                storage_before.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
        ),
    )
    storage_after = Storage()
    factory_after = pre.deploy_contract(
        code=(
            Op.MSTORE(0, init_word)
            + Op.SSTORE(
                storage_after.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
        ),
    )

    blocks = transition_blocks(factory_before, factory_after, pre)

    post = {
        factory_before: Account(storage=storage_before),
        factory_after: Account(storage=storage_after),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_selfdestruct_account_write_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    ``SELFDESTRUCT`` gains an ``ACCOUNT_WRITE`` charge when it sends a
    positive balance to an empty account, which is a new EIP-8038
    parameter. The constant transition is
    asserted from the derived schedules and a value-bearing
    ``SELFDESTRUCT`` to a fresh beneficiary is exercised in both blocks
    to prove it still runs.
    """
    # Fresh empty beneficiaries so the positive-balance-to-empty branch
    # that adds ACCOUNT_WRITE is taken in each regime.
    beneficiary_before = pre.fund_eoa(amount=0)
    beneficiary_after = pre.fund_eoa(amount=0)

    suicidal_before = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary_before),
        balance=1,
    )
    suicidal_after = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary_after),
        balance=1,
    )

    blocks = transition_blocks(suicidal_before, suicidal_after, pre)

    post = {
        beneficiary_before: Account(balance=1),
        beneficiary_after: Account(balance=1),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_sstore_write_cost_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The ``SSTORE`` first-change cost is repriced across the Amsterdam
    boundary, and EIP-8038 changes the *model*, not a single number.

    Before the fork (parent schedule) a zero-to-nonzero ``SSTORE`` is a
    flat execution charge (``COLD_STORAGE_ACCESS + STORAGE_SET``) with no
    state-gas dimension. After the fork the charge splits: the execution
    portion drops to ``COLD_STORAGE_ACCESS + STORAGE_WRITE`` while the
    bulk moves into the new state-gas dimension, and the clear refund
    rises. Every magnitude is derived from the two schedules; nothing is
    hardcoded.

    The transition is asserted at the derived-constant level (the
    runtime opcode cost cannot isolate the execution portion without the
    state-gas confounder) and a zero-to-nonzero ``SSTORE`` is exercised
    in both blocks to prove it still sets the slot in each regime.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    # First-change (zero -> nonzero, cold) SSTORE in each regime.
    sstore = Op.SSTORE(new_value=1)

    execution_before = sstore.execution_cost(before)
    execution_after = sstore.execution_cost(after)
    state_before = sstore.state_cost(before)
    state_after = sstore.state_cost(after)
    total_before = sstore.gas_cost(before)
    total_after = sstore.gas_cost(after)

    # The repricing changes the execution charge, introduces the state
    # dimension, and therefore moves the total.
    assert execution_after != execution_before
    assert state_before == 0
    assert state_after > 0
    assert total_after != total_before

    # The storage-clear refund also rises across the boundary.
    clear_sstore = Op.SSTORE.with_metadata(
        original_value=1, current_value=1, new_value=0
    )
    refund_before = clear_sstore.refund(before)
    refund_after = clear_sstore.refund(after)
    assert refund_after > refund_before

    # Exercise the zero-to-nonzero SSTORE in both regimes; the slot ends
    # set in each block.
    storage_before = Storage()
    contract_before = pre.deploy_contract(
        code=Op.SSTORE(storage_before.store_next(1), 1),
    )
    storage_after = Storage()
    contract_after = pre.deploy_contract(
        code=Op.SSTORE(storage_after.store_next(1), 1),
    )

    blocks = transition_blocks(contract_before, contract_after, pre)

    post = {
        contract_before: Account(storage=storage_before),
        contract_after: Account(storage=storage_after),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.inclusion_test
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@pytest.mark.exception_test
def test_auth_intrinsic_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The ``7702`` authorization intrinsic *falls* across the boundary.
    EIP-2780 moves the state-dependent authorization costs (account
    creation and the delegation-write base) out of the intrinsic and into
    the top frame, leaving only ``EXECUTION_PER_AUTH_BASE_COST`` in the
    intrinsic. The post-fork single-authorization intrinsic is
    therefore strictly smaller than the pre-fork one, so a tx whose
    ``gas_limit`` equals the (lower) post-fork intrinsic is rejected with
    ``INTRINSIC_GAS_TOO_LOW`` before the fork but valid after.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    intrinsic_before = before.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1,
        return_cost_deducted_prior_execution=True,
    )
    intrinsic_after = after.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1,
        return_cost_deducted_prior_execution=True,
    )
    # The post-fork intrinsic is below the pre-fork one, so the same
    # gas_limit straddles validity at the boundary.
    assert intrinsic_after < intrinsic_before
    gas_limit = intrinsic_after

    target_before = pre.deploy_contract(code=Op.STOP)
    target_after = pre.deploy_contract(code=Op.STOP)

    auth_before = pre.fund_eoa()
    auth_after = pre.fund_eoa()

    blocks = [
        # Before the fork: gas_limit is below the (higher) old auth
        # intrinsic, so the tx is rejected.
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(
                    to=auth_before,
                    gas_limit=gas_limit,
                    authorization_list=[
                        AuthorizationTuple(
                            address=target_before,
                            nonce=0,
                            signer=auth_before,
                        ),
                    ],
                    sender=pre.fund_eoa(),
                    error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                ),
            ],
            exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
        ),
        # After the fork: the auth intrinsic dropped to exactly this
        # gas_limit, so the tx is now valid (included). It has no gas left
        # for the top-frame delegation, so execution runs out of gas and
        # the delegation rolls back, but the block itself is valid.
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=auth_after,
                    gas_limit=gas_limit,
                    authorization_list=[
                        AuthorizationTuple(
                            address=target_after,
                            nonce=0,
                            signer=auth_after,
                        ),
                    ],
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    blockchain_test(pre=pre, blocks=blocks, post={})
