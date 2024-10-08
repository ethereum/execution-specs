"""
Execution of CALLF, RETF opcodes within EOF V1 containers tests
"""

from typing import List

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_CODE_SECTIONS, MAX_RETURN_STACK_HEIGHT
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4750.md"
REFERENCE_SPEC_VERSION = "90f716078d0b08ce508a1e57803f885cc2f2e15e"

# List all containers used within execution tests, since they will need to be
# valid EOF V1 containers too

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

contract_call_within_deep_nested_callf = Container(
    name="contract_call_within_deep_nested_callf",
    sections=[
        Section.Code(
            code=Op.CALLF[1] + Op.SSTORE(0, 1) + Op.STOP,
        )
    ]
    + [
        # All sections call next section and on return, store a 1
        # to their call stack height key
        Section.Code(
            code=(Op.CALLF[i] + Op.SSTORE(i - 1, 1) + Op.RETF),
            code_inputs=0,
            code_outputs=0,
        )
        for i in range(2, MAX_CODE_SECTIONS)
    ]
    + [
        # Last section makes external contract call
        Section.Code(
            code=(
                Op.PUSH0
                + Op.PUSH0
                + Op.PUSH0
                + Op.PUSH2(0x200)
                + Op.EXTCALL
                + Op.ISZERO
                + Op.PUSH2(MAX_CODE_SECTIONS - 1)
                + Op.SSTORE
                + Op.RETF
            ),
            code_inputs=0,
            code_outputs=0,
        )
    ],
)

recursive_contract_call_within_deep_nested_callf = Container(
    name="recursive_contract_call_within_deep_nested_callf",
    sections=[
        # All sections call next section and on return, store a 1
        # to their call stack height key
        Section.Code(
            code=Op.CALLF[i + 1] + Op.SSTORE(i, 1) + Op.STOP,
        )
        for i in range(MAX_CODE_SECTIONS - 1)
    ]
    + [
        # Last section makes external contract call
        Section.Code(
            code=(
                Op.PUSH0
                + Op.PUSH0
                + Op.PUSH0
                + Op.PUSH0
                + Op.PUSH0
                + Op.PUSH2(0x200)
                + Op.GAS
                + Op.CALL
                + Op.PUSH2(MAX_CODE_SECTIONS - 1)
                + Op.SSTORE
                + Op.RETF
            ),
            code_inputs=0,
            code_outputs=0,
        )
    ],
)

CALL_SUCCEED_CONTRACTS: List[Container] = [
    Container(
        name="function_finishes_contract_execution",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
            ),
            Section.Code(
                code=(Op.RETF),
                code_inputs=0,
                code_outputs=0,
            ),
        ],
    ),
    Container(
        name="max_recursive_callf",
        sections=[
            Section.Code(
                code=(Op.PUSH1(1) + Op.CALLF[1] + Op.STOP),
            ),
            Section.Code(
                code=(
                    Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.RETF)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.CALLF[1]
                    + Op.RETF
                ),
                code_inputs=1,
                code_outputs=0,
                max_stack_height=3,
            ),
        ],
    ),
    Container(
        name="max_recursive_callf_sstore",
        sections=[
            Section.Code(
                code=Op.SSTORE(0, 1) + Op.CALLF[1] + Op.STOP,
                max_stack_height=2,
            ),
            Section.Code(
                code=(
                    Op.PUSH0
                    + Op.SLOAD
                    + Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.STOP)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.PUSH0
                    + Op.SSTORE
                    + Op.CALLF[1]
                    + Op.RETF
                ),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=3,
            ),
        ],
    ),
    Container(
        name="max_recursive_callf_memory",
        sections=[
            Section.Code(
                code=(Op.PUSH1(1) + Op.PUSH0 + Op.MSTORE + Op.CALLF[1] + Op.STOP),
            ),
            Section.Code(
                code=(
                    Op.PUSH0
                    + Op.MLOAD
                    + Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.RETF)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.PUSH0
                    + Op.MSTORE
                    + Op.CALLF[1]
                    + Op.RETF
                ),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=3,
            ),
        ],
    ),
]
"""
List of all EOF V1 Containers that simply need to succeed on execution.
"""

