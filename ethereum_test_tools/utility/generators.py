"""Test generator decorators."""

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Generator, List, Protocol

import pytest

from ethereum_test_base_types import Account, Address
from ethereum_test_forks import Fork
from ethereum_test_specs import BlockchainTestFiller
from ethereum_test_specs.blockchain import Block
from ethereum_test_types import Alloc, Transaction


class DeploymentTestType(Enum):
    """Represents the type of deployment test."""

    DEPLOY_BEFORE_FORK = "deploy_before_fork"
    DEPLOY_AFTER_FORK = "deploy_after_fork"


class SystemContractDeployTestFunction(Protocol):
    """
    Represents a function to be decorated with the `generate_system_contract_deploy_test`
    decorator.
    """

    def __call__(
        self,
        *,
        fork: Fork,
        pre: Alloc,
        post: Alloc,
        test_type: DeploymentTestType,
    ) -> Generator[Block, None, None]:
        """
        Args:
            fork (Fork): The fork to test.
            pre (Alloc): The pre state of the blockchain.
            post (Alloc): The post state of the blockchain.
            test_type (DeploymentTestType): The type of deployment test currently being filled.

        Yields:
            Block: To add after the block where the contract was deployed (e.g. can contain extra
            transactions to execute after the system contract has been deployed, and/or a header
            object to verify that the headers are correct).

        """
        ...


def generate_system_contract_deploy_test(
    *,
    fork: Fork,
    tx_json_path: Path,
    expected_deploy_address: Address,
    expected_system_contract_storage: Dict | None = None,
):
    """
    Generate a test that verifies the correct deployment of a system contract.

    Generates two tests:
    - One that deploys the contract before the fork.
    - One that deploys the contract after the fork.

    Args:
        fork (Fork): The fork to test.
        tx_json_path (Path): Path to the JSON file with the transaction to deploy the system
            contract.
            Providing a JSON file is useful to copy-paste the transaction from the EIP.
        expected_deploy_address (Address): The expected address of the deployed contract.
        expected_system_contract_storage (Dict | None): The expected storage of the system
            contract.

    """
    with open(tx_json_path, mode="r") as f:
        tx_json = json.loads(f.read())
    if "gasLimit" not in tx_json and "gas" in tx_json:
        tx_json["gasLimit"] = tx_json["gas"]
        del tx_json["gas"]
    if "protected" not in tx_json:
        tx_json["protected"] = False
    deploy_tx = Transaction.model_validate(tx_json).with_signature_and_sender()  # type: ignore
    gas_price = deploy_tx.gas_price
    assert gas_price is not None
    deployer_required_balance = deploy_tx.gas_limit * gas_price
    deployer_address = deploy_tx.sender

    def decorator(func: SystemContractDeployTestFunction):
        @pytest.mark.parametrize(
            "test_type",
            [
                pytest.param(DeploymentTestType.DEPLOY_BEFORE_FORK),
                pytest.param(DeploymentTestType.DEPLOY_AFTER_FORK),
            ],
            ids=lambda x: x.name.lower(),
        )
        @pytest.mark.execute(pytest.mark.skip(reason="modifies pre-alloc"))
        @pytest.mark.valid_at_transition_to(fork.name())
        def wrapper(
            blockchain_test: BlockchainTestFiller,
            pre: Alloc,
            test_type: DeploymentTestType,
            fork: Fork,
        ):
            assert deployer_address is not None
            assert deploy_tx.created_contract == expected_deploy_address
            blocks: List[Block] = []

            if test_type == DeploymentTestType.DEPLOY_BEFORE_FORK:
                blocks = [
                    Block(  # Deployment block
                        txs=[deploy_tx],
                        timestamp=14_999,
                    ),
                    Block(  # Empty block on fork
                        txs=[],
                        timestamp=15_000,
                    ),
                ]
            elif test_type == DeploymentTestType.DEPLOY_AFTER_FORK:
                blocks = [
                    Block(  # Empty block on fork
                        txs=[],
                        timestamp=15_000,
                    ),
                    Block(  # Deployment block
                        txs=[deploy_tx],
                        timestamp=15_001,
                    ),
                ]

            pre[expected_deploy_address] = Account(
                code=b"",  # Remove the code that is automatically allocated on the fork
                nonce=0,
                balance=0,
            )
            pre[deployer_address] = Account(
                balance=deployer_required_balance,
            )

            expected_deploy_address_int = int.from_bytes(expected_deploy_address, "big")

            post = Alloc()
            fork_pre_allocation = fork.pre_allocation_blockchain()
            assert expected_deploy_address_int in fork_pre_allocation
            expected_code = fork_pre_allocation[expected_deploy_address_int]["code"]
            if expected_system_contract_storage is None:
                post[expected_deploy_address] = Account(
                    code=expected_code,
                    nonce=1,
                )
            else:
                post[expected_deploy_address] = Account(
                    storage=expected_system_contract_storage,
                    code=expected_code,
                    nonce=1,
                )
            post[deployer_address] = Account(
                nonce=1,
            )

            # Extra blocks (if any) returned by the decorated function to add after the
            # contract is deployed.
            blocks += list(func(fork=fork, pre=pre, post=post, test_type=test_type))

            blockchain_test(
                pre=pre,
                blocks=blocks,
                post=post,
            )

        wrapper.__name__ = func.__name__  # type: ignore
        wrapper.__doc__ = func.__doc__  # type: ignore

        return wrapper

    return decorator
