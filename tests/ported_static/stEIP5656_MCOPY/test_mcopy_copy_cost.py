"""
Test cases for the cost of memory copy in the MCOPY instruction.

Ported from:
state_tests/Cancun/stEIP5656_MCOPY/MCOPY_copy_costFiller.yml

@manually-enhanced: Do not overwrite. The ported filler probed MCOPY cost via a
tight OOG gas boundary (55697); EIP-8037 reprices the instrumentation SSTORE
into state gas, breaking that boundary. Reframed to measure the MCOPY copy cost
directly with CodeGasMeasure over a pre-expanded memory (so no expansion is
charged), asserting the fork-derived `mcopy.gas_cost(fork)`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_SLOT = 0x0
# MSTORE at this offset grows memory to PREEXPANDED bytes, covering every
# (src, size) copy region below so the measured MCOPY never expands memory.
PREEXPAND_OFFSET = 0xAF00
PREEXPANDED = PREEXPAND_OFFSET + 0x20  # 44832 bytes = 1401 words

SRCS = [0x0, 0x1, 0x1F, 0x20]
SIZES = [0x0, 0x1, 0x1F, 0x20, 0x21, 0xAEDF, 0xAEE0, 0xAEE1]


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP5656_MCOPY/MCOPY_copy_costFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"size{s}")
@pytest.mark.parametrize("src", SRCS, ids=lambda s: f"src{s}")
def test_mcopy_copy_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    src: int,
    size: int,
) -> None:
    """Measure the MCOPY copy cost (linear in size, independent of source)."""
    # Memory is pre-expanded past the largest copy region, so the measured
    # MCOPY charges only its base + per-word copy cost, never expansion.
    mcopy = Op.MCOPY(
        dest_offset=0x0,
        offset=src,
        size=size,
        data_size=size,
        old_memory_size=PREEXPANDED,
        new_memory_size=PREEXPANDED,
    )
    contract = pre.deploy_contract(
        code=Op.MSTORE(offset=PREEXPAND_OFFSET, value=0x1)
        + CodeGasMeasure(
            code=mcopy,
            extra_stack_items=0,
            sstore_key=GAS_SLOT,
        ),
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    post = {contract: Account(storage={GAS_SLOT: mcopy.gas_cost(fork)})}

    state_test(pre=pre, post=post, tx=tx)
