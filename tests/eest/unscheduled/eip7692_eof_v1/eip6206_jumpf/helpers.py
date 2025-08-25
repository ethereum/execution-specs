"""EOF JumpF tests helpers."""

import itertools

"""Storage addresses for common testing fields"""
_slot = itertools.count()
next(_slot)  # don't use slot 0
slot_code_worked = next(_slot)
slot_last_slot = next(_slot)
slot_stack_canary = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015
value_canary_written = 0xDEADB12D
