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
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = [pytest.mark.valid_at("EIP7708"), pytest.mark.mainnet]


def test_simple_transfer_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test that a simple ETH transfer emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()

    tx = Transaction(
        ty=0x02,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=21_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, recipient, 1)]
        ),
    )

    post = {recipient: Account(balance=1)}
    state_test(pre=pre, post=post, tx=tx)


def test_call_with_value_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test that CALL with value emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(Op.STOP)

    contract_code = Op.CALL(gas=50_000, address=recipient, value=100)
    contract = pre.deploy_contract(contract_code, balance=100)

    tx = Transaction(
        ty=0x02,
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, recipient, 100)]
        ),
    )

    post = {recipient: Account(balance=100)}
    state_test(pre=pre, post=post, tx=tx)


def test_selfdestruct_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test that SELFDESTRUCT emits a transfer log on mainnet."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()

    contract_code = Op.SELFDESTRUCT(beneficiary)
    contract = pre.deploy_contract(contract_code, balance=500)

    gas_limit = 100_000
    if fork.is_eip_enabled(8037):
        gas_limit = 500_000

    tx = Transaction(
        ty=0x02,
        sender=sender,
        to=contract,
        value=0,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, beneficiary, 500)]
        ),
    )

    post = {beneficiary: Account(balance=500)}
    state_test(pre=pre, post=post, tx=tx)
