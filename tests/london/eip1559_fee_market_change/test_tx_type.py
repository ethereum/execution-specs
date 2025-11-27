"""Test the tx type validation for EIP-1559."""

from typing import Generator

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    ParameterSet,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing import Opcodes as Op
from execution_testing.forks import Byzantium

from .spec import ref_spec_1559

REFERENCE_SPEC_GIT_PATH = ref_spec_1559.git_path
REFERENCE_SPEC_VERSION = ref_spec_1559.version

TX_TYPE = 2


def tx_validity(fork: Fork) -> Generator[ParameterSet, None, None]:
    """
    Return a generator of parameters for the tx validity test.
    """
    valid = TX_TYPE in fork.tx_types()
    yield pytest.param(
        valid,
        marks=[pytest.mark.exception_test] if not valid else [],
        id="valid" if valid else "invalid",
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/blob/master/Cancun/GeneralStateTests/stEIP1559/typeTwoBerlin.json"
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1754"],
)
@pytest.mark.parametrize_by_fork("valid", tx_validity)
def test_eip1559_tx_validity(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    valid: bool,
) -> None:
    """
    Tests that an EIP-1559 tx has no effect before London.
    """
    account = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        to=account,
        sender=sender,
        gas_limit=100_000,
        max_priority_fee_per_gas=1,
        protected=fork >= Byzantium,
        error=TransactionException.TYPE_2_TX_PRE_FORK if not valid else None,
    )

    post = {account: Account(storage={0: 0xDEADBEEF if not valid else 1})}
    if not valid:
        post[sender] = pre[sender]  # type: ignore

    state_test(pre=pre, post=post, tx=tx)
