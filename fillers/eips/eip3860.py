"""
Test EIP-3860: Limit and meter initcode
EIP: https://eips.ethereum.org/EIPS/eip-3860
Source tests: https://github.com/ethereum/tests/pull/990
              https://github.com/ethereum/tests/pull/1012
"""


from typing import Any, Dict

from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTest,
    Environment,
    Initcode,
    StateTest,
    TestAddress,
    Transaction,
    Yul,
    ceiling_division,
    compute_create2_address,
    compute_create_address,
    eip_2028_transaction_data_cost,
    test_from,
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

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


def calculate_create_tx_intrinsic_cost(
    initcode: Initcode, eip_3860_active: bool
) -> int:
    """
    Calcultes the intrinsic gas cost of a transaction that contains initcode
    and creates a contract
    """
    cost = (
        BASE_TRANSACTION_GAS  # G_transaction
        + CREATE_CONTRACT_BASE_GAS  # G_transaction_create
        + eip_2028_transaction_data_cost(
            initcode.assemble()
        )  # Transaction calldata cost
    )
    if eip_3860_active:
        cost += calculate_initcode_word_cost(len(initcode.assemble()))
    return cost


def calculate_create_tx_execution_cost(
    initcode: Initcode,
    eip_3860_active: bool,
) -> int:
    """
    Calculates the total execution gas cost of a transaction that
    contains initcode and creates a contract
    """
    cost = calculate_create_tx_intrinsic_cost(
        initcode=initcode, eip_3860_active=eip_3860_active
    )
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
    name="max_size_ones_initcode",
)

INITCODE_ZEROS_MAX_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE,
    padding_byte=0x00,
    name="max_size_zeros_initcode",
)

INITCODE_ONES_OVER_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE + 1,
    padding_byte=0x01,
    name="over_limit_ones_initcode",
)

INITCODE_ZEROS_OVER_LIMIT = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=MAX_INITCODE_SIZE + 1,
    padding_byte=0x00,
    name="over_limit_zeros_initcode",
)

INITCODE_ZEROS_32_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=32,
    padding_byte=0x00,
    name="32_bytes_initcode",
)

INITCODE_ZEROS_33_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=33,
    padding_byte=0x00,
    name="33_bytes_initcode",
)

INITCODE_ZEROS_49120_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=49120,
    padding_byte=0x00,
    name="49120_bytes_initcode",
)

INITCODE_ZEROS_49121_BYTES = Initcode(
    deploy_code=INITCODE_RESULTING_DEPLOYED_CODE,
    initcode_length=49121,
    padding_byte=0x00,
    name="49121_bytes_initcode",
)

EMPTY_INITCODE = Initcode(
    deploy_code=bytes(),
    name="empty_initcode",
)
EMPTY_INITCODE.bytecode = bytes()
EMPTY_INITCODE.deployment_gas = 0
EMPTY_INITCODE.execution_gas = 0

SINGLE_BYTE_INITCODE = Initcode(
    deploy_code=bytes(),
    name="single_byte_initcode",
)
SINGLE_BYTE_INITCODE.bytecode = Op.STOP
SINGLE_BYTE_INITCODE.deployment_gas = 0
SINGLE_BYTE_INITCODE.execution_gas = 0

"""
Test cases using a contract creating transaction
"""


def generate_tx_initcode_limit_test_cases(
    initcode: Initcode,
    eip_3860_active: bool,
):
    """
    Generates a BlockchainTest based on the provided `initcode` and
    its length.
    """
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

    block = Block(txs=[tx])

    if len(initcode.assemble()) > MAX_INITCODE_SIZE and eip_3860_active:
        # Initcode is above the max size, tx inclusion in the block makes
        # it invalid.
        post[created_contract_address] = Account.NONEXISTENT
        tx.error = "max initcode size exceeded"
        block.exception = "max initcode size exceeded"
    else:
        # Initcode is at or below the max size, tx inclusion in the block
        # is ok and the contract is successfully created.
        post[created_contract_address] = Account(code=Op.STOP)

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[block],
        genesis_environment=env,
        name=f"initcode_tx_{initcode.name}",
    )


@test_from(fork="shanghai", eips=[3860])
def test_initcode_limit_contract_creating_tx(fork):
    """
    Test creating a contract using a transaction using an initcode that is
    on/over the max allowed limit.
    """
    yield from generate_tx_initcode_limit_test_cases(
        initcode=INITCODE_ZEROS_MAX_LIMIT,
        eip_3860_active=True,
    )
    yield from generate_tx_initcode_limit_test_cases(
        initcode=INITCODE_ONES_MAX_LIMIT,
        eip_3860_active=True,
    )
    yield from generate_tx_initcode_limit_test_cases(
        initcode=INITCODE_ZEROS_OVER_LIMIT,
        eip_3860_active=True,
    )
    yield from generate_tx_initcode_limit_test_cases(
        initcode=INITCODE_ONES_OVER_LIMIT,
        eip_3860_active=True,
    )


