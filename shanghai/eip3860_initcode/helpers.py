"""
Helpers for the EIP-3860 initcode tests.
"""

from ethereum_test_tools import Initcode, ceiling_division, eip_2028_transaction_data_cost
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import Spec

KECCAK_WORD_COST = 6
INITCODE_RESULTING_DEPLOYED_CODE = Op.STOP

BASE_TRANSACTION_GAS = 21000
CREATE_CONTRACT_BASE_GAS = 32000


def calculate_initcode_word_cost(length: int) -> int:
    """
    Calculates the added word cost on contract creation added by the
    length of the initcode based on the formula:
    INITCODE_WORD_COST * ceil(len(initcode) / 32)
    """
    return Spec.INITCODE_WORD_COST * ceiling_division(length, 32)


def calculate_create2_word_cost(length: int) -> int:
    """
    Calculates the added word cost on contract creation added by the
    hashing of the initcode during create2 contract creation.
    """
    return KECCAK_WORD_COST * ceiling_division(length, 32)


def calculate_create_tx_intrinsic_cost(initcode: Initcode) -> int:
    """
    Calculates the intrinsic gas cost of a transaction that contains initcode
    and creates a contract
    """
    return (
        BASE_TRANSACTION_GAS  # G_transaction
        + CREATE_CONTRACT_BASE_GAS  # G_transaction_create
        + eip_2028_transaction_data_cost(initcode)  # Transaction calldata cost
        + calculate_initcode_word_cost(len(initcode))
    )


def calculate_create_tx_execution_cost(
    initcode: Initcode,
) -> int:
    """
    Calculates the total execution gas cost of a transaction that
    contains initcode and creates a contract
    """
    cost = calculate_create_tx_intrinsic_cost(initcode)
    cost += initcode.deployment_gas
    cost += initcode.execution_gas
    return cost


def get_initcode_name(val: Initcode):
    """
    Helper function that returns an Initcode object's name to generate test
    ids.
    """
    return val._name_


def get_create_id(opcode: Op):
    """
    Helper function that returns the opcode name for the test id.
    """
    return opcode._name_.lower()
