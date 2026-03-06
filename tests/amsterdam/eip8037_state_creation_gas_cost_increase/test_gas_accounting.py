"""Tests for EIP-8037 gas validation and code-deposit edge cases."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
)

from .spec import Spec, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.exception_test
@pytest.mark.with_all_contract_creating_tx_types()
def test_create_tx_intrinsic_gas_includes_state_component(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
) -> None:
    """
    Contract-creating transactions must include the EIP-8037 intrinsic state
    gas for account creation.
    """
    intrinsic_gas = 21_000 + Spec.CREATE_REGULAR + Spec.CREATE_STATE

    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=None,
        data=b"",
        gas_limit=intrinsic_gas - 1,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.exception_test
def test_set_code_tx_intrinsic_gas_includes_state_component(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Set-code transactions must include the EIP-8037 intrinsic state gas for
    each authorization.
    """
    intrinsic_gas = 21_000 + Spec.PER_AUTH_BASE_REGULAR + Spec.TOTAL_AUTH_STATE
    auth_signer = pre.fund_eoa()
    delegated_to = pre.fund_eoa(0)
    destination = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        ty=4,
        sender=pre.fund_eoa(),
        to=destination,
        gas_limit=intrinsic_gas - 1,
        authorization_list=[
            AuthorizationTuple(
                address=delegated_to,
                nonce=0,
                signer=auth_signer,
            )
        ],
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "gas_limit,error",
    [
        pytest.param(
            23_000,
            TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
            id="below_floor",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(25_000, None, id="at_floor"),
    ],
)
def test_floor_gas_is_still_enforced_when_state_gas_is_enabled(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_limit: int,
    error: TransactionException | None,
) -> None:
    """
    Amsterdam inherits EIP-7623 floor gas, so below-floor calldata-heavy
    transactions must still be rejected when EIP-8037 is active.
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.fund_eoa(0),
        data=b"\x01" * 100,
        gas_limit=gas_limit,
        error=error,
    )

    state_test(pre=pre, post={}, tx=tx)


def test_nested_create_code_deposit_does_not_borrow_parent_regular_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A CREATE child that ends initcode execution with 1,175 regular gas must
    fail a 1-byte code deposit, which needs 6 regular gas plus a 1,174 gas
    state spill.
    """
    initcode = Op.PUSH1(1) + Op.PUSH1(0) + Op.RETURN
    factory_code = (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode)))
        + Op.POP(Op.CREATE(offset=32 - len(initcode), size=len(initcode)))
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    created_contract = compute_create_address(address=factory, nonce=1)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        # 54,225 is the smallest tx gas limit that makes the inner CREATE
        # finish initcode with 1,175 gas: enough for the 6-gas regular
        # pre-check, but not enough for the 6 + 1,174 state-spill deposit.
        gas_limit=54_225,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            factory: Account(nonce=2),
            created_contract: Account.NONEXISTENT,
        },
    )
