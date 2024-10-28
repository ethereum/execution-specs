"""
abstract: Tests [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251)
    Test execution layer triggered consolidations [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251)

"""  # noqa: E501

from os.path import realpath
from pathlib import Path
from typing import List

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Transaction,
)

from .helpers import ConsolidationRequest, ConsolidationRequestTransaction
from .spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_at_transition_to("Prague")

BLOCKS_BEFORE_FORK = 2


@pytest.mark.parametrize(
    "blocks_consolidation_requests",
    [
        pytest.param(
            [
                [],  # No consolidation requests, but we deploy the contract
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(10),
                                # Pre-fork consolidation request
                                valid=False,
                            )
                        ],
                    ),
                ],
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x03,
                                target_pubkey=0x04,
                                fee=Spec.get_fee(10),
                                # First post-fork consolidation request, will not be included
                                # because the inhibitor is cleared at the end of the block
                                valid=False,
                            )
                        ],
                    ),
                ],
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x05,
                                target_pubkey=0x06,
                                fee=Spec.get_fee(0),
                                # First consolidation that is valid
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
def test_consolidation_requests_during_fork(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
):
    """
    Test making a consolidation request to the beacon chain at the time of the fork.
    """
    # We need to delete the deployed contract that comes by default in the pre state.
    pre[Spec.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS] = Account(
        balance=0,
        code=bytes(),
        nonce=0,
        storage={},
    )

    with open(Path(realpath(__file__)).parent / "contract_deploy_tx.json", mode="r") as f:
        deploy_tx = Transaction.model_validate_json(
            f.read()
        ).with_signature_and_sender()  # type: ignore

    deployer_address = deploy_tx.sender
    assert deployer_address is not None
    assert Address(deployer_address) == Spec.CONSOLIDATION_REQUEST_PREDEPLOY_SENDER

    tx_gas_price = deploy_tx.gas_price
    assert tx_gas_price is not None
    deployer_required_balance = deploy_tx.gas_limit * tx_gas_price

    pre.fund_address(Spec.CONSOLIDATION_REQUEST_PREDEPLOY_SENDER, deployer_required_balance)

    # Append the deployment transaction to the first block
    blocks[0].txs.append(deploy_tx)

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
