"""
EOF RJump tests helpers
"""
import itertools
from enum import Enum

"""Storage addresses for common testing fields"""
_slot = itertools.count()
next(_slot)  # don't use slot 0
slot_code_worked = next(_slot)
slot_conditional_result = next(_slot)
slot_last_slot = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015
value_calldata_true = 10
value_calldata_false = 11


class JumpDirection(Enum):
    """
    Enum for the direction of the jump
    """

    FORWARD = 1
    BACKWARD = -1
