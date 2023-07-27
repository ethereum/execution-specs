"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)

    Test cases for `TSTORE` and `TLOAD` opcode calls in contract initcode.
"""  # noqa: E501

from enum import Enum, unique
from textwrap import dedent

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTestFiller,
    TestAddress,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Shanghai")]

# the address that creates the contract with create/create2
creator_address = 0x100

test_case_description = dedent(
    """

    - TSTORE/TLOAD in initcode should not be able to access the creator's transient storage.
    - TSTORE/TLOAD in initcode should be able to access the created contract's transient storage.
    - TSTORE/TLOAD in creator contract should be able to use its own transient storage.
    """
)


@unique
class TStorageInitCodeTestCases(Enum):
    """
    Test cases for transient storage opcodes use in contract initcode.
    """

    CREATE = {
        "pytest_param": pytest.param(Op.CREATE, id="create"),
        "description": (
            "TSTORE0100: Test TLOAD and TSTORE behavior in a contract's initcode created by "
            "CREATE:" + test_case_description
        ),
    }
    CREATE2 = {
        "pytest_param": pytest.param(Op.CREATE2, id="create2"),
        "description": (
            "TSTORE0101: Test TLOAD and TSTORE behavior in a contract's initcode created by "
            "CREATE2:" + test_case_description
        ),
    }

    def __init__(self, test_case):
        self._value_ = test_case["pytest_param"]
        self.description = test_case["description"]


@pytest.fixture()
def created_contract_initcode() -> bytes:
    """
    The following code will be executed in the constructor of the created contract.
    """
    bytecode = b""
    # creator's transient storage shouldn't be available in the created contract's constructor
    bytecode += Op.SSTORE(0, Op.TLOAD(0))
    # constructor should be able to use its own transient storage / should not be able to use
    # creator's transient storage
    bytecode += Op.TSTORE(0, 1)
    bytecode += Op.SSTORE(1, Op.TLOAD(0))
    # dummy check
    bytecode += Op.SSTORE(2, 2)
    bytecode += Op.RETURN(0, 1)
    return bytecode


@pytest.fixture()
def create2_salt() -> int:  # noqa: D103
    return 0xDEADBEEF


@pytest.fixture()
def creator_contract_code(opcode: Op, create2_salt: int) -> bytes:  # noqa: D103
    if opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, Op.CALLDATASIZE)
    elif opcode == Op.CREATE2:
        create_call = Op.CREATE2(0, 0, Op.CALLDATASIZE, create2_salt)
    else:
        raise Exception("Invalid opcode specified for test.")
    return (
        Op.TSTORE(0, 420)
        + Op.TSTORE(1, 69)
        + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + create_call
        + Op.SSTORE(0, Op.TLOAD(0))
        + Op.SSTORE(1, Op.TLOAD(1))
    )


@pytest.fixture()
def created_contract_address(  # noqa: D103
    opcode: Op, create2_salt: int, created_contract_initcode: bytes
) -> str:
    if opcode == Op.CREATE:
        return compute_create_address(
            address=creator_address,
            nonce=1,
        )
    if opcode == Op.CREATE2:
        return compute_create2_address(
            address=creator_address,
            salt=create2_salt,
            initcode=created_contract_initcode,
        )
    raise Exception("invalid opcode for generator")


@pytest.mark.parametrize(
    "opcode",
    [test_case._value_ for test_case in TStorageInitCodeTestCases],
    ids=[test_case._value_.id for test_case in TStorageInitCodeTestCases],
)
def test_tload_tstore_in_initcode(
    state_test: StateTestFiller,
    creator_contract_code: str,
    created_contract_initcode: str,
    created_contract_address: str,
) -> None:
    """
    Test transient storage in contract creation contexts:

    - TSTORE/TLOAD in initcode should not be able to access the creator's transient storage.
    - TSTORE/TLOAD in initcode should be able to access the created contract's transient storage.
    - TSTORE/TLOAD in creator contract should be able to use its own transient storage.
    """
    pre = {
        TestAddress: Account(balance=100_000_000_000_000),
        creator_address: Account(
            code=creator_contract_code,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=0,
        to=creator_address,
        data=created_contract_initcode,
        gas_limit=1_000_000_000_000,
        gas_price=10,
    )

    post = {
        creator_address: Account(
            nonce=2,
            storage={
                0: 420,
                1: 69,
            },
        ),
        created_contract_address: Account(
            nonce=1,
            code=Op.STOP,
            storage={
                0: 0,
                1: 1,
                2: 2,
            },
        ),
    }

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        txs=[tx],
    )
