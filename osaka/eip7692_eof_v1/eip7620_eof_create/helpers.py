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
slot_counter = next(_slot)

slot_last_slot = next(_slot)

value_code_worked = 0x2015
value_canary_should_not_change = 0x2019
value_canary_to_be_overwritten = 0x2009

smallest_runtime_subcontainer = Container.Code(code=Op.STOP, name="Runtime Subcontainer")

smallest_initcode_subcontainer = Container(
    name="Initcode Subcontainer",
    sections=[
        Section.Code(code=Op.RETURNCONTRACT[0](0, 0)),
        Section.Container(container=smallest_runtime_subcontainer),
    ],
)
smallest_initcode_subcontainer_gas = 2 * 3

aborting_container = Container.Code(Op.INVALID, name="Aborting Container")
reverting_container = Container.Code(Op.REVERT(0, 0), name="Reverting Container")
expensively_reverting_container = Container.Code(
    Op.SHA3(0, 32) + Op.REVERT(0, 0), name="Expensively Reverting Container"
)
expensively_reverting_container_gas = 2 * 3 + 30 + 3 + 6 + 2 * 3
big_runtime_subcontainer = Container.Code(Op.NOOP * 10000 + Op.STOP, name="Big Subcontainer")

bigger_initcode_subcontainer_gas = 3 + 4 + 2 * 3
bigger_initcode_subcontainer = Container(
    name="Bigger Initcode Subcontainer",
    sections=[
        Section.Code(
            code=Op.RJUMPI[len(Op.RETURNCONTRACT[0](0, 0))](1)
            + Op.RETURNCONTRACT[0](0, 0)
            + Op.RETURNCONTRACT[1](0, 0)
        ),
        Section.Container(container=smallest_runtime_subcontainer),
        Section.Container(container=smallest_runtime_subcontainer),
    ],
)

data_runtime_container = smallest_runtime_subcontainer.copy()
data_runtime_container.sections.append(Section.Data("0x00"))

data_initcode_subcontainer = Container(
    name="Data Initcode Subcontainer",
    sections=[
        Section.Code(code=Op.RETURNCONTRACT[0](0, 0)),
        Section.Container(container=data_runtime_container),
    ],
)

data_appending_initcode_subcontainer = Container(
    name="Data Appending Initcode Subcontainer",
    sections=[
        Section.Code(code=Op.RETURNCONTRACT[0](0, 1)),
        Section.Container(container=smallest_runtime_subcontainer),
    ],
)
data_appending_initcode_subcontainer_gas = 2 * 3 + 3
