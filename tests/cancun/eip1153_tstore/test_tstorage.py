"""
EIP-1153 Transient Storage opcode tests.

Ports and extends some tests from
[ethereum/tests/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage).
"""

from enum import unique

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

from . import PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

code_address = 0x100


def test_transient_storage_unset_values(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test that tload returns zero for unset values. Loading an arbitrary value
    is 0 at beginning of transaction: TLOAD(x) is 0.

    Based on
    [ethereum/tests/.../01_tloadBeginningTxnFiller.yml]
    (https://github.com/ethereum/tests/blob/
    9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/
    stEIP1153-transientStorage/01_tloadBeginningTxnFiller.yml)",
    """
    slots_under_test = [0, 1, 2, 2**128, 2**256 - 1]
    code = sum(Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_under_test)

    code_address = pre.deploy_contract(
        code=code,  # type: ignore
        storage=dict.fromkeys(slots_under_test, 1),
    )

    tx = Transaction(sender=pre.fund_eoa(), to=code_address)

    post = {code_address: Account(storage=dict.fromkeys(slots_under_test, 0))}

    state_test(pre=pre, post=post, tx=tx)


def test_tload_after_tstore(state_test: StateTestFiller, pre: Alloc) -> None:
    """
    Loading after storing returns the stored value: TSTORE(x, y), TLOAD(x)
    returns y.

    Based on
    [ethereum/tests/.../02_tloadAfterTstoreFiller.yml]
    (https://github.com/ethereum/tests/blob/
    9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/
    stEIP1153-transientStorage/02_tloadAfterTstoreFiller.yml)",
    """
    slots_under_test = [0, 1, 2, 2**128, 2**256 - 1]
    code = sum(
        Op.TSTORE(slot, slot) + Op.SSTORE(slot, Op.TLOAD(slot))
        for slot in slots_under_test
    )
    code_address = pre.deploy_contract(
        code=code,  # type: ignore
        storage=dict.fromkeys(slots_under_test, 0xFF),
    )

    tx = Transaction(sender=pre.fund_eoa(), to=code_address)

    post = {
        code_address: Account(
            storage={slot: slot for slot in slots_under_test}
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_tload_after_sstore(state_test: StateTestFiller, pre: Alloc) -> None:
    """
    Loading after storing returns the stored value: TSTORE(x, y), TLOAD(x)
    returns y.

    Based on
    [ethereum/tests/.../18_tloadAfterStoreFiller.yml]
    (https://github.com/ethereum/tests/blob/
    9b00b68593f5869eb51a6659e1cc983e875e616b/src/
    EIPTestsFiller/StateTests/stEIP1153-transientStorage/
    18_tloadAfterStoreFiller.yml)",
    """
    slots_under_test = [1, 3, 2**128, 2**256 - 1]
    code = sum(
        Op.SSTORE(slot - 1, 0xFF) + Op.SSTORE(slot, Op.TLOAD(slot - 1))
        for slot in slots_under_test
    )
    code_address = pre.deploy_contract(
        code=code,  # type: ignore
        storage=dict.fromkeys(slots_under_test, 1),
    )

    tx = Transaction(sender=pre.fund_eoa(), to=code_address)

    post = {
        code_address: Account(
            code=code,
            storage={slot - 1: 0xFF for slot in slots_under_test}
            | dict.fromkeys(slots_under_test, 0),
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_tload_after_tstore_is_zero(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test that tload returns zero after tstore is called with zero.

    Based on [ethereum/tests/.../03_tloadAfterStoreIs0Filler.yml]
    (https://github.com/ethereum/tests/blob/
    9b00b68593f5869eb51a6659e1cc983e875e616b/src/
    EIPTestsFiller/StateTests/
    stEIP1153-transientStorage/03_tloadAfterStoreIs0Filler.yml)",
    """
    slots_to_write = [1, 4, 2**128, 2**256 - 2]
    slots_to_read = [slot - 1 for slot in slots_to_write] + [
        slot + 1 for slot in slots_to_write
    ]
    assert set.intersection(set(slots_to_write), set(slots_to_read)) == set()

    code = sum(Op.TSTORE(slot, 1234) for slot in slots_to_write) + sum(
        Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_to_read
    )

    code_address = pre.deploy_contract(
        code=code,  # type: ignore
        storage=dict.fromkeys(slots_to_write + slots_to_read, 0xFFFF),
    )

    tx = Transaction(sender=pre.fund_eoa(), to=code_address)

    post = {
        code_address: Account(
            storage=dict.fromkeys(slots_to_read, 0)
            | dict.fromkeys(slots_to_write, 0xFFFF)
        )
    }

    state_test(pre=pre, post=post, tx=tx)


@unique
class GasMeasureTestCases(PytestParameterEnum):
    """Test cases for gas measurement."""

    TLOAD = {
        "description": "Test that tload() of an empty slot consumes "
        "the expected gas.",
        "bytecode": Op.TLOAD(10),
        "extra_stack_items": 1,
    }
    TSTORE_TLOAD = {
        "description": "Test that tload() of a used slot consumes "
        "the expected gas.",
        "bytecode": Op.TSTORE(10, 10) + Op.TLOAD(10),
        "extra_stack_items": 1,
    }
    TSTORE_COLD = {
        "description": "Test that tstore() of a previously unused "
        "slot consumes the expected gas.",
        "bytecode": Op.TSTORE(10, 10),
        "extra_stack_items": 0,
    }
    TSTORE_WARM = {
        "description": "Test that tstore() of a previously used slot "
        "consumes the expected gas.",
        "bytecode": Op.TSTORE(10, 10) + Op.TSTORE(10, 11),
        "extra_stack_items": 0,
    }


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/Cancun/stEIP1153-transientStorage/17_tstoreGasFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2385"],
)
@GasMeasureTestCases.parametrize()
def test_gas_usage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    bytecode: Bytecode,
    extra_stack_items: int,
) -> None:
    """Test that tstore and tload consume the expected gas."""
    expected_gas = bytecode.gas_cost(fork)
    gas_measure_bytecode = CodeGasMeasure(
        code=bytecode,
        extra_stack_items=extra_stack_items,
    )

    code_address = pre.deploy_contract(code=gas_measure_bytecode)
    tx = Transaction(sender=pre.fund_eoa(), to=code_address)
    post = {
        code_address: Account(
            code=gas_measure_bytecode, storage={0: expected_gas}
        ),
    }
    state_test(pre=pre, tx=tx, post=post)
