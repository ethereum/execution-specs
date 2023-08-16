"""
Shared pytest definitions local to EIP-4788 tests.
"""
from typing import Dict, List

import pytest

from ethereum_test_tools import (
    AccessList,
    Account,
    Environment,
    Storage,
    TestAddress,
    Transaction,
    add_kzg_version,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import (
    BEACON_ROOT_CONTRACT_ADDRESS,
    BEACON_ROOT_CONTRACT_CALL_GAS,
    DEFAULT_BEACON_ROOT_HASH,
    HISTORICAL_ROOTS_MODULUS,
    SYSTEM_ADDRESS,
    expected_storage,
)

BLOB_COMMITMENT_VERSION_KZG = 1


@pytest.fixture
def timestamp() -> int:  # noqa: D103
    return 12


@pytest.fixture
def beacon_root(request) -> bytes:  # noqa: D103
    return to_hash_bytes(request.param) if hasattr(request, "param") else DEFAULT_BEACON_ROOT_HASH


@pytest.fixture
def env(timestamp: int, beacon_root: bytes) -> Environment:  # noqa: D103
    return Environment(
        timestamp=timestamp,
        beacon_root=beacon_root,
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
    return BEACON_ROOT_CONTRACT_CALL_GAS


@pytest.fixture
def caller_address() -> str:  # noqa: D103
    return to_address(0x100)


@pytest.fixture
def precompile_call_account(call_type: Op, call_value: int, call_gas: int) -> Account:
    """
    Code to call the beacon root precompile.
    """
    args_start, args_length, return_start, return_length = 0x20, Op.CALLDATASIZE, 0x00, 0x20
    precompile_call_code = Op.CALLDATACOPY(args_start, 0x00, args_length)
    if call_type == Op.CALL or call_type == Op.CALLCODE:
        precompile_call_code += Op.SSTORE(
            0x00,  # store the result of the precompile call in storage[0]
            call_type(
                call_gas,
                BEACON_ROOT_CONTRACT_ADDRESS,
                call_value,
                args_start,
                args_length,
                return_start,
                return_length,
            ),
        )
    elif call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
        # delegatecall and staticcall use one less argument
        precompile_call_code += Op.SSTORE(
            0x00,
            call_type(
                call_gas,
                BEACON_ROOT_CONTRACT_ADDRESS,
                args_start,
                args_length,
                return_start,
                return_length,
            ),
        )
    precompile_call_code += (
        Op.SSTORE(  # Save the return value of the precompile call
            0x01,
            Op.MLOAD(return_start),
        )
        + Op.SSTORE(  # Save the length of the return value of the precompile call
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
        code=precompile_call_code,
        balance=0x10**10,
    )


@pytest.fixture
def valid_call() -> bool:
    """
    Validity of beacon root precompile call: defaults to True.
    """
    return True


@pytest.fixture
def valid_input() -> bool:
    """
    Validity of timestamp input to precompile call: defaults to True.
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
    precompile_call_account: Account,
    system_address_balance: int,
    caller_address: str,
) -> Dict:
    """
    Prepares the pre state of all test cases, by setting the balance of the
    source account of all test transactions, and the precompile caller account.
    """
    return {
        TestAddress: Account(
            nonce=0,
            balance=0x10**10,
        ),
        caller_address: precompile_call_account,
        SYSTEM_ADDRESS: Account(
            nonce=0,
            balance=system_address_balance,
        ),
    }


@pytest.fixture
def tx_to_address(request, caller_address: Account) -> bytes:  # noqa: D103
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
    Access list included in the transaction to call the beacon root precompile.
    """
    if auto_access_list:
        return [
            AccessList(
                address=BEACON_ROOT_CONTRACT_ADDRESS,
                storage_keys=[
                    timestamp,
                    timestamp + HISTORICAL_ROOTS_MODULUS,
                ],
            ),
        ]
    return []


@pytest.fixture
def tx_data(timestamp: int) -> bytes:
    """
    Data included in the transaction to call the beacon root precompile.
    """
    return to_hash_bytes(timestamp)


@pytest.fixture
def tx_type() -> int:
    """
    Transaction type to call the caller contract or the beacon root contract directly.

    By default use a type 2 transaction.
    """
    return 2


@pytest.fixture
def tx(
    tx_to_address: str,
    tx_data: bytes,
    tx_type: int,
    access_list: List[AccessList],
    call_beacon_root_contract: bool,
) -> Transaction:
    """
    Prepares transaction to call the beacon root precompile caller account.
    """
    to = BEACON_ROOT_CONTRACT_ADDRESS if call_beacon_root_contract else tx_to_address
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
    caller_address: str,
    beacon_root: bytes,
    valid_call: bool,
    valid_input: bool,
    call_beacon_root_contract: bool,
) -> Dict:
    """
    Prepares the expected post state for a single precompile call based upon the success or
    failure of the call, and the validity of the timestamp input.
    """
    storage = Storage()
    if not call_beacon_root_contract:
        storage = expected_storage(
            beacon_root=beacon_root,
            valid_call=valid_call,
            valid_input=valid_input,
        )
    return {
        caller_address: Account(
            storage=storage,
        ),
    }
