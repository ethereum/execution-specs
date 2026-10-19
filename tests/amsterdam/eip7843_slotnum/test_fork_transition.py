"""Tests for EIP-7843 fork transition behavior."""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    EngineAPIError,
    Header,
    Op,
    Transaction,
)

from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version

FORK_TIMESTAMP = 15_000


@EIPChecklist.Opcode.Test.ForkTransition.Invalid()
@EIPChecklist.Opcode.Test.ForkTransition.At()
@EIPChecklist.BlockHeaderField.Test.ForkTransition.Initial()
@pytest.mark.valid_at_transition_to("EIP7843")
def test_slotnum_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SLOTNUM behavior across the EIP-7843 fork transition.

    Before EIP-7843, opcode 0x4B is undefined: execution halts with an
    invalid-opcode exception and consumes all gas, so no SSTORE is observed.

    From EIP-7843 onward, SLOTNUM pushes the block's slot number provided
    by the consensus layer and the SSTORE succeeds.

    The contract keys storage by block number so each block's outcome is
    independently visible in the final post-state:

    * block 1 (pre-fork): slot 1 stays 0 — execution halted before SSTORE.
    * block 2 (transition): slot 2 == ``at_fork_slot``.
    * block 3 (post-fork): slot 3 == ``post_fork_slot``.
    """
    sender = pre.fund_eoa()
    code = Op.SSTORE(Op.NUMBER, Op.SLOTNUM, new_value=1) + Op.STOP
    contract = pre.deploy_contract(code)

    at_fork_slot = 200
    post_fork_slot = 201

    blocks = [
        Block(
            timestamp=ts,
            slot_number=slot,
            txs=[Transaction(sender=sender, to=contract)],
        )
        for ts, slot in [
            (FORK_TIMESTAMP - 1, None),
            (FORK_TIMESTAMP, at_fork_slot),
            (FORK_TIMESTAMP + 1, post_fork_slot),
        ]
    ]
    post = {
        contract: Account(
            storage={
                1: 0,
                2: at_fork_slot,
                3: post_fork_slot,
            },
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.BlockHeaderField.Test.ForkTransition.Before()
@pytest.mark.valid_at_transition_to("EIP7843")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "block_kwargs",
    [
        pytest.param(
            {"rlp_modifier": Header(slot_number=0)},
            id="header_field",
        ),
        pytest.param(
            {"engine_new_payload_slot_number": 0},
            id="engine_payload_field",
            marks=pytest.mark.blockchain_test_engine_only,
        ),
    ],
)
def test_invalid_pre_fork_block_with_slot_number(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_kwargs: dict[str, Any],
) -> None:
    """
    Reject a pre-fork block that carries the slot number field in its
    header or its engine `newPayload`.

    The field must not be present before the fork activates: the extra
    header field changes the header shape, while in the payload case
    the block is otherwise valid, so clients that silently drop
    unknown payload fields would answer VALID and must fail this test.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=receiver, value=100)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP - 1,
                txs=[tx],
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                engine_api_error_code=EngineAPIError.InvalidParams,
                **block_kwargs,
            ),
        ],
    )


@EIPChecklist.BlockHeaderField.Test.ForkTransition.After()
@pytest.mark.valid_at_transition_to("EIP7843")
@pytest.mark.exception_test
def test_invalid_post_fork_block_without_slot_number(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject an activation block whose header lacks the `slot_number`
    field.

    From the fork activation onward the field is mandatory: a header
    without it is malformed and the engine payload is missing a
    parameter required by its version.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=receiver, value=100)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                rlp_modifier=Header(slot_number=Header.REMOVE_FIELD),
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                engine_api_error_code=EngineAPIError.InvalidParams,
            ),
        ],
    )
