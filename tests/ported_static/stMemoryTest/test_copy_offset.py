"""
Test CODECOPY / CALLDATACOPY reading from an out-of-bounds source offset,
which yields zeros.

Ported from:
state_tests/stMemoryTest/codeCopyOffsetFiller.json
state_tests/stMemoryTest/callDataCopyOffsetFiller.json

@manually-enhanced: Do not overwrite. CODECOPY/CALLDATACOPY OOB-offset
zero-fill folded into one parametrize; delivery-CALL dropped; dynamic
addresses; nonzero tx calldata so a wrong in-bounds offset is observable.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Copy 16 bytes from a source offset far past the end of code/calldata; the
# out-of-bounds region reads as zeros, which overwrite memory bytes 0..15
# (the most-significant half of the word MLOAD reads back), leaving only the
# low 128 bits of the pre-filled word set to 0xFF.
OOB_OFFSET = 0xFFFF
COPY_SIZE = 0x10
EXPECTED = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
# Nonzero calldata makes the CALLDATACOPY arm discriminate a wrong (in-bounds)
# source offset from the correct out-of-bounds zero-fill; with empty calldata
# every offset would read zeros and the assertion would be vacuous.
TX_DATA = bytes(range(1, 33))


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryTest/codeCopyOffsetFiller.json",
        "state_tests/stMemoryTest/callDataCopyOffsetFiller.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "copy_op",
    [
        pytest.param(Op.CODECOPY, id="code_copy_offset"),
        pytest.param(Op.CALLDATACOPY, id="call_data_copy_offset"),
    ],
)
def test_copy_offset(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    copy_op: Op,
) -> None:
    """Copying from an out-of-bounds source offset yields zeros."""
    contract = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=(1 << 256) - 1)
        + copy_op(dest_offset=0x0, offset=OOB_OFFSET, size=COPY_SIZE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=TX_DATA,
        protected=fork.supports_protected_txs(),
    )

    post = {contract: Account(storage={0: EXPECTED})}

    state_test(pre=pre, post=post, tx=tx)
