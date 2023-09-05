"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)

    Test cases for `TSTORE` and `TLOAD` opcode calls in reentrancy contexts.
"""  # noqa: E501

from enum import Enum, unique

import pytest

from ethereum_test_tools import Account, Conditional, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, TestAddress, Transaction, to_hash_bytes

from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Shanghai")]

# Address of the callee contract
callee_address = 0x200


SETUP_CONDITION: bytes = Op.EQ(Op.CALLDATALOAD(0), 0x01)
REENTRANT_CALL: bytes = Op.MSTORE(0, 2) + Op.SSTORE(
    0, Op.CALL(Op.GAS(), callee_address, 0, 0, 32, 0, 0)
)


@unique
class TStorageReentrancyTestCases(Enum):
    """
    Transient storage test cases for different contract reentrancy call contexts.
    """

    TSTORE_IN_REENTRANT_CALL = {
        "description": (
            "Reentrant calls access the same transient storage: "
            "TSTORE(x, y), CALL(self, ...), TLOAD(x) returns y."
            ""
            "Based on [ethereum/tests/.../05_tloadReentrancyFiller.yml](https://github.com/ethereum/tests/tree/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage).",  # noqa: E501
        ),
        "caller_bytecode": None,
        "callee_bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(Op.TSTORE(0, 0x100) + REENTRANT_CALL + Op.SSTORE(2, Op.TLOAD(0))),
            # reenter
            if_false=Op.SSTORE(1, Op.TLOAD(0)),
        ),
        "expected_caller_storage": None,
        "expected_callee_storage": {0: 0x01, 1: 0x100, 2: 0x100},
    }
    TLOAD_AFTER_REENTRANT_TSTORE = {
        "description": (
            "Successfully returned calls do not revert transient storage writes: "
            "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), RETURN, TLOAD(x) returns z."
            ""
            "Based on [ethereum/tests/.../07_tloadAfterReentrancyStoreFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/07_tloadAfterReentrancyStoreFiller.yml).",  # noqa: E501
        ),
        "caller_bytecode": None,
        "callee_bytecode": Conditional(
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
        "expected_caller_storage": None,
        "expected_callee_storage": {0: 0x01, 1: 0x100, 2: 0x101},
    }
    MANIPULATE_IN_REENTRANT_CALL = {
        "description": (
            "Reentrant calls can manipulate the same transient storage: "
            "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), TLOAD(x) returns z."
            ""
            "Based on [ethereum/tests/.../06_tstoreInReentrancyCallFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/06_tstoreInReentrancyCallFiller.yml).",  # noqa: E501
        ),
        "caller_bytecode": None,
        "callee_bytecode": Conditional(
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
        "expected_caller_storage": None,
        "expected_callee_storage": {0: 0x01, 1: 0x100, 2: 0x101, 3: 0x101},
    }
    TSTORE_BEFORE_REVERT_HAS_NO_EFFECT = {
        "description": (
            "Revert undoes the transient storage write from the failed call: "
            "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), REVERT, TLOAD(x) returns y."
            "",
            "Based on [ethereum/tests/.../08_revertUndoesTransientStoreFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/08_revertUndoesTransientStoreFiller.yml)",  # noqa: E501
        ),
        "caller_bytecode": None,
        "callee_bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(1, Op.TLOAD(0xFF))
                + REENTRANT_CALL
                + Op.SSTORE(2, Op.TLOAD(0xFF))  # test value not updated during reentrant call
            ),
            # reenter
            if_false=Op.TSTORE(0xFF, 0x101) + Op.REVERT(0, 0),
        ),
        "expected_caller_storage": None,
        "expected_callee_storage": {0: 0x00, 1: 0x100, 2: 0x100},
    }
    REVERT_UNDOES_ALL = (
        {
            "description": (
                "Revert undoes all the transient storage writes to the same key from a failed ",
                "call. TSTORE(x, y), CALL(self, ...), TSTORE(x, z), TSTORE(x, z + 1) REVERT, ",
                "TLOAD(x) returns y.",
                "",
                "Based on [ethereum/tests/.../09_revertUndoesAllFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/09_revertUndoesAllFiller.yml).",  # noqa: E501
            ),
            "caller_bytecode": None,
            "callee_bytecode": Conditional(
                condition=SETUP_CONDITION,
                # setup
                if_true=(
                    Op.TSTORE(0xFE, 0x100)
                    + Op.TSTORE(0xFF, 0x101)
                    + REENTRANT_CALL
                    + Op.SSTORE(1, Op.TLOAD(0xFE))  # test value not updated during reentrant call
                    + Op.SSTORE(2, Op.TLOAD(0xFF))  # test value not updated during reentrant call
                ),
                # reenter
                if_false=(
                    # store twice and revert; none of the stores should take effect
                    Op.TSTORE(0xFE, 0x201)
                    + Op.TSTORE(0xFE, 0x202)
                    + Op.TSTORE(0xFF, 0x201)
                    + Op.TSTORE(0xFF, 0x202)
                    + Op.REVERT(0, 0)
                ),
            ),
            "expected_caller_storage": None,
            "expected_callee_storage": {0: 0x00, 1: 0x100, 2: 0x101},
        },
    )
    """
    REVERT_UNDOES_TSTORAGE_AFTER_SUCCESSFUL_CALL = {
        "description": (
            "Revert undoes transient storage writes from inner calls that successfully returned. ",
            "TSTORE(x, y), CALL(self, ...), CALL(self, ...), TSTORE(x, y + 1), RETURN, REVERT, "
            "TLOAD(x) returns y."
            "",
            "Based on stEIP1153-transientStorage/10_revertUndoesStoreAfterReturnFiller.yml",
        ),
        "caller_bytecode": None,
        "callee_bytecode": Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 0x01),
            # setup
            if_true=(
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(2, Op.TLOAD(0xFF))
                + Op.MSTORE(0, 2)
                + Op.SSTORE(0, Op.CALL(Op.GAS(), callee_address, 0, 0, 32, 0, 0))
                + Op.SSTORE(1, Op.MLOAD(0))  # should be 1 (successful call)
                + Op.SSTORE(3, Op.TLOAD(0xFF))
            ),
            # first, reentrant call, which reverts
            if_false=Conditional(
                condition=Op.EQ(Op.CALLDATALOAD(0), 0x02),
                if_true=(
                    Op.MSTORE(0, 3)
                    + Op.MSTORE(0, Op.CALL(Op.GAS(), callee_address, 0, 0, 32, 0, 0))
                    + Op.REVERT(0, 32)
                ),
                # second, successful reentrant call
                if_false=Op.TSTORE(0xFF, 0x101),
            ),
        ),
        "expected_caller_storage": None,
        "expected_callee_storage": {0: 0x00, 1: 0x01, 2: 0x100, 3: 0x100},
    }
    """

    def __init__(self, test_case):
        self.test_case_id = self.name.lower()
        self.callee_bytecode = test_case["callee_bytecode"]
        self.expected_callee_storage = test_case["expected_callee_storage"]


@pytest.mark.parametrize(
    ["callee_bytecode", "expected_callee_storage"],
    [
        (
            test_case.callee_bytecode,
            test_case.expected_callee_storage,
        )
        for test_case in TStorageReentrancyTestCases
    ],
    ids=[test_case.test_case_id for test_case in TStorageReentrancyTestCases],
)
def test_call_reentrancy(state_test: StateTestFiller, callee_bytecode, expected_callee_storage):
    """
    Test transient storage in different reentrancy contexts.
    """
    env = Environment()

    pre = {
        TestAddress: Account(balance=10**40),
        callee_address: Account(code=callee_bytecode),
    }

    tx = Transaction(
        to=callee_address,
        data=to_hash_bytes(1),
        gas_limit=1_000_000,
    )

    post = {callee_address: Account(code=callee_bytecode, storage=expected_callee_storage)}
    state_test(env=env, pre=pre, post=post, txs=[tx])
