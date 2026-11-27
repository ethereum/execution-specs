"""
Test SSTORE and SLOAD.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/sstore_sloadFiller.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

Each case is a sequence of steps: a `Store` writes a value to a slot, and a
`Copy` stores the value SLOAD reads from one slot into another. The keys
and values reach the stack from PUSH data (static) or calldata (dynamic),
and the expected storage comes from replaying the steps on a dictionary.
Every slot a step writes starts at `SENTINEL`, and one slot holds a value
from the pre-state, so a copy can read storage the transaction never
wrote.
"""

from typing import NamedTuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.helpers import Operands

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmIOandFlowOperations/sstore_sloadFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
]

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1
PRE_STATE_SLOT = 0x50
PRE_STATE_VALUE = 0x5E7
UNWRITTEN_SLOT = 100


class Store(NamedTuple):
    """Write `value` to `key`."""

    key: int
    value: int

    def code(self, operands: Operands) -> Bytecode:
        """Return the SSTORE performing this step."""
        return Op.SSTORE(operands(self.key), operands(self.value))

    def apply(self, storage: dict[int, int]) -> None:
        """Apply this step to the `storage` model."""
        storage[self.key] = self.value

    @property
    def written_key(self) -> int:
        """Return the slot this step writes."""
        return self.key


class Copy(NamedTuple):
    """Store the value SLOAD reads from `source` into `dest`."""

    source: int
    dest: int

    def code(self, operands: Operands) -> Bytecode:
        """Return the SSTORE of the SLOAD performing this step."""
        return Op.SSTORE(operands(self.dest), Op.SLOAD(operands(self.source)))

    def apply(self, storage: dict[int, int]) -> None:
        """Apply this step to the `storage` model."""
        storage[self.dest] = storage.get(self.source, 0)

    @property
    def written_key(self) -> int:
        """Return the slot this step writes."""
        return self.dest


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


@pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str)
@pytest.mark.parametrize(
    "steps",
    [
        pytest.param(
            [Store(0, 0xFF), Store(10, 0xEE), Copy(0, 20)],
            id="copy_written_slot",
        ),
        pytest.param(
            [Store(0, 0xFF), Store(10, 0xEE), Copy(UNWRITTEN_SLOT, 20)],
            id="copy_unwritten_slot",
        ),
        pytest.param(
            [
                Store(0, 0xFF),
                Store(1, 0xEE),
                Store(2, 0xDD),
                Copy(1, 10),
                Copy(2, 20),
            ],
            id="copy_two_slots",
        ),
        pytest.param([Copy(PRE_STATE_SLOT, 20)], id="copy_pre_state_slot"),
        # SLOAD sees the latest write to the slot.
        pytest.param(
            [Store(0, 0xFF), Store(0, 0xEE), Copy(0, 20)],
            id="overwrite_then_copy",
        ),
        # The copy keeps the value read, not a reference to the slot.
        pytest.param(
            [Store(0, 0xFF), Copy(0, 20), Store(0, 0xEE)],
            id="copy_then_overwrite_source",
        ),
        # Writing zero clears the slot.
        pytest.param([Store(0, 0)], id="store_zero"),
        # Each value differs from its key, so a copy of the key itself
        # cannot pass for the loaded value.
        pytest.param(
            [Store(MAX_UINT, MAX_UINT - 1), Copy(MAX_UINT, 20)],
            id="max_key",
        ),
        pytest.param(
            [Store(MAX_UINT - 1, MAX_UINT), Copy(MAX_UINT - 1, 20)],
            id="max_value",
        ),
    ],
)
def test_sstore_sload(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    steps: list[Store | Copy],
    operands: Operands,
) -> None:
    """Run the SSTORE and SLOAD steps and check the resulting storage."""
    pre_storage: dict = {PRE_STATE_SLOT: PRE_STATE_VALUE}
    pre_storage |= {step.written_key: SENTINEL for step in steps}

    code = Bytecode()
    storage = dict(pre_storage)
    for step in steps:
        code += step.code(operands)
        step.apply(storage)
    code += Op.STOP

    contract = pre.deploy_contract(code=code, storage=pre_storage)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
