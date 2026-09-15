"""Reference spec for [EIP-8337: Validated EVM Code](https://eips.ethereum.org/EIPS/eip-8337)."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8337 = ReferenceSpec(
    git_path="EIPS/eip-8337.md",
    version="8a372acd9e931999a260c41d13866f131801c548",
)


class Spec:
    """Constants and parameters from EIP-8337, with placeholders."""

    # Placeholder MAGIC bytes and the version byte naming this fork's
    # validation rules; the EIP fixes only that MAGIC begins with 0xEF.
    MAGIC: bytes = b"\xef\x79"
    MAGIC_VERSION: bytes = b"\x01"
    MAGIC_HEADER: bytes = MAGIC + MAGIC_VERSION
    HEADER_LENGTH: int = 3

    # Gas charged at CREATE per byte of MAGIC code, before validation runs.
    VALIDATION_BYTE_COST: int = 64


def call_chain(n: int) -> str:
    """
    Main calls sub 0; sub i calls sub i+1; the last sub returns.

    Return-stack depth reaches `n`. From the EIP's test assets.
    """
    code = bytes.fromhex("6004B000")  # PUSH1 4, CALLSUB, STOP
    for i in range(n - 1):
        nxt = 4 + 5 * (i + 1)  # each sub is 5 bytes
        code += bytes([0xB1, 0x60, nxt, 0xB0, 0xB2])
    code += bytes([0xB1, 0xB2])  # last sub: CALLDEST, RETURNSUB
    return code.hex().upper()


# The validation vectors of the EIP, as (name, bytecode hex, valid). The
# three overflow vectors are valid here: overflow is not validated.
VECTORS: List[Tuple[str, str, bool]] = [
    # The runtime test cases of EIP-7979
    ("simple_routine", "6004B000B1B2", True),
    ("two_levels_of_subroutines", "6004B000B16009B0B2B1B2", True),
    ("destination_outside_code", "60FFB000B1B2", False),
    ("bare_returnsub", "B2", False),
    ("subroutine_at_end_of_code", "600556B1B25B6003B0", True),
    # Constraint 1: opcodes
    ("lone_stop", "00", True),
    ("undefined_opcode", "21", False),
    ("invalid_is_valid", "FE", True),
    ("undefined_opcode_at_return_point", "6004B021B1B2", False),
    # Constraints 2 and 3: destinations
    ("jump_into_push_immediate", "600156", False),
    ("jump_to_visited_non_jumpdest", "5F5F01600256", False),
    ("jumpdest_byte_in_push_data", "600456605B00", False),
    ("jumpdest_byte_in_live_push_data", "36600857615B00005B600556", False),
    ("calldest_byte_in_push_data", "6004B060B100", False),
    ("jumpdest_in_unreachable_code", "600456005B00", True),
    ("jump_not_preceded_by_push", "365B56", False),
    ("callsub_to_jumpdest", "6004B0005B", False),
    # Constraint 4: underflow and the return stack
    ("add_on_empty_stack", "01", False),
    ("pop_on_empty_stack", "50", False),
    (
        "subroutine_consumes_caller_argument",
        "6002600BB06003600BB000B18002B2",
        True,
    ),
    ("subroutine_underflows_caller", "6004B000B15050B2", False),
    ("fall_into_subroutine_then_returnsub", "B1B2", False),
    # Constraint 5: offsets and net effects
    ("jumpi_arms_disagree_at_join", "366005575F5B00", False),
    ("jumpi_diamond_consistent", "366006575F005B5F00", True),
    ("two_returnsubs_disagree", "6004B000B136600A57B25B5FB2", False),
    ("two_returnsubs_agree", "6004B000B136600A57B25B5F50B2", True),
    ("stack_neutral_loop", "5B600056", True),
    # Reuse and multiple entry points
    ("called_at_two_depths", "6002600BB06003600BB000B18002B2", True),
    ("fall_through_second_entry", "6008B05F600AB000B15FB150B2", True),
    # Recursion
    ("recursion_no_base_case", "6004B000B16004B0B2", True),
    ("recursion_eats_caller_stack", "6004B000B1506004B0", False),
    # Jumps to a CALLDEST (call elimination)
    ("jump_to_calldest", "6004B000B15F600956B150B2", True),
    ("conditional_jump_to_calldest", "6004B000B136600A57B2B1B2", True),
    ("jump_to_calldest_nets_disagree", "6004B000B15F36600B57B2B150B2", False),
    ("unframed_jump_to_called_subroutine", "6006B0600656B1B2", False),
    # Overflow is not validated
    ("seventeen_pushes", "5F" * 17 + "00", True),
    ("sixteen_pushes", "5F" * 16 + "00", True),
    (
        "stack_growth_amplified_by_two_calls",
        "6007B06007B000B1" + "5F" * 9 + "B2",
        True,
    ),
    ("stack_growth_one_call", "6004B000B1" + "5F" * 9 + "B2", True),
    ("call_chain_depth_17", call_chain(17), True),
    ("call_chain_depth_16", call_chain(16), True),
    ("growing_recursion", "6004B000B15F6004B0", True),
]


def relocate(body_hex: str, shift: int = Spec.HEADER_LENGTH) -> bytes:
    """
    Shift every PUSH1 immediate of a vector by `shift`, so that destinations
    written for code starting at position 0 remain correct behind the
    header. Immediates that would exceed 0xFF are clamped, which keeps
    out-of-range destinations out of range. Non-destination PUSH1 values
    are shifted too; validation never interprets them.
    """
    code = bytearray(bytes.fromhex(body_hex))
    i = 0
    while i < len(code):
        op = code[i]
        if op == 0x60:  # PUSH1
            code[i + 1] = min(0xFF, code[i + 1] + shift)
            i += 2
        elif 0x60 < op <= 0x7F:  # PUSH2..PUSH32
            i += op - 0x5F + 1
        elif op in (0xE6, 0xE7, 0xE8):  # DUPN, SWAPN, EXCHANGE
            i += 2
        else:
            i += 1
    return bytes(code)
