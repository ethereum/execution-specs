"""
Shared pytest definitions local to EIP-4788 tests.
"""

from itertools import count
from typing import Dict, Iterator, List

import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_tools import (
    AccessList,
    Account,
    Address,
    Environment,
    Hash,
    Storage,
    TestAddress,
    Transaction,
    add_kzg_version,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import Spec, SpecHelpers

BLOB_COMMITMENT_VERSION_KZG = 1


@pytest.fixture
def timestamp() -> int:  # noqa: D103
    return 12


@pytest.fixture
def beacon_roots() -> Iterator[bytes]:
    """
    By default, return an iterator that returns the keccak of an internal counter.
    """

    class BeaconRoots:
        def __init__(self) -> None:
            self._counter = count(1)

        def __iter__(self) -> "BeaconRoots":
            return self

        def __next__(self) -> bytes:
            return keccak256(int.to_bytes(next(self._counter), length=8, byteorder="big"))

    return BeaconRoots()


@pytest.fixture
def beacon_root(request, beacon_roots: Iterator[bytes]) -> bytes:  # noqa: D103
    return Hash(request.param) if hasattr(request, "param") else next(beacon_roots)


@pytest.fixture
def env(timestamp: int, beacon_root: bytes) -> Environment:  # noqa: D103
    return Environment(
        timestamp=timestamp,
        parent_beacon_block_root=beacon_root,
    )


@pytest.fixture
def call_beacon_root_contract() -> bool:
    """
    By default, do not directly call the beacon root contract.
    """
    return False


@pytest.fixture
def call_type() -> Op:  # noqa: D103
    return Op.CALL


@pytest.fixture
def call_value() -> int:  # noqa: D103
    return 0


@pytest.fixture
def call_gas() -> int:  # noqa: D103
    return Spec.BEACON_ROOTS_CALL_GAS


@pytest.fixture
def caller_address() -> Address:  # noqa: D103
    return Address(0x100)


@pytest.fixture
def contract_call_account(call_type: Op, call_value: int, call_gas: int) -> Account:
    """
    Code to call the beacon root contract.
    """
    args_start, args_length, return_start, return_length = 0x20, Op.CALLDATASIZE, 0x00, 0x20
    contract_call_code = Op.CALLDATACOPY(args_start, 0x00, args_length)
    if call_type == Op.CALL or call_type == Op.CALLCODE:
        contract_call_code += Op.SSTORE(
            0x00,  # store the result of the contract call in storage[0]
            call_type(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
                call_gas,
                Spec.BEACON_ROOTS_ADDRESS,
                call_value,
                args_start,
                args_length,
                return_start,
                return_length,
            ),
        )
    elif call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
        # delegatecall and staticcall use one less argument
        contract_call_code += Op.SSTORE(
            0x00,
            call_type(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
                call_gas,
                Spec.BEACON_ROOTS_ADDRESS,
                args_start,
                args_length,
                return_start,
                return_length,
            ),
        )
    contract_call_code += (
        Op.SSTORE(  # Save the return value of the contract call
            0x01,
            Op.MLOAD(return_start),
        )
        + Op.SSTORE(  # Save the length of the return value of the contract call
            0x02,
            Op.RETURNDATASIZE,
        )
        + Op.RETURNDATACOPY(
            return_start,
            0x00,
            Op.RETURNDATASIZE,
        )
        + Op.SSTORE(
            0x03,
            Op.MLOAD(return_start),
        )
    )
    return Account(
        nonce=0,
        code=contract_call_code,
        balance=0x10**10,
    )


@pytest.fixture
def valid_call() -> bool:
    """
    Validity of beacon root contract call: defaults to True.
    """
    return True


@pytest.fixture
def valid_input() -> bool:
    """
    Validity of timestamp input to contract call: defaults to True.
    """
    return True


@pytest.fixture
def system_address_balance() -> int:
    """
    Balance of the system address.
    """
    return 0


@pytest.fixture
def pre(
    contract_call_account: Account,
    system_address_balance: int,
    caller_address: Address,
) -> Dict:
    """
    Prepares the pre state of all test cases, by setting the balance of the
    source account of all test transactions, and the contract caller account.
    """
    pre_alloc = {
        TestAddress: Account(
            nonce=0,
            balance=0x10**10,
        ),
        caller_address: contract_call_account,
    }
    if system_address_balance > 0:
        pre_alloc[Address(Spec.SYSTEM_ADDRESS)] = Account(
            nonce=0,
            balance=system_address_balance,
        )
    return pre_alloc


@pytest.fixture
def tx_to_address(request, caller_address: Account) -> Address:  # noqa: D103
    return request.param if hasattr(request, "param") else caller_address


@pytest.fixture
def auto_access_list() -> bool:
    """
    Whether to append the accessed storage keys to the transaction.
    """
    return False


@pytest.fixture
def access_list(auto_access_list: bool, timestamp: int) -> List[AccessList]:
    """
    Access list included in the transaction to call the beacon root contract.
    """
    if auto_access_list:
        return [
            AccessList(
                address=Spec.BEACON_ROOTS_ADDRESS,
                storage_keys=[
                    timestamp,
                    timestamp + Spec.HISTORY_BUFFER_LENGTH,
                ],
            ),
        ]
    return []


@pytest.fixture
def tx_data(timestamp: int) -> bytes:
    """
    Data included in the transaction to call the beacon root contract.
    """
    return Hash(timestamp)


@pytest.fixture
def tx_type() -> int:
    """
    Transaction type to call the caller contract or the beacon root contract directly.

    By default use a type 2 transaction.
    """
    return 2


@pytest.fixture
def tx(
    tx_to_address: Address,
    tx_data: bytes,
    tx_type: int,
    access_list: List[AccessList],
    call_beacon_root_contract: bool,
) -> Transaction:
    """
    Prepares transaction to call the beacon root contract caller account.
    """
    to = Spec.BEACON_ROOTS_ADDRESS if call_beacon_root_contract else tx_to_address
    kwargs: Dict = {
        "ty": tx_type,
        "nonce": 0,
        "data": tx_data,
        "to": to,
        "value": 0,
        "gas_limit": 1000000,
    }

    if tx_type > 0:
        kwargs["access_list"] = access_list

    if tx_type <= 1:
        kwargs["gas_price"] = 7
    else:
        kwargs["max_fee_per_gas"] = 7
        kwargs["max_priority_fee_per_gas"] = 0

    if tx_type == 3:
        kwargs["max_fee_per_blob_gas"] = 1
        kwargs["blob_versioned_hashes"] = add_kzg_version([0], BLOB_COMMITMENT_VERSION_KZG)

    if tx_type > 3:
        raise Exception(f"Unexpected transaction type: '{tx_type}'. Test requires update.")

    return Transaction(**kwargs)


@pytest.fixture
def post(
    caller_address: Address,
    beacon_root: bytes,
    valid_call: bool,
    valid_input: bool,
    call_beacon_root_contract: bool,
) -> Dict:
    """
    Prepares the expected post state for a single contract call based upon the success or
    failure of the call, and the validity of the timestamp input.
    """
    storage = Storage()
    if not call_beacon_root_contract:
        storage = SpecHelpers.expected_storage(
            beacon_root=beacon_root,
            valid_call=valid_call,
            valid_input=valid_input,
        )
    return {
        caller_address: Account(
            storage=storage,
        ),
    }
