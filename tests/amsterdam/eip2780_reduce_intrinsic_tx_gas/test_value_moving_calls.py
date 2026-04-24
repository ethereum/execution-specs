"""
Tests for EIP-2780 Reduce Transaction Intrinsic Cost.

Tests that value-moving CALL opcodes charge gas correctly under
Amsterdam's split cold access and restructured value transfer costs.
"""

import enum
from typing import Callable, Optional

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks.gas_costs import GasCosts

from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


class AccessScenario(enum.Enum):
    """Which access cost threshold is being tested."""

    WARM = "warm"
    COLD_NOCODE = "cold_nocode"
    COLD_CODE = "cold_code"


class AccessSuccess(enum.Enum):
    """Whether the gas check at the tested threshold passes."""

    OOG = "oog"
    SUCCESS = "success"


def compute_scenario_gas(
    access: AccessScenario,
    gsc: GasCosts,
) -> int:
    """Return the gas threshold for the given access scenario."""
    match access:
        case AccessScenario.WARM:
            return gsc.WARM_ACCESS
        case AccessScenario.COLD_NOCODE:
            return gsc.COLD_ACCOUNT_COST_NO_CODE
        case AccessScenario.COLD_CODE:
            return gsc.COLD_ACCOUNT_COST_CODE


PostFn = Callable[[Address, Address, int, bool], dict[Address, Account]]


