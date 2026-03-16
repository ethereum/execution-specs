"""
Tests transient storage in reentrancy contexts.
"""

from enum import EnumMeta, unique
from typing import Any, Dict

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CalldataCase,
    Conditional,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Switch,
    Transaction,
)

from . import PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

SETUP_CONDITION: Bytecode = Op.EQ(Op.CALLDATALOAD(0), 0x01)
REENTRANT_CALL: Bytecode = Op.MSTORE(0, 2) + Op.SSTORE(
    0, Op.CALL(address=Op.ADDRESS, args_size=32)
)


class DynamicReentrancyTestCases(EnumMeta):
    """
    Create dynamic transient storage test cases which REVERT or receive INVALID
    (these opcodes should share the same behavior).
    """

    def __new__(  # noqa: D102
        cls, name: str, bases: tuple[type, ...], classdict: Any
    ) -> Any:
        for opcode in [Op.REVERT, Op.INVALID]:
            if opcode == Op.REVERT:
                opcode_call = Op.REVERT(0, 0)
                subcall_gas = Op.GAS()
            elif opcode == Op.INVALID:
                opcode_call = Op.INVALID()
                subcall_gas = Op.PUSH2(0xFFFF)
            else:
                raise ValueError(f"Unknown opcode: {opcode}.")

            reentrant_call = Op.MSTORE(0, 2) + Op.SSTORE(
                0, Op.CALL(gas=subcall_gas, address=Op.ADDRESS, args_size=32)
            )

            classdict[f"TSTORE_BEFORE_{opcode._name_}_HAS_NO_EFFECT"] = {
                "description": (
                    f"{opcode._name_} undoes the transient storage write "
                    "from the failed call: "
                    "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), "
                    f"{opcode._name_}, TLOAD(x) returns y.",
                    "Based on [ethereum/tests/.../08_revertUndoes"
                    "TransientStoreFiller.yml](https://github.com/ethereum/"
                    "tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src"
                    "/EIPTestsFiller/StateTests/stEIP1153-transientStorage/"
                    "08_revertUndoesTransientStoreFiller.yml)",
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
                    f"{opcode._name_} undoes all the transient storage writes "
                    "to the same key from a failed call. "
                    "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), "
                    f"TSTORE(x, z + 1) {opcode._name_}, TLOAD(x) returns y."
                    "",
                    "Based on "
                    "[ethereum/tests/.../09_revertUndoesAllFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/09_revertUndoesAllFiller.yml).",
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
                        # store twice and revert/invalid; none of the stores
                        # should take effect
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

            classdict[
                f"{opcode._name_}_UNDOES_TSTORAGE_AFTER_SUCCESSFUL_CALL"
            ] = {
                "description": (
                    f"{opcode._name_} undoes transient storage writes from "
                    "inner calls that successfully returned. "
                    "TSTORE(x, y), CALL(self, ...), CALL(self, ...), "
                    f"TSTORE(x, y + 1), RETURN, {opcode._name_}, TLOAD(x) "
                    "returns y.",
                    "Based on [ethereum/tests/.../"
                    "10_revertUndoesStoreAfterReturnFiller.yml]"
                    "(https://github.com/ethereum/tests/blob/"
                    "9b00b68593f5869eb51a6659e1cc983e875e616b/src/"
                    "EIPTestsFiller/StateTests/stEIP1153-transientStorage/"
                    "10_revertUndoesStoreAfterReturnFiller.yml).",
                ),
                "bytecode": Switch(
                    default_action=(  # setup; make first reentrant sub-call
                        Op.TSTORE(0xFF, 0x100)
                        + Op.SSTORE(2, Op.TLOAD(0xFF))
                        + Op.MSTORE(0, 2)
                        + Op.SSTORE(
                            0,
                            Op.CALL(
                                gas=subcall_gas,
                                address=Op.ADDRESS,
                                args_size=32,
                                ret_offset=32,
                                ret_size=32,
                            ),
                        )
                        + Op.SSTORE(1, Op.MLOAD(32))  # should be 1 (successful
                        # call)
                        + Op.SSTORE(3, Op.TLOAD(0xFF))
                    ),
                    cases=[
                        # the first, reentrant call, which reverts/receives
                        # invalid
                        CalldataCase(
                            value=2,
                            action=(
                                Op.MSTORE(0, 3)
                                + Op.MSTORE(
                                    0,
                                    Op.CALL(address=Op.ADDRESS, args_size=32),
                                )
                                + opcode_call
                            ),
                        ),
                        # the second, reentrant call, which returns
                        # successfully
                        CalldataCase(
                            value=3,
                            action=Op.TSTORE(0xFF, 0x101),
                        ),
                    ],
                ),
                "expected_storage": {
                    0: 0x00,
                    1: second_call_return_value,
                    2: 0x100,
                    3: 0x100,
                },
            }

        return super().__new__(cls, name, bases, classdict)


@unique
class ReentrancyTestCases(
    PytestParameterEnum, metaclass=DynamicReentrancyTestCases
):
    """Transient storage test cases for different reentrancy call contexts."""

    TSTORE_IN_REENTRANT_CALL = {
        "description": (
            "Reentrant calls access the same transient storage: "
            "TSTORE(x, y), CALL(self, ...), TLOAD(x) returns y."
            ""
            "Based on [ethereum/tests/.../05_tloadReentrancyFiller.yml]"
            "(https://github.com/ethereum/tests/tree/"
            "9b00b68593f5869eb51a6659e1cc983e875e616b/src/"
            "EIPTestsFiller/StateTests/stEIP1153-transientStorage).",
        ),
        "bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(
                Op.TSTORE(0, 0x100)
                + REENTRANT_CALL
                + Op.SSTORE(2, Op.TLOAD(0))
            ),
            # reenter
            if_false=Op.SSTORE(1, Op.TLOAD(0)),
        ),
        "expected_storage": {0: 0x01, 1: 0x100, 2: 0x100},
    }
    TLOAD_AFTER_REENTRANT_TSTORE = {
        "description": (
            "Successfully returned calls do not revert transient "
            "storage writes: "
            "TSTORE(x, y), CALL(self, ...), TSTORE(x, z), RETURN, TLOAD(x) "
            "returns z."
            "Based on [ethereum/tests/.../"
            "07_tloadAfterReentrancyStoreFiller.yml](https://github.com/"
            "ethereum/tests/blob/"
            "9b00b68593f5869eb51a6659e1cc983e875e616b/src/"
            "EIPTestsFiller/StateTests/stEIP1153-transientStorage/"
            "07_tloadAfterReentrancyStoreFiller.yml).",
        ),
        "bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(1, Op.TLOAD(0xFF))
                + REENTRANT_CALL
                + Op.SSTORE(2, Op.TLOAD(0xFF))  # test value updated during
                # reentrant call
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
            "Based on [ethereum/tests/.../06_tstoreInReentrancyCallFiller.yml]"
            "(https://github.com/ethereum/tests/blob/"
            "9b00b68593f5869eb51a6659e1cc983e875e616b/src/"
            "EIPTestsFiller/StateTests/stEIP1153-transientStorage/"
            "06_tstoreInReentrancyCallFiller.yml).",
        ),
        "bytecode": Conditional(
            condition=SETUP_CONDITION,
            # setup
            if_true=(
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(1, Op.TLOAD(0xFF))
                + REENTRANT_CALL
                + Op.SSTORE(3, Op.TLOAD(0xFF))  # test value updated during
                # reentrant call
            ),
            # reenter
            if_false=Op.TSTORE(0xFF, 0x101) + Op.SSTORE(2, Op.TLOAD(0xFF)),
        ),
        "expected_storage": {0: 0x01, 1: 0x100, 2: 0x101, 3: 0x101},
    }
    STATICCALL_PROPAGATES_STATIC_FLAG_THROUGH_CALL = {
        "description": (
            "STATICCALL propagates the static flag through a nested "
            "CALL: TSTORE(x, y), STATICCALL(self, ...) -> CALL(self, "
            "...) -> TSTORE(x, z) fails because the static flag "
            "propagates through CALL. TLOAD(x) returns y.",
        ),
        "bytecode": Switch(
            default_action=(
                Op.TSTORE(0, 10)
                + Op.MSTORE(0, 2)
                + Op.SSTORE(
                    0,
                    Op.STATICCALL(
                        gas=500_000,
                        address=Op.ADDRESS,
                        args_size=32,
                        ret_offset=32,
                        ret_size=32,
                    ),
                )
                + Op.SSTORE(1, Op.MLOAD(32))
                + Op.SSTORE(2, Op.TLOAD(0))
            ),
            cases=[
                CalldataCase(
                    value=2,
                    action=(
                        Op.MSTORE(0, 3)
                        + Op.MSTORE(
                            0,
                            Op.CALL(address=Op.ADDRESS, args_size=32),
                        )
                        + Op.RETURN(0, 32)
                    ),
                ),
                CalldataCase(
                    value=3,
                    action=Op.TSTORE(0, 11),
                ),
            ],
        ),
        "expected_storage": {0: 1, 1: 0, 2: 10},
    }
    TSTORE_IN_CALL_THEN_TLOAD_RETURN_IN_STATICCALL = {
        "description": (
            "A reentrant call followed by a reentrant subcall can "
            "call tload correctly: "
            "TSTORE(x, y), CALL(self, ...), STATICCALL(self, ...), "
            "TLOAD(x), RETURN returns y."
            "Based on [ethereum/tests/.../"
            "10_revertUndoesStoreAfterReturnFiller.yml]"
            "(https://github.com/ethereum/tests/blob/"
            "9b00b68593f5869eb51a6659e1cc983e875e616b/src/"
            "EIPTestsFiller/StateTests/stEIP1153-transientStorage/"
            "10_revertUndoesStoreAfterReturnFiller.yml).",
        ),
        "bytecode": Switch(
            default_action=(  # setup; make first reentrant sub-call
                Op.TSTORE(0xFF, 0x100)
                + Op.SSTORE(2, Op.TLOAD(0xFF))
                + Op.MSTORE(0, 2)
                + Op.SSTORE(0, Op.CALL(address=Op.ADDRESS, args_size=32))
                + Op.SSTORE(4, Op.TLOAD(0xFE))
            ),
            cases=[
                # the first, reentrant call which calls tstore and a further
                # reentrant staticcall
                CalldataCase(
                    value=2,
                    action=(
                        Op.TSTORE(0xFE, 0x101)
                        + Op.MSTORE(0, 3)
                        + Op.SSTORE(
                            1,
                            Op.STATICCALL(
                                address=Op.ADDRESS, args_size=32, ret_size=32
                            ),
                        )
                        + Op.SSTORE(3, Op.MLOAD(0))
                    ),
                ),
                # the second, reentrant call, which calls tload and return
                # returns successfully
                CalldataCase(
                    value=3,
                    action=Op.MSTORE(0, Op.TLOAD(0xFE)) + Op.RETURN(0, 32),
                ),
            ],
        ),
        "expected_storage": {0: 0x01, 1: 0x01, 2: 0x100, 3: 0x101, 4: 0x101},
    }


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/Cancun/stEIP1153_transientStorage/10_revertUndoesStoreAfterReturnFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/Cancun/stEIP1153_transientStorage/14_revertAfterNestedStaticcallFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2481"],
)
@ReentrancyTestCases.parametrize()
def test_reentrant_call(
    state_test: StateTestFiller,
    pre: Alloc,
    bytecode: Bytecode,
    expected_storage: Dict,
) -> None:
    """Test transient storage in different reentrancy contexts."""
    env = Environment()

    callee_address = pre.deploy_contract(bytecode)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=callee_address,
        data=Hash(1),
        gas_limit=1_000_000,
    )

    post = {callee_address: Account(code=bytecode, storage=expected_storage)}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
    ids=["call", "callcode", "delegatecall"],
)
@pytest.mark.parametrize(
    "termination,call_b_expected,tload_expected",
    [
        pytest.param(Op.REVERT(0, 0), 0, 0x60A7, id="revert"),
        pytest.param(Op.INVALID(), 0, 0x60A7, id="invalid"),
        pytest.param(Op.STOP, 1, 0xBEEF, id="stop"),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2481"],
)
def test_revert_in_callback_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    termination: Bytecode,
    call_b_expected: int,
    tload_expected: int,
) -> None:
    """
    Test revert propagation across contract boundaries with callbacks.

    Contract A TSTOREs a value, calls B (via parametrized call opcode).
    B calls back to A which TSTOREs a different value, then B terminates.
    If B reverts/invalids, the callback's TSTORE is undone.
    If B stops, the callback's TSTORE persists.
    """
    storage = Storage()

    # B: calls back to A (address from calldata), then terminates.
    b_code = Op.CALL(address=Op.CALLDATALOAD(0)) + termination
    b_address = pre.deploy_contract(b_code)

    # A: entry (CALLDATASIZE > 0) vs callback (CALLDATASIZE == 0).
    a_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=(
            Op.TSTORE(0, 0x60A7)
            + Op.MSTORE(0, Op.ADDRESS)
            + Op.SSTORE(
                storage.store_next(call_b_expected, "call_b_result"),
                call_opcode(gas=500_000, address=b_address, args_size=32),
            )
            + Op.SSTORE(
                storage.store_next(tload_expected, "tload_after"),
                Op.TLOAD(0),
            )
        ),
        if_false=Op.TSTORE(0, 0xBEEF),
    )
    a_address = pre.deploy_contract(a_code, storage=storage.canary())

    sender = pre.fund_eoa()

    state_test(
        env=Environment(),
        pre=pre,
        post={a_address: Account(storage=storage)},
        tx=Transaction(
            sender=sender,
            to=a_address,
            data=Hash(b_address, left_padding=True),
            gas_limit=1_000_000,
        ),
    )


