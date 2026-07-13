"""Tests for JUMP and JUMPI with runtime-computed destinations."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_LIMIT = 100_000

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
@pytest.mark.parametrize("opcode", [Op.JUMP, Op.JUMPI])
@pytest.mark.parametrize(
    "dest_kind",
    ["push_data_jumpdest", "push_data_non_jumpdest", "beyond_code"],
)
def test_dynamic_jump_invalid_destination(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    dest_kind: str,
) -> None:
    """
    Jump to an invalid destination taken from calldata and verify the
    exceptional halt: storage stays empty and all gas is consumed.

    The destination comes from calldata, so implementations that
    pre-analyze static PUSH+JUMP pairs must still validate it at
    execution time. Covers landing inside PUSH immediate data (on a 0x5B
    byte and on a non-0x5B byte) and landing far beyond the code size at
    a destination whose 64-bit truncation is a valid JUMPDEST.
    """
    storage = Storage()
    if opcode == Op.JUMP:
        dispatch = Op.JUMP(Op.CALLDATALOAD(0))
    else:
        dispatch = Op.JUMPI(Op.CALLDATALOAD(0), 1)
    fallthrough = (
        Op.SSTORE(storage.store_next(0, "jump not halted"), 1) + Op.STOP
    )
    # PUSH2 data holds a 0x5B byte that must not count as a JUMPDEST.
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
    assert bytes(code)[jumpdest] == Op.JUMPDEST.int()
    dest = {
        "push_data_jumpdest": push_data,
        "push_data_non_jumpdest": push_data + 1,
        # An implementation truncating the destination to 64 bits would
        # land on the valid JUMPDEST and store 2 instead of halting.
        "beyond_code": 2**64 + jumpdest,
    }[dest_kind]

    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(dest),
        gas_limit=GAS_LIMIT,
        expected_receipt={"cumulative_gas_used": GAS_LIMIT},
        protected=fork.supports_protected_txs(),
    )

    state_test(pre=pre, post={contract: Account(storage=storage)}, tx=tx)


@pytest.mark.ported_from(
    [
        f"{LEGACY_VM_TESTS}/jumpi1Filler.json",
    ],
)
@pytest.mark.valid_from("Frontier")
def test_jumpi_not_taken_invalid_destination(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify that a false-condition JUMPI whose static destination is
    invalid does not fail and falls through.

    The condition comes from calldata, so implementations that
    eagerly validate a static JUMPI destination must still skip the
    validation when the branch is not taken.
    """
    storage = Storage()
    fallthrough = Op.SSTORE(storage.store_next(1, "fell through"), 1) + Op.STOP
    dispatch = Op.JUMPI(0, Op.CALLDATALOAD(0))
    stop_offset = len(dispatch + fallthrough) - 1
    dispatch = Op.JUMPI(stop_offset, Op.CALLDATALOAD(0))
    code = dispatch + fallthrough
    assert bytes(code)[stop_offset] == Op.STOP.int()

    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(0),
        protected=fork.supports_protected_txs(),
    )

    state_test(pre=pre, post={contract: Account(storage=storage)}, tx=tx)