def _run_call_test(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    access: AccessScenario,
    success: AccessSuccess,
    caller_code_fn: Callable[[Address, int], Bytecode],
    n_args: int,
    value: int,
    has_value_transfer: bool,
    account_new: bool,
    post_fn: PostFn,
    is_self_call: bool = False,
) -> None:
    """
    Core logic shared by all CALL-family opcode tests.

    Deploys or allocates a target, builds a caller that invokes it,
    and asserts post-state based on the access/success combination.
    """
    gsc = fork.gas_costs()
    target_is_warm = access == AccessScenario.WARM
    target_has_code = not account_new

    if account_new:
        target = Address(pre.fund_eoa(amount=0))
    else:
        target = pre.deploy_contract(code=Op.STOP)

    code = caller_code_fn(target, value)
    caller = pre.deploy_contract(code=code, balance=value)
    alice = pre.fund_eoa()

    access_list: Optional[list[AccessList]] = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        recipient_type=RecipientType.CONTRACT,
        return_cost_deducted_prior_execution=True,
    )
    bytecode_cost = gsc.VERY_LOW * n_args

    # Value cost depends on whether the transfer is a self-call and on
    # whether the target is new or existing. Self-calls charge only a
    # single STATE_UPDATE with no TRANSFER_LOG_COST (EIP-7708 does not
    # emit a log for self-transfers).
    value_cost = 0
    if has_value_transfer and value > 0:
        if is_self_call:
            value_cost = gsc.STATE_UPDATE
        elif account_new:
            value_cost = (
                gsc.STATE_UPDATE + gsc.NEW_ACCOUNT + gsc.TRANSFER_LOG_COST
            )
        else:
            value_cost = 2 * gsc.STATE_UPDATE + gsc.TRANSFER_LOG_COST

    # Gas for the tested threshold, minus 1 for OOG.
    scenario_gas = compute_scenario_gas(access, gsc)
    if success == AccessSuccess.OOG:
        scenario_gas -= 1

    gas_limit = intrinsic_cost + bytecode_cost + scenario_gas

    # Overall OOG: true unless we pass the highest applicable
    # threshold for this target.
    if success == AccessSuccess.OOG:
        is_oog = True
    elif access in (AccessScenario.WARM, AccessScenario.COLD_CODE):
        is_oog = False
    else:
        # COLD_NOCODE + SUCCESS: only overall success if target
        # has no code (no second check_gas to fail).
        is_oog = target_has_code

    if not is_oog:
        gas_limit += value_cost

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    post = post_fn(caller, target, value, is_oog)

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.parametrize(
    "account_new",
    [
        pytest.param(False, id="existing_target"),
        pytest.param(True, id="new_account"),
    ],
)
@pytest.mark.parametrize(
    "access",
    list(AccessScenario),
    ids=lambda a: a.value,
)
@pytest.mark.parametrize(
    "success",
    list(AccessSuccess),
    ids=lambda s: s.value,
)
def test_call(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
    account_new: bool,
    access: AccessScenario,
    success: AccessSuccess,
) -> None:
    """
    Test CALL opcode gas charging under EIP-2780.

    CALL transfers value from caller to target. With value > 0, the
    value cost is ``2 * STATE_UPDATE + TRANSFER_LOG_COST`` for existing
    targets or ``STATE_UPDATE + NEW_ACCOUNT + TRANSFER_LOG_COST`` for
    new accounts.
    """
    if account_new and access == AccessScenario.COLD_CODE:
        pytest.skip("Empty target has no code")

    def caller_code_fn(target: Address, val: int) -> Bytecode:
        return Op.CALL(
            gas=0,
            address=target,
            value=val,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )

    def post_fn(
        caller: Address,
        target: Address,
        value: int,
        is_oog: bool,
    ) -> dict[Address, Account]:
        if is_oog:
            if account_new:
                return {caller: Account(balance=value)}
            return {
                caller: Account(balance=value),
                target: Account(balance=0, code=Op.STOP),
            }
        if value > 0:
            target_account = (
                Account(balance=value)
                if account_new
                else Account(balance=value, code=Op.STOP)
            )
            return {
                caller: Account(balance=0),
                target: target_account,
            }
        if account_new:
            # No value sent: target stays non-existent
            return {caller: Account(balance=0)}
        return {
            caller: Account(balance=0),
            target: Account(balance=0, code=Op.STOP),
        }

    _run_call_test(
        fork=fork,
        pre=pre,
        state_test=state_test,
        access=access,
        success=success,
        caller_code_fn=caller_code_fn,
        n_args=7,
        value=value,
        has_value_transfer=True,
        account_new=account_new,
        post_fn=post_fn,
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.parametrize(
    "access",
    list(AccessScenario),
    ids=lambda a: a.value,
)
@pytest.mark.parametrize(
    "success",
    list(AccessSuccess),
    ids=lambda s: s.value,
)
def test_callcode(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
    access: AccessScenario,
    success: AccessSuccess,
) -> None:
    """
    Test CALLCODE opcode gas charging under EIP-2780.

    CALLCODE transfers value to self (caller), so there is no net
    balance change even on success with value > 0. The value cost is
    a single ``STATE_UPDATE`` with no ``TRANSFER_LOG_COST`` because
    EIP-7708 does not emit a log for self-transfers.
    """

    def caller_code_fn(target: Address, val: int) -> Bytecode:
        return Op.CALLCODE(
            gas=0,
            address=target,
            value=val,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )

    def post_fn(
        caller: Address,
        target: Address,
        value: int,
        _is_oog: bool,
    ) -> dict[Address, Account]:
        # CALLCODE transfers value to self: no net change
        return {
            caller: Account(balance=value),
            target: Account(balance=0, code=Op.STOP),
        }

    _run_call_test(
        fork=fork,
        pre=pre,
        state_test=state_test,
        access=access,
        success=success,
        caller_code_fn=caller_code_fn,
        n_args=7,
        value=value,
        has_value_transfer=True,
        account_new=False,
        post_fn=post_fn,
        is_self_call=True,
    )


@pytest.mark.parametrize(
    "access",
    list(AccessScenario),
    ids=lambda a: a.value,
)
@pytest.mark.parametrize(
    "success",
    list(AccessSuccess),
    ids=lambda s: s.value,
)
def test_delegatecall(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    access: AccessScenario,
    success: AccessSuccess,
) -> None:
    """
    Test DELEGATECALL opcode gas charging under EIP-2780.

    DELEGATECALL does not transfer value. Only access costs apply.
    """

    def caller_code_fn(target: Address, _val: int) -> Bytecode:
        return Op.DELEGATECALL(
            gas=0,
            address=target,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )

    def post_fn(
        caller: Address,
        target: Address,
        _value: int,
        _is_oog: bool,
    ) -> dict[Address, Account]:
        return {
            caller: Account(balance=0),
            target: Account(balance=0, code=Op.STOP),
        }

    _run_call_test(
        fork=fork,
        pre=pre,
        state_test=state_test,
        access=access,
        success=success,
        caller_code_fn=caller_code_fn,
        n_args=6,
        value=0,
        has_value_transfer=False,
        account_new=False,
        post_fn=post_fn,
    )


@pytest.mark.parametrize(
    "access",
    list(AccessScenario),
    ids=lambda a: a.value,
)
@pytest.mark.parametrize(
    "success",
    list(AccessSuccess),
    ids=lambda s: s.value,
)
def test_staticcall(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    access: AccessScenario,
    success: AccessSuccess,
) -> None:
    """
    Test STATICCALL opcode gas charging under EIP-2780.

    STATICCALL does not transfer value. Only access costs apply.
    """

    def caller_code_fn(target: Address, _val: int) -> Bytecode:
        return Op.STATICCALL(
            gas=0,
            address=target,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )

    def post_fn(
        caller: Address,
        target: Address,
        _value: int,
        _is_oog: bool,
    ) -> dict[Address, Account]:
        return {
            caller: Account(balance=0),
            target: Account(balance=0, code=Op.STOP),
        }

    _run_call_test(
        fork=fork,
        pre=pre,
        state_test=state_test,
        access=access,
        success=success,
        caller_code_fn=caller_code_fn,
        n_args=6,
        value=0,
        has_value_transfer=False,
        account_new=False,
        post_fn=post_fn,
    )
