"""
Test the gas of memory expansion by MLOAD, MSTORE and MSTORE8.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostMemoryFiller.yml

@manually-enhanced: Do not overwrite. Each parametrization accesses
memory at one `offset` and measures the gas in `gas_meter`, storing it
in slot 0. The first-access operations (MLOAD, MSTORE, MSTORE8) expand
the empty memory of `gas_meter`; the repeated-access operations first
expand memory with an MSTORE at the same offset, so the measured access
pays no expansion; CALL_MSTORE_MLOAD measures a CALL into
`memory_user`, which expands its own fresh memory with an MSTORE and
reads it back with an MLOAD. The expected values come from the
framework gas calculation, with the memory sizes as metadata.
"""

from enum import Enum, auto

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

STORED_WORD = 0x60A7
STORED_BYTE = 0xFF
MEMORY_USER_CALL_GAS = 0x10000

OFFSETS = [
    0x0,
    0x10,
    0x20,
    0x40,
    0x60,
    0x80,
    0x100,
    0x120,
    0x140,
    0x160,
    0x180,
    0x200,
    0x300,
    0x400,
    0x800,
    0x1000,
    0x2000,
    0x3000,
    0x4000,
    0x8000,
]


class MemoryAccess(Enum):
    """Measured memory access."""

    MLOAD = auto()
    MSTORE = auto()
    MSTORE8 = auto()
    REPEATED_MLOAD = auto()
    REPEATED_MSTORE = auto()
    CALL_MSTORE_MLOAD = auto()


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/gasCostMemoryFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize("offset", OFFSETS, ids=lambda offset: hex(offset))
@pytest.mark.parametrize(
    "memory_access",
    list(MemoryAccess),
    ids=lambda memory_access: memory_access.name.lower(),
)
def test_gas_cost_memory(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    memory_access: MemoryAccess,
    offset: int,
) -> None:
    """Store the gas of a memory access at `offset`."""
    sender = pre.fund_eoa()

    word_memory_size = offset + 32
    setup = Bytecode()
    measured: Bytecode
    match memory_access:
        case MemoryAccess.MLOAD:
            measured = Op.MLOAD(
                offset=offset, new_memory_size=word_memory_size
            )
        case MemoryAccess.MSTORE:
            measured = Op.MSTORE(
                offset=offset,
                value=STORED_WORD,
                new_memory_size=word_memory_size,
            )
        case MemoryAccess.MSTORE8:
            measured = Op.MSTORE8(
                offset=offset, value=STORED_BYTE, new_memory_size=offset + 1
            )
        case MemoryAccess.REPEATED_MLOAD:
            setup = Op.MSTORE(offset=offset, value=STORED_WORD)
            measured = Op.MLOAD(
                offset=offset,
                old_memory_size=word_memory_size,
                new_memory_size=word_memory_size,
            )
        case MemoryAccess.REPEATED_MSTORE:
            setup = Op.MSTORE(offset=offset, value=STORED_WORD)
            measured = Op.MSTORE(
                offset=offset,
                value=STORED_WORD,
                old_memory_size=word_memory_size,
                new_memory_size=word_memory_size,
            )
        case MemoryAccess.CALL_MSTORE_MLOAD:
            memory_user_code = (
                Op.MSTORE(
                    offset=offset,
                    value=STORED_WORD,
                    new_memory_size=word_memory_size,
                )
                + Op.MLOAD(
                    offset=offset,
                    old_memory_size=word_memory_size,
                    new_memory_size=word_memory_size,
                )
                + Op.STOP
            )
            memory_user = pre.deploy_contract(code=memory_user_code)
            measured = Op.CALL(
                gas=MEMORY_USER_CALL_GAS,
                address=memory_user,
                address_warm=False,
                inner_call_cost=memory_user_code.gas_cost(fork),
            )

    gas_meter = pre.deploy_contract(
        code=setup
        + CodeGasMeasure(
            code=measured,
            extra_stack_items=measured.pushed_stack_items
            - measured.popped_stack_items,
            sstore_key=0,
        )
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=gas_meter,
        protected=fork.supports_protected_txs(),
    )

    post = {gas_meter: Account(storage={0: measured.gas_cost(fork)})}

    state_test(pre=pre, post=post, tx=tx)
