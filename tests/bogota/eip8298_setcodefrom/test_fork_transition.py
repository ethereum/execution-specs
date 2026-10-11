"""Fork-transition tests for EIP-8298 (`SETCODEFROM`)."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Transaction,
)

from .helpers import RESULT_SLOT, SENTINEL, SHELL_CODE, TEMPLATE_CODE, word
from .spec import ref_spec_8298

REFERENCE_SPEC_GIT_PATH = ref_spec_8298.git_path
REFERENCE_SPEC_VERSION = ref_spec_8298.version

FORK_TIMESTAMP = 15_000


@EIPChecklist.Opcode.Test.ForkTransition.Invalid()
@EIPChecklist.Opcode.Test.ForkTransition.At()
@pytest.mark.valid_at_transition_to("EIP8298")
def test_setcodefrom_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    template: Address,
) -> None:
    """Verify `SETCODEFROM` halts before the fork and adopts from it on."""
    sender = pre.fund_eoa()
    shells = [
        pre.deploy_contract(SHELL_CODE, storage={RESULT_SLOT: SENTINEL})
        for _ in range(3)
    ]
    blocks = [
        Block(
            timestamp=timestamp,
            txs=[Transaction(sender=sender, to=shell, data=word(template))],
        )
        for timestamp, shell in zip(
            (FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1),
            shells,
            strict=True,
        )
    ]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            # Undefined 0xA7 halts the frame before the SSTORE.
            shells[0]: Account(
                code=SHELL_CODE, storage={RESULT_SLOT: SENTINEL}
            ),
            shells[1]: Account(code=TEMPLATE_CODE, storage={RESULT_SLOT: 1}),
            shells[2]: Account(code=TEMPLATE_CODE, storage={RESULT_SLOT: 1}),
        },
    )
