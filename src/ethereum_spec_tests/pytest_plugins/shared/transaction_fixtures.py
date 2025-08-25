"""
Pytest plugin providing default transaction fixtures for each transaction type.

Each fixture can be overridden in test files to customize transaction behavior.
"""

import pytest

from ethereum_test_base_types import AccessList
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import AuthorizationTuple, Transaction, add_kzg_version


@pytest.fixture
def type_0_default_transaction(sender):
    """Type 0 (legacy) default transaction available in all forks."""
    return Transaction(
        ty=0,
        sender=sender,
        gas_price=10**9,
        gas_limit=100_000,
        data=b"\x00" * 100,
    )


@pytest.fixture
def type_1_default_transaction(sender):
    """Type 1 (access list) default transaction introduced in Berlin fork."""
    return Transaction(
        ty=1,
        sender=sender,
        gas_price=10**9,
        gas_limit=100_000,
        data=b"\x00" * 100,
        access_list=[
            AccessList(address=0x1234, storage_keys=[0, 1, 2]),
            AccessList(address=0x5678, storage_keys=[3, 4, 5]),
            AccessList(address=0x9ABC, storage_keys=[]),
        ],
    )


@pytest.fixture
def type_2_default_transaction(sender):
    """Type 2 (dynamic fee) default transaction introduced in London fork."""
    return Transaction(
        ty=2,
        sender=sender,
        max_fee_per_gas=10**10,
        max_priority_fee_per_gas=10**9,
        gas_limit=100_000,
        data=b"\x00" * 200,
        access_list=[
            AccessList(address=0x2468, storage_keys=[10, 20, 30]),
            AccessList(address=0xACE0, storage_keys=[40, 50]),
        ],
    )


@pytest.fixture
def type_3_default_transaction(sender):
    """Type 3 (blob) default transaction introduced in Cancun fork."""
    return Transaction(
        ty=3,
        sender=sender,
        max_fee_per_gas=10**10,
        max_priority_fee_per_gas=10**9,
        max_fee_per_blob_gas=10**9,
        gas_limit=100_000,
        data=b"\x00" * 150,
        access_list=[
            AccessList(address=0x3690, storage_keys=[100, 200]),
            AccessList(address=0xBEEF, storage_keys=[300]),
        ],
        blob_versioned_hashes=add_kzg_version(
            [
                0x1111111111111111111111111111111111111111111111111111111111111111,
                0x2222222222222222222222222222222222222222222222222222222222222222,
            ],
            0x01,
        ),
    )


@pytest.fixture
def type_4_default_transaction(sender, pre):
    """Type 4 (set code) default transaction introduced in Prague fork."""
    # Create authorized accounts with funds
    auth_signer1 = pre.fund_eoa(amount=10**18)
    auth_signer2 = pre.fund_eoa(amount=10**18)

    # Create target addresses that will be authorized
    target1 = pre.deploy_contract(Op.SSTORE(0, 1))
    target2 = pre.deploy_contract(Op.SSTORE(0, 1))

    return Transaction(
        ty=4,
        sender=sender,
        max_fee_per_gas=10**10,
        max_priority_fee_per_gas=10**9,
        gas_limit=150_000,
        data=b"\x00" * 200,
        access_list=[
            AccessList(address=0x4567, storage_keys=[1000, 2000, 3000]),
            AccessList(address=0xCDEF, storage_keys=[4000, 5000]),
        ],
        authorization_list=[
            AuthorizationTuple(
                chain_id=1,
                address=target1,
                nonce=0,
                signer=auth_signer1,
            ),
            AuthorizationTuple(
                chain_id=1,
                address=target2,
                nonce=0,
                signer=auth_signer2,
            ),
        ],
    )


@pytest.fixture
def typed_transaction(request, fork):
    """
    Fixture that provides a Transaction object based on the parametrized tx type.

    This fixture works with the @pytest.mark.with_all_typed_transactions marker,
    which parametrizes the test with all transaction types supported by the fork.

    The actual transaction type value comes from the marker's parametrization.
    """
    # The marker parametrizes 'typed_transaction' with tx type integers
    # Get the parametrized tx_type value
    if hasattr(request, "param"):
        # When parametrized by the marker, request.param contains the tx type
        tx_type = request.param
    else:
        raise ValueError(
            "`typed_transaction` fixture must be used with "
            "`@pytest.mark.with_all_typed_transactions` marker"
        )

    fixture_name = f"type_{tx_type}_default_transaction"

    # Check if fixture exists - try to get it first
    try:
        # This will find fixtures defined in the test file or plugin
        return request.getfixturevalue(fixture_name)
    except pytest.FixtureLookupError as e:
        # Get all supported tx types for better error message
        supported_types = fork.tx_types()
        raise NotImplementedError(
            f"Fork {fork} supports transaction type {tx_type} but "
            f"fixture '{fixture_name}' is not implemented!\n"
            f"Fork {fork} supports transaction types: {supported_types}\n"
            f"Please add the missing fixture to "
            f"src/pytest_plugins/shared/transaction_fixtures.py"
        ) from e
