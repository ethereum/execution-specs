"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)

    Test cases for `TSTORE` and `TLOAD` opcode calls in different execution contexts.
"""  # noqa: E501

from enum import EnumMeta, unique
from typing import List, Mapping

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, TestAddress, Transaction

from . import PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

# Address used to call the test bytecode on every test case.
caller_address = 0x100

# Address of the callee contract
callee_address = 0x200


class DynamicCallContextTestCases(EnumMeta):
    """
    Create dynamic transient storage test cases for contract sub-calls
    using CALLCODE and DELEGATECALL (these opcodes share the same
    signatures and test cases).
    """

    def __new__(cls, name, bases, classdict):  # noqa: D102
        for opcode in [Op.CALLCODE, Op.DELEGATECALL]:
            classdict[opcode._name_] = {
                "description": (
                    "Caller and callee contracts share transient storage when callee is "
                    f"called via {opcode._name_}."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.SSTORE(0, opcode(Op.GAS(), callee_address, 0, 0, 0, 0, 0))
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(4, Op.TLOAD(1))
                ),
                "callee_bytecode": (
                    Op.SSTORE(2, Op.TLOAD(0)) + Op.TSTORE(1, 69) + Op.SSTORE(3, Op.TLOAD(1))
                ),
                "expected_caller_storage": {0: 1, 1: 420, 2: 420, 3: 69, 4: 69},
                "expected_callee_storage": {},
            }
            classdict[f"{opcode._name_}_WITH_REVERT"] = {
                "description": (
                    "Caller and callee contracts share transient storage when callee is "
                    f"called via {opcode._name_} but transient storage usage is discarded "
                    "from  sub-call upon REVERT."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, opcode(Op.GAS(), callee_address, 0, 0, 0, 0, 0))
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.REVERT(0, 0),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{opcode._name_}_WITH_INVALID"] = (
                {
                    "description": (
                        "Caller and callee contracts share transient storage when callee is "
                        f"called via {opcode._name_} but transient storage usage is discarded "
                        "from sub-call upon INVALID. Note: Gas passed to sub-call is capped."
                    ),
                    "caller_bytecode": (
                        Op.TSTORE(0, 420)
                        + Op.TSTORE(1, 420)
                        + Op.SSTORE(0, opcode(0xFF, callee_address, 0, 0, 0, 0, 0))
                        + Op.SSTORE(1, Op.TLOAD(0))
                        + Op.SSTORE(2, Op.TLOAD(1))
                    ),
                    "callee_bytecode": Op.TSTORE(1, 69) + Op.INVALID(),
                    "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                    "expected_callee_storage": {},
                },
            )
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
        "callee_bytecode": Op.TSTORE(0),  # calling tstore fails
        "expected_caller_storage": {0: 0, 1: 420},
        "expected_callee_storage": {},
    }
    STATICCALL_CAN_CALL_TLOAD = {
        # TODO: Not a very useful test; consider removing after implementing ethereum/tests
        # staticcall tests
        "pytest_param": pytest.param(id="staticcalled_context_can_call_tload"),
        "description": ("A STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(Op.GAS(), callee_address, 0, 0, 0, 0))
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "callee_bytecode": Op.TLOAD(0),  # calling tload does fail the call
        "expected_caller_storage": {0: 1, 1: 420},
        "expected_callee_storage": {},
    }

    def __init__(self, value):
        test_case = (
            # env
            Environment(),
            # pre
            {
                TestAddress: Account(balance=10**40),
                caller_address: Account(code=value["caller_bytecode"]),
                callee_address: Account(code=value["callee_bytecode"]),
            },
            # txs
            [
                Transaction(
                    to=caller_address,
                    gas_limit=1_000_000,
                )
            ],
            # post
            {
                caller_address: Account(storage=value["expected_caller_storage"]),
                callee_address: Account(storage=value["expected_callee_storage"]),
            },
        )
        super().__init__(value, test_case)


@pytest.mark.parametrize("env,pre,txs,post", CallContextTestCases.as_list())
def test_subcall(
    state_test: StateTestFiller,
    env: Environment,
    pre: Mapping,
    txs: List[Transaction],
    post: Mapping,
):
    """
    Test transient storage with a subcall using the following opcodes:

    - `CALL`
    - `CALLCODE`
    - `DELEGATECALL`
    - `STATICCALL`
    """
    state_test(env=env, pre=pre, post=post, txs=txs)
