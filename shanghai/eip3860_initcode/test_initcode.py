"""
abstract: Test [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860)
    Tests for  [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860).

note: Tests ported from:
    - [ethereum/tests/pull/990](https://github.com/ethereum/tests/pull/990)
    - [ethereum/tests/pull/1012](https://github.com/ethereum/tests/pull/990)
"""

from typing import Any, Dict

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    Initcode,
    StateTestFiller,
    TestAddress,
    Transaction,
    TransactionException,
    Yul,
    ceiling_division,
    compute_create2_address,
    compute_create_address,
    eip_2028_transaction_data_cost,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3860.md"
REFERENCE_SPEC_VERSION = "5f8151e19ad1c99da4bafd514ce0e8ab89783c8f"

pytestmark = pytest.mark.valid_from("Shanghai")

"""
General constants used for testing purposes
"""

MAX_INITCODE_SIZE = 49152
INITCODE_WORD_COST = 2
KECCAK_WORD_COST = 6
INITCODE_RESULTING_DEPLOYED_CODE = Op.STOP

BASE_TRANSACTION_GAS = 21000
CREATE_CONTRACT_BASE_GAS = 32000
GAS_OPCODE_GAS = 2
PUSH_DUP_OPCODE_GAS = 3
CALLDATASIZE_OPCODE_GAS = 2

"""
Helper functions
"""


def calculate_initcode_word_cost(length: int) -> int:
    """
    Calculates the added word cost on contract creation added by the
    length of the initcode based on the formula:
    INITCODE_WORD_COST * ceil(len(initcode) / 32)
    """
    return INITCODE_WORD_COST * ceiling_division(length, 32)


def calculate_create2_word_cost(length: int) -> int:
    """
    Calculates the added word cost on contract creation added by the
    hashing of the initcode during create2 contract creation.
    """
    return KECCAK_WORD_COST * ceiling_division(length, 32)


def calculate_create_tx_intrinsic_cost(initcode: Initcode, eip_3860_active: bool) -> int:
    """
    Calculates the intrinsic gas cost of a transaction that contains initcode
    and creates a contract
    """
    cost = (
        BASE_TRANSACTION_GAS  # G_transaction
        + CREATE_CONTRACT_BASE_GAS  # G_transaction_create
        + eip_2028_transaction_data_cost(initcode)  # Transaction calldata cost
    )
    if eip_3860_active:
        cost += calculate_initcode_word_cost(len(initcode))
    return cost


def calculate_create_tx_execution_cost(
    initcode: Initcode,
    eip_3860_active: bool,
) -> int:
    """
    Calculates the total execution gas cost of a transaction that
    contains initcode and creates a contract
    """
    cost = calculate_create_tx_intrinsic_cost(initcode=initcode, eip_3860_active=eip_3860_active)
    cost += initcode.deployment_gas
    cost += initcode.execution_gas
    return cost


"""
Initcode templates used throughout the tests
"""
INITCODE_ONES_MAX_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE,
    padding_byte=0x01,
    name="max_size_ones",
)

INITCODE_ZEROS_MAX_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE,
    padding_byte=0x00,
    name="max_size_zeros",
)

INITCODE_ONES_OVER_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE + 1,
    padding_byte=0x01,
    name="over_limit_ones",
)

INITCODE_ZEROS_OVER_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE + 1,
    padding_byte=0x00,
    name="over_limit_zeros",
)

INITCODE_ZEROS_32_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=32,
    padding_byte=0x00,
    name="32_bytes",
)

INITCODE_ZEROS_33_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=33,
    padding_byte=0x00,
    name="33_bytes",
)

INITCODE_ZEROS_49120_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=49120,
    padding_byte=0x00,
    name="49120_bytes",
)

INITCODE_ZEROS_49121_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=49121,
    padding_byte=0x00,
    name="49121_bytes",
)

EMPTY_INITCODE = Initcode(
    deploy_code=bytes(),
    name="empty",
)
EMPTY_INITCODE.bytecode = bytes()
EMPTY_INITCODE.deployment_gas = 0
EMPTY_INITCODE.execution_gas = 0

