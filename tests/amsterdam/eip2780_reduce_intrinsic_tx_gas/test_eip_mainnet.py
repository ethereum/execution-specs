"""
Mainnet-marked tests for
[EIP-2780: Resource-based intrinsic transaction gas](https://eips.ethereum.org/EIPS/eip-2780).

One case per row of the EIP's transaction reference table. This EIP only
reprices, so the pinned ``cumulative_gas_used`` is the sole observable
that catches a client still charging the legacy intrinsic.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    Initcode,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .helpers import (
    EOA_INITIAL_BALANCE,
    RECIPIENT_TYPES_NON_CREATE,
    AuthorizationAction,
    authorization_transaction_cost,
    build_authorization,
    setup_target,
)
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = [pytest.mark.valid_at("EIP2780"), pytest.mark.mainnet]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("recipient_type", RECIPIENT_TYPES_NON_CREATE)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_transaction_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    recipient_type: RecipientType,
    value: int,
) -> None:
    """Gas for a non-create transaction, per recipient type and value."""
    sender = pre.fund_eoa()
    target = setup_target(pre, recipient_type, sender)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=recipient_type,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=recipient_type,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=recipient_type,
    )
    gas_used = intrinsic_gas + top_frame_gas + top_frame_state_gas

    tx = Transaction(
        to=target,
        value=value,
        gas_limit=gas_used,
        sender=sender,
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )

    post: dict[Address, Account | None] = {sender: Account(nonce=1)}
    if recipient_type != RecipientType.SELF:
        target_initial_balance = (
            EOA_INITIAL_BALANCE if recipient_type == RecipientType.EOA else 0
        )
        if recipient_type == RecipientType.EMPTY_ACCOUNT and value == 0:
            post[target] = None
        else:
            post[target] = Account(balance=target_initial_balance + value)

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_contract_creation_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    value: int,
) -> None:
    """Gas for a contract-creation transaction, per value."""
    sender = pre.fund_eoa()
    deploy_code = Op.STOP
    init_code = Initcode(deploy_code=deploy_code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )
    new_account_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    gas_used = intrinsic_gas + new_account_state_gas + init_code.gas_cost(fork)

    tx = Transaction(
        to=None,
        value=value,
        data=init_code,
        gas_limit=gas_used,
        sender=sender,
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )

    created = compute_create_address(address=sender, nonce=0)
    post = {created: Account(balance=value, code=deploy_code)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "action",
    [
        pytest.param(AuthorizationAction.CREATES_ACCOUNT, id="new_authority"),
        pytest.param(
            AuthorizationAction.SETS_NEW_DELEGATION, id="existing_authority"
        ),
    ],
)
def test_authorization_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    action: AuthorizationAction,
) -> None:
    """Gas for one EIP-7702 authorization, per authority pre-state."""
    scenario = build_authorization(pre, action)
    authorization_list = [scenario.authorization]
    gas_used = authorization_transaction_cost(fork, authorization_list)

    tx = Transaction(
        to=pre.deploy_contract(code=Op.STOP),
        authorization_list=authorization_list,
        gas_limit=gas_used,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )

    post = {scenario.authority: scenario.applied_account}
    state_test(pre=pre, post=post, tx=tx)
