"""Fixtures for the EIP-7981 tests."""

from typing import List, Sequence

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Bytes,
    Fork,
    Hash,
    Op,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as EIP_4844_Spec


@pytest.fixture
def to(
    request: pytest.FixtureRequest,
    pre: Alloc,
) -> Address | None:
    """Create the recipient address."""
    if hasattr(request, "param"):
        param = request.param
    else:
        param = Op.STOP

    if param is None:
        return None
    if isinstance(param, str) and param == "eoa":
        return pre.fund_eoa(amount=0)
    if isinstance(param, Bytecode):
        return pre.deploy_contract(param)

    raise ValueError(f"Invalid value for `to` fixture: {param}")


@pytest.fixture
def protected() -> bool:
    """
    Return whether the transaction is protected or not. Only valid for type-0
    transactions.
    """
    return True


@pytest.fixture
def access_list() -> List[AccessList] | None:
    """Access list for the transaction."""
    return None


@pytest.fixture
def authorization_refund() -> bool:
    """
    Return whether the transaction has an existing authority in the
    authorization list.
    """
    return False


@pytest.fixture
def authorization_list(
    request: pytest.FixtureRequest,
    pre: Alloc,
    authorization_refund: bool,
    tx_type: int,
) -> List[AuthorizationTuple] | None:
    """
    Authorization-list for the transaction.

    This fixture needs to be parametrized indirectly in order to generate the
    authorizations with valid signers using `pre` in this function, and the
    parametrized value should be a list of addresses.
    """
    if not hasattr(request, "param"):
        if tx_type == 4:
            return [
                AuthorizationTuple(
                    signer=pre.fund_eoa(1 if authorization_refund else 0),
                    address=Address(1),
                )
            ]
        return None
    if request.param is None:
        if tx_type == 4:
            return [
                AuthorizationTuple(
                    signer=pre.fund_eoa(1 if authorization_refund else 0),
                    address=Address(1),
                )
            ]
        return None
    return [
        AuthorizationTuple(
            signer=pre.fund_eoa(1 if authorization_refund else 0),
            address=address,
        )
        for address in request.param
    ]


@pytest.fixture
def blob_versioned_hashes(tx_type: int) -> Sequence[Hash] | None:
    """Versioned hashes for the transaction."""
    return (
        add_kzg_version(
            [Hash(1)],
            EIP_4844_Spec.BLOB_COMMITMENT_VERSION_KZG,
        )
        if tx_type == 3
        else None
    )


@pytest.fixture
def contract_creating_tx(to: Address | None) -> bool:
    """Return whether the transaction creates a contract or not."""
    return to is None


@pytest.fixture
def tx_data() -> Bytes:
    """
    Transaction data.

    Default is empty, but can be parametrized to test different scenarios.
    """
    return Bytes(b"")


@pytest.fixture
def tx_gas_delta() -> int:
    """
    Gas delta to modify the gas amount included with the transaction.

    If negative, the transaction will be invalid because the intrinsic gas cost
    is greater than the gas limit.

    This value operates regardless of whether the floor data gas cost is
    reached or not.

    If the value is greater than zero, the transaction will also be valid and
    the test will check that transaction processing does not consume more gas
    than it should.
    """
    return 0


@pytest.fixture
def tx_intrinsic_gas_cost_before_execution(
    fork: Fork,
    tx_data: Bytes,
    access_list: List[AccessList] | None,
    authorization_list: List[AuthorizationTuple] | None,
    contract_creating_tx: bool,
) -> int:
    """
    Return the intrinsic gas cost that is applied before the execution start.

    This value never includes the floor data gas cost.
    """
    intrinsic_gas_cost_calculator = (
        fork.transaction_intrinsic_cost_calculator()
    )
    return intrinsic_gas_cost_calculator(
        calldata=tx_data,
        contract_creation=contract_creating_tx,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )


@pytest.fixture
def tx_intrinsic_gas_cost_including_floor_data_cost(
    fork: Fork,
    tx_data: Bytes,
    access_list: List[AccessList] | None,
    authorization_list: List[AuthorizationTuple] | None,
    contract_creating_tx: bool,
) -> int:
    """
    Transaction intrinsic gas cost.

    The calculated value takes into account the normal intrinsic gas cost and
    the floor data gas cost if it is greater than the intrinsic gas cost.

    In other words, this is the value that is required for the transaction to
    be valid.
    """
    intrinsic_gas_cost_calculator = (
        fork.transaction_intrinsic_cost_calculator()
    )
    return intrinsic_gas_cost_calculator(
        calldata=tx_data,
        contract_creation=contract_creating_tx,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
    )


@pytest.fixture
def tx_gas_limit(
    tx_intrinsic_gas_cost_including_floor_data_cost: int,
    tx_gas_delta: int,
) -> int:
    """
    Gas limit for the transaction.

    The gas delta is added to the intrinsic gas cost to generate different test
    scenarios.
    """
    return tx_intrinsic_gas_cost_including_floor_data_cost + tx_gas_delta


@pytest.fixture
def tx_error(
    tx_gas_delta: int,
) -> TransactionException | None:
    """Transaction error, only expected if the gas delta is negative."""
    if tx_gas_delta < 0:
        return TransactionException.INTRINSIC_GAS_TOO_LOW
    return None


@pytest.fixture
def tx(
    sender: EOA,
    tx_type: int,
    tx_data: Bytes,
    to: Address | None,
    protected: bool,
    access_list: List[AccessList] | None,
    authorization_list: List[AuthorizationTuple] | None,
    blob_versioned_hashes: Sequence[Hash] | None,
    tx_gas_limit: int,
    tx_error: TransactionException | None,
) -> Transaction:
    """Create the transaction used in each test."""
    return Transaction(
        ty=tx_type,
        sender=sender,
        data=tx_data,
        to=to,
        protected=protected,
        access_list=access_list,
        authorization_list=authorization_list,
        gas_limit=tx_gas_limit,
        blob_versioned_hashes=blob_versioned_hashes,
        error=tx_error,
    )
