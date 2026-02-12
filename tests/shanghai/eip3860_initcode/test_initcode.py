"""
Test [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860).

Tests ported from:
- [ethereum/tests/pull/990](https://github.com/ethereum/tests/pull/990)
- [ethereum/tests/pull/1012](https://github.com/ethereum/tests/pull/990)
"""

from typing import List

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    ceiling_division,
    compute_create_address,
)

from .helpers import (
    INITCODE_RESULTING_DEPLOYED_CODE,
    get_create_id,
)
from .spec import ref_spec_3860

REFERENCE_SPEC_GIT_PATH = ref_spec_3860.git_path
REFERENCE_SPEC_VERSION = ref_spec_3860.version

pytestmark = pytest.mark.valid_from("Shanghai")


@pytest.fixture
def initcode(fork: Fork, initcode_name: str) -> Initcode:
    """Create an Initcode object with fork-specific gas calculations."""
    if initcode_name == "max_size_ones":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=fork.max_initcode_size(),
            padding_byte=0x01,
        )
    elif initcode_name == "max_size_zeros":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=fork.max_initcode_size(),
            padding_byte=0x00,
        )
    elif initcode_name == "over_limit_ones":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=fork.max_initcode_size() + 1,
            padding_byte=0x01,
        )
    elif initcode_name == "over_limit_zeros":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=fork.max_initcode_size() + 1,
            padding_byte=0x00,
        )
    elif initcode_name == "32_bytes":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=32,
            padding_byte=0x00,
        )
    elif initcode_name == "33_bytes":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=33,
            padding_byte=0x00,
        )
    elif initcode_name == "max_size_minus_word":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=fork.max_initcode_size() - 32,
            padding_byte=0x00,
        )
    elif initcode_name == "max_size_minus_word_plus_byte":
        return Initcode(
            name=initcode_name,
            deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
            initcode_length=fork.max_initcode_size() - 32 + 1,
            padding_byte=0x00,
        )
    elif initcode_name == "empty" or initcode_name == "single_byte":
        ic_bytecode = Op.STOP if initcode_name == "single_byte" else Bytecode()
        # We insist on using `Initcode` to preserve `initcode.deploy_code`
        ic = Initcode(name=initcode_name)
        ic._bytes_ = bytes(ic_bytecode)
        ic.opcode_list = ic_bytecode.opcode_list
        return ic
    else:
        raise ValueError(f"Unknown initcode_name: {initcode_name}")


"""Test cases using a contract creating transaction"""


