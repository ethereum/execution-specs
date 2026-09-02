"""
Tests [EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""  # noqa: E501

from os.path import realpath
from pathlib import Path
from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderExitRequest,
    SystemContractInteractionTransaction,
    Transaction,
)

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [
    pytest.mark.skip(
        reason="EIP-8282 draft: builder predeploy deploy transactions are not "
        "yet defined (placeholder devnet-6 genesis addresses)."
    ),
    pytest.mark.valid_at_transition_to("Amsterdam"),
]

BLOCKS_BEFORE_FORK = 2


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [],  # No builder exit requests, but we deploy the contract
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x01,
                                fee=BuilderExitRequest.get_fee(10),
                                # Pre-fork builder exit request
                                valid=False,
                            )
                        ],
                    ),
                ],
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x02,
                                fee=BuilderExitRequest.get_fee(10),
                                # First post-fork builder exit request, will
                                # not be included because the inhibitor is
                                # cleared at the end of the block
                                valid=False,
                            )
                        ],
                    ),
                ],
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderExitRequest(
                                pubkey=0x03,
                                # First builder exit request that is valid
                                valid=True,
                            )
                        ],
                    ),
                ],
            ],
            id="one_valid_request_second_block_after_fork",
        ),
    ],
)
@pytest.mark.parametrize("timestamp", [15_000 - BLOCKS_BEFORE_FORK], ids=[""])
@pytest.mark.pre_alloc_mutable
def test_builder_requests_during_fork(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """
    Test making a builder exit request to the beacon chain at the time of the
    fork.
    """
    # We need to delete the deployed contract that comes by default in the pre
    # state.
    pre[BuilderExitRequest.system_contract_address] = Account(
        balance=0,
        code=bytes(),
        nonce=0,
        storage={},
    )

    with open(
        Path(realpath(__file__)).parent / "builder_exit_deploy_tx.json",
        mode="r",
    ) as f:
        deploy_tx = Transaction.model_validate_json(
            f.read()
        ).with_signature_and_sender()

    deployer_address = deploy_tx.sender
    assert deployer_address is not None

    tx_gas_price = deploy_tx.gas_price
    assert tx_gas_price is not None
    deployer_required_balance = deploy_tx.gas_limit * tx_gas_price

    pre.fund_address(deployer_address, deployer_required_balance)

    # Append the deployment transaction to the first block
    blocks[0].txs.append(deploy_tx)

    blockchain_test(pre=pre, post={}, blocks=blocks)
