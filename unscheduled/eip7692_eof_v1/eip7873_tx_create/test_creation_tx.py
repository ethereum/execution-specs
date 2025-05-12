"""Test bad TXCREATE cases."""

import pytest

from ethereum_test_base_types.base_types import Address, Bytes
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.code.generators import Initcode as LegacyInitcode
from ethereum_test_types.eof.v1 import Container
from ethereum_test_types.types import TransactionReceipt
from tests.prague.eip7702_set_code_tx.spec import Spec

from .. import EOF_FORK_NAME
from ..eip7620_eof_create.helpers import (
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7873.md"
REFERENCE_SPEC_VERSION = "23d96ceff8f0690432ab91089ae257f08f32340f"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.with_all_contract_creating_tx_types(selector=lambda tx_type: tx_type != 6)
@pytest.mark.parametrize(
    "deploy_code",
    [
        Bytes("0xEF"),
        Bytes("0xEF00"),
        Bytes("0xEF0001"),
        Bytes("0xEF01"),
        smallest_runtime_subcontainer,
        smallest_initcode_subcontainer,
    ],
)
def test_legacy_create_tx_legacy_initcode_eof_bytecode(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    deploy_code: Bytes | Container,
):
    """
    Test that a legacy contract creation tx cannot create EOF code.

    This tests only ensures EIP-3541 behavior is kept, not altered by EIP-7873
    """
    env = Environment()
    sender = pre.fund_eoa()

    initcode = LegacyInitcode(deploy_code=deploy_code)

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
@pytest.mark.parametrize(
    "initcode",
    [
        Bytes("0xEF"),
        Bytes("0xEF01"),
        Bytes("0xEF0101"),
        Spec.delegation_designation(Address(0xAA)),
        Bytes("0xEF02"),
        Bytes("0xEF00"),
        Bytes("0xEF0001"),
        smallest_runtime_subcontainer,
        smallest_initcode_subcontainer,
    ],
)
def test_legacy_create_tx_prefix_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    initcode: Bytes,
):
    """
    Test that a legacy contract creation tx behaves as it did before EIP-7873 for
    initcode stating with `EF`.
    The transaction should be valid but fail on executing of the first byte `EF`.
    """
    env = Environment()
    sender = pre.fund_eoa()
    gas_limit = 100_000

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=None,
        gas_limit=gas_limit,
        data=initcode,
        expected_receipt=TransactionReceipt(gas_used=gas_limit),
    )

    destination_contract_address = tx.created_contract

    post = {destination_contract_address: Account.NONEXISTENT, sender: Account(nonce=1)}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
