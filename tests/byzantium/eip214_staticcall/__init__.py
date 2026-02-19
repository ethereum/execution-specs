"""
Test cases for EIP-214: STATICCALL opcode.

EIP-214 introduced the STATICCALL opcode which creates a read-only call
context. Any state-modifying operations (including CALL with non-zero
value) within a STATICCALL context will cause the call to fail.
"""