SINGLE_BYTE_INITCODE = Initcode(
    deploy_code=bytes(),
    name="single_byte",
)
SINGLE_BYTE_INITCODE.bytecode = bytes(Op.STOP)
SINGLE_BYTE_INITCODE.deployment_gas = 0
SINGLE_BYTE_INITCODE.execution_gas = 0

"""
Test cases using a contract creating transaction
"""


def get_initcode_name(val):
    """
    Helper function that returns an Initcode object's name to generate test
    ids.
    """
    return val.name


@pytest.mark.parametrize(
    "initcode",
    [
        INITCODE_ZEROS_MAX_LIMIT,
        INITCODE_ONES_MAX_LIMIT,
        INITCODE_ZEROS_OVER_LIMIT,
        INITCODE_ONES_OVER_LIMIT,
    ],
    ids=get_initcode_name,
)
def test_contract_creating_tx(state_test: StateTestFiller, initcode: Initcode):
    """
    Test cases using a contract creating transaction

    Test creating a contract using a transaction using an initcode that is
    on/over the max allowed limit.

    Generates a BlockchainTest based on the provided `initcode` and its
    length.
    """
    eip_3860_active = True
    env = Environment()

    pre = {
        TestAddress: Account(balance=1000000000000000000000),
    }

    post: Dict[Any, Any] = {}

    created_contract_address = compute_create_address(
        address=TestAddress,
        nonce=0,
    )

    tx = Transaction(
        nonce=0,
        to=None,
        data=initcode,
        gas_limit=10000000,
        gas_price=10,
    )

    if len(initcode) > MAX_INITCODE_SIZE and eip_3860_active:
        # Initcode is above the max size, tx inclusion in the block makes
        # it invalid.
        post[created_contract_address] = Account.NONEXISTENT
        tx.error = TransactionException.INITCODE_SIZE_EXCEEDED
    else:
        # Initcode is at or below the max size, tx inclusion in the block
        # is ok and the contract is successfully created.
        post[created_contract_address] = Account(code=Op.STOP)

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        env=env,
        tag=f"{initcode.name}",
    )


