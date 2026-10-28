"""Test the empty system contracts that a block adds to the BAL."""

from execution_testing.forks import Amsterdam, SystemCallPhase
from execution_testing.test_types import Account, Alloc

from ..blockchain import empty_system_contracts

AFTER_TRANSACTIONS = [
    address
    for address, phase in Amsterdam.system_contract_call_phases().items()
    if phase == SystemCallPhase.AFTER_TRANSACTIONS
]


def deployed_system_contracts() -> Alloc:
    """Return an allocation in which every system contract has code."""
    return Alloc(
        {
            address: Account(code=b"\x00")
            for address in Amsterdam.system_contract_call_phases()
        }
    )


def test_deployed_contracts_are_not_listed() -> None:
    """Test that no contract is returned when all of them have code."""
    assert empty_system_contracts(Amsterdam, deployed_system_contracts()) == []


def test_missing_and_codeless_contracts_are_listed() -> None:
    """
    Test that a contract absent from the allocation, and one that holds
    only a balance, are both returned.
    """
    missing, codeless = AFTER_TRANSACTIONS[:2]
    alloc = deployed_system_contracts()
    del alloc[missing]
    alloc[codeless] = Account(balance=1)

    assert sorted(empty_system_contracts(Amsterdam, alloc)) == sorted(
        [missing, codeless]
    )


def test_contracts_called_before_transactions_are_not_listed() -> None:
    """
    Test that a contract the block calls before its transactions is not
    returned, because that call does not reject a block for empty code.
    """
    before_transactions = [
        address
        for address, phase in Amsterdam.system_contract_call_phases().items()
        if phase == SystemCallPhase.BEFORE_TRANSACTIONS
    ]
    assert before_transactions
    alloc = deployed_system_contracts()
    for address in before_transactions:
        del alloc[address]

    assert empty_system_contracts(Amsterdam, alloc) == []