@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
    ids=["call", "callcode", "delegatecall"],
)
@pytest.mark.parametrize(
    "depth",
    [
        pytest.param(4, id="depth_4"),
        pytest.param(16, id="depth_16"),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2481"],
)
def test_tstore_recursive_call(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    depth: int,
) -> None:
    """
    Test transient storage persistence across recursive calls.

    Each recursion level TSTOREs its depth value. At the base case,
    all values are TLOADed and stored in persistent storage to verify
    they survived the recursive call chain.
    """
    storage = Storage()

    # Verification code: SSTORE(slot_i, TLOAD(i)) for each depth.
    verify = Bytecode()
    for i in range(1, depth + 1):
        verify += Op.SSTORE(
            storage.store_next(i, f"tload_{i}"),
            Op.TLOAD(i),
        )

    code = Conditional(
        condition=Op.CALLDATALOAD(0),
        if_true=(
            Op.TSTORE(Op.CALLDATALOAD(0), Op.CALLDATALOAD(0))
            + Op.MSTORE(0, Op.SUB(Op.CALLDATALOAD(0), 1))
            + Op.POP(call_opcode(address=Op.ADDRESS, args_size=32))
        ),
        if_false=verify,
    )

    contract = pre.deploy_contract(code, storage=storage.canary())
    sender = pre.fund_eoa()

    state_test(
        env=Environment(),
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=Transaction(
            sender=sender,
            to=contract,
            data=Hash(depth),
            gas_limit=1_000_000,
        ),
    )
