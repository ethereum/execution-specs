"""
Measure the gas cost of every SSTORE transition class (cold/warm x
original/current/new value combinations) via inline GAS deltas (by Ori
Pomerantz qbzzt1@gmail.com).

Ported from:
state_tests/stSStoreTest/sstoreGasFiller.yml

@manually-enhanced: Do not overwrite. Costs derive from SSTORE opcode
metadata, so repricings track automatically. Each figure is the whole
measured window (SSTORE plus its two operand pushes), not the bare
opcode the filler stored. Keep `state_gas_reservoir=0`, or EIP-8037
state gas is hidden from `Op.GAS`. Berlin floor: no cold/warm before
EIP-2929.
"""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Bytecode, Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSStoreTest/sstoreGasFiller.yml"],
)
@pytest.mark.valid_from("Berlin")
def test_sstore_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure each SSTORE transition's gas against opcode metadata."""
    sender = pre.fund_eoa()

    # Measured figures land in slots 0x1000+; slots 0-3 are written to.
    gas_slot_base = 0x1000
    # Slots 0 and 1 start at this; later stores write it to 2 and 3.
    stored_value = 0x60A7
    # Cost depends on the zero / non-zero class, not the magnitude.
    nonzero_a = 0xBEEF
    nonzero_b = 0xDEADBEEF
    nonzero_c = 0x1234

    # (slot, value, SSTORE metadata) - `new_value` is always the value.
    # One table drives both the bytecode and the expected costs.
    measurements: list[tuple[int, int, dict[str, Any]]] = [
        # slot 0 cold: nonzero -> other nonzero
        (
            0,
            nonzero_a,
            dict(key_warm=False, original_value=stored_value),
        ),
        # slot 0 warm dirty: nonzero -> nonzero
        (
            0,
            nonzero_b,
            dict(
                key_warm=True,
                original_value=stored_value,
                current_value=nonzero_a,
            ),
        ),
        # slot 0 warm dirty: nonzero -> zero
        (
            0,
            0,
            dict(
                key_warm=True,
                original_value=stored_value,
                current_value=nonzero_b,
            ),
        ),
        # slot 0 warm dirty: zero -> zero
        (
            0,
            0,
            dict(key_warm=True, original_value=stored_value, current_value=0),
        ),
        # slot 0 warm dirty: zero -> nonzero
        (
            0,
            nonzero_c,
            dict(key_warm=True, original_value=stored_value, current_value=0),
        ),
        # slot 1 cold: nonzero -> zero
        (1, 0, dict(key_warm=False, original_value=stored_value)),
        # slot 2 cold fresh: zero -> nonzero
        (2, stored_value, dict(key_warm=False, original_value=0)),
        # slot 3 cold fresh: zero -> zero
        (3, 0, dict(key_warm=False, original_value=0)),
        # slot 3 warm fresh: zero -> nonzero
        (3, stored_value, dict(key_warm=True, original_value=0)),
    ]

    code = Bytecode()
    expected_gas: dict[int, int] = {}
    for index, (slot, value, metadata) in enumerate(measurements):
        store = Op.SSTORE(key=slot, value=value, new_value=value, **metadata)
        gas_slot = gas_slot_base + index
        code += CodeGasMeasure(code=store, sstore_key=gas_slot)
        expected_gas[gas_slot] = store.gas_cost(fork)

    # Clear the working slots; only the gas figures remain.
    for slot in sorted({slot for slot, _, _ in measurements}):
        code += Op.SSTORE(key=slot, value=0)
    code += Op.STOP

    target = pre.deploy_contract(
        code=code,
        storage={0: stored_value, 1: stored_value},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        # Keep EIP-8037 state gas visible to Op.GAS.
        state_gas_reservoir=0,
    )

    post = {target: Account(storage=expected_gas)}

    state_test(pre=pre, post=post, tx=tx)