@pytest.mark.xdist_group(name="bigmem")
@pytest.mark.parametrize(
    "initcode_name",
    [
        pytest.param("max_size_zeros"),
        pytest.param("max_size_ones"),
        pytest.param("over_limit_zeros", marks=pytest.mark.exception_test),
        pytest.param("over_limit_ones", marks=pytest.mark.exception_test),
    ],
)
def test_contract_creating_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Alloc,
    sender: EOA,
    initcode: Initcode,
    fork: Fork,
) -> None:
    """
    Test creating a contract with initcode that is on/over the allowed limit.
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

    if len(initcode) > fork.max_initcode_size():
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


ZERO_GAS_SPECS = {"empty", "single_byte"}


def valid_gas_test_case(initcode_name: str, gas_case: str) -> bool:
    """Filter invalid gas test case combinations."""
    if (
        gas_case == "too_little_execution_gas"
        and initcode_name in ZERO_GAS_SPECS
    ):
        return False
    return True


@pytest.mark.parametrize(
    "initcode_name,gas_test_case",
    [
        pytest.param(
            i,
            g,
            marks=(
                [pytest.mark.exception_test]
                if g == "too_little_intrinsic_gas"
                else []
            ),
        )
        for i in [
            "max_size_zeros",
            "max_size_ones",
            "empty",
            "single_byte",
            "32_bytes",
            "33_bytes",
            "max_size_minus_word",
            "max_size_minus_word_plus_byte",
        ]
        for g in [
            "too_little_intrinsic_gas",
            "exact_intrinsic_gas",
            "too_little_execution_gas",
            "exact_execution_gas",
        ]
        if valid_gas_test_case(i, g)
    ],
)
class TestContractCreationGasUsage:
    """
    Test the gas cost behavior of a contract creating transaction.

    The following scenarios are tested:

    1. Test with exact intrinsic gas minus one, contract create fails and tx is
        invalid.

    2. Test with exact intrinsic gas, contract create fails, but tx is valid.

    3. Test with exact execution gas minus one, contract create fails, but tx
        is valid.

    4. Test with exact execution gas, contract create succeeds.

    Initcode must be within a valid EIP-3860 length.
    """

    @pytest.fixture
    def tx_access_list(self) -> List[AccessList]:
        """
        Return an access list to raise the intrinsic gas cost.

        Upon EIP-7623 activation, we need to use an access list to raise the
        intrinsic gas cost to be above the floor data cost.
        """
        return [
            AccessList(address=Address(i), storage_keys=[])
            for i in range(1, 478)
        ]

    @pytest.fixture
    def exact_intrinsic_gas(
        self, fork: Fork, initcode: Initcode, tx_access_list: List[AccessList]
    ) -> int:
        """
        Calculate the intrinsic tx gas cost.
        """
        tx_intrinsic_gas_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        assert tx_intrinsic_gas_cost_calculator(
            calldata=initcode,
            contract_creation=True,
            access_list=tx_access_list,
        ) == tx_intrinsic_gas_cost_calculator(
            calldata=initcode,
            contract_creation=True,
            access_list=tx_access_list,
            return_cost_deducted_prior_execution=True,
        )
        return tx_intrinsic_gas_cost_calculator(
            calldata=initcode,
            contract_creation=True,
            access_list=tx_access_list,
        )

    @pytest.fixture
    def exact_execution_gas(
        self, fork: Fork, exact_intrinsic_gas: int, initcode: Initcode
    ) -> int:
        """
        Calculate total execution gas cost.
        """
        return exact_intrinsic_gas + initcode.gas_cost(fork)

    @pytest.fixture
    def tx_error(self, gas_test_case: str) -> TransactionException | None:
        """
        Return the transaction exception, or None, as expected.

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
        tx_access_list: List[AccessList],
        tx_error: TransactionException | None,
        exact_intrinsic_gas: int,
        exact_execution_gas: int,
    ) -> Transaction:
        """
        Return a tx with `gas_limit` corresponding to the `gas_test_case`.

        Implement the gas_test_case by setting the `gas_limit` of the tx
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
            access_list=tx_access_list,
            data=initcode,
            gas_limit=gas_limit,
            gas_price=10,
            error=tx_error,
            sender=sender,
            # The entire gas limit is expected to be consumed.
            expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit),
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
        Test contract creation fails unless enough execution gas is provided.
        """
        create_contract_address = compute_create_address(
            address=sender,
            nonce=0,
        )
        if (
            gas_test_case == "exact_intrinsic_gas"
            and exact_intrinsic_gas == exact_execution_gas
        ):
            # Special scenario where the execution of the initcode and
            # gas cost to deploy are zero
            return Alloc(
                {create_contract_address: Account(code=initcode.deploy_code)}
            )
        elif gas_test_case == "exact_execution_gas":
            return Alloc(
                {create_contract_address: Account(code=initcode.deploy_code)}
            )
        return Alloc({create_contract_address: Account.NONEXISTENT})

    @pytest.mark.slow()
    def test_gas_usage(
        self,
        state_test: StateTestFiller,
        env: Environment,
        pre: Alloc,
        post: Alloc,
        tx: Transaction,
    ) -> None:
        """
        Test transaction and contract creation using different gas limits.
        """
        state_test(
            env=env,
            pre=pre,
            post=post,
            tx=tx,
        )