def generate_gas_cost_test_cases(
    initcode: Initcode,
    eip_3860_active: bool,
):
    """
    Generates 4 test cases that verify the intrinsic gas cost of a
    contract creating transaction:
        1) Test with exact intrinsic gas, contract create fails,
           but tx is valid.
        2) Test with exact intrinsic gas minus one, contract create fails
           and tx is invalid.
        3) Test with exact execution gas minus one, contract create fails,
           but tx is valid.
        4) Test with exact execution gas, contract create succeeds.

    Initcode must be within valid EIP-3860 length.
    """
    # Common setup to all test cases
    env = Environment()
    pre = {
        TestAddress: Account(balance=1000000000000000000000),
    }
    post: Dict[Any, Any] = {}
    created_contract_address = compute_create_address(
        address=TestAddress,
        nonce=0,
    )

    # Calculate both the intrinsic tx gas cost and the total execution
    # gas cost, used throughout all tests
    exact_tx_intrinsic_gas = calculate_create_tx_intrinsic_cost(
        initcode, eip_3860_active
    )
    exact_tx_execution_gas = calculate_create_tx_execution_cost(
        initcode,
        eip_3860_active,
    )

    """
    Test case 1: Test with exact intrinsic gas, contract create fails,
                 but tx is valid.
    """
    tx = Transaction(
        nonce=0,
        to=None,
        data=initcode,
        gas_limit=exact_tx_intrinsic_gas,
        gas_price=10,
    )
    block = Block(txs=[tx])
    if exact_tx_execution_gas == exact_tx_intrinsic_gas:
        # Special scenario where the execution of the initcode and
        # gas cost to deploy are zero
        post[created_contract_address] = Account(code=initcode.deploy_code)
    else:
        post[created_contract_address] = Account.NONEXISTENT

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[block],
        genesis_environment=env,
        name=f"{initcode.name}_tx_exact_intrinsic_gas",
    )

    """
    Test case 2: Test with exact intrinsic gas minus one, contract create fails
                 and tx is invalid.
    """
    tx = Transaction(
        nonce=0,
        to=None,
        data=initcode,
        gas_limit=exact_tx_intrinsic_gas - 1,
        gas_price=10,
        error="intrinsic gas too low",
    )
    block = Block(
        txs=[tx],
        exception="intrinsic gas too low",
    )
    post[created_contract_address] = Account.NONEXISTENT

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[block],
        genesis_environment=env,
        name=f"{initcode.name}_tx_under_intrinsic_gas",
    )

    """
    Test case 3: Test with exact execution gas minus one, contract create
                 fails, but tx is valid.
    """
    if exact_tx_execution_gas == exact_tx_intrinsic_gas:
        # Test case is virtually equal to previous
        pass
    else:
        tx = Transaction(
            nonce=0,
            to=None,
            data=initcode,
            gas_limit=exact_tx_execution_gas - 1,
            gas_price=10,
        )
        block = Block(txs=[tx])
        post[created_contract_address] = Account.NONEXISTENT

        yield BlockchainTest(
            pre=pre,
            post=post,
            blocks=[block],
            genesis_environment=env,
            name=f"{initcode.name}_tx_under_execution_gas",
        )

    """
    Test case 4: Test with exact execution gas, contract create succeeds.
    """
    tx = Transaction(
        nonce=0,
        to=None,
        data=initcode,
        gas_limit=exact_tx_execution_gas,
        gas_price=10,
    )
    block = Block(txs=[tx])
    post[created_contract_address] = Account(code=initcode.deploy_code)

    yield BlockchainTest(
        pre=pre,
        post=post,
        blocks=[block],
        genesis_environment=env,
        name=f"{initcode.name}_tx_exact_execution_gas",
    )


