"""
Fork-transition tests for
[EIP-8038: State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038).

"Same operation, different gas" across the Amsterdam boundary. A block
at ``timestamp=14_999`` runs under the pre-fork (parent) schedule; a
block at ``timestamp=15_000`` runs under the EIP-8038 schedule. Every
before/after magnitude is derived from the opcode's own cost at each
fork (``bytecode.gas_cost`` / ``execution_cost`` / ``refund``) — nothing
is hardcoded.

Four proof styles are used:

* Opcode costs that are pure execution gas (``BALANCE`` cold access, the
  ``EXT*`` code-read surcharge and the ``CREATE`` base) are measured
  exactly with ``CodeGasMeasure`` in each regime and asserted against
  the derived cost.
* Charges that cannot be measured from inside the frame that pays them
  (a value-bearing ``CALL``, ``SELFDESTRUCT`` to a fresh beneficiary,
  the ``SSTORE`` clear refund) are pinned per block through the
  transaction receipt's ``cumulative_gas_used``, which sums both gas
  dimensions and so pins a charge that the fork moves between them.
* Intrinsic repricings are pinned by setting ``gas_limit`` to the
  regime's exact minimum and pinning the receipt, and by straddling
  validity: one ``gas_limit`` that is sufficient before the fork and
  ``INTRINSIC_GAS_TOO_LOW`` after (access lists), or the reverse
  (authorizations, whose intrinsic falls).
* Model-level repricings the runtime cannot isolate (the ``SSTORE``
  execution/state split) are compared across the two schedules via the
  bytecode's own cost methods while the operation is exercised in both
  blocks.
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Fork,
    GasConsumer,
    Op,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
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
    before_gas_used: int | None = None,
    after_gas_used: int | None = None,
) -> List[Block]:
    """
    Return the two blocks that straddle the Amsterdam activation.

    The first block runs at ``BEFORE_TS`` (pre-fork schedule) and the
    second at ``AFTER_TS`` (EIP-8038 schedule). Each carries a single
    transaction from a fresh sender to its respective ``to`` target,
    forwarding ``value`` so a value-bearing operation is exercised in both
    regimes.

    ``*_gas_used`` pins the regime's transaction receipt. A single
    transaction per block makes ``cumulative_gas_used`` that
    transaction's own gas, which sums both gas dimensions — unlike the
    block header's ``gas_used``, where the larger dimension masks the
    other.
    """

    def block(timestamp: int, to: Address, gas_used: int | None) -> Block:
        receipt = (
            TransactionReceipt(cumulative_gas_used=gas_used)
            if gas_used is not None
            else None
        )
        return Block(
            timestamp=timestamp,
            txs=[
                Transaction(
                    to=to,
                    value=value,
                    sender=pre.fund_eoa(),
                    expected_receipt=receipt,
                ),
            ],
        )

    return [
        block(BEFORE_TS, before_to, before_gas_used),
        block(AFTER_TS, after_to, after_gas_used),
    ]


def _cumulative_gas_used(code: Bytecode, fork: Fork) -> int:
    """
    Return the receipt ``cumulative_gas_used`` for a block whose single
    transaction's execution is exactly ``code`` at ``fork``.

    Gross gas is the intrinsic plus the code's own cost; the applied
    refund is capped at the EIP-3529 quotient of the gross.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    gross = intrinsic + code.execution_cost(fork) + code.state_cost(fork)
    return gross - min(gross // fork.max_refund_quotient(), code.refund(fork))


def _access_list(pre: Alloc) -> List[AccessList]:
    """
    Return an access list large enough that its own repricing dominates
    the fall in the transaction base cost across the boundary.
    """
    return [
        AccessList(address=pre.fund_eoa(amount=0), storage_keys=[0, 1])
        for _ in range(2)
    ]


def _minimum_gas_limit(regime: Fork, access_list: List[AccessList]) -> int:
    """Return the regime's intrinsic cost of an access-list transaction."""
    return regime.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )


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
def test_same_account_accessed_at_both_prices(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    One account, accessed on both sides of the boundary, is cold and
    charged its regime's price each time.

    ``test_cold_account_access_at_transition`` gives each block its own
    fresh target; here a *single* target is accessed in both blocks. The
    warm set does not survive the transaction that built it, so the
    post-fork access is still cold and pays the raised
    ``COLD_ACCOUNT_ACCESS`` rather than ``WARM_ACCESS``. The two
    measuring contracts carry byte-identical code, so the only thing
    that differs between the two measurements is the schedule.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    cold_balance = Op.BALANCE.with_metadata(address_warm=False)
    cost_before = cold_balance.gas_cost(before)
    cost_after = cold_balance.gas_cost(after)
    warm_cost_after = Op.BALANCE.with_metadata(address_warm=True).gas_cost(
        after
    )
    assert cost_after > cost_before
    # Leaked warmth would show up as this much cheaper post-fork.
    assert warm_cost_after < cost_after

    target = pre.deploy_contract(code=Op.STOP)

    measure_before = _measure_contract(
        pre, Op.BALANCE(target), cost_before, before
    )
    measure_after = _measure_contract(
        pre, Op.BALANCE(target), cost_after, after
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
    ``ACCOUNT_WRITE + CALL_STIPEND``, and each regime's charge is pinned
    exactly through its receipt.

    The callee is an existing contract, so the value transfer creates no
    account and the whole charge stays on the execution axis in both
    regimes. The callee forwards nothing beyond the value stipend and
    halts without using it, so the gas consumed is the ``CALL``'s charge
    less the returned stipend.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    # Cold, existing, value-receiving callee: the value-transfer charge
    # applies but the account-creation charge does not.
    call = Op.CALL.with_metadata(
        address_warm=False, value_transfer=True, account_new=False
    )
    assert call.gas_cost(after) > call.gas_cost(before)
    # No account is created, so nothing lands on the post-fork state axis
    # and the receipt alone pins the whole charge.
    assert call.state_cost(before) == 0
    assert call.state_cost(after) == 0

    def caller_code(callee: Address) -> Bytecode:
        return (
            Op.POP(
                call(
                    gas=0,
                    address=callee,
                    value=1,
                    args_offset=0,
                    args_size=0,
                    ret_offset=0,
                    ret_size=0,
                )
            )
            + Op.STOP
        )

    callee_before = pre.deploy_contract(code=Op.STOP)
    callee_after = pre.deploy_contract(code=Op.STOP)
    code_before = caller_code(callee_before)
    code_after = caller_code(callee_after)

    # The caller holds the wei it forwards, so the transaction itself
    # carries no value and its intrinsic stays the plain one.
    caller_before = pre.deploy_contract(code=code_before, balance=1)
    caller_after = pre.deploy_contract(code=code_after, balance=1)

    def gas_used(code: Bytecode, regime: Fork) -> int:
        return _cumulative_gas_used(code, regime) - regime.call_value_stipend()

    blocks = transition_blocks(
        caller_before,
        caller_after,
        pre,
        before_gas_used=gas_used(code_before, before),
        after_gas_used=gas_used(code_after, after),
    )

    post = {
        caller_before: Account(balance=0),
        callee_before: Account(balance=1),
        caller_after: Account(balance=0),
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
    ``ACCOUNT_WRITE + COLD_ACCOUNT_ACCESS``) and the account-creation
    charge moves onto the state axis, where the pre-fork schedule has no
    axis at all. Each block measures one ``CREATE`` and asserts its
    regime's execution cost exactly.

    The init code is zero-length, so no memory is touched, no per-init-word
    charge applies and empty code is deposited: the measured value is the
    opcode's own execution cost with no child-frame gas folded in.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    create = Op.CREATE.with_metadata(init_code_size=0, account_new=True)
    execution_before = create.execution_cost(before)
    execution_after = create.execution_cost(after)
    # The creation charge is execution gas before the fork and state gas
    # after it, so what the measurement sees falls even though the
    # operation's total cost rises.
    assert execution_after < execution_before
    assert create.state_cost(before) == 0
    assert create.state_cost(after) > 0
    assert create.gas_cost(after) > create.gas_cost(before)

    def factory(regime: Fork) -> Address:
        """Deploy a factory that stores its ``CREATE``'s own gas."""
        return pre.deploy_contract(
            code=CodeGasMeasure(
                code=Op.CREATE(value=0, offset=0, size=0),
                # Strip the three argument pushes; the CREATE leaves its
                # result on the stack.
                overhead_cost=3 * Op.PUSH1(0).execution_cost(regime),
                extra_stack_items=1,
            ),
        )

    factory_before = factory(before)
    factory_after = factory(after)

    blocks = [
        Block(
            timestamp=BEFORE_TS,
            txs=[Transaction(to=factory_before, sender=pre.fund_eoa())],
        ),
        Block(
            timestamp=AFTER_TS,
            txs=[
                Transaction(
                    to=factory_after,
                    sender=pre.fund_eoa(),
                    # The reservoir funds the post-fork account-creation
                    # state gas so it does not spill into the gas the
                    # measurement reads. The pre-fork block has no state
                    # gas dimension, so it takes no reservoir.
                    state_gas_reservoir=create.state_cost(after),
                ),
            ],
        ),
    ]

    post = {
        factory_before: Account(storage={0: execution_before}),
        factory_after: Account(storage={0: execution_after}),
        # Each factory's first CREATE deploys empty code at nonce 1.
        compute_create_address(address=factory_before, nonce=1): Account(
            nonce=1, code=b"", balance=0
        ),
        compute_create_address(address=factory_after, nonce=1): Account(
            nonce=1, code=b"", balance=0
        ),
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
    positive balance to an empty account, while the beneficiary-creation
    charge it already paid moves from execution gas onto the state axis.

    ``SELFDESTRUCT`` halts its own frame, so the charge is pinned from
    outside, through the receipt. The receipt sums the two gas dimensions
    (unlike the block header, which takes their maximum and would let the
    dominating creation state gas mask the execution side), so one pin
    covers both the added ``ACCOUNT_WRITE`` and the relocated creation
    charge.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    # Fresh empty beneficiaries so the positive-balance-to-empty branch
    # that adds ACCOUNT_WRITE is taken in each regime.
    beneficiary_before = pre.fund_eoa(amount=0)
    beneficiary_after = pre.fund_eoa(amount=0)

    selfdestruct = Op.SELFDESTRUCT.with_metadata(
        address_warm=False, account_new=True
    )
    code_before = selfdestruct(beneficiary_before)
    code_after = selfdestruct(beneficiary_after)

    # Before the fork the creation charge is execution gas and there is no
    # state axis; after it, the creation charge is state gas while the
    # execution charge gains ACCOUNT_WRITE.
    assert code_before.state_cost(before) == 0
    assert code_after.state_cost(after) > 0
    assert code_after.execution_cost(after) > Op.SELFDESTRUCT.with_metadata(
        address_warm=False, account_new=False
    ).execution_cost(after)
    # EIP-6780 keeps the pre-existing originator alive, so no state-gas
    # refund muddies either receipt.
    assert code_before.refund(before) == 0
    assert code_after.refund(after) == 0

    suicidal_before = pre.deploy_contract(code=code_before, balance=1)
    suicidal_after = pre.deploy_contract(code=code_after, balance=1)

    blocks = transition_blocks(
        suicidal_before,
        suicidal_after,
        pre,
        before_gas_used=_cumulative_gas_used(code_before, before),
        after_gas_used=_cumulative_gas_used(code_after, after),
    )

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
    bulk moves into the new state-gas dimension. Every magnitude is
    derived from the two schedules; nothing is hardcoded.

    The split itself is asserted at the derived-constant level, since the
    runtime opcode cost cannot isolate the execution portion from the
    state-gas one. The receipt then pins each regime's total, which sums
    both dimensions and so holds the relocated charge to its exact size.
    The clear refund is exercised on-chain by
    ``test_storage_clear_refund_at_transition``.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    # First-change (zero -> nonzero, cold) SSTORE in each regime.
    sstore = Op.SSTORE(new_value=1)

    # The repricing changes the execution charge, introduces the state
    # dimension, and therefore moves the total.
    assert sstore.execution_cost(after) != sstore.execution_cost(before)
    assert sstore.state_cost(before) == 0
    assert sstore.state_cost(after) > 0
    assert sstore.gas_cost(after) != sstore.gas_cost(before)

    # Exercise the zero-to-nonzero SSTORE in both regimes; the slot ends
    # set in each block.
    storage_before = Storage()
    code_before = Op.SSTORE(storage_before.store_next(1), 1)
    contract_before = pre.deploy_contract(code=code_before)
    storage_after = Storage()
    code_after = Op.SSTORE(storage_after.store_next(1), 1)
    contract_after = pre.deploy_contract(code=code_after)

    blocks = transition_blocks(
        contract_before,
        contract_after,
        pre,
        before_gas_used=_cumulative_gas_used(code_before, before),
        after_gas_used=_cumulative_gas_used(code_after, after),
    )

    post = {
        contract_before: Account(storage=storage_before),
        contract_after: Account(storage=storage_after),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_storage_clear_refund_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    ``REFUND_STORAGE_CLEAR`` rises across the boundary, and a slot is
    actually cleared on each side so the granted refund is observed
    rather than derived.

    Each block clears a slot whose original value is non-zero — so no
    state-creation refund participates and the whole adjustment belongs
    to EIP-8038 — and burns enough unrelated gas that the EIP-3529
    quotient cap does not bind. The regime's full grant is therefore
    visible in ``cumulative_gas_used``.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)

    clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0)
    assert clear.refund(after) > clear.refund(before)

    def clear_code(regime: Fork) -> Bytecode:
        return clear + GasConsumer(gas=clear.refund(regime) * 5, fork=regime)

    def gas_used(code: Bytecode, regime: Fork) -> int:
        expected = _cumulative_gas_used(code, regime)
        intrinsic = regime.transaction_intrinsic_cost_calculator()(
            return_cost_deducted_prior_execution=True
        )
        gross = intrinsic + code.execution_cost(regime)
        # The burn keeps the cap clear of the grant in both regimes, so
        # the observed gas carries the whole refund.
        assert gross // regime.max_refund_quotient() > code.refund(regime)
        assert expected == gross - code.refund(regime)
        return expected

    code_before = clear_code(before)
    code_after = clear_code(after)

    contract_before = pre.deploy_contract(code=code_before, storage={0: 1})
    contract_after = pre.deploy_contract(code=code_after, storage={0: 1})

    blocks = transition_blocks(
        contract_before,
        contract_after,
        pre,
        before_gas_used=gas_used(code_before, before),
        after_gas_used=gas_used(code_after, after),
    )

    post = {
        contract_before: Account(storage={0: 0}),
        contract_after: Account(storage={0: 0}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_access_list_intrinsic_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The per-entry access-list intrinsic surcharge rises across the
    boundary, and each regime's total intrinsic is pinned exactly.

    Each block sends the same access-list transaction with ``gas_limit``
    set to that regime's minimum valid value, to a recipient with no
    code. Nothing is left to execute, so the transaction consumes
    precisely its intrinsic and the receipt pins it: a client pricing
    access-list entries at the other regime's constants either rejects
    the transaction or consumes a different amount.

    The rise combines EIP-8038's access-cost increase with EIP-7981's
    per-entry data surcharge, charged in execution gas. The exact receipt
    pin checks the resulting access-list cost.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)
    access_list = _access_list(pre)

    def surcharge(regime: Fork) -> int:
        calculator = regime.transaction_intrinsic_cost_calculator()
        return calculator(
            access_list=access_list,
            return_cost_deducted_prior_execution=True,
        ) - calculator(return_cost_deducted_prior_execution=True)

    # The access list itself got more expensive, independently of the
    # transaction base cost moving the other way under EIP-2780.
    assert surcharge(after) > surcharge(before)

    recipient = pre.fund_eoa(amount=0)

    def block(timestamp: int, regime: Fork) -> Block:
        gas_limit = _minimum_gas_limit(regime, access_list)
        return Block(
            timestamp=timestamp,
            txs=[
                Transaction(
                    to=recipient,
                    access_list=access_list,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                    expected_receipt=TransactionReceipt(
                        cumulative_gas_used=gas_limit
                    ),
                ),
            ],
        )

    blocks = [block(BEFORE_TS, before), block(AFTER_TS, after)]
    blockchain_test(pre=pre, blocks=blocks, post={})


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.exception_test
def test_access_list_intrinsic_straddles_validity(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    One ``gas_limit`` straddles validity at the boundary: it covers the
    pre-fork intrinsic of an access-list transaction and falls short of
    the post-fork one.

    For this access list the raised per-entry surcharge outweighs the
    EIP-2780 fall in the base cost, so the same transaction that is
    valid before the fork is rejected with ``INTRINSIC_GAS_TOO_LOW``
    after it. Off-by-one limits on either side pin the constraint in
    each regime, so all four accept/reject arms are exercised. EIP-7981's
    per-entry data surcharge, charged in execution gas, also contributes
    to the rise; the off-by-one limits pin the resulting access-list cost.
    """
    before = fork.fork_at(timestamp=BEFORE_TS)
    after = fork.fork_at(timestamp=AFTER_TS)
    access_list = _access_list(pre)

    intrinsic_before = _minimum_gas_limit(before, access_list)
    intrinsic_after = _minimum_gas_limit(after, access_list)
    # The straddle only exists because this access list's surcharge rises
    # by more than the EIP-2780 base cost falls.
    assert intrinsic_after > intrinsic_before

    recipient = pre.fund_eoa(amount=0)

    def make_tx(
        gas_limit: int, error: TransactionException | None = None
    ) -> Transaction:
        return Transaction(
            to=recipient,
            access_list=access_list,
            gas_limit=gas_limit,
            sender=pre.fund_eoa(),
            error=error,
            # Accepted arms are handed exactly their regime's intrinsic
            # and the recipient runs no code, so the whole limit is
            # consumed and the receipt pins it.
            expected_receipt=None
            if error
            else TransactionReceipt(cumulative_gas_used=gas_limit),
        )

    too_low = TransactionException.INTRINSIC_GAS_TOO_LOW
    blocks = [
        # Rejected before the fork: one gas below the pre-fork intrinsic.
        Block(
            timestamp=BEFORE_TS,
            txs=[make_tx(intrinsic_before - 1, error=too_low)],
            exception=too_low,
        ),
        # Accepted before the fork: the exact pre-fork intrinsic.
        Block(timestamp=BEFORE_TS, txs=[make_tx(intrinsic_before)]),
        # Rejected after the fork: the very limit the previous block
        # accepted — the straddle itself.
        Block(
            timestamp=AFTER_TS,
            txs=[make_tx(intrinsic_before, error=too_low)],
            exception=too_low,
        ),
        # Accepted after the fork: the exact post-fork intrinsic.
        Block(timestamp=AFTER_TS, txs=[make_tx(intrinsic_after)]),
    ]

    blockchain_test(pre=pre, blocks=blocks, post={})


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
