"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)

    Test cases for `TSTORE` and `TLOAD` opcode calls in different execution contexts.
"""  # noqa: E501

from enum import Enum, unique

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, TestAddress, Transaction

from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Shanghai")]

# Address used to call the test bytecode on every test case.
caller_address = 0x100

# Address of the callee contract
callee_address = 0x200


@unique
class TStorageCallContextTestCases(Enum):
    """
    Transient storage test cases for different contract subcall contexts.
    """

    CALL = {
        "pytest_param": pytest.param(id="call"),
        "description": (
            "TSTORE0001: Caller and callee contracts use their own transient storage when callee "
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
        "pytest_param": pytest.param(id="staticcalled_context_cant_call_tstore"),
        "description": ("TSTORE0002: A STATICCALL callee can not use transient storage."),
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
        "description": ("TSTORE0002: A STATICCALL callee can not use transient storage."),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.STATICCALL(Op.GAS(), callee_address, 0, 0, 0, 0))
            + Op.SSTORE(1, Op.TLOAD(0))
        ),
        "callee_bytecode": Op.TLOAD(0),  # calling tload does fail the call
        "expected_caller_storage": {0: 1, 1: 420},
        "expected_callee_storage": {},
    }
    CALLCODE = {
        "pytest_param": pytest.param(id="callcode"),
        "description": (
            "TSTORE0003: Caller and callee contracts share transient storage "
            "when callee is called via CALLCODE."
        ),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.CALLCODE(Op.GAS(), callee_address, 0, 0, 0, 0, 0)
            + Op.SSTORE(0, Op.TLOAD(0))
        ),
        "callee_bytecode": Op.SSTORE(1, Op.TLOAD(0)),
        "expected_caller_storage": {0: 420, 1: 420},
        "expected_callee_storage": {0: 0, 0: 0},
    }
    DELEGATECALL = {
        "pytest_param": pytest.param(id="delegatecall"),
        "description": (
            "TSTORE0004: Caller and callee contracts share transient storage "
            "when callee is called via DELEGATECALL."
        ),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.SSTORE(0, Op.DELEGATECALL(Op.GAS(), callee_address, 0, 0, 0, 0))
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.SSTORE(4, Op.TLOAD(1))
        ),
        "callee_bytecode": (
            Op.SSTORE(2, Op.TLOAD(0)) + Op.TSTORE(1, 69) + Op.SSTORE(3, Op.TLOAD(1))
        ),
        "expected_caller_storage": {0: 1, 1: 420, 2: 420, 3: 69, 4: 69},
        "expected_callee_storage": {},
    }
    DELEGATECALL_WITH_REVERT = {
        "pytest_param": pytest.param(id="delegatecall_with_revert"),
        "description": (
            "TSTORE0004: Caller and callee contracts share transient storage "
            "when callee is called via DELEGATECALL. Transient storage usage "
            "from sub-call upon revert."
        ),
        "caller_bytecode": (
            Op.TSTORE(0, 420)
            + Op.TSTORE(1, 420)
            + Op.SSTORE(0, Op.DELEGATECALL(Op.GAS(), callee_address, 0, 0, 0, 0))
            + Op.SSTORE(1, Op.TLOAD(0))
            + Op.SSTORE(2, Op.TLOAD(1))
        ),
        "callee_bytecode": Op.TSTORE(1, 69) + Op.REVERT(0, 0),
        "expected_caller_storage": {0: 0, 1: 420, 2: 420},
        "expected_callee_storage": {},
    }

    def __init__(self, test_case):
        self._value_ = test_case["pytest_param"]
        self.description = test_case["description"]
        self.env = Environment()
        self.pre = {
            TestAddress: Account(balance=10**40),
            caller_address: Account(code=test_case["caller_bytecode"]),
            callee_address: Account(code=test_case["callee_bytecode"]),
        }
        self.post = {
            caller_address: Account(storage=test_case["expected_caller_storage"]),
            callee_address: Account(storage=test_case["expected_callee_storage"]),
        }
        self.txs = [
            Transaction(
                to=caller_address,
                gas_limit=1_000_000,
            )
        ]


@pytest.mark.parametrize(
    "test_case",
    [case for case in TStorageCallContextTestCases],
    ids=[case._value_.id for case in TStorageCallContextTestCases],
)
def test_tstore_tload(
    test_case: TStorageCallContextTestCases,
    state_test: StateTestFiller,
):
    """
    Test transient storage with a subcall using the following opcodes:

    - `CALL`
    - `CALLCODE`
    - `DELEGATECALL`
    - `STATICCALL`
    """
    state_test(
        env=test_case.env,
        pre=test_case.pre,
        post=test_case.post,
        txs=test_case.txs,
    )
