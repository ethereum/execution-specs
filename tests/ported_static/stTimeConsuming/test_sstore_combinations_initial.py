"""
SSTORE combination tests for all initial storage states.

Exercises every combination of call types across four call slots,
varying the update-contract's initial storage state (0, 1, or 2).

Ported from all ``sstore_combinations_initial*_ParisFiller.json``
in ``state_tests/stTimeConsuming/``.
"""

from enum import StrEnum

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        "state_tests/stTimeConsuming/sstore_combinations_initial00_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial00_2_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial01_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial01_2_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial10_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial10_2_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial11_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial11_2_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial20_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial20_2_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial21_ParisFiller.json",
        "state_tests/stTimeConsuming/sstore_combinations_initial21_2_ParisFiller.json",
    ),
    pytest.mark.valid_from("Byzantium"),
    pytest.mark.slow,
]


class MidContractActions(StrEnum):
    """List of actions the middle contracts can perform."""

    NOOP = "noop"
    SSTORE_TOGGLE = "sstore-toggle"
    REVERT = "revert"


# Middle-action combinations: (call_opcode, side_contract_index).
# Side-contract indices: 0=noop, 1=sstore-toggle, 2=reverting.
MIDDLE_ACTIONS = [
    (op, t)
    for op in [
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
    ]
    for t in MidContractActions
]


@pytest.mark.parametrize(
    "update_storage_initial_value",
    range(3),
    ids=["initial0", "initial1", "initial2"],
)
@pytest.mark.parametrize(
    "call_4, call_4_target",
    MIDDLE_ACTIONS,
    ids=[f"call_4_{op}_{target}" for op, target in MIDDLE_ACTIONS],
)
@pytest.mark.parametrize(
    "call_3",
    [Op.STATICCALL, Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
)
@pytest.mark.parametrize(
    "call_2, call_2_target",
    MIDDLE_ACTIONS,
    ids=[f"call_2_{op}_{target}" for op, target in MIDDLE_ACTIONS],
)
@pytest.mark.parametrize(
    "call_1",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
)
def test_sstore_combinations_initial(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    update_storage_initial_value: int,
    call_1: Op,
    call_2: Op,
    call_2_target: MidContractActions,
    call_3: Op,
    call_4: Op,
    call_4_target: MidContractActions,
) -> None:
    """Test SSTORE with four interleaved calls."""
    sender = pre.fund_eoa()
    side = {
        # Noop / balance-only (no executable code)
        MidContractActions.NOOP: pre.deploy_contract(
            Bytecode(),
            balance=10,
            storage={0: 1, 1: 1, 2: 1},
        ),
        # SSTORE-toggle: flip slots 1..16, then set slot 1 = 1
        MidContractActions.SSTORE_TOGGLE: pre.deploy_contract(
            code=sum(
                Op.SSTORE(key=i, value=0x1) + Op.SSTORE(key=i, value=0x0)
                for i in range(0x1, 0x10 + 1)
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP,
        ),
        # Reverting contract
        MidContractActions.REVERT: pre.deploy_contract(
            code=Op.REVERT(offset=0x0, size=0x20) + Op.STOP,
            storage={0: 2, 1: 2, 2: 2},
        ),
    }

    update_contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        storage={
            0: update_storage_initial_value,
            1: update_storage_initial_value,
            2: update_storage_initial_value,
        }
        if update_storage_initial_value > 0
        else {},
    )
    sstore_toggle = side[MidContractActions.SSTORE_TOGGLE]

    call_gas = 0x493E0

    initcode = (
        Op.MSTORE(offset=0x64, value=0x0)
        + Op.POP(
            call_1(
                gas=call_gas,
                address=update_contract,
                args_size=0x20,
            )
        )
        + Op.POP(call_2(gas=call_gas, address=side[call_2_target]))
        + Op.POP(
            call_3(
                gas=call_gas,
                address=update_contract,
                args_size=0x20,
            )
        )
        + Op.POP(call_4(gas=call_gas, address=side[call_4_target]))
        + Op.CALL(gas=call_gas * 2, address=sstore_toggle)
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=2_000_000,
        value=1,
        protected=fork.supports_protected_txs(),
    )

    post = {
        sstore_toggle: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "update_storage_initial_value",
    range(3),
    ids=["initial0", "initial1", "initial2"],
)
def test_sstore_combinations_initial_staticcall_only(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    update_storage_initial_value: int,
) -> None:
    """Base case: STATICCALL to update-contract only."""
    sender = pre.fund_eoa()

    update_contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        storage={
            0: update_storage_initial_value,
            1: update_storage_initial_value,
            2: update_storage_initial_value,
        }
        if update_storage_initial_value > 0
        else {},
    )
    sstore_toggle = pre.deploy_contract(
        code=sum(
            Op.SSTORE(key=i, value=0x1) + Op.SSTORE(key=i, value=0x0)
            for i in range(0x1, 0x10 + 1)
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
    )

    call_gas = 0x493E0

    initcode = (
        Op.MSTORE(offset=0x64, value=0x0)
        + Op.POP(
            Op.STATICCALL(
                gas=call_gas,
                address=update_contract,
                args_size=0x20,
            )
        )
        + Op.CALL(gas=call_gas * 2, address=sstore_toggle)
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=2_000_000,
        value=1,
        protected=fork.supports_protected_txs(),
    )

    post = {
        sstore_toggle: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
