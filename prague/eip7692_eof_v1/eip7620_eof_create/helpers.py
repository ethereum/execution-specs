"""
A collection of contracts used in 7620 EOF tests
"""
import itertools

from ethereum_test_tools import Address
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION

"""Storage addresses for common testing fields"""
_slot = itertools.count()
next(_slot)  # don't use slot 0
slot_code_worked = next(_slot)
slot_code_should_fail = next(_slot)
slot_create_address = next(_slot)
slot_calldata = next(_slot)
slot_call_result = next(_slot)
slot_returndata = next(_slot)
slot_returndata_size = next(_slot)

slot_last_slot = next(_slot)

value_code_worked = 0x2015
value_canary_should_not_change = 0x2019
value_canary_to_be_overwritten = 0x2009
value_create_failed = 0
value_call_result_success = 0

smallest_runtime_subcontainer = Container(
    name="Runtime Subcontainer",
    sections=[
        Section.Code(
            code=Op.STOP, code_inputs=0, code_outputs=NON_RETURNING_SECTION, max_stack_height=0
        )
    ],
)

smallest_initcode_subcontainer = Container(
    name="Initcode Subcontainer",
    sections=[
        Section.Code(
            code=Op.RETURNCONTRACT[0](0, 0),
            code_inputs=0,
            code_outputs=NON_RETURNING_SECTION,
            max_stack_height=2,
        ),
        Section.Container(container=smallest_runtime_subcontainer),
    ],
)


def fixed_address(index: int) -> Address:
    """
    Returns an determinstic address for testing
    Parameters
    ----------
    index - how foar off of the initial to create the address

    Returns
    -------
    An address, unique per index and human friendly for testing

    """
    return Address(0x7E570000 + index)


default_address = fixed_address(0)


def simple_transaction(
    target: Address = default_address, payload: bytes = b"", gas_limit: int = 10_000_000
):
    """
    Creates a simple transaction
    Parameters
    ----------
    target the target address, defaults to 0x100
    payload the payload, defauls to empty

    Returns
    -------
    a transaction instance that can be passed into state_tests
    """
    return Transaction(
        nonce=1, to=target, gas_limit=gas_limit, gas_price=10, protected=False, data=payload
    )
