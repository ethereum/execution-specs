"""
Test_call_recursive_contract.

Ported from:
state_tests/stInitCodeTest/CallRecursiveContractFiller.json

@manually-enhanced: Do not overwrite. This test has been manually reviewed and
enhanced.
"""

from typing import Generator

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def recursive_create_calculator(
    contract: Address, depth: int
) -> Generator[Address, None, None]:
    """
    Calculate the resulting address of a contract creating contracts
    recursively.
    """
    while depth > 0:
        contract = compute_create_address(address=contract, nonce=1)
        yield contract
        depth -= 1


@pytest.mark.ported_from(
    ["state_tests/stInitCodeTest/CallRecursiveContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_recursive_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_call_recursive_contract."""
    sender = pre.fund_eoa()
    # Source: lll
    # {[[ 2 ]](ADDRESS)(CODECOPY 0 0 32)(CREATE 0 0 32)}
    entry_contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.ADDRESS)
        + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.CREATE(value=0x0, offset=0x0, size=0x20)
        + Op.STOP,
    )

    gas_limit = 400_000
    pre_fund_deploy_addresses = False
    if fork.is_eip_enabled(8037):
        gas_limit = 2_000_000
        # In 8037, the cost of creating an account is beared by the parent
        # creating it, so in order to not run out of gas when we return from
        # contract creation we pre-fund the accounts. This way they are
        # already in the trie and don't produce a cost.
        pre_fund_deploy_addresses = True

    tx = Transaction(
        sender=sender,
        to=entry_contract,
        gas_limit=gas_limit,
    )

    expected_depth = 5
    for i, contract in enumerate(
        recursive_create_calculator(entry_contract, depth=expected_depth + 1)
    ):
        if pre_fund_deploy_addresses:
            pre.fund_address(contract, 1)
        if i == expected_depth - 1:
            last_expected_contract = contract
        elif i == expected_depth:
            first_unexpected_contract = contract

    first_unexpected_contract_account = Account.NONEXISTENT
    if pre_fund_deploy_addresses:
        first_unexpected_contract_account = Account(balance=1, code=b"")

    post = {
        entry_contract: Account(
            storage={2: entry_contract}, balance=0, nonce=2
        ),
        last_expected_contract: Account(
            storage={2: last_expected_contract},
            balance=1 if pre_fund_deploy_addresses else 0,
            nonce=2,
        ),
        first_unexpected_contract: first_unexpected_contract_account,
    }

    state_test(pre=pre, post=post, tx=tx)