@pytest.mark.parametrize(
    "initcode",
    [
        INITCODE_ZEROS_MAX_LIMIT,
        INITCODE_ONES_MAX_LIMIT,
        EMPTY_INITCODE,
        SINGLE_BYTE_INITCODE,
        INITCODE_ZEROS_32_BYTES,
        INITCODE_ZEROS_33_BYTES,
        INITCODE_ZEROS_49120_BYTES,
        INITCODE_ZEROS_49121_BYTES,
    ],
    ids=get_initcode_name,
)
@pytest.mark.parametrize(
    "gas_test_case",
    [
        "too_little_intrinsic_gas",
        "exact_intrinsic_gas",
        "too_little_execution_gas",
        "exact_execution_gas",
    ],
    ids=lambda x: x,
)
class TestContractCreationGasUsage:
    """
    Test EIP-3860 Limit Initcode Gas Usage for a contract
    creating transaction, using different initcode lengths.

    Generates 4 test cases that verify the gas cost behavior of a
    contract creating transaction:

    1. Test with exact intrinsic gas minus one, contract create fails
        and tx is invalid.
    2. Test with exact intrinsic gas, contract create fails,
        but tx is valid.
    3. Test with exact execution gas minus one, contract create fails,
        but tx is valid.
    4. Test with exact execution gas, contract create succeeds.

    Initcode must be within valid EIP-3860 length.
    """

    @pytest.fixture
    def eip_3860_active(self):  # noqa: D102
        return True

    @pytest.fixture
    def exact_intrinsic_gas(self, initcode, eip_3860_active):
        """
        Calculates the intrinsic tx gas cost.
        """
        return calculate_create_tx_intrinsic_cost(initcode, eip_3860_active)

    @pytest.fixture
    def exact_execution_gas(self, initcode, eip_3860_active):
        """
        Calculates the total execution gas cost.
        """
        return calculate_create_tx_execution_cost(
            initcode,
            eip_3860_active,
        )

    @pytest.fixture
    def created_contract_address(self):
        """
        Calculates the address of the contract deployed via CREATE.
        """
        return compute_create_address(
            address=TestAddress,
            nonce=0,
        )

    @pytest.fixture
    def env(self) -> Environment:  # noqa: D102
        return Environment()

    @pytest.fixture
    def pre(self) -> Dict[Any, Any]:  # noqa: D102
        return {
            TestAddress: Account(balance=1000000000000000000000),
        }

    @pytest.fixture
    def tx_error(self, gas_test_case) -> TransactionException | None:
        """
        Test that the transaction is invalid if too little intrinsic gas is
        specified, otherwise the tx succeeds.
        """
        if gas_test_case == "too_little_intrinsic_gas":
            return TransactionException.INTRINSIC_GAS_TOO_LOW
        return None

    @pytest.fixture
    def tx(
        self,
        gas_test_case,
        initcode,
        tx_error,
        exact_intrinsic_gas,
        exact_execution_gas,
    ) -> Transaction:
        """
        Implement the gas_test_case by setting the gas_limit of the tx
        appropriately and test whether the tx succeeds or fails with
        appropriate error.
        """
        if gas_test_case == "too_little_intrinsic_gas":
            gas_limit = exact_intrinsic_gas - 1
        elif gas_test_case == "exact_intrinsic_gas":
            gas_limit = exact_intrinsic_gas
        elif gas_test_case == "too_little_execution_gas":
            gas_limit = exact_execution_gas - 1
        elif gas_test_case == "exact_execution_gas":
            gas_limit = exact_execution_gas
        else:
            pytest.fail("Invalid gas test case provided.")

        return Transaction(
            nonce=0,
            to=None,
            data=initcode,
            gas_limit=gas_limit,
            gas_price=10,
            error=tx_error,
        )

    @pytest.fixture
    def post(
        self,
        gas_test_case,
        initcode,
        created_contract_address,
        exact_intrinsic_gas,
        exact_execution_gas,
    ) -> Dict[Any, Any]:
        """
        Test that contract creation fails unless enough execution gas is
        provided.
        """
        if gas_test_case == "exact_intrinsic_gas" and exact_intrinsic_gas == exact_execution_gas:
            # Special scenario where the execution of the initcode and
            # gas cost to deploy are zero
            return {created_contract_address: Account(code=initcode.deploy_code)}
        elif gas_test_case == "exact_execution_gas":
            return {created_contract_address: Account(code=initcode.deploy_code)}
        return {created_contract_address: Account.NONEXISTENT}

    def test_gas_usage(
        self,
        state_test: StateTestFiller,
        gas_test_case: str,
        initcode: Initcode,
        exact_intrinsic_gas,
        exact_execution_gas,
        env,
        pre,
        tx,
        post,
    ):
        """
        Test transaction and contract creation behavior for different gas
        limits.
        """
        if (gas_test_case == "too_little_execution_gas") and (
            exact_execution_gas == exact_intrinsic_gas
        ):
            pytest.skip(
                "Special case, the execution of the initcode and gas "
                "cost to deploy are zero: Then this test case is "
                "equivalent to that of 'test_exact_intrinsic_gas'."
            )

        state_test(
            pre=pre,
            post=post,
            tx=tx,
            env=env,
            tag=f"{initcode.name}_{gas_test_case}",
        )


"""
Test cases using the CREATE and CREATE2 opcodes
"""


def get_create_id(opcode: Op):  # noqa: D103
    if opcode == Op.CREATE:
        return "create"
    if opcode == Op.CREATE2:
        return "create2"
    raise Exception("Invalid opcode specified for test.")


