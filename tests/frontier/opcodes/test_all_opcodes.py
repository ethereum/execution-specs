"""
Call every possible opcode and test that the subcall is successful if the
opcode is supported by the fork and fails otherwise.
"""

from typing import Dict, Generator, Iterator

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
    ParameterSet,
    StateTestFiller,
    Transaction,
    UndefinedOpcodes,
    gas_test,
)
from execution_testing.forks import SpuriousDragon

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
        protected=fork >= SpuriousDragon,
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


def prepare_stack_constant_gas_oog(opcode: Opcode) -> Bytecode:
    """Prepare valid stack for opcode."""
    if opcode == Op.JUMPI:
        return Op.PUSH1(1) + Op.PUSH1(3) + Op.PC + Op.ADD
    if opcode == Op.JUMP:
        return Op.PUSH1(3) + Op.PC + Op.ADD
    if opcode == Op.BLOCKHASH:
        return Op.PUSH1(0x01)
    return Op.PUSH1(0x00) * opcode.min_stack_height


def constant_gas_opcodes(fork: Fork) -> Generator[ParameterSet, None, None]:
    """
    Return the list of opcodes that are constant gas and their warm gas cost
    per fork.
    """
    valid_opcodes = set(fork.valid_opcodes())
    for opcode in sorted(valid_opcodes):
        # SSTORE - untestable due to 2300 gas stipend rule
        if opcode == Op.SSTORE:
            continue
        if opcode.gas_cost(fork) == 0:
            # zero constant gas opcodes - untestable
            continue
        yield pytest.param(
            opcode,
            id=f"{opcode}",
        )


@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize_by_fork("opcode", constant_gas_opcodes)
def test_constant_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Opcode,
    fork: Fork,
) -> None:
    """Test that constant gas opcodes work as expected."""
    # Using Op.GAS as salt to guarantee no address collision on CREATE2.
    create2_salt = Op.GAS if opcode == Op.CREATE2 else Bytecode()
    setup_code = (
        Op.MLOAD(0)
        + Op.POP
        + prepare_stack_constant_gas_oog(opcode)
        + create2_salt
    )
    warm_opcode_metadata = {}
    if "address_warm" in opcode.metadata:
        warm_opcode_metadata["address_warm"] = True
    if "key_warm" in opcode.metadata:
        warm_opcode_metadata["key_warm"] = True
    if warm_opcode_metadata:
        warm_opcode = opcode(**warm_opcode_metadata)
    else:
        warm_opcode = opcode
    gas_test(
        fork=fork,
        state_test=state_test,
        pre=pre,
        setup_code=setup_code,
        subject_code=opcode,
        subject_code_warm=warm_opcode,
        tear_down_code=prepare_suffix(opcode),
    )
