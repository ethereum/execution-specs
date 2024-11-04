"""
Helpers for the EIP-3860 initcode tests.
"""

from ethereum_test_tools import Initcode
from ethereum_test_tools.vm.opcode import Opcodes as Op

INITCODE_RESULTING_DEPLOYED_CODE = Op.STOP


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