CALL_FAIL_CONTRACTS: List[Container] = [
    Container(
        name="invalid_opcode",
        sections=[
            Section.Code(
                code=(Op.INVALID),
            ),
        ],
    ),
    Container(
        name="overflow_recursive_callf",
        sections=[
            Section.Code(
                code=(Op.PUSH1(1) + Op.CALLF[1] + Op.STOP),
            ),
            Section.Code(
                code=(
                    Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT + 1)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.RETF)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.CALLF[1]
                    + Op.RETF
                ),
                code_inputs=1,
                code_outputs=0,
                max_stack_height=3,
            ),
        ],
    ),
    Container(
        name="overflow_recursive_callf_sstore",
        sections=[
            Section.Code(
                code=Op.SSTORE(0, 1) + Op.CALLF[1] + Op.STOP,
                max_stack_height=2,
            ),
            Section.Code(
                code=(
                    Op.PUSH0
                    + Op.SLOAD
                    + Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT + 1)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.RETF)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.PUSH0
                    + Op.SSTORE
                    + Op.CALLF[1]
                    + Op.RETF
                ),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=3,
            ),
        ],
    ),
    Container(
        name="overflow_recursive_callf_memory",
        sections=[
            Section.Code(
                code=Op.MSTORE(0, 1) + Op.CALLF[1] + Op.STOP,
                max_stack_height=2,
            ),
            Section.Code(
                code=(
                    Op.PUSH0
                    + Op.MLOAD
                    + Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT + 1)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.RETF)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.PUSH0
                    + Op.MSTORE
                    + Op.CALLF[1]
                    + Op.RETF
                ),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=3,
            ),
        ],
    ),
]
"""
List of all EOF V1 Containers that simply need to fail (exceptional halt) on
execution.
These contracts have a valid EOF V1 container format but fail when executed.
"""

VALID: List[Container] = CALL_SUCCEED_CONTRACTS + CALL_FAIL_CONTRACTS
"""
List of all EOF V1 Containers used during execution tests.
"""


@pytest.mark.parametrize("container", CALL_SUCCEED_CONTRACTS, ids=lambda x: x.name)
def test_eof_functions_contract_call_succeed(
    state_test: StateTestFiller,
    pre: Alloc,
    container: Container,
):
    """
    Test simple contracts that are simply expected to succeed on call.
    """
    env = Environment()

    sender = pre.fund_eoa()
    container_address = pre.deploy_contract(container)
    caller_contract = Op.SSTORE(0, Op.CALL(Op.GAS, container_address, 0, 0, 0, 0, 0)) + Op.STOP()
    caller_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        to=caller_address,
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
        sender=sender,
    )

    post = {caller_address: Account(storage={0: 1})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize("container", CALL_FAIL_CONTRACTS, ids=lambda x: x.name)
def test_eof_functions_contract_call_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    container: Container,
):
    """
    Test simple contracts that are simply expected to fail on call.
    """
    env = Environment()

    sender = pre.fund_eoa()
    container_address = pre.deploy_contract(container)
    caller_contract = Op.SSTORE(Op.CALL(Op.GAS, container_address, 0, 0, 0, 0, 0), 1) + Op.STOP()
    caller_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        to=caller_address,
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
        sender=sender,
    )

    post = {caller_address: Account(storage={0: 1})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


def test_eof_functions_contract_call_within_deep_nested(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test performing a call within a nested callf and verify correct behavior of
    return stack in calling contract.

    TODO: This test belongs in EIP-7069 test folder, not code validation.
    """
    env = Environment()

    nested_callee_address = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP())
    contract_call_within_deep_nested_callf = Container(
        name="contract_call_within_deep_nested_callf",
        sections=[
            Section.Code(
                code=Op.CALLF[1] + Op.SSTORE(0, 1) + Op.STOP,
            )
        ]
        + [
            # All sections call next section and on return, store a 1
            # to their call stack height key
            Section.Code(
                code=(Op.CALLF[i] + Op.SSTORE(i - 1, 1) + Op.RETF),
                code_outputs=0,
            )
            for i in range(2, MAX_CODE_SECTIONS)
        ]
        + [
            # Last section makes external contract call
            Section.Code(
                code=(
                    Op.EXTCALL(nested_callee_address, 0, 0, 0)
                    + Op.ISZERO
                    + Op.PUSH2(MAX_CODE_SECTIONS - 1)
                    + Op.SSTORE
                    + Op.RETF
                ),
                code_outputs=0,
            )
        ],
    )
    callee_address = pre.deploy_contract(contract_call_within_deep_nested_callf)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=callee_address,
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
        sender=sender,
    )
    post = {
        callee_address: Account(storage={i: 1 for i in range(MAX_CODE_SECTIONS)}),
        nested_callee_address: Account(
            storage={
                0: 1,
            }
        ),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
