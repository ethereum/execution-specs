"""
Call every possible opcode and test that the subcall is successful if the
opcode is supported by the fork supports and fails otherwise.
"""

from typing import Dict, Iterator

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Fork,
    Op,
    Opcode,
    StateTestFiller,
    Transaction,
    UndefinedOpcodes,
)
from execution_testing.base_types.base_types import ZeroPaddedHexNumber
from execution_testing.forks import Byzantium

from tests.unscheduled.eip7692_eof_v1.eip3540_eof_v1.opcodes import (
    V1_EOF_ONLY_OPCODES,
)
from tests.unscheduled.eip7692_eof_v1.gas_test import gas_test

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def prepare_stack(opcode: Opcode) -> Bytecode:
    """Prepare valid stack for opcode."""
    if opcode == Op.CREATE:
        return (
            Op.MSTORE(0, 0x6001600155)
            + Op.PUSH1(5)
            + Op.PUSH1(27)
            + Op.PUSH1(5)
        )
    if opcode == Op.CREATE2:
        return (
            Op.MSTORE(0, 0x6001600155)
            + Op.PUSH1(1)
            + Op.PUSH1(5)
            + Op.PUSH1(27)
            + Op.PUSH1(5)
        )
    if opcode == Op.JUMPI:
        return Op.PUSH1(1) + Op.PUSH1(5)
    if opcode == Op.JUMP:
        return Op.PUSH1(3)
    if opcode == Op.RETURNDATACOPY:
        return Op.PUSH1(0) * 3
    return Op.PUSH1(0x01) * 32