@pytest.mark.parametrize(
    "initcode_name",
    [
        "max_size_zeros",
        "max_size_ones",
        "over_limit_zeros",
        "over_limit_ones",
        "empty",
        "single_byte",
        "32_bytes",
        "33_bytes",
        "max_size_minus_word",
        "max_size_minus_word_plus_byte",
    ],
)
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2], ids=get_create_id)
class TestCreateInitcode:
    """
    Test contract creation with valid and invalid initcode lengths.

    Test contract creation via CREATE/CREATE2, parametrized by initcode that is
    on/over the max allowed limit.
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
        Generate code for the creator contract which calls CREATE/CREATE2.
        """
        return (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.GAS
            + (
                opcode(size=Op.CALLDATASIZE, salt=create2_salt)
                if opcode == Op.CREATE2
                else opcode(size=Op.CALLDATASIZE)
            )
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
    def creator_contract_address(
        self, pre: Alloc, creator_code: Bytecode
    ) -> Address:
        """Return address of creator contract."""
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
        Calculate address of the contract created by the creator contract.
        """
        return compute_create_address(
            address=creator_contract_address,
            nonce=1,
            salt=create2_salt,
            initcode=initcode,
            opcode=opcode,
        )

    @pytest.fixture
    def caller_code(self, creator_contract_address: Address) -> Bytecode:
        """
        Generate code for the caller contract that calls the creator contract.
        """
        return Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(
            Op.CALL(
                5000000, creator_contract_address, 0, 0, Op.CALLDATASIZE, 0, 0
            ),
            1,
        )

    @pytest.fixture
    def caller_contract_address(
        self, pre: Alloc, caller_code: Bytecode
    ) -> Address:
        """Return address of the caller contract."""
        return pre.deploy_contract(caller_code)

    @pytest.fixture
    def tx(
        self, caller_contract_address: Address, initcode: Initcode, sender: EOA
    ) -> Transaction:
        """Generate transaction that executes the caller contract."""
        return Transaction(
            nonce=0,
            to=caller_contract_address,
            data=initcode,
            gas_limit=10000000,
            gas_price=10,
            sender=sender,
        )

    @pytest.fixture
    def contract_creation_gas_cost(
        self, fork: Fork, opcode: Op, create2_salt: int
    ) -> int:
        """Calculate gas cost of the contract creation operation."""
        create_code = (
            opcode(size=Op.CALLDATASIZE, salt=create2_salt)
            if opcode == Op.CREATE2
            else opcode(size=Op.CALLDATASIZE)
        )
        return (create_code + Op.GAS).gas_cost(fork)

    @pytest.fixture
    def initcode_word_cost(self, fork: Fork, initcode: Initcode) -> int:
        """Calculate gas cost charged for the initcode length."""
        gas_costs = fork.gas_costs()
        return ceiling_division(len(initcode), 32) * gas_costs.G_INITCODE_WORD

    @pytest.fixture
    def create2_word_cost(
        self, opcode: Op, fork: Fork, initcode: Initcode
    ) -> int:
        """Calculate gas cost charged for the initcode length."""
        if opcode == Op.CREATE:
            return 0

        gas_costs = fork.gas_costs()
        return (
            ceiling_division(len(initcode), 32) * gas_costs.G_KECCAK_256_WORD
        )

    @pytest.mark.xdist_group(name="bigmem")
    @pytest.mark.slow()
    def test_create_opcode_initcode(
        self,
        state_test: StateTestFiller,
        env: Environment,
        pre: Alloc,
        post: Alloc,
        tx: Transaction,
        initcode: Initcode,
        caller_contract_address: Address,
        creator_contract_address: Address,
        created_contract_address: Address,
        contract_creation_gas_cost: int,
        initcode_word_cost: int,
        create2_word_cost: int,
        fork: Fork,
    ) -> None:
        """
        Test contract creation with valid and invalid initcode lengths.

        Test contract creation via CREATE/CREATE2, parametrized by initcode
        that is on/over the max allowed limit.
        """
        if len(initcode) > fork.max_initcode_size():
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
            expected_gas_usage += initcode.gas_cost(fork)

            # CREATE2 hashing cost should only be deducted if the initcode
            # does not exceed the max length
            expected_gas_usage += create2_word_cost

            # Initcode word cost is only deducted if the length check
            # succeeds
            expected_gas_usage += initcode_word_cost

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
