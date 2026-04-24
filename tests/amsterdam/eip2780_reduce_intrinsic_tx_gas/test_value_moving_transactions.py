"""
Tests for EIP-2780 Reduce Transaction Intrinsic Cost.

Test gas costs with EIP-2780 for value-moving transactions to:
- EOAs,
- contracts,
- empty accounts.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Fork,
    Initcode,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "recipient_type",
    [
        RecipientType.EOA,
        RecipientType.CONTRACT,
        RecipientType.EMPTY_ACCOUNT,
    ],
)
@pytest.mark.parametrize(
    "warm_target",
    [True, False],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_value_moving_transactions(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    recipient_type: RecipientType,
    warm_target: bool,
    value: int,
) -> None:
    """Ensure value moving transactions charge gas correctly."""
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    target_initial_balance = 0
    target: Address

    match recipient_type:
        case RecipientType.EOA:
            # ETH transfer to EOA
            target_initial_balance = 100
            target = pre.fund_eoa(amount=target_initial_balance)

        case RecipientType.CONTRACT:
            # ETH transfer to contract
            target = pre.deploy_contract(code=Op.STOP)

        case RecipientType.EMPTY_ACCOUNT:
            # ETH transfer to empty account
            target = pre.fund_eoa(amount=0)

        case _:
            raise ValueError(f"Unknown recipient type {recipient_type}")

    access_list = []
    if warm_target:
        access_list.append(AccessList(address=target, storage_keys=[]))

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    total_gas_cost = intrinsic_gas_calculator(
        access_list=access_list,
        sends_value=bool(value),
        recipient_type=recipient_type,
        recipient_is_warm=warm_target,
        return_cost_deducted_prior_execution=True,
    )

    tx_gas_limit = total_gas_cost + 1000  # add a small buffer
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        access_list=access_list,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    # Account for both the value sent and gas cost (gas_price * gas_used)
    sender_final_balance = (
        sender_initial_balance - value - (total_gas_cost * gas_price)
    )
    if recipient_type == RecipientType.EMPTY_ACCOUNT and value == 0:
        expected_target = None
    else:
        expected_target = Account(balance=target_initial_balance + value)

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: expected_target,
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "warm_target",
    [True, False],
)
@pytest.mark.parametrize(
    "warm_delegation",
    [True, False],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_value_moving_transaction_to_delegated_eoa(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    warm_target: bool,
    warm_delegation: bool,
    value: int,
) -> None:
    """
    Ensure value moving transactions to 7702 delegated EOAs
    charge gas correctly.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = pre.deploy_contract(code=Op.STOP)
    target = pre.deploy_contract(
        code=Spec7702.delegation_designation(delegated_to)
    )

    access_list = []
    if warm_target:
        access_list.append(AccessList(address=target, storage_keys=[]))
    if warm_delegation:
        access_list.append(AccessList(address=delegated_to, storage_keys=[]))

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    total_gas_cost = intrinsic_gas_calculator(
        access_list=access_list,
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        recipient_delegation_is_warm=warm_delegation,
        recipient_is_warm=warm_target,
        return_cost_deducted_prior_execution=True,
    )

    tx_gas_limit = total_gas_cost + 1000  # add a small buffer
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        access_list=access_list,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - (total_gas_cost * gas_price)
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=value),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "warm_target",
    [True, False],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_value_transfer_to_self(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    warm_target: bool,
    value: int,
) -> None:
    """Test value moving transaction to self."""
    initial_balance = 10**18
    sender = pre.fund_eoa(initial_balance)
    access_list = (
        [AccessList(address=sender, storage_keys=[])] if warm_target else []
    )

    # Contract creation transaction
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    total_gas_cost = intrinsic_gas_calculator(
        access_list=access_list,
        sends_value=bool(value),
        recipient_type=RecipientType.SELF,
        return_cost_deducted_prior_execution=True,
    )

    tx_gas_limit = total_gas_cost + 1000  # add a small buffer
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=sender,
        value=value,
        access_list=access_list,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = initial_balance - (total_gas_cost * gas_price)

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_value_contract_creation_tx(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """Test value moving contract creation transactions."""
    gsc = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    # Contract creation transaction
    code_to_deploy = Op.STOP
    call_data = Initcode(deploy_code=code_to_deploy)
    execution_gas = call_data.execution_gas(
        fork
    ) + gsc.CODE_DEPOSIT_PER_BYTE * len(code_to_deploy)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    total_gas_cost = (
        intrinsic_gas_calculator(
            calldata=call_data,
            contract_creation=True,
            sends_value=bool(value),
            return_cost_deducted_prior_execution=True,
        )
        + execution_gas
    )

    tx_gas_limit = total_gas_cost + 1000  # add a small buffer
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=None,
        value=value,
        data=call_data,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    expected_target_address = compute_create_address(address=sender, nonce=0)
    sender_final_balance = (
        sender_initial_balance - value - (total_gas_cost * gas_price)
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        expected_target_address: Account(code=code_to_deploy, balance=value),
    }

    state_test(pre=pre, tx=tx, post=post)
