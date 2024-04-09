"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)
    Test cases for `TSTORE` and `TLOAD` opcode calls in different execution contexts.
"""  # noqa: E501

from enum import EnumMeta, unique
from typing import Mapping

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, TestAddress, Transaction

from . import PytestParameterEnum
from .spec import Spec, ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

# Address used to call the test bytecode on every test case.
caller_address = 0x100

# Address of the callee contract
callee_address = 0x200

PUSH_OPCODE_COST = 3


class DynamicCallContextTestCases(EnumMeta):
    """
    Create dynamic transient storage test cases for contract sub-calls
    using CALLCODE and DELEGATECALL (these opcodes share the same
    signatures and test cases).
    """

    def __new__(cls, name, bases, classdict):  # noqa: D102
        for opcode in [Op.CALLCODE, Op.DELEGATECALL]:
            if opcode == Op.DELEGATECALL:
                contract_call = opcode(Op.GAS(), callee_address, 0, 0, 0, 0)
            elif opcode == Op.CALLCODE:
                contract_call = opcode(Op.GAS(), callee_address, 0, 0, 0, 0, 0)
            else:
                raise ValueError("Unexpected opcode.")
            classdict[opcode._name_] = {
                "description": (
                    "Caller and callee contracts share transient storage when callee is "
                    f"called via {opcode._name_}."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(4, Op.TLOAD(1))
                ),
                "callee_bytecode": (
                    Op.SSTORE(2, Op.TLOAD(0)) + Op.TSTORE(1, 69) + Op.SSTORE(3, Op.TLOAD(1))
                ),
                "expected_caller_storage": {0: 1, 1: 420, 2: 420, 3: 69, 4: 69},
                "expected_callee_storage": {},
            }

        for opcode in [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]:
            if opcode == Op.DELEGATECALL:
                contract_call = opcode(Op.GAS(), callee_address, 0, 0, 0, 0)
            elif opcode in [Op.CALL, Op.CALLCODE]:
                contract_call = opcode(Op.GAS(), callee_address, 0, 0, 0, 0, 0)
            else:
                raise ValueError("Unexpected opcode.")
            classdict[f"{opcode._name_}_WITH_REVERT"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon REVERT."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.REVERT(0, 0),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            if opcode == Op.DELEGATECALL:
                contract_call = opcode(0xFF, callee_address, 0, 0, 0, 0)
            elif opcode in [Op.CALL, Op.CALLCODE]:
                contract_call = opcode(0xFF, callee_address, 0, 0, 0, 0, 0)
            else:
                raise ValueError("Unexpected opcode.")
            classdict[f"{opcode._name_}_WITH_INVALID"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon REVERT. Note: Gas passed to sub-call is capped."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.INVALID(),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            if opcode == Op.DELEGATECALL:
                contract_call = opcode(0xFFFF, callee_address, 0, 0, 0, 0)
            elif opcode in [Op.CALL, Op.CALLCODE]:
                contract_call = opcode(0xFFFF, callee_address, 0, 0, 0, 0, 0)
            else:
                raise ValueError("Unexpected opcode.")
            classdict[f"{opcode._name_}_WITH_STACK_OVERFLOW"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon stack overflow."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.PUSH0() * 1025,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{opcode._name_}_WITH_TSTORE_STACK_UNDERFLOW"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon stack underflow because of TSTORE parameters (1)."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, unchecked=True),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{opcode._name_}_WITH_TSTORE_STACK_UNDERFLOW_2"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    " upon stack underflow because of TSTORE parameters (0)."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{opcode._name_}_WITH_TLOAD_STACK_UNDERFLOW"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon stack underflow because of TLOAD parameters (0)."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TLOAD + Op.TSTORE(0, 1),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            gas_limit = Spec.TSTORE_GAS_COST + (PUSH_OPCODE_COST * 2) - 1
            if opcode == Op.DELEGATECALL:
                contract_call = opcode(gas_limit, callee_address, 0, 0, 0, 0)
            elif opcode in [Op.CALL, Op.CALLCODE]:
                contract_call = opcode(gas_limit, callee_address, 0, 0, 0, 0, 0)
            else:
                raise ValueError("Unexpected opcode.")
            classdict[f"{opcode._name_}_WITH_OUT_OF_GAS"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon out of gas during TSTORE. Note: Gas passed to sub-call is capped."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, 69),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            if opcode == Op.DELEGATECALL:
                contract_call = opcode(0xFF, callee_address, 0, 0, 0, 0)
            elif opcode in [Op.CALL, Op.CALLCODE]:
                contract_call = opcode(0xFF, callee_address, 0, 0, 0, 0, 0)
            else:
                raise ValueError("Unexpected opcode.")
            classdict[f"{opcode._name_}_WITH_OUT_OF_GAS_2"] = {
                "description": (
                    f"Transient storage usage is discarded from sub-call with {opcode._name_} "
                    "upon out of gas after TSTORE. Note: Gas passed to sub-call is capped."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + (Op.PUSH0() + Op.POP) * 512,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

        return super().__new__(cls, name, bases, classdict)


@unique
class CallContextTestCases(PytestParameterEnum, metaclass=DynamicCallContextTestCases):
    """
    Transient storage test cases for different contract subcall contexts.
    """

    CALL = {
        "description": (
            "Caller and callee contracts use their own transient storage when callee "
            "is called via CALL."
        ),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.CALL(Op.GAS(), callee_address, 0, 0, 0, 0, 0))
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.SSTORE(2, Op.TLOAD(1))
        ),
        "callee_bytecode": (
            Op.SSTORE(0, Op.TLOAD(0)) + Op.TSTORE(1, 69) + Op.SSTORE(1, Op.TLOAD(1))
        ),
        "expected_caller_storage": {0: 1, 1: 420, 2: 0},
        "expected_callee_storage": {0: 0, 1: 69},
    }
    STATICCALL_CANT_CALL_TSTORE = {
        "description": ("TA STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(0xFFFF, callee_address, 0, 0, 0, 0))  # limit gas
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "callee_bytecode": Op.TSTORE(0, 69),  # calling tstore fails
        "expected_caller_storage": {0: 0, 1: 420},
        "expected_callee_storage": {},
    }
    STATICCALL_CANT_CALL_TSTORE_WITH_STACK_UNDERFLOW = {
        "description": ("TA STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(0xFFFF, callee_address, 0, 0, 0, 0))  # limit gas
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "callee_bytecode": Op.TSTORE(
            0, unchecked=True
        ),  # calling with stack underflow still fails
        "expected_caller_storage": {0: 0, 1: 420},
        "expected_callee_storage": {},
    }
    STATICCALL_CAN_CALL_TLOAD = {
        # TODO: Not a very useful test; consider removing after implementing ethereum/tests
        # staticcall tests
        "pytest_id": "staticcalled_context_can_call_tload",
        "description": ("A STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(Op.GAS(), callee_address, 0, 0, 0, 0))
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "callee_bytecode": Op.TLOAD(0),  # calling tload does not cause the call to fail
        "expected_caller_storage": {0: 1, 1: 420},
        "expected_callee_storage": {},
    }

    def __init__(self, value):
        value = {
            "env": Environment(),
            "pre": {
                TestAddress: Account(balance=10**40),
                caller_address: Account(code=value["caller_bytecode"]),
                callee_address: Account(code=value["callee_bytecode"]),
            },
            "tx": Transaction(
                to=caller_address,
                gas_limit=1_000_000,
            ),
            "post": {
                caller_address: Account(storage=value["expected_caller_storage"]),
                callee_address: Account(storage=value["expected_callee_storage"]),
            },
        } | {k: value[k] for k in value.keys() if k in self.special_keywords()}
        super().__init__(value)


@CallContextTestCases.parametrize()
def test_subcall(
    state_test: StateTestFiller,
    env: Environment,
    pre: Mapping,
    tx: Transaction,
    post: Mapping,
):
    """
    Test transient storage with a subcall using the following opcodes:

    - `CALL`
    - `CALLCODE`
    - `DELEGATECALL`
    - `STATICCALL`
    """
    state_test(env=env, pre=pre, post=post, tx=tx)
