"""Tests for SSTORE combinations across nested call types."""

from enum import StrEnum

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2200.md"
REFERENCE_SPEC_VERSION = "ad4eaaa1fe5c7aa394b2ab09e885b73b898f5da0"

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
]


# Writes slots 0..2 of the executing frame's storage account.
UPDATE_CONTRACT_CODE = (
    Op.SSTORE(key=0x0, value=0x0)
    + Op.SSTORE(key=0x1, value=0x1)
    + Op.SSTORE(key=0x2, value=0x2)
    + Op.STOP
)

# Flip slots 1..16 to accumulate net-metering refunds, then set slot 1.
SSTORE_TOGGLE_CODE = (
    sum(
        Op.SSTORE(key=i, value=0x1) + Op.SSTORE(key=i, value=0x0)
        for i in range(0x1, 0x10 + 1)
    )
    + Op.SSTORE(key=0x1, value=0x1)
    + Op.STOP
)


class MidContractActions(StrEnum):
    """List of actions the middle contracts can perform."""

    NOOP = "noop"
    SSTORE_TOGGLE = "sstore-toggle"
    REVERT = "revert"


# Middle-action combinations: (call_opcode, side_contract_kind).
# The no-op contract has no code and the reverting contract performs no
# SSTORE, so for those two targets the calling opcode is unobservable:
# CALL and CALLCODE produce identical executions, as do DELEGATECALL and
# STATICCALL (confirmed by tracing all combinations), and one opcode of
# each pair is kept. The storage-toggling contract behaves differently
# under each opcode, so all four are kept there.
MIDDLE_ACTIONS = [
    (op, MidContractActions.SSTORE_TOGGLE)
    for op in [
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
    ]
] + [
    (op, t)
    for op in [Op.CALL, Op.DELEGATECALL]
    for t in [MidContractActions.NOOP, MidContractActions.REVERT]
]


@pytest.mark.parametrize("initial", range(3))
@pytest.mark.parametrize("call_4, call_4_target", MIDDLE_ACTIONS)
@pytest.mark.parametrize("call_3", [Op.CALL, Op.DELEGATECALL])
@pytest.mark.parametrize("call_2, call_2_target", MIDDLE_ACTIONS)
@pytest.mark.parametrize("call_1", [Op.CALL, Op.DELEGATECALL])
def test_sstore_combinations_initial(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initial: int,
    call_1: Op,
    call_2: Op,
    call_2_target: MidContractActions,
    call_3: Op,
    call_4: Op,
    call_4_target: MidContractActions,
) -> None:
    """
    Test SSTORE with four interleaved calls.

    Exercises every combination of call types across four call slots,
    varying the update-contract's initial storage state (0, 1, or 2).
    Valid from Byzantium (REVERT and STATICCALL availability) so the
    pre-EIP-2200 storage gas rules are covered as a baseline.
    Consolidated replacement for the twelve legacy
    ``sstore_combinations_initial*_ParisFiller.json`` fillers from
    ``state_tests/stTimeConsuming/``.
    """
    sender = pre.fund_eoa()

    def deploy_side(kind: MidContractActions) -> Address:
        if kind == MidContractActions.NOOP:
            return pre.deploy_contract(Bytecode())
        if kind == MidContractActions.SSTORE_TOGGLE:
            return pre.deploy_contract(code=SSTORE_TOGGLE_CODE)
        return pre.deploy_contract(
            code=Op.REVERT(offset=0x0, size=0x20) + Op.STOP,
        )

    side = {
        kind: deploy_side(kind)
        for kind in MidContractActions
        if kind
        in {call_2_target, call_4_target, MidContractActions.SSTORE_TOGGLE}
    }

    update_contract = pre.deploy_contract(
        code=UPDATE_CONTRACT_CODE,
        storage={0: initial, 1: initial, 2: initial} if initial > 0 else {},
    )
    sstore_toggle = side[MidContractActions.SSTORE_TOGGLE]

    call_gas = SSTORE_TOGGLE_CODE.gas_cost(fork)

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
        + Op.CALL(gas=call_gas, address=sstore_toggle)
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        value=1,
        protected=fork.supports_protected_txs(),
    )

    post = {
        sstore_toggle: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("dirty", [False, True])
@pytest.mark.parametrize("initial", range(3))
def test_sstore_combinations_initial_staticcall_only(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initial: int,
    dirty: bool,
) -> None:
    """
    Test a STATICCALL to the update contract, whose SSTORE must fault.

    With dirty=True a plain CALL to the update contract runs first, so
    the faulting SSTORE observes a slot whose current value already
    differs from its original value.
    """
    sender = pre.fund_eoa()

    update_contract = pre.deploy_contract(
        code=UPDATE_CONTRACT_CODE,
        storage={0: initial, 1: initial, 2: initial} if initial > 0 else {},
    )
    sstore_toggle = pre.deploy_contract(code=SSTORE_TOGGLE_CODE)

    call_gas = SSTORE_TOGGLE_CODE.gas_cost(fork)

    dirtying_call = (
        Op.POP(Op.CALL(gas=call_gas, address=update_contract, args_size=0x20))
        if dirty
        else Bytecode()
    )
    initcode = (
        Op.MSTORE(offset=0x64, value=0x0)
        + dirtying_call
        + Op.POP(
            Op.STATICCALL(
                gas=call_gas,
                address=update_contract,
                args_size=0x20,
            )
        )
        + Op.CALL(gas=call_gas, address=sstore_toggle)
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        value=1,
        protected=fork.supports_protected_txs(),
    )

    post = {
        sstore_toggle: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
