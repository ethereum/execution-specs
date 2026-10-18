"""
Mainnet marked test for [EIP-5920: PAY opcode](https://eips.ethereum.org/EIPS/eip-5920).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_5920, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_5920.git_path
REFERENCE_SPEC_VERSION = ref_spec_5920.version

pytestmark = [pytest.mark.valid_from("Bogota"), pytest.mark.mainnet]


def test_eip_5920_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Mainnet smoke test for EIP-5920:
    1. Successful `PAY` to a contract with `REVERT` code (does not execute
       code, emits EIP-7708 transfer log).
    2. Failed `PAY` with insufficient balance (returns `0`, no transfer).
    """
    sender = pre.fund_eoa()
    reverting_recipient = pre.deploy_contract(
        code=Op.REVERT(0, 0), balance=100
    )

    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(1),
                Op.PAY(reverting_recipient, 400),
            )
            + Op.SSTORE(
                storage.store_next(0),
                Op.PAY(reverting_recipient, 10_000),
            )
            + Op.SSTORE(
                storage.store_next(500),
                Op.BALANCE(reverting_recipient),
            )
            + Op.STOP
        ),
        balance=1_000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract_address, reverting_recipient, 400)]
        ),
    )
    post = {
        contract_address: Account(balance=600, storage=storage),
        reverting_recipient: Account(balance=500),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
