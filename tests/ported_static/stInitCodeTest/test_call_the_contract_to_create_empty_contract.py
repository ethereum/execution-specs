"""
Test_call_the_contract_to_create_empty_contract.

Ported from:
state_tests/stInitCodeTest/CallTheContractToCreateEmptyContractFiller.json

@manually-enhanced: Do not overwrite. tx gas budget bumped
for EIP-8037 NEW_ACCOUNT state-gas headroom on Amsterdam (post-state
expectations are unchanged on all forks).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/CallTheContractToCreateEmptyContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_the_contract_to_create_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_call_the_contract_to_create_empty_contract."""
    sender = pre.fund_eoa(amount=0x989680)

    # Source: lll
    # {(CREATE 0 0 32)}
    contract_0 = pre.deploy_contract(
        code=Op.CREATE(value=0x0, offset=0x0, size=0x20) + Op.STOP,
    )

    # EIP-8037 NEW_ACCOUNT state-gas spill on Amsterdam; pre-EIP-8037
    # keeps the original 100 000 budget.
    tx_gas_limit = 100_000
    if fork.is_eip_enabled(8037):
        tx_gas_limit = 500_000
    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = {
        contract_0: Account(balance=1, nonce=2),
        sender: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=1): Account(
            storage={}, code=b"", balance=0, nonce=1
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
