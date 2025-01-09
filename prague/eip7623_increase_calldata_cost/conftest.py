"""Fixtures for the EIP-7623 tests."""

from typing import List, Sequence

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    EOA,
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Bytes,
    Hash,
    Transaction,
    TransactionException,
    add_kzg_version,
)
from ethereum_test_tools import Opcodes as Op

from ...cancun.eip4844_blobs.spec import Spec as EIP_4844_Spec
from .helpers import DataTestType, find_floor_cost_threshold


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Create the sender account."""
    return pre.fund_eoa()


@pytest.fixture
def to(
    request: pytest.FixtureRequest,
    pre: Alloc,
) -> Address | None:
    """Create the sender account."""
    if hasattr(request, "param"):
        param = request.param
    else:
        param = Op.STOP

    if param is None:
        return None
    if isinstance(param, Address):
        return param
    if isinstance(param, Bytecode):
        return pre.deploy_contract(param)

    raise ValueError(f"Invalid value for `to` fixture: {param}")


@pytest.fixture
def protected() -> bool:
    """
    Return whether the transaction is protected or not.
    Only valid for type-0 transactions.
    """
    return True


@pytest.fixture
def access_list() -> List[AccessList] | None:
    """Access list for the transaction."""
    return None


@pytest.fixture
def authorization_refund() -> bool:
    """Return whether the transaction has an existing authority in the authorization list."""
    return False


@pytest.fixture
def authorization_list(
    request: pytest.FixtureRequest,
    pre: Alloc,
    authorization_refund: bool,
) -> List[AuthorizationTuple] | None:
    """
    Authorization-list for the transaction.

    This fixture needs to be parametrized indirectly in order to generate the authorizations with
    valid signers using `pre` in this function, and the parametrized value should be a list of
    addresses.
    """
    if not hasattr(request, "param"):
        return None
    if request.param is None:
        return None
    return [
        AuthorizationTuple(signer=pre.fund_eoa(1 if authorization_refund else 0), address=address)
        for address in request.param
    ]


@pytest.fixture
def blob_versioned_hashes(ty: int) -> Sequence[Hash] | None:
    """Versioned hashes for the transaction."""
    return (
        add_kzg_version(
            [Hash(1)],
            EIP_4844_Spec.BLOB_COMMITMENT_VERSION_KZG,
        )
        if ty == 3
        else None
    )


@pytest.fixture
def contract_creating_tx(to: Address | None) -> bool:
    """Return whether the transaction creates a contract or not."""
    return to is None


@pytest.fixture
def intrinsic_gas_data_floor_minimum_delta() -> int:
    """
    Induce a minimum delta between the transaction intrinsic gas cost and the
    floor data gas cost.
    """
    return 0


@pytest.fixture
def tx_data(
    fork: Fork,
    data_test_type: DataTestType,
    access_list: List[AccessList] | None,
    authorization_list: List[AuthorizationTuple] | None,
    contract_creating_tx: bool,
    intrinsic_gas_data_floor_minimum_delta: int,
) -> Bytes:
    """
    All tests in this file use data that is generated dynamically depending on the case and the
    attributes of the transaction in order to reach the edge cases where the floor gas cost is
    equal or barely greater than the intrinsic gas cost.

    We have two different types of tests:
    - FLOOR_GAS_COST_LESS_THAN_OR_EQUAL_TO_INTRINSIC_GAS: The floor gas cost is less than or equal
        to the intrinsic gas cost, which means that the size of the tokens in the data are not
        enough to trigger the floor gas cost.
    - FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS: The floor gas cost is greater than the intrinsic
        gas cost, which means that the size of the tokens in the data are enough to trigger the
        floor gas cost.

    E.g. Given a transaction with a single access list and a single storage key, its intrinsic gas
    cost (as of Prague fork) can be calculated as:
    - 21,000 gas for the transaction
    - 2,400 gas for the access list
    - 1,900 gas for the storage key
    - 16 gas for each non-zero byte in the data
    - 4 gas for each zero byte in the data

    Its floor data gas cost can be calculated as:
    - 21,000 gas for the transaction
    - 40 gas for each non-zero byte in the data
    - 10 gas for each zero byte in the data

    Notice that the data included in the transaction affects both the intrinsic gas cost and the
    floor data cost, but at different rates.

    The purpose of this function is to find the exact amount of data where the floor data gas
    cost starts exceeding the intrinsic gas cost.

    After a binary search we find that adding 717 tokens of data (179 non-zero bytes +
    1 zero byte) triggers the floor gas cost.

    Therefore, this function will return a Bytes object with 179 non-zero bytes and 1 zero byte
    for `FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS` and a Bytes object with 179 non-zero bytes
    and no zero bytes for `FLOOR_GAS_COST_LESS_THAN_OR_EQUAL_TO_INTRINSIC_GAS`
    """

    def tokens_to_data(tokens: int) -> Bytes:
        return Bytes(b"\x01" * (tokens // 4) + b"\x00" * (tokens % 4))

    fork_intrinsic_cost_calculator = fork.transaction_intrinsic_cost_calculator()

    def transaction_intrinsic_cost_calculator(tokens: int) -> int:
        return (
            fork_intrinsic_cost_calculator(
                calldata=tokens_to_data(tokens),
                contract_creation=contract_creating_tx,
                access_list=access_list,
                authorization_list_or_count=authorization_list,
                return_cost_deducted_prior_execution=True,
            )
            + intrinsic_gas_data_floor_minimum_delta
        )

    fork_data_floor_cost_calculator = fork.transaction_data_floor_cost_calculator()

    def transaction_data_floor_cost_calculator(tokens: int) -> int:
        return fork_data_floor_cost_calculator(data=tokens_to_data(tokens))

    # Start with zero data and check the difference in the gas calculator between the
    # intrinsic gas cost and the floor gas cost.
    if transaction_data_floor_cost_calculator(0) >= transaction_intrinsic_cost_calculator(0):
        # Special case which is a transaction with no extra intrinsic gas costs other than the
        # data cost, any data will trigger the floor gas cost.
        if data_test_type == DataTestType.FLOOR_GAS_COST_LESS_THAN_OR_EQUAL_TO_INTRINSIC_GAS:
            return Bytes(b"")
        else:
            return Bytes(b"\0")

    tokens = find_floor_cost_threshold(
        floor_data_gas_cost_calculator=transaction_data_floor_cost_calculator,
        intrinsic_gas_cost_calculator=transaction_intrinsic_cost_calculator,
    )

    if data_test_type == DataTestType.FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS:
        return tokens_to_data(tokens + 1)
    return tokens_to_data(tokens)


@pytest.fixture
def tx_gas_delta() -> int:
    """
    Gas delta to modify the gas amount included with the transaction.

    If negative, the transaction will be invalid because the intrinsic gas cost is greater than the
    gas limit.

    This value operates regardless of whether the floor data gas cost is reached or not.

    If the value is greater than zero, the transaction will also be valid and the test will check
    that transaction processing does not consume more gas than it should.
    """
    return 0


@pytest.fixture
def tx_intrinsic_gas_cost(
    fork: Fork,
    tx_data: Bytes,
    access_list: List[AccessList] | None,
    authorization_list: List[AuthorizationTuple] | None,
    contract_creating_tx: bool,
) -> int:
    """
    Transaction intrinsic gas cost.

    The calculated value takes into account the normal intrinsic gas cost and the floor data gas
    cost.
    """
    intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    return intrinsic_gas_cost_calculator(
        calldata=tx_data,
        contract_creation=contract_creating_tx,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
    )


@pytest.fixture
def tx_floor_data_cost(
    fork: Fork,
    tx_data: Bytes,
) -> int:
    """Floor data cost for the given transaction data."""
    fork_data_floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
    return fork_data_floor_cost_calculator(data=tx_data)


@pytest.fixture
def tx_gas_limit(
    tx_intrinsic_gas_cost: int,
    tx_gas_delta: int,
) -> int:
    """
    Gas limit for the transaction.

    The gas delta is added to the intrinsic gas cost to generate different test scenarios.
    """
    return tx_intrinsic_gas_cost + tx_gas_delta


@pytest.fixture
def tx_error(tx_gas_delta: int) -> TransactionException | None:
    """Transaction error, only expected if the gas delta is negative."""
    return TransactionException.INTRINSIC_GAS_TOO_LOW if tx_gas_delta < 0 else None


@pytest.fixture
def tx(
    sender: EOA,
    ty: int,
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
        ty=ty,
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
