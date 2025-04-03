"""
abstract: Tests [EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935).
    Test system contract deployment for [EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935).
"""  # noqa: E501

from os.path import realpath
from pathlib import Path
from typing import Dict

from ethereum_test_forks import Prague
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    DeploymentTestType,
    Transaction,
    generate_system_contract_deploy_test,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, ref_spec_2935

REFERENCE_SPEC_GIT_PATH = ref_spec_2935.git_path
REFERENCE_SPEC_VERSION = ref_spec_2935.version


@generate_system_contract_deploy_test(
    fork=Prague,
    tx_json_path=Path(realpath(__file__)).parent / "contract_deploy_tx.json",
    expected_deploy_address=Address(Spec.HISTORY_STORAGE_ADDRESS),
    fail_on_empty_code=False,
)
def test_system_contract_deployment(
    *,
    pre: Alloc,
    post: Alloc,
    test_type: DeploymentTestType,
    **kwargs,
):
    """Verify deployment of the block hashes system contract."""
    # Deploy a contract that calls the history contract and verifies the block hashes.
    yield Block()  # Empty block just to have more history in the contract.

    # We are going to query blocks even before contract deployment.
    code = (
        sum(
            Op.MSTORE(0, block_number)
            + Op.POP(
                Op.CALL(
                    address=Spec.HISTORY_STORAGE_ADDRESS,
                    args_offset=0,
                    args_size=32,
                    ret_offset=32,
                    ret_size=32,
                ),
            )
            + Op.SSTORE(block_number, Op.ISZERO(Op.ISZERO(Op.MLOAD(32))))
            for block_number in range(1, 4)
        )
        + Op.STOP
    )
    deployed_contract = pre.deploy_contract(code)

    tx = Transaction(
        to=deployed_contract,
        gas_limit=10_000_000,
        sender=pre.fund_eoa(),
    )

    yield Block(txs=[tx])

    storage: Dict
    if test_type == DeploymentTestType.DEPLOY_BEFORE_FORK:
        # Fork happens at block 2, and the contract is already there, so from block number 1 and
        # after, the block hashes should be there.
        storage = {
            1: 1,  # Block prior to the fork, it's the first hash saved.
            2: 1,  # Fork block, hash should be there.
            3: 1,  # Empty block added at the start of this function, hash should be there.
        }
    elif test_type == DeploymentTestType.DEPLOY_ON_FORK_BLOCK:
        # The contract should have the block hashes after contract deployment.
        storage = {
            1: 1,  # Fork and deployment block, the first hash that gets added.
            2: 1,  # Deployment block, hash should be there.
            3: 1,  # Empty block added at the start of this function, hash should be there.
        }
    elif test_type == DeploymentTestType.DEPLOY_AFTER_FORK:
        # The contract should have the block hashes after contract deployment.
        storage = {
            1: 0,  # Fork block, but contract is not there yet.
            2: 1,  # Deployment block, this is the first hash that gets added because it's added on
            # the next block.
            3: 1,  # Empty block added at the start of this function, hash should be there.
        }

    post[deployed_contract] = Account(
        balance=0,
        storage=storage,
    )
