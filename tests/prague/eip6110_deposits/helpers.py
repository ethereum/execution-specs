"""Helpers for the EIP-6110 deposit tests."""

from typing import Dict, Tuple

from execution_testing import Bytecode, Fork, Op, Opcode

# The deposit contract is a compiled predeploy, so the gas it charges cannot
# be read off its source. The tables below are the opcodes it executes for one
# deposit, counted from an EVM trace, so that the fork's own gas schedule
# prices them and the estimate follows repricings. Regenerate them by filling
# any single deposit test with `--traces --evm-dump-dir <dir>` and counting
# the `opName` of the depth-2 steps of one call frame.

_DEPOSIT_CALL_OPCODES: Dict[Opcode, int] = {
    Op.PUSH1: 270,
    Op.ADD: 177,
    Op.SWAP1: 175,
    Op.POP: 164,
    Op.DUP2: 142,
    Op.PUSH2: 123,
    Op.DUP1: 117,
    Op.SWAP2: 110,
    Op.JUMPDEST: 104,
    Op.MLOAD: 104,
    Op.DUP3: 97,
    Op.DUP4: 91,
    Op.JUMPI: 86,
    Op.MSTORE: 66,
    Op.SWAP3: 61,
    Op.LT: 54,
    Op.ISZERO: 46,
    Op.AND: 43,
    Op.SUB: 40,
    Op.DUP5: 37,
    Op.BYTE: 32,
    Op.NOT: 28,
    Op.JUMP: 27,
    Op.PUSH32: 27,
    Op.SWAP4: 26,
    Op.SHL: 19,
    Op.GT: 18,
    Op.DUP6: 17,
    Op.MSTORE8: 16,
    Op.PUSH31: 16,
    Op.SWAP5: 13,
    Op.OR: 11,
    Op.DUP10: 10,
    Op.CALLDATALOAD: 8,
    Op.DUP7: 8,
    Op.EQ: 7,
    Op.GAS: 7,
    Op.RETURNDATASIZE: 7,
    Op.DUP13: 6,
    Op.PUSH5: 6,
    Op.DUP11: 5,
    Op.DUP9: 5,
    Op.PUSH4: 5,
    Op.CALLDATASIZE: 4,
    Op.PUSH8: 4,
    Op.CALLVALUE: 3,
    Op.DUP15: 3,
    Op.MUL: 3,
    Op.DUP16: 2,
    Op.DUP8: 2,
    Op.SWAP6: 2,
    Op.DIV: 1,
    Op.DUP12: 1,
    Op.DUP14: 1,
    Op.MOD: 1,
    Op.SHR: 1,
    Op.STOP: 1,
    Op.SWAP14: 1,
}
"""
Fixed-cost opcodes a deposit call executes, excluding the Merkle branch loop
(`_BRANCH_UPDATE_OPCODES`) and the opcodes whose cost depends on their
operands, which are added with the metadata seen in the trace.
"""

_BRANCH_UPDATE_OPCODES: Dict[Opcode, int] = {
    Op.PUSH1: 26,
    Op.ADD: 14,
    Op.PUSH2: 12,
    Op.POP: 12,
    Op.MLOAD: 11,
    Op.DUP2: 10,
    Op.SWAP2: 10,
    Op.DUP1: 9,
    Op.JUMPDEST: 9,
    Op.JUMPI: 8,
    Op.SWAP1: 8,
    Op.DUP3: 8,
    Op.DUP4: 8,
    Op.MSTORE: 6,
    Op.LT: 6,
    Op.SWAP3: 6,
    Op.ISZERO: 5,
    Op.SUB: 4,
    Op.JUMP: 3,
    Op.AND: 3,
    Op.PUSH32: 3,
    Op.DUP5: 2,
    Op.SWAP4: 2,
    Op.EQ: 1,
    Op.OR: 1,
    Op.DIV: 1,
    Op.NOT: 1,
    Op.DUP6: 1,
    Op.SWAP5: 1,
    Op.GAS: 1,
    Op.RETURNDATASIZE: 1,
}
"""
Fixed-cost opcodes added by one iteration of the deposit contract's Merkle
branch loop, which hashes a sibling node into the accumulated deposit root.
"""

