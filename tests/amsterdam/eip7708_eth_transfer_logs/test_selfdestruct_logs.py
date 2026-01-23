"""
Tests for EIP-7708 Selfdestruct logs.

Tests for the Selfdestruct(address,uint256) log emitted when:
- SELFDESTRUCT to self with nonzero balance
- Account closure after SELFDESTRUCT
"""

import pytest
from execution_testing import (
    EOA,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_7708, selfdestruct_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def test_selfdestruct_to_self_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that selfdestruct-to-self emits a Selfdestruct log.

    Since the contract selfdestructs to itself, there is no transfer.
    Instead, a Selfdestruct log is emitted with the contract's balance.
    """
    contract_balance = 2000

    contract_code = Op.SELFDESTRUCT(Op.ADDRESS)
    contract = pre.deploy_contract(contract_code, balance=contract_balance)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[selfdestruct_log(contract, contract_balance)]
        ),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)
