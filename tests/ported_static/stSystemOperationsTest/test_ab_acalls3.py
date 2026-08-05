"""
Verify mutual A<->B recursion where each side reserves 100,000 gas.

Both contracts bump their own depth counter during descent, then call
the other side forwarding everything but a 100,000-gas reserve (A sends
one wei each level; B sends nothing back). Nothing runs after the call,
so only the single deepest level dies of gas and every completed
level's counter bump and transfer persist: the counters and balances
pin exactly how many rounds the budget sustains.

Ported from:
state_tests/stSystemOperationsTest/ABAcalls3Filler.json

@manually-enhanced: Do not overwrite. The post state (counters and
balances) is predicted by an exact fork-derived replay of the gas flow
(EIP-150 grants, stipend gifting, warm/cold and SSTORE pricing via
opcode metadata, EIP-8037 state-gas spill), validated against the
ported Cancun counters. B reaches A as its CALLER instead of a
hardcoded address.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

COUNTER_SLOT = 0
# Gas each level keeps back for itself before forwarding the rest.
GAS_RESERVE = 100_000
A_CALL_VALUE = 1
# One transfer per level up to the call-depth limit can never run dry.
A_INITIAL_BALANCE = A_CALL_VALUE * 1024
# Ported budget; pins how many rounds the recursion sustains.
TX_GAS_LIMIT = 10_000_000


def predict_depths(
    fork: Fork, tx_gas_limit: int, b_address: Address
) -> tuple[int, int]:
    """
    Replay the mutual recursion's gas flow.

    Return how many A and B levels complete. Descend the alternating
    call chain: each level bumps its own counter (one cold set per
    contract, then dirty rewrites), pays its call charges, and forwards
    everything but the reserve under the EIP-150 63/64 rule; once the
    reserve underflows, the wrapped ask forwards the 63/64 maximum.
    Nothing runs after a call, so only the single deepest level dies
    and its bump and incoming transfer revert. Every cost is derived
    from the fork via opcode metadata, including EIP-8037 state gas:
    with a sub-cap gas limit the state reservoir is zero, so state
    charges spill from the charging frame's own gas.
    """
    push_cost = Op.PUSH1[0].gas_cost(fork)
    # The ask expression's SUB runs after GAS reads gas_left.
    post_gas_read = Op.SUB.gas_cost(fork)
    # EIP-2200: any SSTORE with gas_left <= stipend halts exceptionally.
    stipend = fork.gas_costs().CALL_STIPEND

    def raw_store_cost(key_warm: bool, current: int, new: int) -> int:
        """Cost of a bare SSTORE; original value is always zero here."""
        return Op.SSTORE(
            key_warm=key_warm,
            original_value=0,
            current_value=current,
            new_value=new,
        ).gas_cost(fork)

    sstore_warm_set = raw_store_cost(True, 0, 1)
    sstore_warm_dirty = raw_store_cost(True, 1, 2)

    def bump_statics(key_warm: bool) -> int:
        """Counter-bump costs before its SSTORE (value expr plus key)."""
        return (
            Op.ADD(Op.SLOAD(key=COUNTER_SLOT, key_warm=key_warm), 1).gas_cost(
                fork
            )
            + push_cost
        )

    def call_split(
        address: Address | Op, warm: bool, value: int
    ) -> tuple[int, int]:
        """Pre-GAS-read and upfront charges of one side's call."""
        upfront = Op.CALL(
            address_warm=warm, value_transfer=value > 0
        ).gas_cost(fork)
        composite = Op.CALL(
            gas=Op.SUB(Op.GAS, GAS_RESERVE),
            address=address,
            value=value,
            address_warm=warm,
            value_transfer=value > 0,
        ).gas_cost(fork)
        return composite - upfront - post_gas_read, upfront

    a_pre, a_upfront_cold = call_split(b_address, False, A_CALL_VALUE)
    _, a_upfront_warm = call_split(b_address, True, A_CALL_VALUE)
    # A is the transaction target: always warm for B's call back.
    b_pre, b_upfront = call_split(Op.CALLER, True, 0)

    gas = (
        tx_gas_limit
        - fork.transaction_intrinsic_cost_calculator()()
        - fork.transaction_top_frame_state_gas()
    )
    level = 0
    a_balance = A_INITIAL_BALANCE
    while True:
        level += 1
        is_a = level % 2 == 1
        # Each contract's first level pays the cold counter set.
        first = level <= 2
        gas -= bump_statics(key_warm=not first)
        if gas < 0 or gas <= stipend:
            break
        gas -= sstore_warm_set if first else sstore_warm_dirty
        if gas < 0:
            break
        gas -= a_pre if is_a else b_pre
        if gas < 0:
            break
        gas_read = gas
        if is_a:
            gas -= post_gas_read + (
                a_upfront_cold if level == 1 else a_upfront_warm
            )
        else:
            gas -= post_gas_read + b_upfront
        if gas < 0:
            break
        assert level < 1024, "recursion must die of gas, not depth"
        if is_a:
            assert a_balance >= A_CALL_VALUE, "transfer must be funded"
            a_balance -= A_CALL_VALUE
        # A reserve underflow wraps mod 2**256: an effectively infinite
        # ask, clamped to the 63/64 forwardable maximum.
        ask = gas_read - GAS_RESERVE if gas_read >= GAS_RESERVE else 1 << 256
        forwarded = min(ask, gas - gas // 64)
        gas = forwarded + (stipend if is_a else 0)

    completed = level - 1
    assert completed >= 2, "both sides must run at least once"
    a_count = (completed + 1) // 2
    b_count = completed // 2
    return a_count, b_count


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/ABAcalls3Filler.json"],
)
@pytest.mark.valid_from("Berlin")
def test_ab_acalls3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Pin how many rounds a reserve-throttled A<->B recursion runs."""

    def bounce_code(call: Bytecode) -> Bytecode:
        """Bump the own-depth counter, then call the other side."""
        return (
            Op.SSTORE(
                key=COUNTER_SLOT,
                value=Op.ADD(Op.SLOAD(key=COUNTER_SLOT), 1),
            )
            + call
            + Op.STOP
        )

    # B calls whoever called it, so it needs no embedded address.
    contract_b = pre.deploy_contract(
        code=bounce_code(
            Op.CALL(gas=Op.SUB(Op.GAS, GAS_RESERVE), address=Op.CALLER)
        ),
    )
    contract_a = pre.deploy_contract(
        code=bounce_code(
            Op.CALL(
                gas=Op.SUB(Op.GAS, GAS_RESERVE),
                address=contract_b,
                value=A_CALL_VALUE,
            )
        ),
        balance=A_INITIAL_BALANCE,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_a,
        gas_limit=TX_GAS_LIMIT,
    )

    a_count, b_count = predict_depths(fork, TX_GAS_LIMIT, contract_b)
    # Each completed B level keeps the wei its calling A level sent.
    post = {
        contract_a: Account(
            storage={COUNTER_SLOT: a_count},
            balance=A_INITIAL_BALANCE - b_count * A_CALL_VALUE,
        ),
        contract_b: Account(
            storage={COUNTER_SLOT: b_count},
            balance=b_count * A_CALL_VALUE,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
