"""Test account touch behavior."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)


@pytest.mark.valid_from("Frontier")
@pytest.mark.valid_before("EIP1559")
@pytest.mark.eels_base_coverage
def test_zero_gas_price_and_touching(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test sending a zero gasprice transaction in early forks respects
    account touching rules.
    """
    sender = pre.fund_eoa()
    value = 0x01

    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, value) + Op.STOP),
    )

    tx = Transaction(
        to=contract,
        gas_price=0,  # Part of the test, do not change.
        sender=sender,
        protected=False,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={contract: Account(storage={0: value})},
    )


@pytest.mark.valid_from("Frontier")
@pytest.mark.valid_before("EIP1559")
def test_zero_gas_price_nonexistent_sender(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a zero gasprice, zero value transaction from a sender that does not
    exist in the pre-state.

    Because the transaction is free (gas_price=0) and transfers no value, no
    balance is ever deducted from the sender, so the sender account is only
    materialized when its nonce is incremented. Clients must create the sender
    account in this case rather than failing on a missing account.

    """
    # amount=0 means the sender is NOT added to the pre-alloc.
    sender = pre.fund_eoa(amount=0)

    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 0x01) + Op.STOP),
    )

    tx = Transaction(
        to=contract,
        gas_price=0,  # Part of the test, do not change.
        value=0,  # Part of the test, do not change.
        sender=sender,
        protected=False,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(storage={0: 0x01}),
            sender: Account(nonce=1, balance=0),
        },
    )
