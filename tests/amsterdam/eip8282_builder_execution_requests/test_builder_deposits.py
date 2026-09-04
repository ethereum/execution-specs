"""
Builder deposit request tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderDepositRequest,
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

MIN_DEPOSIT_GWEI = BuilderDepositRequest.min_deposit_wei // 10**9


def minimum_deposit(
    pubkey: int,
    amount: int = MIN_DEPOSIT_GWEI,
    *,
    valid: bool = True,
    extra_wei: int = 0,
) -> BuilderDepositRequest:
    """Build a deposit with fixed credentials and signature."""
    return BuilderDepositRequest(
        pubkey=pubkey,
        withdrawal_credentials=0x02,
        amount=amount,
        signature=0x03,
        valid=valid,
        extra_wei=extra_wei,
    )


@EIPChecklist.SystemContract.Test.CallContexts.Normal()
@EIPChecklist.SystemContract.Test.CallContexts.TxEntry()
@EIPChecklist.SystemContract.Test.Inputs.Valid()
@EIPChecklist.SystemContract.Test.Inputs.Boundary()
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
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_from_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                # A top-up of more than the minimum stake.
                                amount=32 * MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_above_minimum",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            ),
                            BuilderDepositRequest(
                                pubkey=0x04,
                                withdrawal_credentials=0x05,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x06,
                            ),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_same_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x04,
                                withdrawal_credentials=0x05,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x06,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_different_eoa",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=i + 1,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                            for i in range(BuilderDepositRequest.max_per_block)
                        ],
                    ),
                ],
            ],
            id="single_block_max_builder_deposits_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=i + 1,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                            for i in range(
                                BuilderDepositRequest.max_per_block + 1
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_carry_over_builder_deposits_from_contract",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                # One gwei below the minimum stake.
                                amount=MIN_DEPOSIT_GWEI - 1,
                                signature=0x03,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_below_minimum",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                # One wei short of `fee + amount * 1 gwei`.
                                extra_wei=-1,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_insufficient_value",
            marks=EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Under(),
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                calldata_modifier=lambda x: x[:-1],
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_input_too_short",
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
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                                calldata_modifier=lambda x: x + b"\x00",
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_input_too_long",
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
                            # One wei over `fee + amount * 1 gwei`, kept by
                            # the predeploy.
                            minimum_deposit(0x01, extra_wei=1),
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_excess_value",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x00,
                                withdrawal_credentials=0x00,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x00,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_zero_fields",
            marks=EIPChecklist.SystemContract.Test.Inputs.AllZeros(),
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x00,
                                withdrawal_credentials=0x00,
                                amount=0,
                                signature=0x00,
                                valid=False,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_all_zeros",
            marks=EIPChecklist.SystemContract.Test.Inputs.AllZeros(),
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=2**384 - 1,
                                withdrawal_credentials=2**256 - 1,
                                amount=2**64 - 1,
                                signature=2**768 - 1,
                            )
                        ],
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_max_values",
            marks=[
                pytest.mark.execute(
                    pytest.mark.skip(reason="Stakes 2**64 - 1 gwei")
                ),
                EIPChecklist.SystemContract.Test.Inputs.MaxValues(),
            ],
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            minimum_deposit(0x01, amount=0, valid=False),
                            minimum_deposit(0x04),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_first_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            minimum_deposit(0x01),
                            minimum_deposit(0x04, amount=0, valid=False),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            minimum_deposit(0x01, amount=0, valid=False),
                            minimum_deposit(0x04),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_contract_first_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            minimum_deposit(0x01),
                            minimum_deposit(0x04, amount=0, valid=False),
                        ],
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_contract_last_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            minimum_deposit(0x01, valid=False),
                            minimum_deposit(0x04, valid=False),
                        ],
                        extra_code=Op.REVERT(0, 0),
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_contract_caller_reverts",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            minimum_deposit(0x01, valid=False),
                            minimum_deposit(0x04, valid=False),
                        ],
                        extra_code=Om.OOG(),
                    ),
                ],
            ],
            id="single_block_multiple_builder_deposits_from_contract_caller_oog",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x01)],
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_from_contract_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x01)],
                        call_depth=128,
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_from_contract_call_depth_high",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x01, valid=False)],
                        call_type=Op.DELEGATECALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x02, valid=False)],
                        call_type=Op.STATICCALL,
                    ),
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x03, valid=False)],
                        call_type=Op.CALLCODE,
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_delegatecall_staticcall_callcode",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x01, valid=False)],
                        call_type=Op.DELEGATECALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x02, valid=False)],
                        call_type=Op.STATICCALL,
                        call_depth=3,
                    ),
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x03, valid=False)],
                        call_type=Op.CALLCODE,
                        call_depth=3,
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_delegatecall_staticcall_callcode_call_depth_3",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x01, valid=False)],
                        call_type=Op.DELEGATECALL,
                        call_depth=128,
                    ),
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x02, valid=False)],
                        call_type=Op.STATICCALL,
                        call_depth=128,
                    ),
                    SystemContractInteractionContract(
                        requests=[minimum_deposit(0x03, valid=False)],
                        call_type=Op.CALLCODE,
                        call_depth=128,
                    ),
                ],
            ],
            id="single_block_single_builder_deposit_delegatecall_staticcall_callcode_call_depth_high",
        ),
        pytest.param(
            fee_increment_blocks(BuilderDepositRequest, 50),
            id="multiple_block_fee_increments",
            marks=pytest.mark.execute(
                pytest.mark.skip(reason="Stakes hundreds of ETH")
            ),
        ),
    ],
)
def test_builder_deposit_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """
    Test submitting valid builder deposit requests to the builder deposit
    predeploy and verifying they are dequeued into the block's requests.
    """
    blockchain_test(pre=pre, post={}, blocks=blocks)
