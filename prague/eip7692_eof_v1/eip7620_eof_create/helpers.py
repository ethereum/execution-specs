"""
A collection of contracts used in 7620 EOF tests
"""
import itertools

from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section

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
slot_max_depth = next(_slot)
slot_call_or_create = next(_slot)

slot_last_slot = next(_slot)

value_code_worked = 0x2015
value_canary_should_not_change = 0x2019
value_canary_to_be_overwritten = 0x2009
value_create_failed = 0
value_legacy_call_result_failed = 0
value_eof_call_result_success = 0
value_eof_call_result_reverted = 1
value_eof_call_result_failed = 2

smallest_runtime_subcontainer = Container(
    name="Runtime Subcontainer",
    sections=[
        Section.Code(code=Op.STOP),
    ],
)

smallest_initcode_subcontainer = Container(
    name="Initcode Subcontainer",
    sections=[
        Section.Code(code=Op.RETURNCONTRACT[0](0, 0)),
        Section.Container(container=smallest_runtime_subcontainer),
    ],
)

aborting_container = Container.Code(Op.INVALID)
