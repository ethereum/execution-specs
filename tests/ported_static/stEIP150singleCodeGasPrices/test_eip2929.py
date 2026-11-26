"""
Test the gas of state access operations run back to back.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml

@manually-enhanced: Do not overwrite. Each parametrization runs three
operations back to back in the same contract and stores each one's
measured gas in slots 0, 1 and 2. Whether an operation pays the cold or
warm access cost depends on what the preceding operations already
warmed (the `target` account and storage slot 0x100), so the expected
value of each slot comes from the framework gas calculation of the
operation with the matching warm/cold metadata. The `FAR_*` operations
call `target_balance_reader` (which does `BALANCE(target)`) or
`slot_reader` (which does `SLOAD(0x100)`), so their cost includes the
inner access.
"""

from enum import Enum, auto
from typing import Generator

import pytest
from _pytest.mark.structures import ParameterSet
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ACCESSED_SLOT = 0x100
ACCESSED_SLOT_ORIGINAL_VALUE = 24743
ACCESSED_SLOT_NEW_VALUE = 5
CALL_GAS = 0x1000


class Operation(Enum):
    """Measured state access operation."""

    NOP = auto()
    SLOAD = auto()
    SSTORE = auto()
    BALANCE = auto()
    EXTCODESIZE = auto()
    EXTCODECOPY = auto()
    EXTCODEHASH = auto()
    CALL = auto()
    CALLCODE = auto()
    DELEGATECALL = auto()
    STATICCALL = auto()
    FAR_CALL = auto()
    FAR_CALLCODE = auto()
    FAR_DELEGATECALL = auto()


# Opcodes each operation executes, directly or inside the far-call callee.
OPERATION_OPCODES: dict[Operation, tuple[Opcode, ...]] = {
    Operation.NOP: (),
    Operation.SLOAD: (Op.SLOAD,),
    Operation.SSTORE: (Op.SSTORE,),
    Operation.BALANCE: (Op.BALANCE,),
    Operation.EXTCODESIZE: (Op.EXTCODESIZE,),
    Operation.EXTCODECOPY: (Op.EXTCODECOPY,),
    Operation.EXTCODEHASH: (Op.EXTCODEHASH,),
    Operation.CALL: (Op.CALL,),
    Operation.CALLCODE: (Op.CALLCODE,),
    Operation.DELEGATECALL: (Op.DELEGATECALL,),
    Operation.STATICCALL: (Op.STATICCALL,),
    Operation.FAR_CALL: (Op.CALL, Op.BALANCE),
    Operation.FAR_CALLCODE: (Op.CALLCODE, Op.SLOAD),
    Operation.FAR_DELEGATECALL: (Op.DELEGATECALL, Op.SLOAD),
}

