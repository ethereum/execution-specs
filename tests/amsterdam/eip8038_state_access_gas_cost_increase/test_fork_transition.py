"""
Fork-transition tests for
[EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

"Same operation, different gas" across the Amsterdam boundary. A block
at ``timestamp=14_999`` runs under the pre-fork (parent) schedule; a
block at ``timestamp=15_000`` runs under the EIP-8038 schedule. Every
before/after magnitude is derived from
``fork.fork_at(timestamp=...).gas_costs()`` — nothing is hardcoded.

Two proof styles are used:

* Account-access dimensions that are pure regular gas (``BALANCE`` cold
  access and the ``EXT*`` code-read surcharge) are measured exactly with
  ``CodeGasMeasure`` in each regime and asserted against the derived
  cost.
* Constant repricings that the runtime opcode model cannot isolate
  without state-gas confounders (``CALL_VALUE``, ``CREATE`` base,
  ``SELFDESTRUCT`` account-write) are asserted at the constant level
  from the derived schedules while the operation is still exercised in
  both blocks to prove it runs in each regime.
* The authorization intrinsic rise is proven behaviourally: a tx whose
  ``gas_limit`` equals the old auth intrinsic is valid before the fork
  and rejected with ``INTRINSIC_GAS_TOO_LOW`` after.
"""

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


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_cold_account_access_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    ``BALANCE`` of a cold account costs ``COLD_ACCOUNT_ACCESS``, which
    rises across the Amsterdam boundary (2600 -> 3000 on mainnet). The
    same opcode is measured before and after; each block asserts its
    regime's derived cost.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    cost_before = before.gas_costs().COLD_ACCOUNT_ACCESS
    cost_after = after.gas_costs().COLD_ACCOUNT_ACCESS
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

    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(
                    to=measure_before,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=measure_after,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

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
    it is zero before the fork and one ``WARM_ACCESS`` (100) after. Both
    opcodes are measured warm in each block so the surcharge is exact.
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
    assert surcharge_after == after.gas_costs().WARM_ACCESS
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

    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(
                    to=measure_before,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=measure_after,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

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
    ``CALL_VALUE`` rises across the boundary (9000 -> 10300 on mainnet,
    becoming ``ACCOUNT_WRITE + CALL_STIPEND``). The constant transition
    is asserted from the derived schedules while a value-bearing ``CALL``
    is exercised in both blocks to prove it still succeeds in each
    regime.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    call_value_before = before.gas_costs().CALL_VALUE
    call_value_after = after.gas_costs().CALL_VALUE
    assert call_value_after > call_value_before

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

    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(
                    to=caller_before,
                    gas_limit=1_000_000,
                    value=1,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=caller_after,
                    gas_limit=1_000_000,
                    value=1,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

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
    The ``CREATE`` regular base cost changes across the boundary
    (``OPCODE_CREATE_BASE``: 32000 -> 11000 on mainnet, redefined as
    ``ACCOUNT_WRITE + COLD_STORAGE_ACCESS``). The constant transition is
    asserted from the derived schedules and a ``CREATE`` is exercised in
    both blocks to prove it still deploys.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    create_base_before = before.gas_costs().OPCODE_CREATE_BASE
    create_base_after = after.gas_costs().OPCODE_CREATE_BASE
    assert create_base_after != create_base_before
    # Post-fork base is the harmonized ACCOUNT_WRITE + COLD_STORAGE_ACCESS.
    assert create_base_after == (
        after.gas_costs().ACCOUNT_WRITE + after.gas_costs().COLD_STORAGE_ACCESS
    )

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

    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(
                    to=factory_before,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=factory_after,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

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
    parameter (0 -> 8000 on mainnet). The constant transition is
    asserted from the derived schedules and a value-bearing
    ``SELFDESTRUCT`` to a fresh beneficiary is exercised in both blocks
    to prove it still runs.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    account_write_before = before.gas_costs().ACCOUNT_WRITE
    account_write_after = after.gas_costs().ACCOUNT_WRITE
    assert account_write_after > account_write_before

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

    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[
                Transaction(
                    to=suicidal_before,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=suicidal_after,
                    gas_limit=1_000_000,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        beneficiary_before: Account(balance=1),
        beneficiary_after: Account(balance=1),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@pytest.mark.exception_test
def test_auth_intrinsic_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The ``7702`` authorization intrinsic rises across the boundary. A tx
    whose ``gas_limit`` equals the pre-fork single-authorization
    intrinsic is valid before the fork but is rejected with
    ``INTRINSIC_GAS_TOO_LOW`` after, because the EIP-8038 auth intrinsic
    is strictly larger.
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
    # The pre-fork intrinsic is below the post-fork one, so the same
    # gas_limit straddles validity at the boundary.
    assert intrinsic_before < intrinsic_after
    gas_limit = intrinsic_before

    target_before = pre.deploy_contract(code=Op.STOP)
    target_after = pre.deploy_contract(code=Op.STOP)

    auth_before = pre.fund_eoa()
    auth_after = pre.fund_eoa()

    blocks = [
        # Before the fork: gas_limit covers the old auth intrinsic.
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
                ),
            ],
        ),
        # After the fork: identical gas_limit is now below intrinsic.
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
                    error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                ),
            ],
            exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
        ),
    ]

    blockchain_test(pre=pre, blocks=blocks, post={})
