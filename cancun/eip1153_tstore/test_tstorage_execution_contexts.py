"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)
    Test cases for `TSTORE` and `TLOAD` opcode calls in different execution contexts.
"""  # noqa: E501

from enum import EnumMeta, unique
from typing import Dict, Mapping

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from . import PytestParameterEnum
from .spec import Spec, ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

PUSH_OPCODE_COST = 3


class DynamicCallContextTestCases(EnumMeta):
    """
    Create dynamic transient storage test cases for contract sub-calls
    using CALLCODE and DELEGATECALL (these opcodes share the same
    signatures and test cases).
    """

    def __new__(cls, name, bases, classdict):  # noqa: D102
        for call_opcode in [Op.CALLCODE, Op.DELEGATECALL]:
            contract_call = call_opcode(address=Op.CALLDATALOAD(0))
            classdict[call_opcode._name_] = {
                "description": (
                    "Caller and callee contracts share transient storage when callee is "
                    f"called via {call_opcode._name_}."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(4, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": (
                    Op.SSTORE(2, Op.TLOAD(0))
                    + Op.TSTORE(1, 69)
                    + Op.SSTORE(3, Op.TLOAD(1))
                    + Op.STOP
                ),
                "expected_caller_storage": {0: 1, 1: 420, 2: 420, 3: 69, 4: 69},
                "expected_callee_storage": {},
            }

        for call_opcode in [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]:
            contract_call = call_opcode(address=Op.CALLDATALOAD(0))
            classdict[f"{call_opcode._name_}_WITH_REVERT"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon REVERT."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.REVERT(0, 0),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            contract_call = call_opcode(gas=0xFF, address=Op.CALLDATALOAD(0))
            classdict[f"{call_opcode._name_}_WITH_INVALID"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon REVERT. Note: Gas passed to sub-call is capped."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.INVALID(),
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            contract_call = call_opcode(gas=0xFFFF, address=Op.CALLDATALOAD(0))
            classdict[f"{call_opcode._name_}_WITH_STACK_OVERFLOW"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon stack overflow."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.PUSH0() * 1025 + Op.STOP,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{call_opcode._name_}_WITH_TSTORE_STACK_UNDERFLOW"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon stack underflow because of TSTORE parameters (1)."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE(1, unchecked=True) + Op.STOP,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{call_opcode._name_}_WITH_TSTORE_STACK_UNDERFLOW_2"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon stack underflow because of TSTORE parameters (0)."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE + Op.STOP,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }
            classdict[f"{call_opcode._name_}_WITH_TLOAD_STACK_UNDERFLOW"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon stack underflow because of TLOAD parameters (0)."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TLOAD + Op.TSTORE(0, 1) + Op.STOP,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            gas_limit = Spec.TSTORE_GAS_COST + (PUSH_OPCODE_COST * 2) - 1
            contract_call = call_opcode(gas=gas_limit, address=Op.CALLDATALOAD(0))
            classdict[f"{call_opcode._name_}_WITH_OUT_OF_GAS"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon out of gas during TSTORE. "
                    "Note: Gas passed to sub-call is capped."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + Op.STOP,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

            contract_call = call_opcode(gas=0xFF, address=Op.CALLDATALOAD(0))
            classdict[f"{call_opcode._name_}_WITH_OUT_OF_GAS_2"] = {
                "description": (
                    "Transient storage usage is discarded from sub-call with "
                    f"{call_opcode._name_} upon out of gas after TSTORE. "
                    "Note: Gas passed to sub-call is capped."
                ),
                "caller_bytecode": (
                    Op.TSTORE(0, 420)
                    + Op.TSTORE(1, 420)
                    + Op.SSTORE(0, contract_call)
                    + Op.SSTORE(1, Op.TLOAD(0))
                    + Op.SSTORE(2, Op.TLOAD(1))
                    + Op.STOP
                ),
                "callee_bytecode": Op.TSTORE(1, 69) + (Op.PUSH0() + Op.POP) * 512 + Op.STOP,
                "expected_caller_storage": {0: 0, 1: 420, 2: 420},
                "expected_callee_storage": {},
            }

        return super().__new__(cls, name, bases, classdict)


@unique
class CallContextTestCases(PytestParameterEnum, metaclass=DynamicCallContextTestCases):
    """Transient storage test cases for different contract subcall contexts."""

    CALL = {
        "description": (
            "Caller and callee contracts use their own transient storage when callee "
            "is called via CALL."
        ),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.CALL(address=Op.CALLDATALOAD(0)))
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.SSTORE(2, Op.TLOAD(1))
            + Op.STOP
        ),
        "callee_bytecode": (
            Op.SSTORE(0, Op.TLOAD(0)) + Op.TSTORE(1, 69) + Op.SSTORE(1, Op.TLOAD(1)) + Op.STOP
        ),
        "expected_caller_storage": {0: 1, 1: 420, 2: 0},
        "expected_callee_storage": {0: 0, 1: 69},
    }
    STATICCALL_CANT_CALL_TSTORE = {
        "description": ("TA STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(gas=0xFFFF, address=Op.CALLDATALOAD(0)))  # limit gas
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.STOP
        ),
        "callee_bytecode": Op.TSTORE(0, 69) + Op.STOP,  # calling tstore fails
        "expected_caller_storage": {0: 0, 1: 420},
        "expected_callee_storage": {},
    }
    STATICCALL_CANT_CALL_TSTORE_WITH_STACK_UNDERFLOW = {
        "description": ("TA STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(gas=0xFFFF, address=Op.CALLDATALOAD(0)))  # limit gas
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.STOP
        ),
        "callee_bytecode": Op.TSTORE(0, unchecked=True)  # calling with stack underflow still fails
        + Op.STOP,
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
            + Op.SSTORE(0, Op.STATICCALL(address=Op.CALLDATALOAD(0)))
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.STOP
        ),
        "callee_bytecode": Op.TLOAD(0) + Op.STOP,  # calling tload does not cause the call to fail
        "expected_caller_storage": {0: 1, 1: 420},
        "expected_callee_storage": {},
    }

    def __init__(self, value):
        """Initialize the test case with the given value."""
        value = {
            "env": Environment(),
            "caller_bytecode": value["caller_bytecode"],
            "callee_bytecode": value["callee_bytecode"],
            "expected_caller_storage": value["expected_caller_storage"],
            "expected_callee_storage": value["expected_callee_storage"],
        } | {k: value[k] for k in value.keys() if k in self.special_keywords()}
        super().__init__(value)


@pytest.fixture()
def caller_address(pre: Alloc, caller_bytecode: Bytecode) -> Address:
    """Address used to call the test bytecode on every test case."""
    return pre.deploy_contract(caller_bytecode)


@pytest.fixture()
def callee_address(pre: Alloc, callee_bytecode: Bytecode) -> Address:
    """Address called by the test bytecode on every test case."""
    return pre.deploy_contract(callee_bytecode)


@pytest.fixture()
def tx(pre: Alloc, caller_address: Address, callee_address: Address) -> Transaction:  # noqa: D103
    return Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
        data=Hash(callee_address),
        gas_limit=1_000_000,
    )


@pytest.fixture()
def post(  # noqa: D103
    caller_address: Address,
    callee_address: Address,
    expected_caller_storage: Dict,
    expected_callee_storage: Dict,
) -> Dict:
    return {
        caller_address: Account(storage=expected_caller_storage),
        callee_address: Account(storage=expected_callee_storage),
    }


@CallContextTestCases.parametrize()
def test_subcall(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    tx: Transaction,
    post: Mapping,
):
    """
    Test transient storage with a subcall using the following opcodes.

    - `CALL`
    - `CALLCODE`
    - `DELEGATECALL`
    - `STATICCALL`
    """
    state_test(env=env, pre=pre, post=post, tx=tx)
