"""Test generator decorators."""

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Generator, List, Protocol

import pytest

from ethereum_test_base_types import Account, Address, Hash
from ethereum_test_exceptions import BlockException
from ethereum_test_forks import Fork
from ethereum_test_specs import BlockchainTestFiller
from ethereum_test_specs.blockchain import Block
from ethereum_test_types import Alloc, Transaction


class DeploymentTestType(Enum):
    """Represents the type of deployment test."""

    DEPLOY_BEFORE_FORK = "deploy_before_fork"
    DEPLOY_ON_FORK_BLOCK = "deploy_on_fork_block"
    DEPLOY_AFTER_FORK = "deploy_after_fork"


class ContractAddressHasBalance(Enum):
    """Represents whether the target deployment test has a balance before deployment."""

    ZERO_BALANCE = "zero_balance"
    NONZERO_BALANCE = "nonzero_balance"


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
    fail_on_empty_code: bool,
    expected_system_contract_storage: Dict | None = None,
):
    """
    Generate a test that verifies the correct deployment of a system contract.

    Generates following test cases:

                                          | before/after fork | fail on     | invalid block |
                                          |                   | empty block |               |
    --------------------------------------|-------------------|-------------|---------------|
    `deploy_before_fork-nonzero_balance`  | before            | False       | False         |
    `deploy_before_fork-zero_balance`     | before            | True        | False         |
    `deploy_on_fork_block-nonzero_balance`| on fork block     | False       | False         |
    `deploy_on_fork_block-zero_balance`   | on fork block     | True        | False         |
    `deploy_after_fork-nonzero_balance`   | after             | False       | False         |
    `deploy_after_fork-zero_balance`      | after             | True        | True          |

    The `has balance` parametrization does not have an effect on the expectation of the test.

    Args:
        fork (Fork): The fork to test.
        tx_json_path (Path): Path to the JSON file with the transaction to deploy the system
            contract.
            Providing a JSON file is useful to copy-paste the transaction from the EIP.
        expected_deploy_address (Address): The expected address of the deployed contract.
        fail_on_empty_code (bool): If True, the test is expected to fail on empty code.
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
    if "hash" in tx_json:
        assert deploy_tx.hash == Hash(tx_json["hash"])
    if "sender" in tx_json:
        assert deploy_tx.sender == Address(tx_json["sender"])

    def decorator(func: SystemContractDeployTestFunction):
        @pytest.mark.parametrize(
            "has_balance",
            [
                pytest.param(ContractAddressHasBalance.NONZERO_BALANCE),
                pytest.param(ContractAddressHasBalance.ZERO_BALANCE),
            ],
            ids=lambda x: x.name.lower(),
        )
        @pytest.mark.parametrize(
            "test_type",
            [
                pytest.param(DeploymentTestType.DEPLOY_BEFORE_FORK),
                pytest.param(DeploymentTestType.DEPLOY_ON_FORK_BLOCK),
                pytest.param(
                    DeploymentTestType.DEPLOY_AFTER_FORK,
                    marks=[pytest.mark.exception_test] if fail_on_empty_code else [],
                ),
            ],
            ids=lambda x: x.name.lower(),
        )
        @pytest.mark.execute(pytest.mark.skip(reason="modifies pre-alloc"))
        @pytest.mark.valid_at_transition_to(fork.name())
        def wrapper(
            blockchain_test: BlockchainTestFiller,
            has_balance: ContractAddressHasBalance,
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
            elif test_type == DeploymentTestType.DEPLOY_ON_FORK_BLOCK:
                blocks = [
                    Block(  # Deployment on fork block
                        txs=[deploy_tx],
                        timestamp=15_000,
                    ),
                    Block(  # Empty block after fork
                        txs=[],
                        timestamp=15_001,
                    ),
                ]
            elif test_type == DeploymentTestType.DEPLOY_AFTER_FORK:
                blocks = [
                    Block(  # Empty block on fork
                        txs=[],
                        timestamp=15_000,
                        exception=BlockException.SYSTEM_CONTRACT_EMPTY
                        if fail_on_empty_code
                        else None,
                    )
                ]
                if not fail_on_empty_code:
                    blocks.append(
                        Block(  # Deployment after fork block
                            txs=[deploy_tx],
                            timestamp=15_001,
                        )
                    )
                    blocks.append(
                        Block(  # Empty block after deployment
                            txs=[],
                            timestamp=15_002,
                        ),
                    )
            balance = 1 if has_balance == ContractAddressHasBalance.NONZERO_BALANCE else 0
            pre[expected_deploy_address] = Account(
                code=b"",  # Remove the code that is automatically allocated on the fork
                nonce=0,
                balance=balance,
            )
            pre[deployer_address] = Account(
                balance=deployer_required_balance,
            )

            expected_deploy_address_int = int.from_bytes(expected_deploy_address, "big")

            post = Alloc()
            fork_pre_allocation = fork.pre_allocation_blockchain()
            assert expected_deploy_address_int in fork_pre_allocation
            expected_code = fork_pre_allocation[expected_deploy_address_int]["code"]
            # Note: balance check is omitted; it may be modified by the underlying, decorated test
            account_kwargs = {
                "code": expected_code,
                "nonce": 1,
            }
            if expected_system_contract_storage:
                account_kwargs["storage"] = expected_system_contract_storage
            if test_type != DeploymentTestType.DEPLOY_AFTER_FORK or not fail_on_empty_code:
                post[expected_deploy_address] = Account(**account_kwargs)
                post[deployer_address] = Account(
                    nonce=1,
                )

            # Extra blocks (if any) returned by the decorated function to add after the
            # contract is deployed.
            if test_type != DeploymentTestType.DEPLOY_AFTER_FORK or not fail_on_empty_code:
                # Only fill more blocks if the deploy block does not fail.
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
