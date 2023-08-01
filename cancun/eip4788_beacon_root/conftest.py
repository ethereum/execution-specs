"""
Shared pytest definitions local to EIP-4788 tests.
"""
from typing import Dict

import pytest

from ethereum_test_tools import (
    Account,
    Environment,
    HistoryStorageAddress,
    TestAddress,
    Transaction,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import (
    BEACON_ROOT_PRECOMPILE_ADDRESS,
    BEACON_ROOT_PRECOMPILE_GAS,
    DEFAULT_BEACON_ROOT_HASH,
    expected_storage,
)


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
def call_type() -> Op:  # noqa: D103
    return Op.CALL


@pytest.fixture
def call_gas() -> int:  # noqa: D103
    return BEACON_ROOT_PRECOMPILE_GAS


@pytest.fixture
def caller_address() -> str:  # noqa: D103
    return to_address(0x100)


@pytest.fixture
def precompile_call_account(call_type: Op, call_gas: int) -> Account:
    """
    Code to call the beacon root precompile.
    """
    precompile_call_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    if call_type == Op.CALL or call_type == Op.CALLCODE:
        precompile_call_code += Op.SSTORE(
            0,  # store the result of the precompile call in storage[0]
            call_type(
                call_gas,
                BEACON_ROOT_PRECOMPILE_ADDRESS,
                0x00,
                0x00,
                Op.CALLDATASIZE,
                0x00,
                0x20,
            ),
        )
    elif call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
        # delegatecall and staticcall use one less argument
        precompile_call_code += Op.SSTORE(
            0,
            call_type(
                call_gas,
                BEACON_ROOT_PRECOMPILE_ADDRESS,
                0x00,
                Op.CALLDATASIZE,
                0x00,
                0x20,
            ),
        )
    precompile_call_code += (
        Op.SSTORE(1, Op.MLOAD(0x00))
        + Op.SSTORE(2, Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(0, 0x0, Op.RETURNDATASIZE)
        + Op.SSTORE(3, Op.MLOAD(0x00))
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
def pre(
    precompile_call_account: Account,
    caller_address: str,
) -> Dict:
    """
    Prepares the pre state of all test cases, by setting the balance of the
    source account of all test transactions, and the precompile caller account.
    """
    return {
        HistoryStorageAddress: Account(balance=1),
        TestAddress: Account(
            nonce=0,
            balance=0x10**10,
        ),
        caller_address: precompile_call_account,
    }


@pytest.fixture
def tx_to_address(request, caller_address: Account) -> bytes:  # noqa: D103
    return request.param if hasattr(request, "param") else caller_address


@pytest.fixture
def tx(
    tx_to_address: str,
    timestamp: int,
) -> Transaction:
    """
    Prepares transaction to call the beacon root precompile caller account.
    """
    return Transaction(
        ty=2,
        nonce=0,
        data=to_hash_bytes(timestamp),
        to=tx_to_address,
        value=0,
        gas_limit=1000000,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=0,
    )


@pytest.fixture
def post(
    caller_address: str,
    beacon_root: bytes,
    timestamp: int,
    valid_call: bool,
    valid_input: bool,
) -> Dict:
    """
    Prepares the expected post state for a single precompile call based upon the success or
    failure of the call, and the validity of the timestamp input.
    """
    return {
        caller_address: Account(
            storage=expected_storage(
                beacon_root,
                timestamp,
                valid_call,
                valid_input,
            ),
        ),
    }
