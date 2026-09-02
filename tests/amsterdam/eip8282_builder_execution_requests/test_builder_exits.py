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
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = pytest.mark.valid_from("Amsterdam")


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
