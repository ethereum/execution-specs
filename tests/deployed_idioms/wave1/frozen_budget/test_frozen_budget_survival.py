"""
Frozen-budget survival: a deployed caller forwards a hardcoded gas
operand and depends on the callee completing.

This is the archetype the official suite structurally cannot contain.
Every official test that touches a repriced opcode derives its budget
from the fork -- `probe_code.execution_cost(fork)`,
`SSTORE_TOGGLE_CODE.gas_cost(fork)`, `child_execution * 64 // 63` --
so the budget moves with the gas schedule and the test cannot fail when
a cost changes. The only frozen operands left in the tree
(`ported_static/stPreCompiledContracts{,2}/`, `gas=0xBB8`) target
operations that were never repriced. See `docs/COVERAGE-GAP.md`.

Deployed contracts do the opposite: the operand is a constant compiled
into immutable code and cannot be rebased. The invariant such a caller
relies on is "the callee still fits in the budget I froze". This test
asserts that invariant directly, so a future reprice that pushes the
callee past the frozen operand fails a test instead of shipping.

These tests are intentionally fragile: a failure means a real on-chain
idiom just broke. Do not repair one by raising `FROZEN_*` -- that
deletes the alarm. That is how the legacy frozen-budget corpus lost its
canaries (`@manually-enhanced`: "Do not hardcode the Amsterdam
number.").
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Frozen gas operands taken from deployed mainnet code. Each is a
# literal in immutable bytecode, so it cannot be rebased by a fork.
FROZEN_BUDGETS = {
    # a deployed randomness coordinator forwards the consumer-supplied
    # callbackGasLimit, capped at 2_500_000 by the coordinator; 200_000
    # is the value the overwhelming majority of deployed consumers
    # request, and it is a compile-time constant in the consumer.
    "vrf_callback_200k": 200_000,
    # Circle a cross-chain transfer protocol MessageTransmitter-style relayer budget.
    "cctp_relay_250k": 250_000,
    # a deployed staking-pod module: `_SHARE_POD_GAS_LIMIT = 140_000` is a Solidity
    # `constant`, and DelegatedShare's `podCallGasLimit` is `immutable`,
    # so neither can be raised without redeploying. Confirmed live by
    # eth_call at block ~26,245,933: `podCallGasLimit() == 140000`
    # (8037-coordination/findings/mainnet-a deployed DEX aggregator-podmodule-farms.md).
    # This is the tightest known deployed budget: it clears the measured
    # Amsterdam floor by only ~1.27x, so it is the corpus's most
    # sensitive canary. See README.md.
    "podmodule_pod_call_140k": 140_000,
}

@pytest.mark.parametrize(
    "frozen_gas",
    [pytest.param(v, id=k) for k, v in FROZEN_BUDGETS.items()],
)
@pytest.mark.valid_from("Berlin")
def test_frozen_budget_callee_commits_fresh_store(
    state_test: StateTestFiller,
    pre: Alloc,
    frozen_gas: int,
) -> None:
    """
    Test a callee writing one fresh storage slot still fits a frozen
    gas operand forwarded by its caller.

    The callee performs the single most repriced operation in Ethereum's
    history -- creating a storage slot that did not exist -- and the
    caller forwards a budget it froze at deployment. Both the callee's
    write and the caller's success marker are asserted, so the test
    distinguishes "callee completed" from "call returned 0".

    The transaction pins `state_gas_reservoir=0`, which is the hostile
    and realistic case for a legacy caller: there is no reservoir to
    absorb an EIP-8037 state charge, so the charge must fit inside the
    frozen operand like any other cost.
    """
    callee_storage = Storage()
    callee_code = Op.SSTORE(callee_storage.store_next(1, "work_committed"), 1) + Op.STOP
    callee = pre.deploy_contract(callee_code)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.SSTORE(
            caller_storage.store_next(1, "callee_succeeded"),
            Op.CALL(gas=frozen_gas, address=callee),
        )
        + Op.STOP
    )

    tx = Transaction(
        to=caller,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        callee: Account(storage=callee_storage),
        caller: Account(storage=caller_storage),
    }
    state_test(pre=pre, post=post, tx=tx)