_DEPOSIT_CALL_CALLDATACOPY_SIZES: Tuple[int, ...] = (
    8,
    8,
    48,
    32,
    96,
    48,
    64,
    32,
    32,
)
"""Bytes copied by each `CALLDATACOPY` of a deposit call."""

_DEPOSIT_CALL_EXP_COUNT = 10
"""`EXP` operations of a deposit call, all with a single-byte exponent."""

_DEPOSIT_CALL_SLOAD_COUNT = 3
"""Storage slots a deposit call reads, all warm after the first deposit."""

_DEPOSIT_CALL_SSTORE_COUNT = 2
"""Storage slots a deposit call writes: the deposit count and a branch node."""

_DEPOSIT_CALL_SHA256_COUNT = 7
"""`sha256` calls a deposit call makes outside the Merkle branch loop."""

_SHA256_INPUT_WORDS = 2
"""Words of input of every `sha256` call the deposit contract makes."""

_DEPOSIT_LOG_DATA_SIZE = 576
"""Bytes of log data the deposit event carries."""

_DEPOSIT_CALL_MEMORY_SIZE = 1024
"""Bytes of memory a deposit call expands to."""

_BRANCH_UPDATE_MEMORY_SIZE = 1120
"""Bytes of memory a deposit call expands to for each branch loop iteration."""

_DIRTIED_SSTORE = Op.SSTORE.with_metadata(
    key_warm=True, original_value=1, current_value=2, new_value=3
)
"""
An `SSTORE` to a slot already written earlier in the same transaction, which
is what every deposit but the first of a transaction pays.
"""


def _counted(opcode_counts: Dict[Opcode, int]) -> Bytecode:
    """Return the opcodes of a count table concatenated into one bytecode."""
    code = Bytecode()
    for opcode, count in opcode_counts.items():
        code += opcode * count
    return code


def _sha256_call(fork: Fork) -> Bytecode:
    """
    Return the `STATICCALL` the deposit contract makes to the `sha256`
    precompile, charged with the precompile's own gas.
    """
    gas_costs = fork.gas_costs()
    return Op.STATICCALL.with_metadata(
        address_warm=True,
        inner_call_cost=(
            gas_costs.PRECOMPILE_SHA256_BASE
            + gas_costs.PRECOMPILE_SHA256_PER_WORD * _SHA256_INPUT_WORDS
        ),
    )


def deposit_contract_execution_gas(fork: Fork, *, branch_updates: int) -> int:
    """
    Return the gas the deposit contract consumes to process one deposit.

    `branch_updates` is the number of Merkle branch loop iterations to
    account for; the loop runs once per trailing zero bit of the new deposit
    count.
    """
    deposit_call = (
        _counted(_DEPOSIT_CALL_OPCODES)
        + Op.EXP.with_metadata(exponent=0xFF) * _DEPOSIT_CALL_EXP_COUNT
        + Op.SLOAD.with_metadata(key_warm=True) * _DEPOSIT_CALL_SLOAD_COUNT
        + _DIRTIED_SSTORE * _DEPOSIT_CALL_SSTORE_COUNT
        + Op.LOG1.with_metadata(data_size=_DEPOSIT_LOG_DATA_SIZE)
        + _sha256_call(fork) * _DEPOSIT_CALL_SHA256_COUNT
        + Op.MSTORE.with_metadata(new_memory_size=_DEPOSIT_CALL_MEMORY_SIZE)
    )
    for size in _DEPOSIT_CALL_CALLDATACOPY_SIZES:
        deposit_call += Op.CALLDATACOPY.with_metadata(data_size=size)
    branch_update = (
        _counted(_BRANCH_UPDATE_OPCODES)
        + Op.EXP.with_metadata(exponent=0xFF)
        + Op.SLOAD.with_metadata(key_warm=True)
        + _sha256_call(fork)
        + Op.MSTORE.with_metadata(
            old_memory_size=_DEPOSIT_CALL_MEMORY_SIZE,
            new_memory_size=_BRANCH_UPDATE_MEMORY_SIZE,
        )
    )
    return (deposit_call + branch_update * branch_updates).gas_cost(fork)
