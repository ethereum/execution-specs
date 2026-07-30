"""
Tests for JUMP and JUMPI with runtime-computed destinations or conditions.
"""

from typing import Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_LIMIT = 100_000

DESTINATION_SLOT = 0xDE

DESTINATION_KINDS = [
    "push_data_jumpdest",
    "push_data_non_jumpdest",
    "one_past_code",
    "jumpdest_alias_2_64",
    "max_u256",
]

LEGACY_VM_TESTS = (
    "https://github.com/ethereum/legacytests/blob/master/"
    "src/LegacyTests/Constantinople/VMTestsFiller/vmIOandFlowOperations"
)


@pytest.mark.ported_from(
    [
        f"{LEGACY_VM_TESTS}/DynamicJumpInsidePushWithJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpInsidePushWithoutJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpifInsidePushWithJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpifInsidePushWithoutJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpiOutsideBoundaryFiller.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpJD_DependsOnJumps0Filler.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpPathologicalTest1Filler.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpPathologicalTest2Filler.json",
        f"{LEGACY_VM_TESTS}/DynamicJumpPathologicalTest3Filler.json",
        f"{LEGACY_VM_TESTS}/BlockNumberDynamicJumpInsidePushWithJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/BlockNumberDynamicJumpInsidePushWithoutJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/BlockNumberDynamicJumpifInsidePushWithJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/BlockNumberDynamicJumpifInsidePushWithoutJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/BlockNumberDynamicJumpiOutsideBoundaryFiller.json",
        f"{LEGACY_VM_TESTS}/JDfromStorageDynamicJumpInsidePushWithJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/JDfromStorageDynamicJumpInsidePushWithoutJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/JDfromStorageDynamicJumpifInsidePushWithJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/JDfromStorageDynamicJumpifInsidePushWithoutJumpDestFiller.json",
        f"{LEGACY_VM_TESTS}/JDfromStorageDynamicJumpiOutsideBoundaryFiller.json",
        f"{LEGACY_VM_TESTS}/bad_indirect_jump2Filler.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "opcode,condition",
    [
        pytest.param(Op.JUMP, (), id="jump"),
        pytest.param(Op.JUMPI, (1,), id="jumpi"),
    ],
)
@pytest.mark.parametrize(
    "dest_source,dest_kind",
    [
        (source, kind)
        for source in ("calldata", "storage", "number")
        for kind in DESTINATION_KINDS
    ],
)
def test_dynamic_jump_invalid_destination(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    condition: Tuple[int, ...],
    dest_source: str,
    dest_kind: str,
) -> None:
    """
    Jump to an invalid destination computed at run time and verify the
    exceptional halt: storage stays empty and all gas is consumed.

    The destination is never a static PUSH, so implementations that
    pre-analyze PUSH+JUMP pairs must still validate it at execution time.
    It is read from calldata, read from storage, or derived from the
    block number, and it lands inside PUSH immediate data (on a 0x5B byte
    and on a non-0x5B byte), one byte past the code, at an offset whose
    truncation to 64 bits is a valid JUMPDEST, or at the maximum word.
    """
    env = Environment()
    storage = Storage()
    dest_expression = {
        "calldata": Op.CALLDATALOAD(0),
        "storage": Op.SLOAD(DESTINATION_SLOT),
        "number": Op.ADD(Op.NUMBER, Op.CALLDATALOAD(0)),
    }[dest_source]
    dispatch = opcode(dest_expression, *condition)
    fallthrough = (
        Op.SSTORE(storage.store_next(0, "jump not halted"), 1) + Op.STOP
    )
    island = Op.PUSH2(0x5B00) + Op.POP
    code = (
        dispatch
        + fallthrough
        + island
        + Op.JUMPDEST
        + Op.SSTORE(storage.store_next(0, "invalid destination taken"), 2)
        + Op.STOP
    )
    push_data = len(dispatch + fallthrough) + 1
    jumpdest = len(dispatch + fallthrough + island)
    assert bytes(code)[push_data] == Op.JUMPDEST.int()
    assert bytes(code)[push_data + 1] != Op.JUMPDEST.int()
    assert bytes(code)[jumpdest] == Op.JUMPDEST.int()
    dest = {
        "push_data_jumpdest": push_data,
        "push_data_non_jumpdest": push_data + 1,
        "one_past_code": len(code),
        "jumpdest_alias_2_64": 2**64 + jumpdest,
        "max_u256": 2**256 - 1,
    }[dest_kind]

    initial_storage = Storage()
    if dest_source == "storage":
        initial_storage[DESTINATION_SLOT] = dest
        storage[DESTINATION_SLOT] = dest
    contract = pre.deploy_contract(code, storage=initial_storage)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data={
            "calldata": Hash(dest),
            "storage": b"",
            "number": Hash(dest - env.number),
        }[dest_source],
        gas_limit=GAS_LIMIT,
        expected_receipt=TransactionReceipt(cumulative_gas_used=GAS_LIMIT),
        protected=fork.supports_protected_txs(),
    )

    state_test(
        env=env, pre=pre, post={contract: Account(storage=storage)}, tx=tx
    )


@pytest.mark.ported_from(
    [
        f"{LEGACY_VM_TESTS}/jumpi1Filler.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "dest",
    [pytest.param(1, id="push_data"), pytest.param(2**256 - 1, id="max_u256")],
)
def test_jumpi_not_taken_invalid_destination(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    dest: int,
) -> None:
    """
    Verify that a false-condition JUMPI whose destination is invalid does
    not fail and falls through.

    The condition comes from calldata, so implementations that eagerly
    validate a static JUMPI destination must still skip the validation
    when the branch is not taken. The code holds no JUMPDEST at all, so
    both an in-code destination inside PUSH immediate data and one past
    the maximum code size are invalid.
    """
    storage = Storage()
    code = (
        Op.JUMPI(dest, Op.CALLDATALOAD(0))
        + Op.SSTORE(storage.store_next(1, "fell through"), 1)
        + Op.STOP
    )
    assert Op.JUMPDEST.int() not in bytes(code)

    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(0),
        protected=fork.supports_protected_txs(),
    )

    state_test(pre=pre, post={contract: Account(storage=storage)}, tx=tx)