def prepare_suffix(opcode: Opcode) -> Bytecode:
    """Prepare after opcode instructions."""
    if opcode == Op.JUMPI or opcode == Op.JUMP:
        return Op.JUMPDEST
    return Op.STOP


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stBadOpcode/badOpcodesFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stBugs/evmBytecodeFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/748"],
)
@pytest.mark.valid_from("Frontier")
def test_all_opcodes(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Test each possible opcode on the fork with a single contract that calls
    each opcode in succession. Check that each subcall passes if the opcode is
    supported and fails otherwise.
    """
    code_worked = 1000

    code_contract: Dict[Opcode, Address] = {}
    for opcode in sorted(set(Op) | set(UndefinedOpcodes)):
        code_contract[opcode] = pre.deploy_contract(
            balance=10,
            code=prepare_stack(opcode) + opcode + prepare_suffix(opcode),
            storage={},
        )

    # EVM code to make the call and store the result
    contract_address = pre.deploy_contract(
        code=sum(
            Op.SSTORE(
                Op.PUSH1(opcode.int()),
                # Limit gas to limit the gas consumed by the exceptional aborts
                # in each subcall that uses an undefined opcode.
                Op.CALL(35_000, opcode_address, 0, 0, 0, 0, 0),
            )
            for opcode, opcode_address in code_contract.items()
        )
        + Op.SSTORE(code_worked, 1)
        + Op.STOP,
    )

    post = {
        contract_address: Account(
            storage={
                **{
                    opcode.int(): 1 if opcode != Op.REVERT else 0
                    for opcode in fork.valid_opcodes()
                },
                code_worked: 1,
            }
        ),
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=9_000_000,
        to=contract_address,
        data=b"",
        value=0,
        protected=False,
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_cover_revert(state_test: StateTestFiller, pre: Alloc) -> None:
    """Cover state revert from original tests for the coverage script."""
    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        data=Op.SSTORE(1, 1) + Op.REVERT(0, 0),
        to=None,
        value=0,
        protected=False,
    )

    state_test(env=Environment(), pre=pre, post={}, tx=tx)


def fork_opcodes_increasing_stack(
    fork: Fork,
) -> Iterator[Op]:
    """
    Yields opcodes which are valid for `fork` and increase the operand stack.
    """
    for opcode in fork.valid_opcodes():
        if opcode.pushed_stack_items > opcode.popped_stack_items:
            yield opcode


@pytest.mark.parametrize_by_fork("opcode", fork_opcodes_increasing_stack)
@pytest.mark.parametrize("fails", [True, False])
def test_stack_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    fails: bool,
    env: Environment,
) -> None:
    """Test that opcodes which leave new items on the stack can overflow."""
    pre_stack_items = fork.max_stack_height()
    if not fails:
        pre_stack_items -= (
            opcode.pushed_stack_items - opcode.popped_stack_items
        )
    slot_code_worked = 1
    value_code_failed = 0xDEADBEEF
    value_code_worked = 1

    contract = pre.deploy_contract(
        code=Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.PUSH1(0) * pre_stack_items
        + opcode
        + Op.STOP,
        storage={slot_code_worked: value_code_failed},
    )

    tx = Transaction(
        gas_limit=100_000,
        to=contract,
        sender=pre.fund_eoa(),
        protected=fork >= Byzantium,
    )
    expected_storage = {
        slot_code_worked: value_code_failed if fails else value_code_worked
    }

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={contract: Account(storage=expected_storage)},
    )


opcode_to_gas = {
    Op.ADD: 3,
    Op.MUL: 5,
    Op.SUB: 3,
    Op.DIV: 5,
    Op.SDIV: 5,
    Op.MOD: 5,
    Op.SMOD: 5,
    Op.ADDMOD: 8,
    Op.MULMOD: 8,
    Op.EXP: 10,
    Op.SIGNEXTEND: 5,
    Op.LT: 3,
    Op.GT: 3,
    Op.SLT: 3,
    Op.SGT: 3,
    Op.EQ: 3,
    Op.ISZERO: 3,
    Op.AND: 3,
    Op.OR: 3,
    Op.XOR: 3,
    Op.NOT: 3,
    Op.BYTE: 3,
    Op.SHL: 3,
    Op.SHR: 3,
    Op.SAR: 3,
    Op.CLZ: 5,
    Op.SHA3: 30,
    Op.ADDRESS: 2,
    Op.BALANCE: 100,
    Op.ORIGIN: 2,
    Op.CALLER: 2,
    Op.CALLVALUE: 2,
    Op.CALLDATALOAD: 3,
    Op.CALLDATASIZE: 2,
    Op.CALLDATACOPY: 3,
    Op.CODESIZE: 2,
    Op.CODECOPY: 3,
    Op.GASPRICE: 2,
    Op.EXTCODESIZE: 100,
    Op.EXTCODECOPY: 100,
    Op.RETURNDATASIZE: 2,
    Op.RETURNDATACOPY: 3,
    Op.EXTCODEHASH: 100,
    Op.BLOCKHASH: 20,
    Op.COINBASE: 2,
    Op.TIMESTAMP: 2,
    Op.NUMBER: 2,
    Op.PREVRANDAO: 2,
    Op.GASLIMIT: 2,
    Op.CHAINID: 2,
    Op.SELFBALANCE: 5,
    Op.BASEFEE: 2,
    Op.BLOBHASH: 3,
    Op.BLOBBASEFEE: 2,
    Op.POP: 2,
    Op.MLOAD: 3,
    Op.MSTORE: 3,
    Op.MSTORE8: 3,
    Op.SLOAD: 100,
    Op.JUMP: 8,
    Op.JUMPI: 10,
    Op.PC: 2,
    Op.MSIZE: 2,
    Op.GAS: 2,
    Op.JUMPDEST: 1,
    Op.TLOAD: 100,
    Op.TSTORE: 100,
    Op.MCOPY: 3,
    Op.PUSH0: 2,
    Op.LOG0: 375,
    Op.LOG1: 2 * 375,
    Op.LOG2: 3 * 375,
    Op.LOG3: 4 * 375,
    Op.LOG4: 5 * 375,
    Op.CREATE: 32000,
    Op.CALL: 100,
    Op.CALLCODE: 100,
    Op.DELEGATECALL: 100,
    Op.CREATE2: 32000,
    Op.STATICCALL: 100,
    Op.SELFDESTRUCT: 5000,
}

# PUSHx, SWAPx, DUPx have uniform gas costs
for opcode in set(Op):
    if 0x60 <= opcode.int() <= 0x9F:
        opcode_to_gas[opcode] = 3

constant_gas_opcodes = (
    set(Op)
    -
    # zero constant gas opcodes - untestable
    {Op.STOP, Op.RETURN, Op.REVERT, Op.INVALID}
    -
    # TODO: EOF opcodes. Remove once EOF is removed
    set(V1_EOF_ONLY_OPCODES)
    -
    # SSTORE - untestable due to 2300 gas stipend rule
    {Op.SSTORE}
)


def prepare_stack_constant_gas_oog(opcode: Opcode) -> Bytecode:
    """Prepare valid stack for opcode."""
    if opcode == Op.JUMPI:
        return Op.PUSH1(1) + Op.PUSH1(3) + Op.PC + Op.ADD
    if opcode == Op.JUMP:
        return Op.PUSH1(3) + Op.PC + Op.ADD
    if opcode == Op.BLOCKHASH:
        return Op.PUSH1(0x01)
    return Op.PUSH1(0x00) * 32


# NOTE: Gas costs varying across forks not being supported yet would make this
# test very complex.
@pytest.mark.valid_at("Osaka")
@pytest.mark.parametrize("opcode", sorted(constant_gas_opcodes))
def test_constant_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    fork: Fork,
    env: Environment,
) -> None:
    """Test that constant gas opcodes work as expected."""
    warm_gas = opcode_to_gas[opcode]
    cold_gas = warm_gas + (
        2500
        if opcode
        in [
            Op.BALANCE,
            Op.EXTCODESIZE,
            Op.EXTCODECOPY,
            Op.EXTCODEHASH,
            Op.CALL,
            Op.CALLCODE,
            Op.DELEGATECALL,
            Op.STATICCALL,
        ]
        else 2600
        if opcode == Op.SELFDESTRUCT
        else 2000
        if opcode == Op.SLOAD
        else 0
    )

    if cap := fork.transaction_gas_limit_cap():
        env.gas_limit = ZeroPaddedHexNumber(cap)

    # Using `TLOAD` / `TSTORE` to work around warm/cold gas differences. We
    # need a counter to pick a distinct salt on each `CREATE2` and avoid
    # running into address conflicts.
    code_increment_counter = (
        Op.TLOAD(1234) + Op.DUP1 + Op.TSTORE(1234, Op.PUSH1(1) + Op.ADD)
    )
    setup_code = (
        Op.MLOAD(0)
        + Op.POP
        + prepare_stack_constant_gas_oog(opcode)
        + (code_increment_counter if opcode == Op.CREATE2 else Bytecode())
    )
    gas_test(
        fork,
        state_test,
        env,
        pre,
        setup_code=setup_code,
        subject_code=opcode,
        tear_down_code=prepare_suffix(opcode),
        cold_gas=cold_gas,
        warm_gas=warm_gas,
        eof=False,
    )
