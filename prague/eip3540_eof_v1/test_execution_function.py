"""
Execution of CALLF, RETF opcodes within EOF V1 containers tests
"""

from typing import List

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_CODE_SECTIONS, MAX_RETURN_STACK_HEIGHT
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import EOF_FORK_NAME

# List all containers used within execution tests, since they will need to be
# valid EOF V1 containers too

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

contract_call_within_deep_nested_callf = Container(
    name="contract_call_within_deep_nested_callf",
    sections=[
        # All sections call next section and on return, store a 1
        # to their call stack height key
        Section.Code(
            code=(Op.CALLF[i + 1] + Op.PUSH1(1) + Op.PUSH2(i) + Op.SSTORE + Op.RETF),
            code_inputs=0,
            code_outputs=0,
            max_stack_height=2,
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
            max_stack_height=7,
        )
    ],
)

recursive_contract_call_within_deep_nested_callf = Container(
    name="recursive_contract_call_within_deep_nested_callf",
    sections=[
        # All sections call next section and on return, store a 1
        # to their call stack height key
        Section.Code(
            code=(Op.CALLF[i + 1] + Op.PUSH1(1) + Op.PUSH2(i) + Op.SSTORE + Op.RETF),
            code_inputs=0,
            code_outputs=0,
            max_stack_height=2,
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
            max_stack_height=7,
        )
    ],
)

CALL_SUCCEED_CONTRACTS: List[Container] = [
    Container(
        name="retf_top_frame",
        sections=[
            Section.Code(
                code=(Op.RETF),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            ),
        ],
    ),
    Container(
        name="function_finishes_contract_execution",
        sections=[
            Section.Code(
                code=(Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            ),
            Section.Code(
                code=(Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            ),
        ],
    ),
    Container(
        name="max_recursive_callf",
        sections=[
            Section.Code(
                code=(Op.PUSH1(1) + Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=1,
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
                code=(
                    Op.PUSH0
                    + Op.SLOAD
                    + Op.DUP1
                    + Op.PUSH2(MAX_RETURN_STACK_HEIGHT)
                    + Op.SUB
                    + Op.RJUMPI[len(Op.POP) + len(Op.RETF)]
                    + Op.POP
                    + Op.RETF
                    + Op.PUSH1(1)
                    + Op.ADD
                    + Op.PUSH0
                    + Op.SSTORE
                    + Op.CALLF[0]
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
                    + Op.CALLF[0]
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
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            ),
        ],
    ),
    Container(
        name="overflow_recursive_callf",
        sections=[
            Section.Code(
                code=(Op.PUSH1(1) + Op.CALLF[1] + Op.STOP),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=1,
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
                    + Op.CALLF[0]
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
                    + Op.CALLF[0]
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

VALID: List[Container] = (
    CALL_SUCCEED_CONTRACTS
    + CALL_FAIL_CONTRACTS
    + [
        contract_call_within_deep_nested_callf,
    ]
)
"""
List of all EOF V1 Containers used during execution tests.
"""


@pytest.mark.parametrize("container", CALL_SUCCEED_CONTRACTS, ids=lambda x: x.name)
def test_eof_functions_contract_call_succeed(
    state_test: StateTestFiller,
    container: Container,
):
    """
    Test simple contracts that are simply expected to succeed on call.
    """
    env = Environment()

    caller_contract = Op.SSTORE(0, Op.CALL(Op.GAS, 0x200, 0, 0, 0, 0, 0)) + Op.STOP()

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        Address(0x100): Account(
            code=caller_contract,
            nonce=1,
        ),
        Address(0x200): Account(
            code=container,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(0x100),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
    )

    post = {Address(0x100): Account(storage={0: 1})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize("container", CALL_FAIL_CONTRACTS, ids=lambda x: x.name)
def test_eof_functions_contract_call_fail(
    state_test: StateTestFiller,
    container: Container,
):
    """
    Test simple contracts that are simply expected to fail on call.
    """
    env = Environment()

    caller_contract = Op.SSTORE(Op.CALL(Op.GAS, 0x200, 0, 0, 0, 0, 0), 1) + Op.STOP()

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        Address(0x100): Account(
            code=caller_contract,
            nonce=1,
        ),
        Address(0x200): Account(
            code=container,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(0x100),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
    )

    post = {Address(0x100): Account(storage={0: 1})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize("container", CALL_FAIL_CONTRACTS, ids=lambda x: x.name)
def test_eof_functions_contract_call_within_deep_nested(
    state_test: StateTestFiller,
    container: Container,
):
    """
    Test performing a call within a nested callf and verify correct behavior of
    return stack in calling contract.
    """
    env = Environment()

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        Address(0x100): Account(
            code=contract_call_within_deep_nested_callf,
        ),
        Address(0x200): Account(
            code=Op.SSTORE(0, 1) + Op.STOP(),
        ),
    }
    tx = Transaction(
        nonce=1,
        to=Address(0x100),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
    )
    post = {
        Address(0x100): Account(storage={i: 1 for i in range(MAX_CODE_SECTIONS)}),
        Address(0x200): Account(
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
