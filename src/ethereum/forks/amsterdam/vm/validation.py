"""
Ethereum Virtual Machine (EVM) Code Validation (EIP-8337).

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Validation of `MAGIC` code at `CREATE` time, as specified by EIP-8337.
Code beginning with the `MAGIC` header is proven, once, when it is
created, to have fully static control flow and to never underflow the
data stack. Its execution begins immediately after the header.

Placeholders, to be settled by the EIP:

* `MAGIC` is `0xEF 0x79`; `MAGIC_VERSION` (`0x01`) names the validation
  rules of this fork. The header is `MAGIC + MAGIC_VERSION`.
* `VALIDATION_BYTE_COST` is 64 gas per byte of created code.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U8, Uint, ulen

from .exceptions import InvalidParameter
from .instructions import Ops
from .stack import decode_pair, decode_single

MAGIC = b"\xef\x79"
MAGIC_VERSION = b"\x01"
MAGIC_HEADER = MAGIC + MAGIC_VERSION
MAGIC_HEADER_LENGTH = ulen(MAGIC_HEADER)

STACK_LIMIT = 1024

# Placeholders for the *entry* of top-level code and for the destination
# requirement recorded by jumps (`LABEL`: JUMPDEST or CALLDEST) and by
# calls (`ENTRY`: CALLDEST only).
_OUTER = -1
_LABEL = 1
_ENTRY = 2


def is_magic_code(code: Bytes) -> bool:
    """
    Return whether `code` begins with the `MAGIC` bytes.

    Parameters
    ----------
    code :
        The code to inspect.

    Returns
    -------
    is_magic : `bool`
        `True` if `code` begins with `MAGIC`.

    """
    return bytes(code[: len(MAGIC)]) == MAGIC


def code_entry_point(code: Bytes) -> Uint:
    """
    Return the position at which execution of `code` begins: immediately
    after the header for `MAGIC` code, position zero otherwise.

    Parameters
    ----------
    code :
        The code to be executed.

    Returns
    -------
    entry_point : `Uint`
        The initial program counter.

    """
    if is_magic_code(code):
        return MAGIC_HEADER_LENGTH
    return Uint(0)


def validate_code(code: Bytes) -> bool:
    """
    Validate `MAGIC` code: the header must name this fork's validation
    rules, the body must not be empty, and the body must satisfy the
    five constraints of EIP-8337.

    Parameters
    ----------
    code :
        The complete created code, including the header.

    Returns
    -------
    valid : `bool`
        `True` if the code is valid.

    """
    if bytes(code[: len(MAGIC_HEADER)]) != MAGIC_HEADER:
        return False
    if ulen(code) <= MAGIC_HEADER_LENGTH:
        return False
    return validate(code, int(MAGIC_HEADER_LENGTH))


def _push_value(code: Bytes, pc: int) -> int:
    """
    Immediate value of the `PUSH` at `pc`, zero-padded past end of code.
    """
    n = code[pc] - Ops.PUSH0.value
    data = bytes(code[pc + 1 : pc + 1 + n]).ljust(n, b"\x00")
    return int.from_bytes(data, "big")


# (pops, pushes, is_terminator) for opcodes without a data portion and
# with fixed stack effects, for the instruction set of this fork.
# Opcodes absent from this table (and not handled by ranges in
# `_opcode_info`) are invalid. A terminator cannot fall through to the
# next instruction.
_TABLE: Dict[int, Tuple[int, int, bool]] = {
    Ops.STOP.value: (0, 0, True),
    **dict.fromkeys(
        (
            *range(0x01, 0x08),  # ADD..SMOD
            0x0A,  # EXP
            0x0B,  # SIGNEXTEND
            *range(0x10, 0x15),  # LT..EQ
            0x16,  # AND
            0x17,  # OR
            0x18,  # XOR
            *range(0x1A, 0x1E),  # BYTE..SAR
            0x20,  # KECCAK256
        ),
        (2, 1, False),
    ),
    0x08: (3, 1, False),  # ADDMOD
    0x09: (3, 1, False),  # MULMOD
    **dict.fromkeys(
        (
            0x15,  # ISZERO
            0x19,  # NOT
            0x1E,  # CLZ
            0x31,  # BALANCE
            0x35,  # CALLDATALOAD
            0x3B,  # EXTCODESIZE
            0x3F,  # EXTCODEHASH
            0x40,  # BLOCKHASH
            0x49,  # BLOBHASH
            0x51,  # MLOAD
            0x54,  # SLOAD
            0x5C,  # TLOAD
        ),
        (1, 1, False),
    ),
    **dict.fromkeys(
        (
            0x30,  # ADDRESS
            0x32,  # ORIGIN
            0x33,  # CALLER
            0x34,  # CALLVALUE
            0x36,  # CALLDATASIZE
            0x38,  # CODESIZE
            0x3A,  # GASPRICE
            0x3D,  # RETURNDATASIZE
            *range(0x41, 0x49),  # COINBASE..BASEFEE
            0x4A,  # BLOBBASEFEE
            0x4B,  # SLOTNUM
            0x58,  # PC
            0x59,  # MSIZE
            0x5A,  # GAS
        ),
        (0, 1, False),
    ),
    # CALLDATACOPY, CODECOPY, RETURNDATACOPY, MCOPY
    **dict.fromkeys((0x37, 0x39, 0x3E, 0x5E), (3, 0, False)),
    0x3C: (4, 0, False),  # EXTCODECOPY
    0x50: (1, 0, False),  # POP
    # MSTORE, MSTORE8, SSTORE, TSTORE
    **dict.fromkeys((0x52, 0x53, 0x55, 0x5D), (2, 0, False)),
    Ops.JUMP.value: (1, 0, True),
    Ops.JUMPI.value: (2, 0, False),
    Ops.JUMPDEST.value: (0, 0, False),
    Ops.CALLSUB.value: (1, 0, True),
    Ops.CALLDEST.value: (0, 0, False),
    Ops.RETURNSUB.value: (0, 0, True),
    0xF0: (3, 1, False),  # CREATE
    0xF5: (4, 1, False),  # CREATE2
    0xF1: (7, 1, False),  # CALL
    0xF2: (7, 1, False),  # CALLCODE
    0xF4: (6, 1, False),  # DELEGATECALL
    0xFA: (6, 1, False),  # STATICCALL
    0xF3: (2, 0, True),  # RETURN
    0xFD: (2, 0, True),  # REVERT
    0xFE: (0, 0, True),  # INVALID
    0xFF: (1, 0, True),  # SELFDESTRUCT
}


def _opcode_info(code: Bytes, pc: int) -> Tuple[int, int, int, bool]:
    """
    Return `(size, pops, pushes, is_terminator)` for the instruction at
    `pc`. A size of 0 marks an invalid instruction, including an EIP-8024
    instruction whose immediate is out of range.
    """
    op = code[pc]
    if Ops.PUSH0.value <= op <= Ops.PUSH32.value:
        return op - Ops.PUSH0.value + 1, 0, 1, False
    if 0x80 <= op <= 0x8F:  # DUP1..DUP16
        n = op - 0x7F
        return 1, n, n + 1, False
    if 0x90 <= op <= 0x9F:  # SWAP1..SWAP16
        n = op - 0x8F
        return 1, n + 1, n + 1, False
    if 0xA0 <= op <= 0xA4:  # LOG0..LOG4
        return 1, op - 0xA0 + 2, 0, False
    if op in (Ops.DUPN.value, Ops.SWAPN.value, Ops.EXCHANGE.value):
        if pc + 1 >= len(code):
            return 0, 0, 0, False
        immediate = U8(code[pc + 1])
        try:
            if op == Ops.DUPN.value:
                n = int(decode_single(immediate))
                return 2, n, n + 1, False
            if op == Ops.SWAPN.value:
                n = int(decode_single(immediate))
                return 2, n + 1, n + 1, False
            a, b = decode_pair(immediate)
            depth = max(int(a), int(b)) + 1
            return 2, depth, depth, False
        except InvalidParameter:
            return 0, 0, 0, False
    if op in _TABLE:
        pops, pushes, term = _TABLE[op]
        return 1, pops, pushes, term
    return 0, 0, 0, False


def _instruction_positions(code: Bytes, start: int) -> Set[int]:
    """
    The sequential scan from `start`: the positions that are instructions
    rather than immediate data, following the same rules as the JUMPDEST
    analysis (`PUSH` data and valid EIP-8024 immediates are skipped).
    """
    instructions: Set[int] = set()
    i = start
    n = len(code)
    while i < n:
        instructions.add(i)
        op = code[i]
        if Ops.PUSH1.value <= op <= Ops.PUSH32.value:
            i += op - Ops.PUSH0.value
        elif op in (Ops.DUPN.value, Ops.SWAPN.value):
            if not (i + 1 < n and 0x5B <= code[i + 1] <= 0x7F):
                i += 1
        elif op == Ops.EXCHANGE.value:
            if not (i + 1 < n and 0x52 <= code[i + 1] <= 0x7F):
                i += 1
        i += 1
    return instructions


def validate(code: Bytes, start: int, stack_limit: int = STACK_LIMIT) -> bool:
    """
    Return whether the code from `start` satisfies the five constraints
    of EIP-8337: valid opcodes, proven destinations, framed returns, no
    data-stack underflow, and one static stack offset per instruction.

    The traversal visits every reachable instruction once, following both
    arms of every `JUMPI`, and measures the data stack relative to the
    subroutine being traversed, so that each subroutine is checked once
    however many call sites invoke it.

    Parameters
    ----------
    code :
        The code, including any header before `start`.
    start :
        The position at which execution begins.
    stack_limit :
        The data-stack limit, bounding subroutine demands.

    Returns
    -------
    valid : `bool`
        `True` if the code is valid.

    """
    if len(code) <= start:
        return False

    instructions = _instruction_positions(code, start)

    # pc -> (offset, entry, framed) at first visit
    visited: Dict[int, Tuple[int, int, bool]] = {}
    # pc -> _LABEL or _ENTRY, set by jumps and calls
    required: Dict[int, int] = {}
    # entry -> its net stack effect, once known
    net_effect: Dict[int, int] = {}
    # entry -> its demand: the items it needs from its caller
    inputs: Dict[int, int] = defaultdict(int)
    # Two parent lists with different lifetimes. `parents` is permanent
    # and complete (every call and entrance) for propagating demands.
    # `enter_parents` holds only arrivals whose entry's net is still
    # unknown; each record is consumed once, when that net is first set.
    parents: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    enter_parents: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    # entry -> return points waiting on its net
    pending: Dict[int, List[Tuple[int, int, int, bool]]] = defaultdict(list)
    # (pc, offset, entry, framed, preceding push value)
    work_items: List[Tuple[int, int, int, bool, Optional[int]]] = [
        (start, 0, _OUTER, False, None)
    ]

    def resolve(entry: int, value: int) -> bool:
        """
        Record an entry's net: release the return points waiting on it,
        and settle the entries that jump or fall into it, whose nets
        follow from this one. Return `False` on a conflict.
        """
        settle = [(entry, value)]
        while settle:
            e, v = settle.pop()
            if e in net_effect:
                if net_effect[e] != v:
                    return False  # Constraint 5: one net per entry
                continue
            net_effect[e] = v
            for ret_pc, offset, caller, framed in pending.pop(e, []):
                work_items.append((ret_pc, offset + v, caller, framed, None))
            for parent, d in enter_parents[e]:
                settle.append((parent, d + v))
        return True

    while work_items:
        pc, offset, entry, framed, push = work_items.pop()
        if pc >= len(code):
            continue  # implicit STOP: a valid end
        if pc not in instructions:
            return False  # Constraints 2, 3: immediate data
        op = code[pc]
        size, pops, pushes, term = _opcode_info(code, pc)
        if size == 0:
            return False  # Constraint 1: not a valid instruction

        # A CALLDEST is visited at offset 0, as its own entry; arriving
        # any other way first records the link between the subroutines.
        if op == Ops.CALLDEST.value and (entry != pc or offset != 0):
            parents[pc].append((entry, offset))
            if pc in net_effect:  # settled: the arriving net follows
                if not resolve(entry, offset + net_effect[pc]):
                    return False
            else:  # each record is consumed exactly once
                enter_parents[pc].append((entry, offset))
            offset, entry = 0, pc

        if pc in visited:
            # Constraint 5: paths must agree.
            if visited[pc] != (offset, entry, framed):
                return False
            continue
        visited[pc] = (offset, entry, framed)

        # Constraints 2 and 3: a required destination type, if any.
        requirement = required.get(pc)
        if requirement == _LABEL and op not in (
            Ops.JUMPDEST.value,
            Ops.CALLDEST.value,
        ):
            return False
        if requirement == _ENTRY and op != Ops.CALLDEST.value:
            return False

        # Constraint 4: items used from below the subroutine's start.
        need = pops - offset
        if need > inputs[entry]:
            if need > stack_limit:
                return False
            inputs[entry] = need
        offset += pushes - pops
        nxt = pc + size

        if op == Ops.CALLSUB.value:
            if push is None:
                return False  # Constraint 3: PUSH before CALLSUB
            dest = push
            if dest >= len(code):
                return False
            if dest in visited and code[dest] != Ops.CALLDEST.value:
                return False
            required[dest] = _ENTRY  # a jump's LABEL upgrades to ENTRY
            parents[dest].append((entry, offset))
            work_items.append((dest, 0, dest, True, None))
            if dest in net_effect:
                # Return point: call-site offset plus the callee's net.
                work_items.append(
                    (nxt, offset + net_effect[dest], entry, framed, None)
                )
            else:
                pending[dest].append((nxt, offset, entry, framed))
        elif op == Ops.RETURNSUB.value:
            if not framed:
                return False  # no CALLSUB to return from
            if not resolve(entry, offset):
                return False
        elif op in (Ops.JUMP.value, Ops.JUMPI.value):
            if push is None:
                return False  # Constraint 2: PUSH before JUMP/JUMPI
            dest = push
            if dest >= len(code):
                return False
            if dest in visited and code[dest] not in (
                Ops.JUMPDEST.value,
                Ops.CALLDEST.value,
            ):
                return False
            required.setdefault(dest, _LABEL)
            work_items.append((dest, offset, entry, framed, None))
            if op == Ops.JUMPI.value:  # and the fall-through arm
                work_items.append((nxt, offset, entry, framed, None))
        elif not term:  # everything else falls through
            value: Optional[int] = None
            if Ops.PUSH0.value <= op <= Ops.PUSH32.value:
                value = _push_value(code, pc)
            work_items.append((nxt, offset, entry, framed, value))

    # The demand checking: a subroutine's demand for caller items, less
    # the depth already on the stack at the entrance, becomes its
    # parent's demand. Demands only rise and the limit caps them, so
    # this ends.
    queue: List[int] = [e for e in inputs if inputs[e]]
    queued: Set[int] = set(queue)
    head = 0
    while head < len(queue):
        e = queue[head]
        head += 1
        queued.discard(e)
        for parent, d in parents[e]:
            need = inputs[e] - d
            if need > inputs[parent]:
                if need > stack_limit:
                    return False
                inputs[parent] = need
                if parent not in queued:
                    queue.append(parent)
                    queued.add(parent)

    # Top-level code has no caller to take items from.
    return inputs[_OUTER] == 0
