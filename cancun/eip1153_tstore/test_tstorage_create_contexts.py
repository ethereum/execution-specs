"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)
    Test cases for `TSTORE` and `TLOAD` opcode calls in contract initcode.
"""  # noqa: E501

from enum import unique
from typing import Optional

import pytest

from ethereum_test_tools import Account, Address, Environment, Initcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTestFiller,
    TestAddress,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

from . import CreateOpcodeParams, PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

# the address that creates the contract with create/create2
creator_address = 0x100


@unique
class InitcodeTestCases(PytestParameterEnum):
    """
    Defines test cases for transient storage opcode usage in contract constructor
    and deployed code.
    """

    ONLY_CONSTRUCTOR_CODE = {
        "description": (
            "Test TLOAD and TSTORE behavior in contract constructor without deployed code"
        ),
        "constructor_code": (
            # test creator's transient storage inaccessible from constructor code
            Op.SSTORE(0, Op.TLOAD(0))
            # test constructor code can use its own transient storage & creator storage unaffected
            + Op.TSTORE(0, 1)
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "deploy_code": b"",
        "expected_storage": {0: 0x0000, 1: 0x0001},
    }
    IN_CONSTRUCTOR_AND_DEPLOYED_CODE = {
        "description": "Test TLOAD and TSTORE behavior in contract constructor and deployed code",
        "constructor_code": (
            # test creator's transient storage inaccessible from constructor code
            Op.SSTORE(0, Op.TLOAD(0))
        ),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(1, Op.TLOAD(0))
            # test deploy code can use its own transient storage & creator storage unaffected
            + Op.TSTORE(1, 1)
            + Op.SSTORE(2, Op.TLOAD(1))
        ),
        "expected_storage": {0: 0x0000, 1: 0x0000, 2: 0x0001},
    }
    ACROSS_CONSTRUCTOR_AND_DEPLOYED_CODE_V0 = {
        "description": ("Test TSTORE behavior across contract constructor and deploy code. "),
        "constructor_code": (
            # constructor code should be able to store its own transient storage
            Op.TSTORE(1, 1)
        ),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(0, Op.TLOAD(0))
            # test deploy code can use its own transient storage stored from constructor code
            + Op.SSTORE(1, Op.TLOAD(1))
            # test deploy code can use its own transient storage stored from deployed code
            + Op.TSTORE(2, 1)
            + Op.SSTORE(2, Op.TLOAD(2))
        ),
        "expected_storage": {0: 0x0000, 1: 0x0001, 2: 0x0001},
    }
    ACROSS_CONSTRUCTOR_AND_DEPLOYED_CODE_V1 = {
        "description": (
            "Test TSTORE and TLOAD behavior across contract constructor and deploy code",
        ),
        "constructor_code": (
            # test creator's transient storage inaccessible from constructor
            Op.SSTORE(0, Op.TLOAD(0))
            # constructor code should be able to use its own transient storage / creator storage
            # unaffected
            + Op.TSTORE(1, 1)
            + Op.SSTORE(1, Op.TLOAD(1))
        ),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(2, Op.TLOAD(0))
            # test deploy code can use its own transient storage stored from constructor code
            + Op.SSTORE(3, Op.TLOAD(1))
            # test deploy code can use its own transient storage stored from deployed code
            + Op.TSTORE(2, 1)
            + Op.SSTORE(4, Op.TLOAD(2))
        ),
        "expected_storage": {0: 0x0000, 1: 0x0001, 2: 0x0000, 3: 0x0001, 4: 0x0001},
    }
    NO_CONSTRUCTOR_CODE = {
        "description": (
            "Test TLOAD and TSTORE behavior in contract deployed code with no constructor code"
        ),
        "constructor_code": b"",
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(0, Op.TLOAD(0))
            # test deployed code can use its own transient storage & creator storage unaffected
            + Op.TSTORE(0, 1)
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "expected_storage": {0: 0x0000, 1: 0x0001},
    }


@CreateOpcodeParams.parametrize()
@InitcodeTestCases.parametrize()
class TestTransientStorageInContractCreation:
    """
    Test transient storage in contract creation contexts:

    - TSTORE/TLOAD in initcode should not be able to access the creator's transient storage.
    - TSTORE/TLOAD in initcode should be able to access the created contract's transient
        storage.
    - TSTORE/TLOAD in creator contract should be able to use its own transient storage.
    """

    @pytest.fixture()
    def create2_salt(self) -> int:  # noqa: D102
        return 0xDEADBEEF

    @pytest.fixture()
    def initcode(  # noqa: D102
        self, deploy_code: bytes, constructor_code: bytes
    ) -> Optional[bytes]:
        initcode = Initcode(deploy_code=deploy_code, initcode_prefix=constructor_code).bytecode
        return initcode

    @pytest.fixture()
    def creator_contract_code(  # noqa: D102
        self,
        opcode: Op,
        create2_salt: int,
        created_contract_address: Address,
    ) -> bytes:
        if opcode == Op.CREATE:
            create_call = Op.CREATE(0, 0, Op.CALLDATASIZE)
        elif opcode == Op.CREATE2:
            create_call = Op.CREATE2(0, 0, Op.CALLDATASIZE, create2_salt)
        else:
            raise Exception("Invalid opcode specified for test.")
        contract_call = Op.SSTORE(4, Op.CALL(Op.GAS(), created_contract_address, 0, 0, 0, 0, 0))
        return (
            Op.TSTORE(0, 0x0100)
            + Op.TSTORE(1, 0x0200)
            + Op.TSTORE(2, 0x0300)
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + create_call
            + contract_call
            # Save the state of transient storage following call to storage; the transient
            # storage should not have been overwritten
            + Op.SSTORE(0, Op.TLOAD(0))
            + Op.SSTORE(1, Op.TLOAD(1))
            + Op.SSTORE(2, Op.TLOAD(2))
        )

    @pytest.fixture()
    def expected_creator_storage(self) -> dict:  # noqa: D102
        return {0: 0x0100, 1: 0x0200, 2: 0x0300, 4: 0x0001}

    @pytest.fixture()
    def created_contract_address(  # noqa: D102
        self, opcode: Op, create2_salt: int, initcode: bytes
    ) -> Address:
        if opcode == Op.CREATE:
            return compute_create_address(address=creator_address, nonce=1)
        if opcode == Op.CREATE2:
            return compute_create2_address(
                address=creator_address, salt=create2_salt, initcode=initcode
            )
        raise Exception("invalid opcode for generator")

    def test_contract_creation(
        self,
        state_test: StateTestFiller,
        creator_contract_code: bytes,
        created_contract_address: Address,
        initcode: bytes,
        deploy_code: bytes,
        expected_creator_storage: dict,
        expected_storage: dict,
    ) -> None:
        """
        Test transient storage in contract creation contexts.
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
            data=initcode,
            gas_limit=1_000_000_000_000,
            gas_price=10,
        )

        post = {
            creator_address: Account(
                nonce=2,
                storage=expected_creator_storage,
            ),
            created_contract_address: Account(
                nonce=1,
                code=deploy_code,
                storage=expected_storage,
            ),
        }

        state_test(
            env=Environment(),
            pre=pre,
            post=post,
            tx=tx,
        )
