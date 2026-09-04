"""
State gas fork transition tests for EIP-8037.

Verify that state gas pricing, the modified transaction validity constraint
(tx.gas can exceed TX_MAX_GAS_LIMIT), and the two-dimensional block inclusion
constraint activate correctly at the EIP-8037 fork boundary.

Before EIP-8037: no state gas dimension, tx.gas capped at
TX_MAX_GAS_LIMIT (EIP-7825).

At/after EIP-8037: state gas charges apply, tx.gas above
TX_MAX_GAS_LIMIT is valid (excess feeds the reservoir).

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    EIPChecklist,
    Fork,
    Header,
    Op,
    Storage,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8037")


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_block_gas_used_dimension_switch_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the block header switches to two-dimensional accounting at the
    fork boundary.

    The same storage-creating transaction is mined either side of the
    boundary. Before the fork the header reports the scalar execution
    total; after it the header reports `max(execution, state)`, which the
    state charge dominates. Only a header assertion separates the two —
    the post-state is identical.
    """
    before_fork = fork.fork_at(timestamp=14_999)
    after_fork = fork.fork_at(timestamp=15_000)

    code = Op.SSTORE(0, 1, original_value=0, new_value=1)
    state_gas = code.state_cost(after_fork)
    assert code.state_cost(before_fork) == 0, "no state dimension yet"

    before_gas_used = (
        before_fork.transaction_intrinsic_cost_calculator()()
        + code.gas_cost(before_fork)
    )
    after_execution = (
        after_fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(after_fork)
    )
    assert state_gas > after_execution, (
        "the state dimension must set the post-fork header"
    )

    storage_before = Storage()
    writer_before = pre.deploy_contract(
        code=Op.SSTORE(storage_before.store_next(1), 1)
    )
    storage_after = Storage()
    writer_after = pre.deploy_contract(
        code=Op.SSTORE(storage_after.store_next(1), 1)
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=14_999,
                txs=[
                    Transaction(
                        to=writer_before,
                        state_gas_reservoir=0,
                        sender=pre.fund_eoa(),
                    )
                ],
                header_verify=Header(gas_used=before_gas_used),
            ),
            Block(
                timestamp=15_000,
                txs=[
                    Transaction(
                        to=writer_after,
                        state_gas_reservoir=0,
                        sender=pre.fund_eoa(),
                    )
                ],
                header_verify=Header(gas_used=state_gas),
            ),
        ],
        post={
            writer_before: Account(storage=storage_before),
            writer_after: Account(storage=storage_after),
        },
    )


