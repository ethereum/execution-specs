"""
abstract: Test [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860)
    Tests for  [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860).

note: Tests ported from:
    - [ethereum/tests/pull/990](https://github.com/ethereum/tests/pull/990)
    - [ethereum/tests/pull/1012](https://github.com/ethereum/tests/pull/990)
"""

import pytest

from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Initcode,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create2_address,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import (
    INITCODE_RESULTING_DEPLOYED_CODE,
    calculate_create2_word_cost,
    calculate_create_tx_execution_cost,
    calculate_create_tx_intrinsic_cost,
    calculate_initcode_word_cost,
    get_create_id,
    get_initcode_name,
)
from .spec import Spec, ref_spec_3860

REFERENCE_SPEC_GIT_PATH = ref_spec_3860.git_path
REFERENCE_SPEC_VERSION = ref_spec_3860.version

pytestmark = pytest.mark.valid_from("Shanghai")


"""
Initcode templates used throughout the tests
"""
INITCODE_ONES_MAX_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=Spec.MAX_INITCODE_SIZE,
    padding_byte=0x01,
    name="max_size_ones",
)

INITCODE_ZEROS_MAX_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=Spec.MAX_INITCODE_SIZE,
    padding_byte=0x00,
    name="max_size_zeros",
)

INITCODE_ONES_OVER_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=Spec.MAX_INITCODE_SIZE + 1,
    padding_byte=0x01,
    name="over_limit_ones",
)

INITCODE_ZEROS_OVER_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=Spec.MAX_INITCODE_SIZE + 1,
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
    name="empty",
)
EMPTY_INITCODE._bytes_ = bytes()
EMPTY_INITCODE.deployment_gas = 0
EMPTY_INITCODE.execution_gas = 0

SINGLE_BYTE_INITCODE = Initcode(
    name="single_byte",
)
SINGLE_BYTE_INITCODE._bytes_ = bytes(Op.STOP)
SINGLE_BYTE_INITCODE.deployment_gas = 0
SINGLE_BYTE_INITCODE.execution_gas = 0