OPERATION_TRIPLES: list[tuple[Operation, Operation, Operation]] = [
    (Operation.NOP, Operation.NOP, Operation.NOP),
    (Operation.SLOAD, Operation.SLOAD, Operation.SLOAD),
    (Operation.SSTORE, Operation.SSTORE, Operation.SSTORE),
    (Operation.BALANCE, Operation.BALANCE, Operation.BALANCE),
    (
        Operation.EXTCODESIZE,
        Operation.EXTCODESIZE,
        Operation.EXTCODESIZE,
    ),
    (
        Operation.EXTCODECOPY,
        Operation.EXTCODECOPY,
        Operation.EXTCODECOPY,
    ),
    (
        Operation.EXTCODEHASH,
        Operation.EXTCODEHASH,
        Operation.EXTCODEHASH,
    ),
    (Operation.CALL, Operation.CALL, Operation.CALL),
    (Operation.CALLCODE, Operation.CALLCODE, Operation.CALLCODE),
    (
        Operation.DELEGATECALL,
        Operation.DELEGATECALL,
        Operation.DELEGATECALL,
    ),
    (Operation.STATICCALL, Operation.STATICCALL, Operation.STATICCALL),
    (Operation.FAR_CALL, Operation.FAR_CALL, Operation.FAR_CALL),
    (
        Operation.FAR_CALLCODE,
        Operation.FAR_CALLCODE,
        Operation.FAR_CALLCODE,
    ),
    (
        Operation.FAR_DELEGATECALL,
        Operation.FAR_DELEGATECALL,
        Operation.FAR_DELEGATECALL,
    ),
    (Operation.SLOAD, Operation.SSTORE, Operation.SLOAD),
    (Operation.SLOAD, Operation.FAR_CALLCODE, Operation.FAR_DELEGATECALL),
    (Operation.SLOAD, Operation.SSTORE, Operation.FAR_DELEGATECALL),
    (Operation.FAR_CALLCODE, Operation.SLOAD, Operation.FAR_DELEGATECALL),
    (Operation.FAR_DELEGATECALL, Operation.SLOAD, Operation.SSTORE),
    (Operation.BALANCE, Operation.EXTCODESIZE, Operation.EXTCODEHASH),
    (Operation.BALANCE, Operation.EXTCODEHASH, Operation.EXTCODESIZE),
    (Operation.EXTCODESIZE, Operation.BALANCE, Operation.EXTCODEHASH),
    (Operation.EXTCODESIZE, Operation.EXTCODEHASH, Operation.BALANCE),
    (Operation.EXTCODEHASH, Operation.EXTCODESIZE, Operation.BALANCE),
    (Operation.EXTCODEHASH, Operation.BALANCE, Operation.EXTCODESIZE),
    (Operation.CALL, Operation.CALLCODE, Operation.CALL),
    (Operation.CALLCODE, Operation.CALLCODE, Operation.CALL),
    (
        Operation.DELEGATECALL,
        Operation.STATICCALL,
        Operation.DELEGATECALL,
    ),
    (Operation.DELEGATECALL, Operation.STATICCALL, Operation.STATICCALL),
    (Operation.BALANCE, Operation.CALL, Operation.CALLCODE),
    (Operation.EXTCODESIZE, Operation.CALL, Operation.CALLCODE),
    (Operation.EXTCODEHASH, Operation.CALL, Operation.CALLCODE),
    (Operation.BALANCE, Operation.CALLCODE, Operation.CALL),
    (Operation.EXTCODESIZE, Operation.CALLCODE, Operation.CALL),
    (Operation.EXTCODEHASH, Operation.CALLCODE, Operation.CALL),
    (Operation.BALANCE, Operation.EXTCODESIZE, Operation.FAR_CALL),
    (Operation.BALANCE, Operation.FAR_CALL, Operation.EXTCODEHASH),
    (Operation.FAR_CALL, Operation.EXTCODEHASH, Operation.BALANCE),
]


