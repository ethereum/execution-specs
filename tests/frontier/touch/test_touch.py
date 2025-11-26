"""test account touch behavior."""

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
@pytest.mark.valid_until("Berlin")
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
        gas_limit=500_000,
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
