"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)
    Test cases for `TSTORE` and `TLOAD` opcode calls in reentrancy contexts.
"""  # noqa: E501

from enum import EnumMeta, unique

import pytest

from ethereum_test_tools import Account, CalldataCase, Conditional, Environment, Hash
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Switch, TestAddress, Transaction

from . import PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

# Address of the callee contract
callee_address = 0x200

SETUP_CONDITION: bytes = Op.EQ(Op.CALLDATALOAD(0), 0x01)
REENTRANT_CALL: bytes = Op.MSTORE(0, 2) + Op.SSTORE(
    0, Op.CALL(Op.GAS(), callee_address, 0, 0, 32, 0, 0)
)


class DynamicReentrancyTestCases(EnumMeta):
    """
    Create dynamic transient storage test cases which REVERT or receive INVALID
    (these opcodes should share the same behavior).
    """

    def __new__(cls, name, bases, classdict):  # noqa: D102
        for opcode in [Op.REVERT, Op.INVALID]:
            if opcode == Op.REVERT:
                opcode_call = Op.REVERT(0, 0)
                subcall_gas = Op.GAS()
            elif opcode == Op.INVALID:
                opcode_call = Op.INVALID()
                subcall_gas = 0xFFFF
            else:
                raise ValueError(f"Unknown opcode: {opcode}.")

            reentrant_call: bytes = Op.MSTORE(0, 2) + Op.SSTORE(
                0, Op.CALL(subcall_gas, callee_address, 0, 0, 32, 0, 0)
            )

            classdict[f"TSTORE_BEFORE_{opcode._name_}_HAS_NO_EFFECT"] = {
                "description": (
                    f"{opcode._name_} undoes the transient storage write from the failed call: "
                    f"TSTORE(x, y), CALL(self, ...), TSTORE(x, z), {opcode._name_}, TLOAD(x) "
                    "returns y."
                    "",
                    "Based on [ethereum/tests/.../08_revertUndoesTransientStoreFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/08_revertUndoesTransientStoreFiller.yml)",  # noqa: E501
                ),
                "bytecode": Conditional(
                    condition=SETUP_CONDITION,
                    # setup
                    if_true=(
                        Op.TSTORE(0xFF, 0x100)
                        + Op.SSTORE(1, Op.TLOAD(0xFF))
                        + reentrant_call
                        + Op.SSTORE(
                            2, Op.TLOAD(0xFF)
                        )  # test value not updated during reentrant call
                    ),
                    # reenter
                    if_false=Op.TSTORE(0xFF, 0x101) + opcode_call,
                ),
                "expected_storage": {0: 0x00, 1: 0x100, 2: 0x100},
            }

            classdict[f"{opcode._name_}_UNDOES_ALL"] = {
                "description": (
                    f"{opcode._name_} undoes all the transient storage writes to the same key ",
                    "from a failed call. TSTORE(x, y), CALL(self, ...), TSTORE(x, z), ",
                    f"TSTORE(x, z + 1) {opcode._name_}, TLOAD(x) returns y.",
                    "",
                    "Based on [ethereum/tests/.../09_revertUndoesAllFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/09_revertUndoesAllFiller.yml).",  # noqa: E501
                ),
                "bytecode": Conditional(
                    condition=SETUP_CONDITION,
                    # setup
                    if_true=(
                        Op.TSTORE(0xFE, 0x100)
                        + Op.TSTORE(0xFF, 0x101)
                        + reentrant_call
                        + Op.SSTORE(
                            1, Op.TLOAD(0xFE)
                        )  # test value not updated during reentrant call
                        + Op.SSTORE(
                            2, Op.TLOAD(0xFF)
                        )  # test value not updated during reentrant call
                    ),
                    # reenter
                    if_false=(
                        # store twice and revert/invalid; none of the stores should take effect
                        Op.TSTORE(0xFE, 0x201)
                        + Op.TSTORE(0xFE, 0x202)
                        + Op.TSTORE(0xFF, 0x201)
                        + Op.TSTORE(0xFF, 0x202)
                        + opcode_call
                    ),
                ),
                "expected_storage": {0: 0x00, 1: 0x100, 2: 0x101},
            }

            if opcode == Op.REVERT:
                opcode_call = Op.REVERT(0, 32)
                second_call_return_value = 1
            elif opcode == Op.INVALID:
                opcode_call = Op.INVALID()
                second_call_return_value = 0
            else:
                raise ValueError(f"Unknown opcode: {opcode}.")

            classdict[f"{opcode._name_}_UNDOES_TSTORAGE_AFTER_SUCCESSFUL_CALL"] = {
                "description": (
                    f"{opcode._name_} undoes transient storage writes from inner calls that "
                    "successfully returned. TSTORE(x, y), CALL(self, ...), CALL(self, ...), "
                    f"TSTORE(x, y + 1), RETURN, {opcode._name_}, TLOAD(x) returns y."
                    "",
                    "Based on [ethereum/tests/.../10_revertUndoesStoreAfterReturnFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/10_revertUndoesStoreAfterReturnFiller.yml).",  # noqa: E501
                ),
                "bytecode": Switch(
                    default_action=(  # setup; make first reentrant sub-call
                        Op.TSTORE(0xFF, 0x100)
                        + Op.SSTORE(2, Op.TLOAD(0xFF))
                        + Op.MSTORE(0, 2)
                        + Op.SSTORE(0, Op.CALL(subcall_gas, callee_address, 0, 0, 32, 32, 32))
                        + Op.SSTORE(1, Op.MLOAD(32))  # should be 1 (successful call)
                        + Op.SSTORE(3, Op.TLOAD(0xFF))
                    ),
                    cases=[
                        # the first, reentrant call, which reverts/receives invalid
                        CalldataCase(
                            value=2,
                            action=(
                                Op.MSTORE(0, 3)
                                + Op.MSTORE(0, Op.CALL(Op.GAS(), callee_address, 0, 0, 32, 0, 0))
                                + opcode_call
                            ),
                        ),
                        # the second, reentrant call, which returns successfully
                        CalldataCase(
                            value=3,
                            action=Op.TSTORE(0xFF, 0x101),
                        ),
                    ],
                ),
                "expected_storage": {0: 0x00, 1: second_call_return_value, 2: 0x100, 3: 0x100},
            }

        return super().__new__(cls, name, bases, classdict)


@unique
class ReentrancyTestCases(PytestParameterEnum, metaclass=DynamicReentrancyTestCases):
    """
    Transient storage test cases for different reentrancy call contexts.
    """

    TSTORE_IN_REENTRANT_CALL = {
        "description": (
            "Reentrant calls access the same transient storage: "
            "TSTORE(x, y), CALL(self, ...), TLOAD(x) returns y."
            ""
            "Based on [ethereum/tests/.../05_tloadReentrancyFiller.yml](https://github.com/ethereum/tests/tree/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage).",  # noqa: E501
        ),
        "bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(Op.TSTORE(0, 0x100) + REENTRANT_CALL + Op.SSTORE(2, Op.TLOAD(0))),
            # reenter
            if_false=Op.SSTORE(1, Op.TLOAD(0)),
        ),
        "expected_storage": {0: 0x01, 1: 0x100, 2: 0x100},
    }
    TLOAD_AFTER_REENTRANT_TSTORE = {
        "description": (
            "Successfully returned calls do not revert transient storage writes: "
            "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), RETURN, TLOAD(x) returns z."
            ""
            "Based on [ethereum/tests/.../07_tloadAfterReentrancyStoreFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/07_tloadAfterReentrancyStoreFiller.yml).",  # noqa: E501
        ),
        "bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(1, Op.TLOAD(0xFF))
                + REENTRANT_CALL
                + Op.SSTORE(2, Op.TLOAD(0xFF))  # test value updated during reentrant call
            ),
            # reenter
            if_false=Op.TSTORE(0xFF, 0x101),
        ),
        "expected_storage": {0: 0x01, 1: 0x100, 2: 0x101},
    }
    MANIPULATE_IN_REENTRANT_CALL = {
        "description": (
            "Reentrant calls can manipulate the same transient storage: "
            "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), TLOAD(x) returns z."
            ""
            "Based on [ethereum/tests/.../06_tstoreInReentrancyCallFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/06_tstoreInReentrancyCallFiller.yml).",  # noqa: E501
        ),
        "bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(1, Op.TLOAD(0xFF))
                + REENTRANT_CALL
                + Op.SSTORE(3, Op.TLOAD(0xFF))  # test value updated during reentrant call
            ),
            # reenter
            if_false=Op.TSTORE(0xFF, 0x101) + Op.SSTORE(2, Op.TLOAD(0xFF)),
        ),
        "expected_storage": {0: 0x01, 1: 0x100, 2: 0x101, 3: 0x101},
    }
    TSTORE_IN_CALL_THEN_TLOAD_RETURN_IN_STATICCALL = {
        "description": (
            "A reentrant call followed by a reentrant subcall can call tload correctly: "
            "TSTORE(x, y), CALL(self, ...), STATICCALL(self, ...), TLOAD(x), RETURN returns y."
            "Based on [ethereum/tests/.../10_revertUndoesStoreAfterReturnFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/10_revertUndoesStoreAfterReturnFiller.yml).",  # noqa: E501
        ),
        "bytecode": Switch(
            default_action=(  # setup; make first reentrant sub-call
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(2, Op.TLOAD(0xFF))
                + Op.MSTORE(0, 2)
                + Op.SSTORE(0, Op.CALL(Op.GAS(), callee_address, 0, 0, 32, 0, 0))
                + Op.SSTORE(4, Op.TLOAD(0xFE))
            ),
            cases=[
                # the first, reentrant call which calls tstore and a further reentrant staticcall
                CalldataCase(
                    value=2,
                    action=(
                        Op.TSTORE(0xFE, 0x101)
                        + Op.MSTORE(0, 3)
                        + Op.SSTORE(1, Op.STATICCALL(Op.GAS(), callee_address, 0, 32, 0, 32))
                        + Op.SSTORE(3, Op.MLOAD(0))
                    ),
                ),
                # the second, reentrant call, which calls tload and return returns successfully
                CalldataCase(
                    value=3,
                    action=Op.MSTORE(0, Op.TLOAD(0xFE)) + Op.RETURN(0, 32),
                ),
            ],
        ),
        "expected_storage": {0: 0x01, 1: 0x01, 2: 0x100, 3: 0x101, 4: 0x101},
    }


@ReentrancyTestCases.parametrize()
def test_reentrant_call(state_test: StateTestFiller, bytecode, expected_storage):
    """
    Test transient storage in different reentrancy contexts.
    """
    env = Environment()

    pre = {
        TestAddress: Account(balance=10**40),
        callee_address: Account(code=bytecode),
    }

    tx = Transaction(
        to=callee_address,
        data=Hash(1),
        gas_limit=10_000_000,
    )

    post = {callee_address: Account(code=bytecode, storage=expected_storage)}

    state_test(env=env, pre=pre, post=post, tx=tx)
