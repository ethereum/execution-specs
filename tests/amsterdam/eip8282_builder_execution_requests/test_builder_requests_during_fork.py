"""
Fork-transition tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from os.path import realpath
from pathlib import Path
from typing import List, Tuple

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
    BuilderDepositRequest,
    BuilderExitRequest,
    FactoryDeployment,
    Header,
    Requests,
    SystemContractInteractionTransaction,
    Transaction,
    TransitionFork,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version


def factory_deployment(factory_json_name: str) -> FactoryDeployment:
    """Load one predeploy's EIP-7997 factory deployment."""
    return FactoryDeployment.model_validate_json(
        (Path(realpath(__file__)).parent / factory_json_name).read_text()
    )


def slot_changes(slot: int, *changes: Tuple[int, int]) -> BalStorageSlot:
    """Return `(block_access_index, post_value)` changes for one slot."""
    return BalStorageSlot(
        slot=slot,
        slot_changes=[
            BalStorageChange(block_access_index=index, post_value=value)
            for index, value in changes
        ],
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@EIPChecklist.SystemContract.Test.ForkTransition.CallBeforeFork()
@EIPChecklist.SystemContract.Test.Deployment.Address()
def test_builder_requests_during_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Deploy both predeploys before the fork, then submit a deposit and an exit
    before, on and after the fork block.

    Only the exit contract's constructor stores the inhibitor that blocks
    requests. A deposit sent before the fork is therefore accepted and sits
    in the queue until the fork block's system call returns it, while every
    exit reverts until that same call clears the inhibitor.
    """
    deposit_predeploy = BuilderDepositRequest.system_contract_address
    exit_predeploy = BuilderExitRequest.system_contract_address
    for predeploy in (deposit_predeploy, exit_predeploy):
        pre[predeploy] = Account(balance=0, code=b"", nonce=0, storage={})
    predeploys = Alloc.model_validate(
        fork.transitions_to().pre_allocation_blockchain()
    )

    deployer = pre.fund_eoa()
    deposit_sender = pre.fund_eoa()
    exit_sender = pre.fund_eoa()
    deposits = [
        BuilderDepositRequest.from_index(i).copy(
            fee=BuilderDepositRequest.get_fee(0)
        )
        for i in range(3)
    ]
    exits = [
        BuilderExitRequest.from_index(i).copy(
            source_address=exit_sender, fee=BuilderExitRequest.get_fee(0)
        )
        for i in range(3)
    ]

    def request_transactions(index: int) -> List[Transaction]:
        return (
            SystemContractInteractionTransaction(
                sender_account=deposit_sender, requests=[deposits[index]]
            ).transactions()
            + SystemContractInteractionTransaction(
                sender_account=exit_sender, requests=[exits[index]]
            ).transactions()
        )

    blocks = [
        Block(
            timestamp=fork.at_timestamp - 2,
            txs=[
                factory_deployment(
                    "builder_deposit_factory_deploy.json"
                ).deploy_transaction(deployer),
                factory_deployment(
                    "builder_exit_factory_deploy.json"
                ).deploy_transaction(deployer),
            ],
            header_verify=Header(requests_hash=Requests()),
        ),
        Block(
            timestamp=fork.at_timestamp - 1,
            txs=request_transactions(0),
            header_verify=Header(requests_hash=Requests()),
        ),
        Block(
            timestamp=fork.at_timestamp,
            txs=request_transactions(1),
            header_verify=Header(
                requests_hash=Requests(deposits[0], deposits[1])
            ),
            # The pre-fork deposit left the count at one; the fork block's
            # system call sweeps both and clears the exit inhibitor.
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    deposit_predeploy: BalAccountExpectation(
                        storage_changes=[
                            slot_changes(
                                BuilderDepositRequest.count_slot,
                                (1, 2),
                                (3, 0),
                            )
                        ],
                    ),
                    exit_predeploy: BalAccountExpectation(
                        storage_changes=[
                            slot_changes(
                                BuilderExitRequest.excess_slot, (3, 0)
                            )
                        ],
                    ),
                }
            ),
        ),
        Block(
            timestamp=fork.at_timestamp + 1,
            txs=request_transactions(2),
            header_verify=Header(
                requests_hash=Requests(deposits[2], exits[2])
            ),
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    deposit_predeploy: BalAccountExpectation(
                        storage_changes=[
                            slot_changes(
                                BuilderDepositRequest.count_slot,
                                (1, 1),
                                (3, 0),
                            )
                        ],
                    ),
                    exit_predeploy: BalAccountExpectation(
                        storage_changes=[
                            slot_changes(
                                BuilderExitRequest.count_slot, (2, 1), (3, 0)
                            )
                        ],
                    ),
                }
            ),
        ),
        Block(
            timestamp=fork.at_timestamp + 2,
            header_verify=Header(requests_hash=Requests()),
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    deposit_predeploy: BalAccountExpectation(
                        storage_changes=[]
                    ),
                    exit_predeploy: BalAccountExpectation(storage_changes=[]),
                }
            ),
        ),
    ]

    # Every deposit was accepted; only the post-fork exit paid its fee.
    post = {}
    for predeploy, balance in (
        (deposit_predeploy, sum(deposit.value for deposit in deposits)),
        (exit_predeploy, exits[2].value),
    ):
        genesis_account = predeploys[predeploy]
        assert genesis_account is not None
        post[predeploy] = Account(
            nonce=1, code=genesis_account.code, balance=balance
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)
