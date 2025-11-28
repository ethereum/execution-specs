"""Test the tx type validation for EIP-2930."""

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

from .spec import ref_spec_2930

REFERENCE_SPEC_GIT_PATH = ref_spec_2930.git_path
REFERENCE_SPEC_VERSION = ref_spec_2930.version

TX_TYPE = 1


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
        "https://github.com/ethereum/legacytests/blob/master/src/LegacyTests/Cancun/GeneralStateTestsFiller/stExample/accessListExampleFiller.yml"
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1754"],
)
@pytest.mark.parametrize_by_fork("valid", tx_validity)
def test_eip2930_tx_validity(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    valid: bool,
) -> None:
    """
    Tests that an EIP-2930 tx is correctly rejected before fork activation.
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
        access_list=[],
        protected=fork >= Byzantium,
        error=TransactionException.TYPE_1_TX_PRE_FORK if not valid else None,
    )

    post = {account: Account(storage={0: 0xDEADBEEF if not valid else 1})}
    if not valid:
        post[sender] = pre[sender]  # type: ignore

    state_test(pre=pre, post=post, tx=tx)
