"""
Mainnet marked execute checklist tests for
[EIP-7708: ETH transfers emit a log](https://eips.ethereum.org/EIPS/eip-7708).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

from .spec import ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = [pytest.mark.valid_at("EIP7708"), pytest.mark.mainnet]


def test_simple_transfer_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test that a simple ETH transfer emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    gas_limit = intrinsic_gas + top_frame_state_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, recipient, 1)]
        ),
    )

    post = {recipient: Account(balance=1)}
    state_test(pre=pre, post=post, tx=tx)


def test_call_with_value_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test that CALL with value emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(Op.STOP)
    transfer_value = 1

    # The callee is a bare STOP, so the stipend covers the inner frame.
    contract_code = Op.CALL(
        gas=0,
        address=recipient,
        value=transfer_value,
        # gas accounting
        value_transfer=True,
    )
    contract = pre.deploy_contract(contract_code, balance=transfer_value)
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + contract_code.gas_cost(fork)
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, recipient, transfer_value)]
        ),
    )

    post = {recipient: Account(balance=transfer_value)}
    state_test(pre=pre, post=post, tx=tx)


def test_create_endowment_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test that a CREATE endowment emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    create_value = 1

    contract_code = Op.CREATE(value=create_value, offset=0, size=0)
    contract = pre.deploy_contract(contract_code, balance=create_value)
    created = compute_create_address(address=contract, nonce=1)
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + contract_code.gas_cost(fork)
        + fork.create_state_gas()
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, created, create_value)]
        ),
    )

    post = {created: Account(balance=create_value)}
    state_test(pre=pre, post=post, tx=tx)


def test_selfdestruct_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test that SELFDESTRUCT emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()
    balance = 1

    contract_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    contract = pre.deploy_contract(contract_code, balance=balance)
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + contract_code.gas_cost(fork)
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, beneficiary, balance)]
        ),
    )

    post = {beneficiary: Account(balance=balance)}
    state_test(pre=pre, post=post, tx=tx)