def operation_triples_by_fork(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield the operation triples whose opcodes all exist on `fork`."""
    valid_opcodes = set(fork.valid_opcodes())
    for operations in OPERATION_TRIPLES:
        if all(
            opcode in valid_opcodes
            for operation in operations
            for opcode in OPERATION_OPCODES[operation]
        ):
            yield pytest.param(
                operations,
                id="-".join(
                    operation.name.lower() for operation in operations
                ),
            )


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize_by_fork("operations", operation_triples_by_fork)
def test_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    operations: tuple[Operation, Operation, Operation],
) -> None:
    """Store the gas of three back-to-back state access operations."""
    sender = pre.fund_eoa()

    target = pre.deploy_contract(code=Op.STOP)

    def target_balance_reader_code(target_warm: bool) -> Bytecode:
        return Op.BALANCE(address=target, address_warm=target_warm) + Op.STOP

    def slot_reader_code(slot_warm: bool) -> Bytecode:
        return Op.SLOAD(key=ACCESSED_SLOT, key_warm=slot_warm) + Op.STOP

    target_balance_reader = pre.deploy_contract(
        code=target_balance_reader_code(target_warm=False)
    )
    slot_reader = pre.deploy_contract(code=slot_reader_code(slot_warm=False))

    # Warm both far-call callees, so only the accesses they perform
    # inside depend on the preceding operations.
    gas_meter_code = Op.POP(Op.BALANCE(address=target_balance_reader)) + (
        Op.POP(Op.BALANCE(address=slot_reader))
    )
    target_warm = False
    slot_warm = False
    slot_value = ACCESSED_SLOT_ORIGINAL_VALUE
    expected_storage = {}
    for result_slot, operation in enumerate(operations):
        code: Bytecode
        match operation:
            case Operation.NOP:
                code = Bytecode()
            case Operation.SLOAD:
                code = Op.SLOAD(key=ACCESSED_SLOT, key_warm=slot_warm)
            case Operation.SSTORE:
                code = Op.SSTORE(
                    key=ACCESSED_SLOT,
                    value=ACCESSED_SLOT_NEW_VALUE,
                    key_warm=slot_warm,
                    original_value=ACCESSED_SLOT_ORIGINAL_VALUE,
                    current_value=slot_value,
                    new_value=ACCESSED_SLOT_NEW_VALUE,
                )
                slot_value = ACCESSED_SLOT_NEW_VALUE
            case Operation.BALANCE:
                code = Op.BALANCE(address=target, address_warm=target_warm)
            case Operation.EXTCODESIZE:
                code = Op.EXTCODESIZE(address=target, address_warm=target_warm)
            case Operation.EXTCODECOPY:
                code = Op.EXTCODECOPY(
                    address=target,
                    dest_offset=0,
                    offset=0,
                    size=0,
                    address_warm=target_warm,
                )
            case Operation.EXTCODEHASH:
                code = Op.EXTCODEHASH(address=target, address_warm=target_warm)
            case Operation.CALL:
                code = Op.CALL(
                    gas=CALL_GAS, address=target, address_warm=target_warm
                )
            case Operation.CALLCODE:
                code = Op.CALLCODE(
                    gas=CALL_GAS, address=target, address_warm=target_warm
                )
            case Operation.DELEGATECALL:
                code = Op.DELEGATECALL(
                    gas=CALL_GAS, address=target, address_warm=target_warm
                )
            case Operation.STATICCALL:
                code = Op.STATICCALL(
                    gas=CALL_GAS, address=target, address_warm=target_warm
                )
            case Operation.FAR_CALL:
                code = Op.CALL(
                    gas=CALL_GAS,
                    address=target_balance_reader,
                    address_warm=True,
                    inner_call_cost=target_balance_reader_code(
                        target_warm
                    ).gas_cost(fork),
                )
            case Operation.FAR_CALLCODE:
                code = Op.CALLCODE(
                    gas=CALL_GAS,
                    address=slot_reader,
                    address_warm=True,
                    inner_call_cost=slot_reader_code(slot_warm).gas_cost(fork),
                )
            case Operation.FAR_DELEGATECALL:
                code = Op.DELEGATECALL(
                    gas=CALL_GAS,
                    address=slot_reader,
                    address_warm=True,
                    inner_call_cost=slot_reader_code(slot_warm).gas_cost(fork),
                )
        if operation in (
            Operation.SLOAD,
            Operation.SSTORE,
            Operation.FAR_CALLCODE,
            Operation.FAR_DELEGATECALL,
        ):
            slot_warm = True
        elif operation not in (Operation.NOP,):
            # Every other operation accesses `target`, directly or (for
            # FAR_CALL) from inside `target_balance_reader`.
            target_warm = True

        gas_meter_code += CodeGasMeasure(
            code=code,
            extra_stack_items=code.pushed_stack_items
            - code.popped_stack_items,
            sstore_key=result_slot,
        )
        expected_storage[result_slot] = code.gas_cost(fork)

    gas_meter = pre.deploy_contract(
        code=gas_meter_code + Op.SSTORE(key=ACCESSED_SLOT, value=0) + Op.STOP,
        storage={ACCESSED_SLOT: ACCESSED_SLOT_ORIGINAL_VALUE},
    )

    tx = Transaction(
        sender=sender,
        to=gas_meter,
        protected=fork.supports_protected_txs(),
    )

    post = {gas_meter: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)
