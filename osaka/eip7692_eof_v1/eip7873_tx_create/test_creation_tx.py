"""Test bad TXCREATE cases."""

import pytest

from ethereum_test_exceptions.exceptions import TransactionException
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.code.generators import Initcode as LegacyInitcode

from .. import EOF_FORK_NAME
from ..eip7620_eof_create.helpers import (
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7873.md"
REFERENCE_SPEC_VERSION = "1115fe6110fcc0efc823fb7f8f5cd86c42173efe"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.with_all_contract_creating_tx_types(selector=lambda tx_type: tx_type != 6)
def test_legacy_create_tx_legacy_initcode_eof_bytecode(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
):
    """Test that a legacy contract creation tx cannot create EOF code."""
    env = Environment()
    sender = pre.fund_eoa()

    initcode = LegacyInitcode(deploy_code=smallest_runtime_subcontainer)

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=None,
        gas_limit=100000,
        data=initcode,
    )

    destination_contract_address = tx.created_contract

    post = {
        destination_contract_address: Account.NONEXISTENT,
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.with_all_contract_creating_tx_types(selector=lambda tx_type: tx_type != 6)
@pytest.mark.xfail(reason="evmone incorrectly deploys the contract")
@pytest.mark.exception_test
def test_legacy_create_tx_eof_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
):
    """Test that a legacy contract creation tx cannot use EOF initcode."""
    env = Environment()
    sender = pre.fund_eoa()

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=None,
        gas_limit=100_000,
        data=smallest_initcode_subcontainer,
        error=TransactionException.EOF_CREATION_TRANSACTION,
    )

    destination_contract_address = tx.created_contract

    post = {
        destination_contract_address: Account.NONEXISTENT,
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
