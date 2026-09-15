"""
Builder exit request tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BuilderExitRequest,
    Op,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    fee_increment_blocks,
)
from execution_testing import Macros as Om
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    # The cases assume the predeploy at its genesis state: no balance and
    # the fee at its minimum.
    pytest.mark.execute(
        pytest.mark.skip(reason="Assumes the predeploy's genesis state")
    ),
]

# The predeploy adds the requests already queued in the block, beyond the
# target, onto the stored excess when it prices a request, so the fee first
# rises after this many requests in a single block.
EXITS_BEFORE_FEE_INCREASE = (
    BuilderExitRequest.target_per_block
    + BuilderExitRequest.get_n_fee_increments(1)[0]
)
assert EXITS_BEFORE_FEE_INCREASE < BuilderExitRequest.max_per_block, (
    "the fee must rise before the per-block cap, or the case below tests "
    "carry-over instead"
)


@EIPChecklist.SystemContract.Test.CallContexts.Normal()
@EIPChecklist.SystemContract.Test.CallContexts.TxEntry()
@EIPChecklist.SystemContract.Test.Inputs.Valid()
@EIPChecklist.SystemContract.Test.Inputs.Invalid()
@EIPChecklist.SystemContract.Test.InputLengths.Static.Correct()
@EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Exact()
@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[BuilderExitRequest(pubkey=0x01)],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[BuilderExitRequest(pubkey=0x01)],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(pubkey=0x01),
                            BuilderExitRequest(pubkey=0x02),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_same_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[BuilderExitRequest(pubkey=0x01)],
                    ),
                    SystemContractInteractionTransaction(
                        requests=[BuilderExitRequest(pubkey=0x02)],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_different_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=i + 1)
                            for i in range(BuilderExitRequest.max_per_block)
                        ],
                    ),
                ],
            ],
            id="single_block_max_builder_exits_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=i + 1)
                            for i in range(
                                BuilderExitRequest.max_per_block * 2 + 1
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_carry_over_builder_exits_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                # No fee paid covers the call value.
                                fee=BuilderExitRequest.get_fee(0) - 1,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_insufficient_fee",
            marks=[
                EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Under(),
                EIPChecklist.SystemContract.Test.Inputs.Invalid.Checks(),
            ],
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                calldata_modifier=lambda x: x[:-1],
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_input_too_short",
            marks=[
                EIPChecklist.SystemContract.Test.Inputs.Invalid.Corrupted(),
                EIPChecklist.SystemContract.Test.InputLengths.Static.TooShort(),
            ],
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                calldata_modifier=lambda x: x + b"\x00",
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_input_too_long",
            marks=[
                EIPChecklist.SystemContract.Test.Inputs.Invalid.Corrupted(),
                EIPChecklist.SystemContract.Test.InputLengths.Static.TooLong(),
            ],
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                # One wei over the fee, kept by the predeploy.
                                fee=BuilderExitRequest.get_fee(0) + 1,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_excess_fee",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[BuilderExitRequest(pubkey=0x00)],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_all_zeros",
            marks=EIPChecklist.SystemContract.Test.Inputs.AllZeros(),
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[BuilderExitRequest(pubkey=2**384 - 1)],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_max_values",
            marks=EIPChecklist.SystemContract.Test.Inputs.MaxValues(),
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                fee=BuilderExitRequest.get_fee(0) - 1,
                                valid=False,
                            ),
                            BuilderExitRequest(pubkey=0x02),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_first_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(pubkey=0x01),
                            BuilderExitRequest(
                                pubkey=0x02,
                                fee=BuilderExitRequest.get_fee(0) - 1,
                                valid=False,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                fee=BuilderExitRequest.get_fee(0) - 1,
                                valid=False,
                            ),
                            BuilderExitRequest(pubkey=0x02),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_contract_first_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x01),
                            BuilderExitRequest(
                                pubkey=0x02,
                                fee=BuilderExitRequest.get_fee(0) - 1,
                                valid=False,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_contract_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x01, valid=False),
                            BuilderExitRequest(pubkey=0x02, valid=False),
                        ],
                        extra_code=Op.REVERT(0, 0),
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_contract_caller_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x01, valid=False),
                            BuilderExitRequest(pubkey=0x02, valid=False),
                        ],
                        extra_code=Om.OOG(),
                    ),
                ],
            ],
            id="single_block_multiple_builder_exits_from_contract_caller_oog",
        ),
        # Depth is not a boundary: the transaction gas cap keeps the stack
        # limit out of reach, so these only show a deep call still queues.
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[BuilderExitRequest(pubkey=0x01)],
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_builder_exit_from_contract_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[BuilderExitRequest(pubkey=0x01)],
                        call_depth=128,
                    ),
                ],
            ],
            id="single_block_single_builder_exit_from_contract_call_depth_high",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=i + 1)
                            for i in range(EXITS_BEFORE_FEE_INCREASE)
                        ]
                        + [
                            # Priced at the fee the earlier requests paid,
                            # which no longer covers the raised fee.
                            BuilderExitRequest(
                                pubkey=EXITS_BEFORE_FEE_INCREASE + 1,
                                fee=BuilderExitRequest.get_fee(0),
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_builder_exit_below_raised_fee",
        ),
        pytest.param(
            fee_increment_blocks(BuilderExitRequest, 50),
            id="multiple_block_fee_increments",
        ),
    ],
)
def test_builder_exit_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
    included_requests: List[List[BuilderExitRequest]],
) -> None:
    """
    Submit builder exit requests, valid and invalid, and verify that exactly
    the accepted ones are dequeued into the blocks' requests with
    `source_address` set to the caller, and that the predeploy keeps exactly
    their fees.
    """
    accepted_value = sum(
        request.value for block in included_requests for request in block
    )
    blockchain_test(
        pre=pre,
        post={
            BuilderExitRequest.system_contract_address: Account(
                balance=accepted_value
            )
        },
        blocks=blocks,
    )


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest.from_index(i + 1)
                            for i in range(
                                BuilderExitRequest.max_per_block + 3
                            )
                        ]
                    )
                ],
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest.from_index(
                                BuilderExitRequest.max_per_block + 4 + i
                            )
                            for i in range(BuilderExitRequest.max_per_block)
                        ]
                    )
                ],
                [],
                # Reuse the drained queue, overwriting old fields with zeros.
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest.from_index(0).copy(pubkey=0)
                        ]
                    )
                ],
                [],
            ],
            id="backlog_then_reuse",
        ),
    ],
)
@EIPChecklist.SystemContract.Test.Inputs.Valid()
def test_builder_exit_backlog_with_new_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """Drain old requests first and reuse the emptied queue."""
    # The third block drains the remaining backlog without new transactions.
    blocks[2].expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            BuilderExitRequest.system_contract_address: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=slot,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1,
                                post_value=0,
                            )
                        ],
                    )
                    for slot in (
                        BuilderExitRequest.queue_head_slot,
                        BuilderExitRequest.queue_tail_slot,
                    )
                ],
            ),
        },
    )
    blockchain_test(pre=pre, blocks=blocks, post={})
