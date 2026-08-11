"""
Verify the exact gas each opcode needs to succeed: given precisely that
much, the frame running it completes; given one gas less, it does not.

Ported from:
state_tests/stBadOpcode/measureGasFiller.yml
state_tests/stBadOpcode/opcodeDiffGasFiller.yml
Written by Ori Pomerantz (qbzzt1@gmail.com).

@manually-enhanced: Do not overwrite. The filler bisected the gas operand
of a CALL inside EVM bytecode to find the gas it consumed in runtime.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Op,
    Opcodes,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

FLAG_SLOT = 0x0
# Seeded so a frame that never ran stays distinct from one that ran and
# reported a failed call.
SENTINEL = 0x60A7

# The ported operands: an init code window, a call's argument/return
# window, a memory offset well past anything already allocated, and a
# hash over a large span.
INIT_CODE_SIZE = 0x200
CALL_WINDOW = 0x100
MEMORY_OFFSET = 0xB000
HASH_SIZE = 0xBEEF

OPCODES = [
    Op.CREATE,
    Op.CREATE2,
    Op.CALL,
    Op.CALLCODE,
    Op.DELEGATECALL,
    Op.STATICCALL,
    Op.MLOAD,
    Op.MSTORE,
    Op.MSTORE8,
    Op.SHA3,
    Op.EXTCODECOPY,
]


@pytest.fixture
def probe_code(opcode: Opcodes, pre: Alloc) -> Bytecode:
    """
    Return a frame that performs `opcode` once and stops.

    Each opcode carries the metadata describing the access it makes, so
    `gas_cost(fork)` is the exact budget the frame needs.
    """
    body: Bytecode
    if opcode in (Op.CREATE, Op.CREATE2):
        # CREATE2's salt defaults to zero: one probe per case, so there is
        # nothing for it to collide with.
        body = Op.POP(
            opcode(
                value=0x0,
                offset=0x0,
                size=INIT_CODE_SIZE,
                new_memory_size=INIT_CODE_SIZE,
                init_code_size=INIT_CODE_SIZE,
            )
        )
    elif opcode in (Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL):
        # The value-passing forms default to transferring nothing, which
        # keeps all four variants at the same base cost.
        callee = pre.deploy_contract(code=Op.STOP)
        body = Op.POP(
            opcode(
                gas=Op.GAS,
                address=callee,
                args_offset=0x0,
                args_size=CALL_WINDOW,
                ret_offset=0x0,
                ret_size=CALL_WINDOW,
                address_warm=False,
                new_memory_size=CALL_WINDOW,
            )
        )
    elif opcode == Op.MLOAD:
        body = Op.POP(
            Op.MLOAD(
                offset=MEMORY_OFFSET, new_memory_size=MEMORY_OFFSET + 0x20
            )
        )
    elif opcode in (Op.MSTORE, Op.MSTORE8):
        written = 0x20 if opcode == Op.MSTORE else 0x1
        body = opcode(
            offset=MEMORY_OFFSET,
            value=0xFF,
            new_memory_size=MEMORY_OFFSET + written,
        )
    elif opcode == Op.SHA3:
        body = Op.POP(
            Op.SHA3(
                offset=0x0,
                size=HASH_SIZE,
                new_memory_size=HASH_SIZE,
                data_size=HASH_SIZE,
            )
        )
    elif opcode == Op.EXTCODECOPY:
        # The size operand warms the account, so the copy that follows is
        # a warm access.
        callee = pre.deploy_contract(code=Op.STOP)
        body = Op.EXTCODECOPY(
            address=callee,
            dest_offset=0x0,
            offset=0x0,
            size=0x1,
            address_warm=False,
            data_size=0x1,
            new_memory_size=0x1,
        )
    elif opcode == Op.EXTCODESIZE:
        callee = pre.deploy_contract(code=Op.STOP)
        body = Op.EXTCODESIZE(address=callee, address_warm=False)
    else:
        raise ValueError(f"Opcode {opcode} not yet supported by test")
    return body + Op.STOP


@pytest.mark.ported_from(
    [
        "state_tests/stBadOpcode/measureGasFiller.yml",
        "state_tests/stBadOpcode/opcodeDiffGasFiller.yml",
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "sufficient", [True, False], ids=["sufficient", "insufficient"]
)
@pytest.mark.parametrize("opcode", OPCODES)
def test_measure_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    probe_code: Bytecode,
    sufficient: bool,
) -> None:
    """One gas decides whether the opcode's frame completes."""
    threshold = probe_code.gas_cost(fork)
    probe = pre.deploy_contract(code=probe_code)

    # Handing the probe exactly its own cost is what makes the boundary
    # exact; the cold access to it is charged here, not there.
    entry = pre.deploy_contract(
        code=Op.SSTORE(
            FLAG_SLOT,
            Op.CALL(
                gas=threshold if sufficient else threshold - 1,
                address=probe,
            ),
        )
        + Op.STOP,
        storage={FLAG_SLOT: SENTINEL},
    )

    # Without an empty reservoir the creations draw their state gas from
    # it rather than from the probe, and one gas short still succeeds.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        state_gas_reservoir=0,
    )

    post = {entry: Account(storage={FLAG_SLOT: 1 if sufficient else 0})}

    state_test(pre=pre, post=post, tx=tx)
