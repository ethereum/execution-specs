"""
Verify mutual A<->B recursion with value transfers and fixed gas asks.

Contract A calls B forwarding a fixed 100,000-gas ask with 24 wei; B
calls its caller back with a 50,000 ask and 23 wei, storing one plus
the result. Both store into a PC-derived slot only after their call
returns, so every level's store competes with what the descent left
behind: levels too deep to afford it halt and forfeit, rolling back
their stores and transfers, and the surviving storage and balances pin
exactly how far the budget reaches.

Ported from:
state_tests/stSystemOperationsTest/ABAcalls0Filler.json

@manually-enhanced: Do not overwrite. The post state (stores and
balances) is predicted by an exact fork-derived replay of the gas flow
(EIP-150 grants, stipend gifting and return, warm/cold and SSTORE
pricing via opcode metadata, EIP-8037 state-gas spill), validated
against the ported Cancun stores. B reaches A as its CALLER instead of
a hardcoded address, which shifts B's PC-derived slot; both slots are
computed from the assembled code.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

A_CALL_GAS = 100_000
A_CALL_VALUE = 0x18
B_CALL_GAS = 50_000
B_CALL_VALUE = 0x17
# One transfer per level up to the call-depth limit can never run dry.
A_INITIAL_BALANCE = A_CALL_VALUE * 1024
# Exactly one return payment before any income (the ported balance).
B_INITIAL_BALANCE = B_CALL_VALUE
# Ported budget; pins how deep the mutual recursion reaches.
TX_GAS_LIMIT = 1_000_000


def predict_final_state(
    fork: Fork, tx_gas_limit: int, b_address: Address
) -> tuple[int, int, int, int]:
    """
    Replay the mutual recursion's gas flow.

    Return A's stored value, B's stored value, and the committed
    balance deltas of A and B. Descend the alternating call chain
    computing each level's EIP-150 grant (both asks are pushed
    constants; a value-bearing call gifts the callee the stipend and
    gets any unused part back), then unwind: a level that cannot afford
    its post-call store (EIP-2200's stipend rule included) halts and
    forfeits its grant, reverting its own store and the transfer that
    funded it. Every cost is derived from the fork via opcode metadata,
    including EIP-8037 state gas: with a sub-cap gas limit the state
    reservoir is zero, so state charges spill from the charging frame's
    own gas.
    """
    stipend = fork.gas_costs().CALL_STIPEND
    pc_cost = Op.PC.gas_cost(fork)

    def raw_store_cost(key_warm: bool, current: int, new: int) -> int:
        """Cost of a bare SSTORE; original value is always zero here."""
        return Op.SSTORE(
            key_warm=key_warm,
            original_value=0,
            current_value=current,
            new_value=new,
        ).gas_cost(fork)

    # A's charges before forwarding: argument pushes plus the call's
    # upfront costs (B is cold only in the top level). The ask is a
    # pushed constant, so the whole call expression charges up front.
    def a_charges(b_warm: bool) -> int:
        return Op.CALL(
            gas=A_CALL_GAS,
            address=b_address,
            value=A_CALL_VALUE,
            address_warm=b_warm,
            value_transfer=True,
        ).gas_cost(fork)

    b_value_expr = Op.ADD(
        1,
        Op.CALL(
            gas=B_CALL_GAS,
            address=Op.CALLER,
            value=B_CALL_VALUE,
            # A is the transaction target: always warm.
            address_warm=True,
            value_transfer=True,
        ),
    )
    # B's ADD and its constant push run only after the call returns.
    b_post_call = Op.PUSH1[0].gas_cost(fork) + Op.ADD.gas_cost(fork)
    b_charges = b_value_expr.gas_cost(fork) - b_post_call

    # Descend: alternate A and B levels until one dies mid-charges.
    gas = (
        tx_gas_limit
        - fork.transaction_intrinsic_cost_calculator()()
        - fork.transaction_top_frame_state_gas()
    )
    levels: list[tuple[int, int]] = []
    level = 0
    balance = {"A": A_INITIAL_BALANCE, "B": B_INITIAL_BALANCE}
    while True:
        level += 1
        is_a = level % 2 == 1
        if is_a:
            gas -= a_charges(b_warm=level > 1)
            ask, value = A_CALL_GAS, A_CALL_VALUE
        else:
            gas -= b_charges
            ask, value = B_CALL_GAS, B_CALL_VALUE
        if gas < 0:
            break
        assert level < 1024, "recursion must die of gas, not depth"
        payer = "A" if is_a else "B"
        assert balance[payer] >= value, "value transfer must be funded"
        balance[payer] -= value
        balance["B" if is_a else "A"] += value
        forwarded = min(ask, gas - gas // 64)
        levels.append((gas, forwarded))
        gas = forwarded + stipend

    # Unwind: a failed level forfeits its grant and reverts the whole
    # committed state below it (stores, warmth, and transfers).
    child_ok = False
    leftover = 0
    a_val, a_warm, b_val, b_warm = 0, False, 0, False
    a_delta, b_delta = 0, 0
    for lvl in range(len(levels), 0, -1):
        available, forwarded = levels[lvl - 1]
        is_a = lvl % 2 == 1
        gas = available - forwarded + (leftover if child_ok else 0)
        result = 1 if child_ok else 0
        if is_a:
            gas -= pc_cost
            store_value, current, warm = result, a_val, a_warm
        else:
            gas -= b_post_call + pc_cost
            store_value, current, warm = 1 + result, b_val, b_warm
        ok = gas >= 0 and gas > stipend
        if ok:
            gas -= raw_store_cost(warm, current, store_value)
            ok = gas >= 0
        if ok:
            # Commit this level: its store and the transfer into it.
            if is_a:
                a_val, a_warm = store_value, True
                if lvl > 1:
                    a_delta += B_CALL_VALUE
                    b_delta -= B_CALL_VALUE
            else:
                b_val, b_warm = store_value, True
                a_delta -= A_CALL_VALUE
                b_delta += A_CALL_VALUE
            leftover = gas
            child_ok = True
        else:
            child_ok = False
            leftover = 0
            a_val, a_warm, b_val, b_warm = 0, False, 0, False
            a_delta, b_delta = 0, 0
    assert child_ok, "the top level must complete"
    return a_val, b_val, a_delta, b_delta


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/ABAcalls0Filler.json"],
)
@pytest.mark.valid_from("Berlin")
def test_ab_acalls0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Pin how deep a value-bearing A<->B recursion reaches."""
    # B calls whoever called it, so it needs no embedded address.
    b_value_expr = Op.ADD(
        1,
        Op.CALL(gas=B_CALL_GAS, address=Op.CALLER, value=B_CALL_VALUE),
    )
    contract_b = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=b_value_expr) + Op.STOP,
        balance=B_INITIAL_BALANCE,
    )

    a_value_expr = Op.CALL(
        gas=A_CALL_GAS, address=contract_b, value=A_CALL_VALUE
    )
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=a_value_expr) + Op.STOP,
        balance=A_INITIAL_BALANCE,
    )

    # PC keys: each store's key is the code offset of its PC opcode,
    # which sits right after the assembled value expression.
    a_key = len(bytes(a_value_expr))
    b_key = len(bytes(b_value_expr))

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_a,
        gas_limit=TX_GAS_LIMIT,
    )

    a_val, b_val, a_delta, b_delta = predict_final_state(
        fork, TX_GAS_LIMIT, contract_b
    )
    post = {
        contract_a: Account(
            storage={a_key: a_val},
            balance=A_INITIAL_BALANCE + a_delta,
        ),
        contract_b: Account(
            storage={b_key: b_val},
            balance=B_INITIAL_BALANCE + b_delta,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