@pytest.mark.parametrize(
    "state_op",
    [Op.CREATE, Op.CREATE2, Op.CALL, Op.SELFDESTRUCT],
)
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_account_state_gas_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    state_op: Op,
) -> None:
    """
    Test the account-creating state charges activate at the fork
    boundary.

    EIP-8037 splits four charges out of the execution dimension; the
    SSTORE one is covered separately. Each of the remaining three is
    driven from a sub-call granted only what its own fork prices as
    execution gas: it completes before the fork and, after it, only when
    a reservoir carries the new state charge into the child frame.
    """
    before_fork = fork.fork_at(timestamp=14_999)
    after_fork = fork.fork_at(timestamp=15_000)

    def probe() -> tuple[Bytecode, int]:
        """Return code exercising `state_op` and the balance it needs."""
        match state_op:
            case Op.CREATE:
                return Op.POP(Op.CREATE(0, 0, 0)), 0
            case Op.CREATE2:
                return Op.POP(Op.CREATE2(0, 0, 0, 0)), 0
            case Op.CALL:
                return Op.POP(
                    Op.CALL(
                        gas=0,
                        address=pre.nonexistent_account(),
                        value=1,
                        value_transfer=True,
                        account_new=True,
                    )
                ), 1
            case _:
                return (
                    Op.SELFDESTRUCT(
                        pre.nonexistent_account(), account_new=True
                    ),
                    1,
                )

    scenarios = [
        # timestamp, fork pricing the grant, reservoir funded, charge paid
        (14_999, before_fork, False, True),
        (15_000, after_fork, True, True),
        (15_001, after_fork, False, False),
    ]

    blocks = []
    post = {}
    for timestamp, grant_fork, funded, paid in scenarios:
        # Rebuild so each scenario gets a fresh account to create.
        target_code, balance = probe()
        grant = target_code.execution_cost(grant_fork)
        reservoir = target_code.state_cost(grant_fork) if funded else 0
        target = pre.deploy_contract(code=target_code, balance=balance)
        caller = pre.deploy_contract(
            code=Op.POP(Op.CALL(gas=grant, address=target))
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        to=caller,
                        state_gas_reservoir=reservoir,
                        sender=pre.fund_eoa(),
                    )
                ],
            )
        )
        match state_op:
            case Op.CREATE | Op.CREATE2:
                post[target] = Account(nonce=2 if paid else 1)
            case _:
                post[target] = Account(balance=0 if paid else 1)

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_sstore_state_gas_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas activates at the EIP-8037 fork boundary.

    A sub-call granted only the store's execution gas succeeds before
    the fork, and after it only when a reservoir carries the new state
    charge into the child frame.
    """
    before_fork = fork.fork_at(timestamp=14_999)
    after_fork = fork.fork_at(timestamp=15_000)

    sstore_code = Op.SSTORE(0, 1, original_value=0, new_value=1)
    # Each side gets only what its own fork prices as execution gas.
    before_grant = sstore_code.gas_cost(before_fork)
    execution_gas = sstore_code.execution_cost(after_fork)
    state_gas = sstore_code.state_cost(after_fork)
    assert sstore_code.state_cost(before_fork) == 0, "no state dimension yet"
    assert state_gas > 0

    storage_before = Storage()
    target_before = pre.deploy_contract(code=sstore_code)
    caller_before = pre.deploy_contract(
        code=Op.SSTORE(
            storage_before.store_next(1, "subcall_succeeds"),
            Op.CALL(gas=before_grant, address=target_before),
        ),
    )

    storage_funded = Storage()
    target_funded = pre.deploy_contract(code=sstore_code)
    caller_funded = pre.deploy_contract(
        code=Op.SSTORE(
            storage_funded.store_next(1, "reservoir_pays_state_gas"),
            Op.CALL(gas=execution_gas, address=target_funded),
        ),
    )

    storage_starved = Storage()
    target_starved = pre.deploy_contract(code=sstore_code)
    caller_starved = pre.deploy_contract(
        code=Op.SSTORE(
            storage_starved.store_next(0, "subcall_runs_out_of_state_gas"),
            Op.CALL(gas=execution_gas, address=target_starved),
        ),
    )

    blocks = [
        # Pre-fork: the grant is the whole price.
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=caller_before,
                    state_gas_reservoir=0,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        # Post-fork: the reservoir pays the state charge.
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=caller_funded,
                    state_gas_reservoir=state_gas,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        # Post-fork, no reservoir: the state charge halts the child.
        Block(
            timestamp=15_001,
            txs=[
                Transaction(
                    to=caller_starved,
                    state_gas_reservoir=0,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        caller_before: Account(storage=storage_before),
        target_before: Account(storage={0: 1}),
        caller_funded: Account(storage=storage_funded),
        target_funded: Account(storage={0: 1}),
        caller_starved: Account(storage=storage_starved),
        target_starved: Account(storage={0: 0}),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def _access_list_over_execution_cap(
    fork: Fork, cap: int
) -> tuple[list[AccessList], int]:
    """
    Return an access list whose intrinsic execution cost exceeds ``cap``,
    along with that cost.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()
    per_address_execution = intrinsic(
        access_list=[AccessList(address=Address(0x100), storage_keys=[])],
        return_cost_deducted_prior_execution=True,
    ) - intrinsic(return_cost_deducted_prior_execution=True)
    access_list = [
        AccessList(address=Address(0x10000 + i), storage_keys=[])
        for i in range(cap // per_address_execution)
    ]
    execution_intrinsic = intrinsic(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    assert execution_intrinsic > cap
    # The floor must stay under the cap so a rejection is attributable to
    # the execution intrinsic rather than the data floor.
    assert (
        fork.transaction_data_floor_cost_calculator()(
            data=b"", access_list=access_list
        )
        <= cap
    )
    return access_list, execution_intrinsic


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(
            "at_cap",
            id="at_cap",
            marks=[
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork(),
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork(),
            ],
        ),
        pytest.param(
            "gas_limit_above_cap",
            id="gas_limit_above_cap",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork(),
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork(),
            ],
        ),
        pytest.param(
            "intrinsic_above_cap",
            id="intrinsic_above_cap",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork(),
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork(),
            ],
        ),
    ],
)
def test_tx_gas_above_cap_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scenario: str,
    fork: Fork,
) -> None:
    """
    Test transaction and block gas constraints at the EIP-8037 transition.

    Before EIP-8037, EIP-7825 rejects any tx with gas > TX_MAX_GAS_LIMIT.
    After EIP-8037 that gas limit is allowed — the excess feeds the state
    gas reservoir — but the replacement constraint still rejects a
    transaction whose intrinsic execution gas exceeds the cap. The scenarios
    pin acceptance at the cap, the old-rule rejection/new-rule acceptance flip
    at ``cap + 1``, and rejection by the new transaction rule.
    """
    after_fork = fork.fork_at(timestamp=15_000)
    gas_limit_cap = after_fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage_before = Storage()
    contract_before = pre.deploy_contract(
        code=(Op.SSTORE(storage_before.store_next(1), 1)),
    )

    storage_after = Storage()
    contract_after = pre.deploy_contract(
        code=(Op.SSTORE(storage_after.store_next(1), 1)),
    )

    tx_kwargs: dict = {}
    after_error = None
    if scenario == "at_cap":
        gas_limit = gas_limit_cap
        before_error = None
    elif scenario == "gas_limit_above_cap":
        gas_limit = gas_limit_cap + 1
        before_error = TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
    else:
        access_list, execution_intrinsic = _access_list_over_execution_cap(
            after_fork, gas_limit_cap
        )
        gas_limit = execution_intrinsic + 1_000_000
        before_error = TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        after_error = TransactionException.INTRINSIC_GAS_TOO_LOW
        tx_kwargs = {"ty": 1, "access_list": access_list}

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=contract_before,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                    error=before_error,
                    **tx_kwargs,
                ),
            ],
            exception=before_error,
        ),
        # After fork: above-cap tx is now valid (excess feeds reservoir)
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=contract_after,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                    error=after_error,
                    **tx_kwargs,
                ),
            ],
            exception=after_error,
        ),
    ]

    post = {
        contract_before: Account(
            storage=storage_before if before_error is None else {0: 0},
        ),
        contract_after: Account(
            storage=storage_after if after_error is None else {0: 0},
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_reservoir_available_after_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reservoir is available for state ops after the fork.

    Before the fork, tx.gas is capped at TX_MAX_GAS_LIMIT and there is
    no reservoir. After the fork, gas above the cap feeds the reservoir,
    which child calls can draw from for state operations.
    """
    after_fork = fork.fork_at(timestamp=15_000)
    child_code = Op.SSTORE(0, 1, original_value=0, new_value=1)
    sstore_state_gas = child_code.state_cost(after_fork)

    child_storage = Storage()
    child_storage.store_next(1, "child_slot_set")
    child = pre.deploy_contract(code=child_code)

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=Op.SSTORE(
            parent_storage.store_next(1, "subcall_succeeds"),
            Op.CALL(gas=child_code.execution_cost(after_fork), address=child),
        ),
    )

    blocks = [
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=parent,
                    state_gas_reservoir=sstore_state_gas,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
