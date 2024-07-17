"""
EOF extcall tests helpers
"""
import itertools

"""Storage addresses for common testing fields"""
_slot = itertools.count()
next(_slot)  # don't use slot 0
slot_code_worked = next(_slot)
slot_eof_target_call_status = next(_slot)
slot_legacy_target_call_status = next(_slot)
slot_eof_target_returndata = next(_slot)
slot_eof_target_returndatasize = next(_slot)
slot_legacy_target_returndatasize = next(_slot)
slot_delegate_code_worked = next(_slot)
slot_call_status = next(_slot)
slot_calldata_1 = next(_slot)
slot_calldata_2 = next(_slot)

slot_last_slot = next(_slot)

"""Storage value indicating an abort"""
value_exceptional_abort_canary = 0x1984

"""Storage values for common testing fields"""
value_code_worked = 0x2015

"""Memory and storage value for calldata"""
value_calldata_1 = 0xC1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1
value_calldata_2 = 0xC2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2
size_calldata = 32