@pytest.mark.parametrize(
    "initcode",
    [
        INITCODE_ZEROS_MAX_LIMIT,
        INITCODE_ONES_MAX_LIMIT,
        INITCODE_ZEROS_OVER_LIMIT,
        INITCODE_ONES_OVER_LIMIT,
        EMPTY_INITCODE,
        SINGLE_BYTE_INITCODE,
        INITCODE_ZEROS_32_BYTES,
        INITCODE_ZEROS_33_BYTES,
        INITCODE_ZEROS_49120_BYTES,
        INITCODE_ZEROS_49121_BYTES,
    ],
    ids=get_initcode_name,
)
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2], ids=get_create_id)
class TestCreateInitcode:
    """
    Test contract creation via the CREATE/CREATE2 opcodes that have an initcode
    that is on/over the max allowed limit.
    """

    @pytest.fixture
    def create_code(self, opcode: Op, initcode: Initcode):  # noqa: D102
        if opcode == Op.CREATE:
            create_call = Op.CREATE(0, 0, Op.CALLDATASIZE)
        elif opcode == Op.CREATE2:
            create_call = Op.CREATE2(0, 0, Op.CALLDATASIZE, 0xDEADBEEF)
        else:
            raise Exception("Invalid opcode specified for test.")
        return (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.GAS
            + create_call
            + Op.GAS
            # stack: [Gas 2, Call Result, Gas 1]
            + Op.SWAP1
            # stack: [Call Result, Gas 2, Gas 1]
            + Op.SSTORE(0, unchecked=True)
            # stack: [Gas 2, Gas 1]
            + Op.SWAP1
            # stack: [Gas 1, Gas 2]
            + Op.SUB
            # stack: [Gas 1 - Gas 2]
            + Op.SSTORE(1, unchecked=True)
        )

    @pytest.fixture
    def created_contract_address(self, initcode: Initcode, opcode: Op):  # noqa: D102
        if opcode == Op.CREATE:
            return compute_create_address(
                address=0x100,
                nonce=1,
            )
        if opcode == Op.CREATE2:
            return compute_create2_address(
                address=0x100,
                salt=0xDEADBEEF,
                initcode=initcode,
            )
        raise Exception("invalid opcode for generator")

    def test_create_opcode_initcode(
        self,
        state_test: StateTestFiller,
        opcode: Op,
        initcode: Initcode,
        create_code: Yul,
        created_contract_address: str,
    ):
        """
        Test contract creation via the CREATE/CREATE2 opcodes that have an
        initcode that is on/over the max allowed limit.
        """
        eip_3860_active = True
        env = Environment()

        call_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        call_code += Op.SSTORE(
            Op.CALL(5000000, 0x100, 0, 0, Op.CALLDATASIZE, 0, 0),
            1,
        )

        pre = {
            TestAddress: Account(balance=1000000000000000000000),
            Address(0x100): Account(
                code=create_code,
                nonce=1,
            ),
            Address(0x200): Account(
                code=call_code,
                nonce=1,
            ),
        }

        post: Dict[Any, Any] = {}

        tx = Transaction(
            nonce=0,
            to=Address(0x200),
            data=initcode,
            gas_limit=10000000,
            gas_price=10,
        )

        # Calculate the expected gas of the contract creation operation
        expected_gas_usage = (
            CREATE_CONTRACT_BASE_GAS
            + GAS_OPCODE_GAS
            + (2 * PUSH_DUP_OPCODE_GAS)
            + CALLDATASIZE_OPCODE_GAS
        )
        if opcode == Op.CREATE2:
            # Extra PUSH operation
            expected_gas_usage += PUSH_DUP_OPCODE_GAS

        if len(initcode) > MAX_INITCODE_SIZE and eip_3860_active:
            # Call returns 0 as out of gas s[0]==1
            post[Address(0x200)] = Account(
                nonce=1,
                storage={
                    0: 1,
                    1: 0,
                },
            )

            post[created_contract_address] = Account.NONEXISTENT
            post[Address(0x100)] = Account(
                nonce=1,
                storage={
                    0: 0,
                    1: 0,
                },
            )

        else:
            # The initcode is only executed if the length check succeeds
            expected_gas_usage += initcode.execution_gas
            # The code is only deployed if the length check succeeds
            expected_gas_usage += initcode.deployment_gas

            if opcode == Op.CREATE2:
                # CREATE2 hashing cost should only be deducted if the initcode
                # does not exceed the max length
                expected_gas_usage += calculate_create2_word_cost(len(initcode))

            if eip_3860_active:
                # Initcode word cost is only deducted if the length check
                # succeeds
                expected_gas_usage += calculate_initcode_word_cost(len(initcode))

            # Call returns 1 as valid initcode length s[0]==1 && s[1]==1
            post[Address(0x200)] = Account(
                nonce=1,
                storage={
                    0: 0,
                    1: 1,
                },
            )

            post[created_contract_address] = Account(code=initcode.deploy_code)
            post[Address(0x100)] = Account(
                nonce=2,
                storage={
                    0: created_contract_address,
                    1: expected_gas_usage,
                },
            )

        state_test(
            env=env,
            pre=pre,
            post=post,
            tx=tx,
            tag=f"{initcode.name}_{opcode}",
        )
