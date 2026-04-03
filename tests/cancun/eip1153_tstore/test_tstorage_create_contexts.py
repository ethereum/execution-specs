"""
Test transient storage in contract creation contexts.
"""

from enum import unique

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing import Macros as Om

from . import CreateOpcodeParams, PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]


@unique
class InitcodeTestCases(PytestParameterEnum):
    """
    Defines test cases for transient storage opcode usage in contract
    constructor and deployed code.
    """

    ONLY_CONSTRUCTOR_CODE = {
        "description": (
            "Test TLOAD and TSTORE behavior in contract constructor without"
            " deployed code"
        ),
        "constructor_code": (
            # test creator's transient storage inaccessible from constructor
            # code
            Op.SSTORE(0, Op.TLOAD(0))
            # test constructor code can use its own transient storage & creator
            # storage unaffected
            + Op.TSTORE(0, 1)
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "deploy_code": Bytecode(),
        "expected_storage": {0: 0x0000, 1: 0x0001},
    }
    IN_CONSTRUCTOR_AND_DEPLOYED_CODE = {
        "description": "Test TLOAD and TSTORE behavior in contract "
        "constructor and deployed code",
        "constructor_code": (
            # test creator's transient storage inaccessible from constructor
            # code
            Op.SSTORE(0, Op.TLOAD(0))
        ),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(1, Op.TLOAD(0))
            # test deploy code can use its own transient storage & creator
            # storage unaffected
            + Op.TSTORE(1, 1)
            + Op.SSTORE(2, Op.TLOAD(1))
        ),
        "expected_storage": {0: 0x0000, 1: 0x0000, 2: 0x0001},
    }
    ACROSS_CONSTRUCTOR_AND_DEPLOYED_CODE_V0 = {
        "description": (
            "Test TSTORE behavior across contract constructor "
            "and deploy code. "
        ),
        "constructor_code": (
            # constructor code should be able to store its own transient
            # storage
            Op.TSTORE(1, 1)
        ),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(0, Op.TLOAD(0))
            # test deploy code can use its own transient storage stored from
            # constructor code
            + Op.SSTORE(1, Op.TLOAD(1))
            # test deploy code can use its own transient storage stored from
            # deployed code
            + Op.TSTORE(2, 1)
            + Op.SSTORE(2, Op.TLOAD(2))
        ),
        "expected_storage": {0: 0x0000, 1: 0x0001, 2: 0x0001},
    }
    ACROSS_CONSTRUCTOR_AND_DEPLOYED_CODE_V1 = {
        "description": (
            "Test TSTORE and TLOAD behavior across contract constructor "
            "and deploy code",
        ),
        "constructor_code": (
            # test creator's transient storage inaccessible from constructor
            Op.SSTORE(0, Op.TLOAD(0))
            # constructor code should be able to use its own transient storage
            # / creator storage unaffected
            + Op.TSTORE(1, 1)
            + Op.SSTORE(1, Op.TLOAD(1))
        ),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(2, Op.TLOAD(0))
            # test deploy code can use its own transient storage stored from
            # constructor code
            + Op.SSTORE(3, Op.TLOAD(1))
            # test deploy code can use its own transient storage stored from
            # deployed code
            + Op.TSTORE(2, 1)
            + Op.SSTORE(4, Op.TLOAD(2))
        ),
        "expected_storage": {
            0: 0x0000,
            1: 0x0001,
            2: 0x0000,
            3: 0x0001,
            4: 0x0001,
        },
    }
    NO_CONSTRUCTOR_CODE = {
        "description": (
            "Test TLOAD and TSTORE behavior in contract deployed code with "
            "no constructor code"
        ),
        "constructor_code": Bytecode(),
        "deploy_code": (
            # test creator's transient storage inaccessible from deployed code
            Op.SSTORE(0, Op.TLOAD(0))
            # test deployed code can use its own transient storage & creator
            # storage unaffected
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
    - TSTORE/TLOAD in initcode should not be able to access the creator's
      transient storage.
    - TSTORE/TLOAD in initcode should be able to access the created contract's
      transient storage.
    - TSTORE/TLOAD in creator contract should be able to use its own
      transient storage.
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
        return Initcode(
            deploy_code=deploy_code, initcode_prefix=constructor_code
        )

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
            + Op.SSTORE(
                4,
                Op.CALL(
                    address=(
                        opcode(size=Op.CALLDATASIZE, salt=create2_salt)
                        if opcode == Op.CREATE2
                        else opcode(size=Op.CALLDATASIZE)
                    )
                ),
            )
            # Save the state of transient storage following call to storage;
            # the transient storage should not have been overwritten
            + Op.SSTORE(0, Op.TLOAD(0))
            + Op.SSTORE(1, Op.TLOAD(1))
            + Op.SSTORE(2, Op.TLOAD(2))
        )

    @pytest.fixture()
    def creator_address(
        self, pre: Alloc, creator_contract_code: Bytecode
    ) -> Address:
        """Address that creates the contract with create/create2."""
        return pre.deploy_contract(creator_contract_code)

    @pytest.fixture()
    def expected_creator_storage(self) -> dict:  # noqa: D102
        return {0: 0x0100, 1: 0x0200, 2: 0x0300, 4: 0x0001}

    @pytest.fixture()
    def created_contract_address(  # noqa: D102
        self,
        creator_address: Address,
        opcode: Op,
        create2_salt: int,
        initcode: Initcode,
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

        state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/holiman/goevmlab/blob/master/examples/tstore_bug-2/main.go",
    ],
)
@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_tstore_rollback_on_failed_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Test TSTORE is rolled back after failed CREATE/CREATE2 initcode.

    Regression test for
    https://github.com/ethereum/execution-specs/issues/917

    Initcode does TLOAD(1) to compute a return size, then does
    TSTORE(1, max_code_size), then returns data of the computed size.
    When TLOAD(1) is 0, the return size is max_code_size + 0x0a
    (exceeds max code size), so creation fails.

    The caller invokes CREATE/CREATE2 twice with the same initcode.
    If TSTORE from the first (failed) creation is properly rolled
    back, the second creation also sees TLOAD(1)==0 and fails the
    same way. If not rolled back, TLOAD(1)==max_code_size and the
    second creation succeeds.
    """
    max_code_size = fork.max_code_size()
    fail_size = max_code_size + 0x0A

    # Initcode:
    #   return_size = fail_size - TLOAD(1)
    #   TSTORE(1, max_code_size)
    #   RETURN(offset=0, size=return_size)
    #
    # TLOAD(1)==0:              return_size = fail_size > max code size -> fail
    # TLOAD(1)==max_code_size:  return_size = 0x0a <= max code size -> succeed
    initcode = (
        Op.TLOAD(1)
        + Op.PUSH2(fail_size)
        + Op.SUB
        + Op.TSTORE(1, max_code_size)
        + Op.PUSH1(0)
        + Op.RETURN
    )
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    caller_code = (
        Om.MSTORE(initcode_bytes, 0)
        + Op.SSTORE(
            0,
            create_opcode(0, 0, initcode_len, 0)
            if create_opcode == Op.CREATE2
            else create_opcode(0, 0, initcode_len),
        )
        + Op.SSTORE(
            1,
            create_opcode(0, 0, initcode_len, 0)
            if create_opcode == Op.CREATE2
            else create_opcode(0, 0, initcode_len),
        )
    )
    caller_address = pre.deploy_contract(caller_code, storage={0: 1, 1: 1})

    # Amsterdam EIP-8037 charges state gas for CREATE (new account +
    # code deposit). Supply extra gas via reservoir.
    gas_limit = 16_000_000
    if fork.code_deposit_state_gas(code_size=1) > 0:
        gas_limit_cap = fork.transaction_gas_limit_cap() or gas_limit
        code_deposit_state = fork.code_deposit_state_gas(code_size=fail_size)
        new_account_state = fork.gas_costs().GAS_NEW_ACCOUNT
        state_gas = 2 * (code_deposit_state + new_account_state)
        gas_limit = gas_limit_cap + state_gas

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller_address,
        gas_limit=gas_limit,
        access_list=[
            AccessList(address=caller_address, storage_keys=[0, 1]),
        ],
    )

    post = {
        # Both creations fail because TSTORE is rolled back;
        # initial storage {0: 1, 1: 1} is overwritten to zeros
        caller_address: Account(storage={0: 0, 1: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
