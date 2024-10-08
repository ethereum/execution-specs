"""
A collection of contracts used in 7698 EOF tests
"""
import itertools

from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container

"""Storage addresses for common testing fields"""
_slot = itertools.count()
next(_slot)  # don't use slot 0
slot_call_result = next(_slot)

slot_last_slot = next(_slot)

smallest_runtime_subcontainer = Container.Code(code=Op.STOP, name="Runtime Subcontainer")
