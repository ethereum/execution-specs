"""
Builder exit request tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
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

pytestmark = pytest.mark.valid_from("Amsterdam")


@EIPChecklist.SystemContract.Test.CallContexts.Normal()
@EIPChecklist.SystemContract.Test.CallContexts.TxEntry()
@EIPChecklist.SystemContract.Test.Inputs.Valid()
@EIPChecklist.SystemContract.Test.Inputs.Invalid()
@EIPChecklist.SystemContract.Test.Inputs.Invalid.Checks()
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
                                fee=0,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_exit_insufficient_fee",
            marks=EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Under(),
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
                                pubkey=0x01, fee=0, valid=False
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
                                pubkey=0x02, fee=0, valid=False
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
                                pubkey=0x01, fee=0, valid=False
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
                                pubkey=0x02, fee=0, valid=False
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
                            BuilderExitRequest(pubkey=0x01, valid=False)
                        ],
                        call_type=Op.DELEGATECALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x02, valid=False)
                        ],
                        call_type=Op.STATICCALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x03, valid=False)
                        ],
                        call_type=Op.CALLCODE,
                    ),
                ],
            ],
            id="single_block_single_builder_exit_delegatecall_staticcall_callcode",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x01, valid=False)
                        ],
                        call_type=Op.DELEGATECALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x02, valid=False)
                        ],
                        call_type=Op.STATICCALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x03, valid=False)
                        ],
                        call_type=Op.CALLCODE,
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_builder_exit_delegatecall_staticcall_callcode_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x01, valid=False)
                        ],
                        call_type=Op.DELEGATECALL,
                        call_depth=128,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x02, valid=False)
                        ],
                        call_type=Op.STATICCALL,
                        call_depth=128,
                    ),
                    SystemContractInteractionContract(
                        requests=[
                            BuilderExitRequest(pubkey=0x03, valid=False)
                        ],
                        call_type=Op.CALLCODE,
                        call_depth=128,
                    ),
                ],
            ],
            id="single_block_single_builder_exit_delegatecall_staticcall_callcode_call_depth_high",
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
) -> None:
    """
    Test submitting valid builder exit requests to the builder exit predeploy
    and verifying they are dequeued into the block's requests, with
    `source_address` set to the caller.
    """
    blockchain_test(pre=pre, post={}, blocks=blocks)
