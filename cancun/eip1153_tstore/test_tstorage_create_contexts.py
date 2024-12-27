"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)
    Test cases for `TSTORE` and `TLOAD` opcode calls in contract initcode.
"""  # noqa: E501

from enum import unique

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools import Opcodes as Op

from . import CreateOpcodeParams, PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]


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
        "deploy_code": Bytecode(),
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
        "constructor_code": Bytecode(),
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
    Test transient storage in contract creation contexts.
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
        self,
        deploy_code: Bytecode,
        constructor_code: Bytecode,
    ) -> Initcode:
        return Initcode(deploy_code=deploy_code, initcode_prefix=constructor_code)

    @pytest.fixture()
    def creator_contract_code(  # noqa: D102
        self,
        opcode: Op,
        create2_salt: int,
    ) -> Bytecode:
        return (
            Op.TSTORE(0, 0x0100)
            + Op.TSTORE(1, 0x0200)
            + Op.TSTORE(2, 0x0300)
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.SSTORE(4, Op.CALL(address=opcode(size=Op.CALLDATASIZE, salt=create2_salt)))
            # Save the state of transient storage following call to storage; the transient
            # storage should not have been overwritten
            + Op.SSTORE(0, Op.TLOAD(0))
            + Op.SSTORE(1, Op.TLOAD(1))
            + Op.SSTORE(2, Op.TLOAD(2))
        )

    @pytest.fixture()
    def creator_address(self, pre: Alloc, creator_contract_code: Bytecode) -> Address:
        """Address that creates the contract with create/create2."""
        return pre.deploy_contract(creator_contract_code)

    @pytest.fixture()
    def expected_creator_storage(self) -> dict:  # noqa: D102
        return {0: 0x0100, 1: 0x0200, 2: 0x0300, 4: 0x0001}

    @pytest.fixture()
    def created_contract_address(  # noqa: D102
        self, creator_address: Address, opcode: Op, create2_salt: int, initcode: Initcode
    ) -> Address:
        return compute_create_address(
            address=creator_address,
            nonce=1,
            salt=create2_salt,
            initcode=initcode,
            opcode=opcode,
        )

    def test_contract_creation(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        creator_address: Address,
        created_contract_address: Address,
        initcode: Initcode,
        deploy_code: Bytecode,
        expected_creator_storage: dict,
        expected_storage: dict,
    ) -> None:
        """Test transient storage in contract creation contexts."""
        sender = pre.fund_eoa()

        tx = Transaction(
            sender=sender,
            to=creator_address,
            data=initcode,
            gas_limit=1_000_000,
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
