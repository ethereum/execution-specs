"""Test the tx type validation for EIP-1559."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing import Opcodes as Op
from execution_testing.forks import Byzantium, London
from requests_cache import Callable

from .spec import ref_spec_1559

REFERENCE_SPEC_GIT_PATH = ref_spec_1559.git_path
REFERENCE_SPEC_VERSION = ref_spec_1559.version


@pytest.fixture
def eip1559_tx_validity_test(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, env: Environment
) -> Callable[[], None]:
    """
    Returns a function which applies a `state_test`, where a typed transaction
    is either valid and has an effect on state or not, depending on the fork.
    """

    def test_function() -> None:
        valid = fork >= London

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
            error=TransactionException.TYPE_2_TX_PRE_FORK
            if not valid
            else None,
        )

        post = {account: Account(storage={0: 0xDEADBEEF if not valid else 1})}
        if not valid:
            post[sender] = pre[sender]  # type: ignore

        state_test(env=env, pre=pre, post=post, tx=tx)

    return test_function


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/blob/master/Cancun/GeneralStateTests/stEIP1559/typeTwoBerlin.json"
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1754"],
)
@pytest.mark.exception_test
@pytest.mark.valid_until("Berlin")
def test_eip1559_tx_invalid(
    eip1559_tx_validity_test: Callable[[], None],
) -> None:
    """
    Tests that an EIP-1559 tx has no effect before London.
    """
    eip1559_tx_validity_test()


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/blob/master/Cancun/GeneralStateTests/stEIP1559/typeTwoBerlin.json"
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1754"],
)
@pytest.mark.valid_from("London")
def test_eip1559_tx_valid(
    eip1559_tx_validity_test: Callable[[], None],
) -> None:
    """
    Tests that an EIP-1559 tx has an effect after London.
    """
    eip1559_tx_validity_test()