@test_from(fork="shanghai", eips=[3860])
def test_initcode_limit_contract_creating_tx_gas_usage(fork):
    """
    Test EIP-3860 Limit Initcode Gas Usage for a contract
    creating transaction, using different initcode lengths.
    """
    yield from generate_gas_cost_test_cases(
        initcode=INITCODE_ZEROS_MAX_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_gas_cost_test_cases(
        initcode=INITCODE_ONES_MAX_LIMIT,
        eip_3860_active=True,
    )

    # Test cases to verify the initcode word cost limits

    yield from generate_gas_cost_test_cases(
        initcode=EMPTY_INITCODE,
        eip_3860_active=True,
    )

    yield from generate_gas_cost_test_cases(
        initcode=SINGLE_BYTE_INITCODE,
        eip_3860_active=True,
    )

    yield from generate_gas_cost_test_cases(
        initcode=INITCODE_ZEROS_32_BYTES,
        eip_3860_active=True,
    )

    yield from generate_gas_cost_test_cases(
        initcode=INITCODE_ZEROS_33_BYTES,
        eip_3860_active=True,
    )

    yield from generate_gas_cost_test_cases(
        initcode=INITCODE_ZEROS_49120_BYTES,
        eip_3860_active=True,
    )

    yield from generate_gas_cost_test_cases(
        initcode=INITCODE_ZEROS_49121_BYTES,
        eip_3860_active=True,
    )


"""
Test cases using the CREATE opcode
"""


def generate_create_opcode_initcode_test_cases(
    opcode: str,
    initcode: Initcode,
    eip_3860_active: bool,
):
    """
    Generates a StateTest using the `CREATE`/`CREATE2` opcode based on the
    provided `initcode`, its executing cost, and the deployed code.
    """
    env = Environment()

    if opcode == "create":
        code = Yul(
            """
            {
                let contract_length := calldatasize()
                calldatacopy(0, 0, contract_length)
                let gas1 := gas()
                let res := create(0, 0, contract_length)
                let gas2 := gas()
                sstore(0, res)
                sstore(1, sub(gas1, gas2))
            }
            """
        )
        created_contract_address = compute_create_address(
            address=0x100,
            nonce=1,
        )

    elif opcode == "create2":
        code = Yul(
            """
            {
                let contract_length := calldatasize()
                calldatacopy(0, 0, contract_length)
                let gas1 := gas()
                let res := create2(0, 0, contract_length, 0xdeadbeef)
                let gas2 := gas()
                sstore(0, res)
                sstore(1, sub(gas1, gas2))
            }
            """
        )
        created_contract_address = compute_create2_address(
            address=0x100,
            salt=0,
            initcode=initcode.assemble(),
        )
    else:
        raise Exception("invalid opcode for generator")

    pre = {
        TestAddress: Account(balance=1000000000000000000000),
        to_address(0x100): Account(
            code=code,
            nonce=1,
        ),
    }

    post: Dict[Any, Any] = {}

    tx = Transaction(
        nonce=0,
        to=to_address(0x100),
        data=initcode,
        gas_limit=10000000,
        gas_price=10,
    )

    # Calculate the expected gas of the contract creation operation
    expected_gas_usage = (
        CREATE_CONTRACT_BASE_GAS + GAS_OPCODE_GAS + (3 * PUSH_DUP_OPCODE_GAS)
    )
    if opcode == "create2":
        # Extra PUSH operation
        expected_gas_usage += PUSH_DUP_OPCODE_GAS

    if len(initcode.assemble()) > MAX_INITCODE_SIZE and eip_3860_active:
        post[created_contract_address] = Account.NONEXISTENT
        post[to_address(0x100)] = Account(
            nonce=1,
            storage={
                0: 0,
                1: expected_gas_usage,
            },
        )
    else:
        # The initcode is only executed if the length check succeeds
        expected_gas_usage += initcode.execution_gas
        # The code is only deployed if the length check succeeds
        expected_gas_usage += initcode.deployment_gas

        if opcode == "create2":
            # CREATE2 hashing cost should only be deducted if the initcode
            # does not exceed the max length
            expected_gas_usage += calculate_create2_word_cost(
                len(initcode.assemble())
            )

        if eip_3860_active:
            # Initcode word cost is only deducted if the length check succeeds
            expected_gas_usage += calculate_initcode_word_cost(
                len(initcode.assemble())
            )

        post[created_contract_address] = Account(code=initcode.deploy_code)
        post[to_address(0x100)] = Account(
            nonce=2,
            storage={
                0: created_contract_address,
                1: expected_gas_usage,
            },
        )

    yield StateTest(
        env=env,
        pre=pre,
        post=post,
        txs=[tx],
        name=f"{opcode}_opcode_{initcode.name}",
    )


@test_from(fork="shanghai", eips=[3860])
def test_initcode_limit_create_opcode(fork):
    """
    Test creating a contract using the CREATE opcode with an initcode that is
    on/over the max allowed limit.
    """
    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ZEROS_MAX_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ONES_MAX_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ZEROS_OVER_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ONES_OVER_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=EMPTY_INITCODE,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=SINGLE_BYTE_INITCODE,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ZEROS_32_BYTES,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ZEROS_33_BYTES,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ZEROS_49120_BYTES,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create",
        initcode=INITCODE_ZEROS_49121_BYTES,
        eip_3860_active=True,
    )


@test_from(fork="shanghai", eips=[3860])
def test_initcode_limit_create2_opcode(fork):
    """
    Test creating a contract using the CREATE2 opcode with an initcode that is
    on/over the max allowed limit.
    """
    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ZEROS_MAX_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ONES_MAX_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ZEROS_OVER_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ONES_OVER_LIMIT,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=EMPTY_INITCODE,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=SINGLE_BYTE_INITCODE,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ZEROS_32_BYTES,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ZEROS_33_BYTES,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ZEROS_49120_BYTES,
        eip_3860_active=True,
    )

    yield from generate_create_opcode_initcode_test_cases(
        opcode="create2",
        initcode=INITCODE_ZEROS_49121_BYTES,
        eip_3860_active=True,
    )