"""
Test cases using a contract creating transaction
"""


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
def test_contract_creating_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Alloc,
    sender: EOA,
    initcode: Initcode,
):
    """
    Tests creating a contract using a transaction with an initcode that is
    on/over the max allowed limit.
    """
    create_contract_address = compute_create_address(
        address=sender,
        nonce=0,
    )

    tx = Transaction(
        nonce=0,
        to=None,
        data=initcode,
        gas_limit=10000000,
        gas_price=10,
        sender=sender,
    )

    if len(initcode) > Spec.MAX_INITCODE_SIZE:
        # Initcode is above the max size, tx inclusion in the block makes
        # it invalid.
        post[create_contract_address] = Account.NONEXISTENT
        tx.error = TransactionException.INITCODE_SIZE_EXCEEDED
    else:
        # Initcode is at or below the max size, tx inclusion in the block
        # is ok and the contract is successfully created.
        post[create_contract_address] = Account(code=Op.STOP)

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
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
    Tests the following cases that verify the gas cost behavior of a
    contract creating transaction:

    1. Test with exact intrinsic gas minus one, contract create fails
        and tx is invalid.
    2. Test with exact intrinsic gas, contract create fails,
        but tx is valid.
    3. Test with exact execution gas minus one, contract create fails,
        but tx is valid.
    4. Test with exact execution gas, contract create succeeds.

    Initcode must be within a valid EIP-3860 length.
    """

    @pytest.fixture
    def exact_intrinsic_gas(self, initcode: Initcode) -> int:
        """
        Calculates the intrinsic tx gas cost.
        """
        return calculate_create_tx_intrinsic_cost(initcode)

    @pytest.fixture
    def exact_execution_gas(self, initcode: Initcode) -> int:
        """
        Calculates the total execution gas cost.
        """
        return calculate_create_tx_execution_cost(initcode)

    @pytest.fixture
    def tx_error(self, gas_test_case: str) -> TransactionException | None:
        """
        Check that the transaction is invalid if too little intrinsic gas is
        specified, otherwise the tx is valid and succeeds.
        """
        if gas_test_case == "too_little_intrinsic_gas":
            return TransactionException.INTRINSIC_GAS_TOO_LOW
        return None

    @pytest.fixture
    def tx(
        self,
        sender: EOA,
        initcode: Initcode,
        gas_test_case: str,
        tx_error: TransactionException | None,
        exact_intrinsic_gas: int,
        exact_execution_gas: int,
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
            sender=sender,
        )

    @pytest.fixture
    def post(
        self,
        sender: EOA,
        initcode: Initcode,
        gas_test_case: str,
        exact_intrinsic_gas: int,
        exact_execution_gas: int,
    ) -> Alloc:
        """
        Test that contract creation fails unless enough execution gas is
        provided.
        """
        create_contract_address = compute_create_address(
            address=sender,
            nonce=0,
        )
        if gas_test_case == "exact_intrinsic_gas" and exact_intrinsic_gas == exact_execution_gas:
            # Special scenario where the execution of the initcode and
            # gas cost to deploy are zero
            return Alloc({create_contract_address: Account(code=initcode.deploy_code)})
        elif gas_test_case == "exact_execution_gas":
            return Alloc({create_contract_address: Account(code=initcode.deploy_code)})
        return Alloc({create_contract_address: Account.NONEXISTENT})

    def test_gas_usage(
        self,
        state_test: StateTestFiller,
        env: Environment,
        pre: Alloc,
        post: Alloc,
        tx: Transaction,
        gas_test_case: str,
        initcode: Initcode,
        exact_intrinsic_gas: int,
        exact_execution_gas: int,
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
            env=env,
            pre=pre,
            post=post,
            tx=tx,
        )


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
    def create2_salt(self) -> int:
        """
        Salt value used for CREATE2 contract creation.
        """
        return 0xDEADBEEF

    @pytest.fixture
    def creator_code(self, opcode: Op, create2_salt: int) -> Bytecode:
        """
        Generates the code for the creator contract which performs the CREATE/CREATE2 operation.
        """
        return (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.GAS
            + opcode(size=Op.CALLDATASIZE, salt=create2_salt)
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
    def creator_contract_address(self, pre: Alloc, creator_code: Bytecode) -> Address:
        """
        Returns the address of creator contract.
        """
        return pre.deploy_contract(creator_code)

    @pytest.fixture
    def created_contract_address(  # noqa: D103
        self,
        opcode: Op,
        create2_salt: int,
        initcode: Initcode,
        creator_contract_address: Address,
    ) -> Address:
        """
        Calculates the address of the contract created by the creator contract.
        """
        if opcode == Op.CREATE:
            return compute_create_address(
                address=creator_contract_address,
                nonce=1,
            )
        if opcode == Op.CREATE2:
            return compute_create2_address(
                address=creator_contract_address,
                salt=create2_salt,
                initcode=initcode,
            )
        raise Exception("Invalid opcode for generator")

    @pytest.fixture
    def caller_code(self, creator_contract_address: Address) -> Bytecode:
        """
        Generates the code for the caller contract that calls the creator contract.
        """
        return Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(
            Op.CALL(5000000, creator_contract_address, 0, 0, Op.CALLDATASIZE, 0, 0), 1
        )

    @pytest.fixture
    def caller_contract_address(self, pre: Alloc, caller_code: Bytecode) -> Address:
        """
        Returns the address of the caller contract.
        """
        return pre.deploy_contract(caller_code)

    @pytest.fixture
    def tx(self, caller_contract_address: Address, initcode: Initcode, sender: EOA) -> Transaction:
        """
        Generates the transaction that executes the caller contract.
        """
        return Transaction(
            nonce=0,
            to=caller_contract_address,
            data=initcode,
            gas_limit=10000000,
            gas_price=10,
            sender=sender,
        )

    @pytest.fixture
    def contract_creation_gas_cost(self, opcode: Op) -> int:
        """
        Calculates the gas cost of the contract creation operation.
        """
        CREATE_CONTRACT_BASE_GAS = 32000
        GAS_OPCODE_GAS = 2
        PUSH_DUP_OPCODE_GAS = 3
        CALLDATASIZE_OPCODE_GAS = 2
        contract_creation_gas_usage = (
            CREATE_CONTRACT_BASE_GAS
            + GAS_OPCODE_GAS
            + (2 * PUSH_DUP_OPCODE_GAS)
            + CALLDATASIZE_OPCODE_GAS
        )
        if opcode == Op.CREATE2:  # Extra push operation
            contract_creation_gas_usage += PUSH_DUP_OPCODE_GAS
        return contract_creation_gas_usage

    def test_create_opcode_initcode(
        self,
        state_test: StateTestFiller,
        env: Environment,
        pre: Alloc,
        post: Alloc,
        tx: Transaction,
        opcode: Op,
        initcode: Initcode,
        caller_contract_address: Address,
        creator_contract_address: Address,
        created_contract_address: Address,
        contract_creation_gas_cost: int,
    ):
        """
        Test contract creation via the CREATE/CREATE2 opcodes that have an
        initcode that is on/over the max allowed limit.
        """
        if len(initcode) > Spec.MAX_INITCODE_SIZE:
            # Call returns 0 as out of gas s[0]==1
            post[caller_contract_address] = Account(
                nonce=1,
                storage={
                    0: 1,
                    1: 0,
                },
            )

            post[created_contract_address] = Account.NONEXISTENT
            post[creator_contract_address] = Account(
                nonce=1,
                storage={
                    0: 0,
                    1: 0,
                },
            )

        else:
            expected_gas_usage = contract_creation_gas_cost
            # The initcode is only executed if the length check succeeds
            expected_gas_usage += initcode.execution_gas
            # The code is only deployed if the length check succeeds
            expected_gas_usage += initcode.deployment_gas

            if opcode == Op.CREATE2:
                # CREATE2 hashing cost should only be deducted if the initcode
                # does not exceed the max length
                expected_gas_usage += calculate_create2_word_cost(len(initcode))

            # Initcode word cost is only deducted if the length check
            # succeeds
            expected_gas_usage += calculate_initcode_word_cost(len(initcode))

            # Call returns 1 as valid initcode length s[0]==1 && s[1]==1
            post[caller_contract_address] = Account(
                nonce=1,
                storage={
                    0: 0,
                    1: 1,
                },
            )

            post[created_contract_address] = Account(code=initcode.deploy_code)
            post[creator_contract_address] = Account(
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
        )
