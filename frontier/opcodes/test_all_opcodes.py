"""
Call every possible opcode and test that the subcall is successful
if the opcode is supported by the fork supports and fails otherwise.
"""

from typing import Dict

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcode
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_tools.vm.opcode import UndefinedOpcodes

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def prepare_stack(opcode: Opcode) -> Bytecode:
    """Prepare valid stack for opcode"""
    if opcode == Op.CREATE:
        return Op.MSTORE(0, 0x6001600155) + Op.PUSH1(5) + Op.PUSH1(27) + Op.PUSH1(5)
    if opcode == Op.CREATE2:
        return Op.MSTORE(0, 0x6001600155) + Op.PUSH1(1) + Op.PUSH1(5) + Op.PUSH1(27) + Op.PUSH1(5)
    if opcode == Op.JUMPI:
        return Op.PUSH1(1) + Op.PUSH1(5)
    if opcode == Op.JUMP:
        return Op.PUSH1(3)
    return Op.PUSH1(0x01) * 32


def prepare_suffix(opcode: Opcode) -> Bytecode:
    """Prepare after opcode instructions"""
    if opcode == Op.JUMPI or opcode == Op.JUMP:
        return Op.JUMPDEST
    return Op.STOP


@pytest.mark.valid_from("Frontier")
def test_all_opcodes(state_test: StateTestFiller, pre: Alloc, fork: Fork):
    """
    Test each possible opcode on the fork with a single contract that
    calls each opcode in succession. Check that each subcall passes
    if the opcode is supported and fails otherwise.
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
                Op.CALL(1_000_000, opcode_address, 0, 0, 0, 0, 0),
            )
            for opcode, opcode_address in code_contract.items()
        )
        + Op.SSTORE(code_worked, 1)
        + Op.STOP,
    )

    post = {
        contract_address: Account(
            storage={**{opcode.int(): 1 for opcode in fork.valid_opcodes()}, code_worked: 1}
        ),
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=500_000_000,
        to=contract_address,
        data=b"",
        value=0,
        protected=False,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_cover_revert(state_test: StateTestFiller, pre: Alloc):
    """Cover state revert from original tests for the coverage script"""
    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        data=Op.SSTORE(1, 1) + Op.REVERT,
        to=b"",
        value=0,
        protected=False,
    )

    state_test(env=Environment(), pre=pre, post={}, tx=tx)
