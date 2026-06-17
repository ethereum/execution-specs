"""Test the tx type validation for EIP-1559."""

from typing import Final, Generator, Sequence

import pytest
from execution_testing import (
    Account,
    Alloc,
    ChainConfig,
    Fork,
    ParameterSet,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionType,
)
from execution_testing import Opcodes as Op
from execution_testing.base_types import Hash

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
        protected=fork.supports_protected_txs(),
        error=TransactionException.TYPE_2_TX_PRE_FORK if not valid else None,
    )

    post = {account: Account(storage={0: 0xDEADBEEF if not valid else 1})}
    if not valid:
        post[sender] = pre[sender]  # type: ignore

    state_test(pre=pre, post=post, tx=tx)


TX_TYPES: Final[Sequence[object]] = [
    pytest.param(TransactionType.LEGACY, None),
    pytest.param(
        TransactionType.ACCESS_LIST,
        None,
        marks=[pytest.mark.valid_from("Berlin")],
    ),
    pytest.param(
        TransactionType.BASE_FEE,
        None,
        marks=[pytest.mark.valid_from("London")],
    ),
    pytest.param(
        TransactionType.BLOB_TRANSACTION,
        [0],
        marks=[pytest.mark.valid_from("Cancun")],
    ),
    pytest.param(
        TransactionType.SET_CODE,
        None,
        marks=[pytest.mark.valid_from("Prague")],
    ),
]

if len(TX_TYPES) != len(TransactionType):
    raise Exception("missing tx type")


@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.exception_test
@pytest.mark.parametrize(("tx_type", "blob_versioned_hashes"), TX_TYPES)
def test_invalid_chain_id(
    state_test: StateTestFiller,
    pre: Alloc,
    chain_config: ChainConfig,
    tx_type: int,
    blob_versioned_hashes: None | Sequence[Hash],
) -> None:
    """
    Test that a transaction with a different chain id is not valid.
    """
    to = pre.fund_eoa(0xDEADBEEE)

    tx = Transaction(
        sender=pre.fund_eoa(),
        value=1,
        chain_id=chain_config.chain_id + 1,
        ty=tx_type,
        to=to,
        error=TransactionException.INVALID_CHAINID,
        blob_versioned_hashes=blob_versioned_hashes,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            to: Account(balance=0xDEADBEEE),
        },
    )
