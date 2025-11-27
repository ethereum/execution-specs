"""Test generator decorators."""

import itertools
import json
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Protocol

import pytest

from execution_testing.base_types import Account, Address, Hash
from execution_testing.exceptions import BlockException
from execution_testing.forks import Berlin, Fork
from execution_testing.specs import BlockchainTestFiller, StateTestFiller
from execution_testing.specs.blockchain import Block
from execution_testing.test_types import Alloc, Transaction
from execution_testing.vm import Bytecode, Op


class DeploymentTestType(StrEnum):
    """Represents the type of deployment test."""

    DEPLOY_BEFORE_FORK = "deploy_before_fork"
    DEPLOY_ON_FORK_BLOCK = "deploy_on_fork_block"
    DEPLOY_AFTER_FORK = "deploy_after_fork"


class SystemContractTestType(StrEnum):
    """Represents the type of system contract test."""

    GAS_LIMIT = "system_contract_reaches_gas_limit"
    OUT_OF_GAS_ERROR = "system_contract_out_of_gas"
    REVERT_ERROR = "system_contract_reverts"
    EXCEPTION_ERROR = "system_contract_throws"

    def param(self) -> Any:
        """Return the parameter for the test."""
        return pytest.param(
            self,
            id=self.value,
            marks=pytest.mark.exception_test
            if self != SystemContractTestType.GAS_LIMIT
            else [],
        )


class ContractAddressHasBalance(StrEnum):
    """
    Represents whether the target deployment test has a balance before
    deployment.
    """

    ZERO_BALANCE = "zero_balance"
    NONZERO_BALANCE = "nonzero_balance"


class SystemContractDeployTestFunction(Protocol):
    """
    Represents a function to be decorated with the
    `generate_system_contract_deploy_test` decorator.
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
        Arguments:
          fork (Fork): The fork to test.
          pre (Alloc): The pre state of the blockchain.
          post (Alloc): The post state of the blockchain.
          test_type(DeploymentTestType): The type of deployment test
                                         currently being filled.

        Yields:
          Block: To add after the block where the contract was deployed
                 (e.g. can contain extra transactions to execute after
                 the system contract has been deployed, and/or a header
                 object to verify that the headers are correct).

        """
        pass


def generate_system_contract_deploy_test(
    *,
    fork: Fork,
    tx_json_path: Path,
    expected_deploy_address: Address,
    fail_on_empty_code: bool,
    expected_system_contract_storage: Dict | None = None,
) -> Callable[[SystemContractDeployTestFunction], Callable]:
    """
    Generate a test that verifies the correct deployment of a system contract.

    Generates following test cases:

                        | before/after fork | fail on      | invalid block  |
                                              empty block  |                |
    --------------------|-------------------|--------------|----------------|
    `deploy_before_fork-| before            | False        | False          |
    nonzero_balance`

    `deploy_before_fork-| before            | True         | False          |
    zero_balance`

    `deploy_on_fork_    | on fork block     | False        | False          |
    block-nonzero_
    balance`

    `deploy_on_fork_    | on fork block     | True         | False          |
    block-zero_balance`

    `deploy_after_fork  | after             | False        | False          |
    -nonzero_balance`

    `deploy_after_fork  | after             | True         | True           |
    -zero_balance`


    The `has balance` parametrization does not have an effect on the
    expectation of the test.

    Arguments:
      fork (Fork): The fork to test.
      tx_json_path (Path): Path to the JSON file with the transaction to
                           deploy the system contract. Providing a JSON
                           file is useful to copy-paste the transaction
                           from the EIP.
      expected_deploy_address (Address): The expected address of the deployed
                                         contract.
      fail_on_empty_code (bool): If True, the test is expected to fail
                                 on empty code.
      expected_system_contract_storage (Dict | None): The expected storage of
                                                      the system contract.

    """
    with open(tx_json_path, mode="r") as f:
        tx_json = json.loads(f.read())
    if "gasLimit" not in tx_json and "gas" in tx_json:
        tx_json["gasLimit"] = tx_json["gas"]
        del tx_json["gas"]
    if "protected" not in tx_json:
        tx_json["protected"] = False
    deploy_tx = Transaction.model_validate(tx_json).with_signature_and_sender()
    gas_price = deploy_tx.gas_price
    assert gas_price is not None
    deployer_required_balance = deploy_tx.gas_limit * gas_price
    deployer_address = deploy_tx.sender
    if "hash" in tx_json:
        assert deploy_tx.hash == Hash(tx_json["hash"])
    if "sender" in tx_json:
        assert deploy_tx.sender == Address(tx_json["sender"])

    def decorator(func: SystemContractDeployTestFunction) -> Callable:
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
                    marks=[pytest.mark.exception_test]
                    if fail_on_empty_code
                    else [],
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
        ) -> None:
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
            balance = (
                1
                if has_balance == ContractAddressHasBalance.NONZERO_BALANCE
                else 0
            )
            pre[expected_deploy_address] = Account(
                code=b"",  # Remove the code that is automatically allocated on
                # the fork
                nonce=0,
                balance=balance,
            )
            pre[deployer_address] = Account(
                balance=deployer_required_balance,
            )

            expected_deploy_address_int = int.from_bytes(
                expected_deploy_address, "big"
            )

            post = Alloc()
            fork_pre_allocation = fork.pre_allocation_blockchain()
            assert expected_deploy_address_int in fork_pre_allocation
            expected_code = fork_pre_allocation[expected_deploy_address_int][
                "code"
            ]
            # Note: balance check is omitted; it may be modified by the
            # underlying, decorated test
            account_kwargs = {
                "code": expected_code,
                "nonce": 1,
            }
            if expected_system_contract_storage:
                account_kwargs["storage"] = expected_system_contract_storage
            if (
                test_type != DeploymentTestType.DEPLOY_AFTER_FORK
                or not fail_on_empty_code
            ):
                post[expected_deploy_address] = Account(**account_kwargs)
                post[deployer_address] = Account(
                    nonce=1,
                )

            # Extra blocks (if any) returned by the decorated function to add
            # after the contract is deployed.
            if (
                test_type != DeploymentTestType.DEPLOY_AFTER_FORK
                or not fail_on_empty_code
            ):
                # Only fill more blocks if the deploy block does not fail.
                blocks += list(
                    func(fork=fork, pre=pre, post=post, test_type=test_type)
                )

            blockchain_test(
                pre=pre,
                blocks=blocks,
                post=post,
            )

        wrapper.__name__ = func.__name__  # type: ignore
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator


def generate_system_contract_error_test(
    *,
    max_gas_limit: int,
) -> Callable[[SystemContractDeployTestFunction], Callable]:
    """
    Generate a test that verifies the correct behavior when a system contract
    fails execution.

    Parametrizations required:
    - system_contract (Address): The address of the system contract to deploy.
    - valid_from (Fork): The fork from which the test is valid.

    Arguments:
      max_gas_limit (int): The maximum gas limit for the system transaction.

    """

    def decorator(func: SystemContractDeployTestFunction) -> Callable:
        @pytest.mark.parametrize(
            "test_type", [v.param() for v in SystemContractTestType]
        )
        @pytest.mark.execute(pytest.mark.skip(reason="modifies pre-alloc"))
        def wrapper(
            blockchain_test: BlockchainTestFiller,
            pre: Alloc,
            test_type: SystemContractTestType,
            system_contract: Address,
            fork: Fork,
        ) -> None:
            modified_system_contract_code = Bytecode()

            # Depending on the test case, we need to modify the system contract
            # code accordingly.
            if (
                test_type == SystemContractTestType.GAS_LIMIT
                or test_type == SystemContractTestType.OUT_OF_GAS_ERROR
            ):
                # Run code so that it reaches the gas limit.
                gas_costs = fork.gas_costs()
                # The code works by storing N values to storage, and N is
                # calculated based on the gas costs for the given fork. This
                # code will only work once, so if the system contract is re-
                # executed in a subsequent block, it will consume less gas.
                gas_used_per_storage = (
                    gas_costs.G_STORAGE_SET
                    + gas_costs.G_COLD_SLOAD
                    + (gas_costs.G_VERY_LOW * 2)
                )
                modified_system_contract_code += sum(
                    Op.SSTORE(i, 1)
                    for i in range(max_gas_limit // gas_used_per_storage)
                )
                # If the gas limit is not divisible by the gas used per
                # storage, we need to add some NO-OP (JUMPDEST) to the code
                # that each consume 1 gas.
                assert gas_costs.G_JUMPDEST == 1, (
                    f"JUMPDEST gas cost should be 1, but got {gas_costs.G_JUMPDEST}. "
                    "Generator `generate_system_contract_error_test` needs to be updated."
                )
                modified_system_contract_code += sum(
                    Op.JUMPDEST
                    for _ in range(max_gas_limit % gas_used_per_storage)
                )

                if test_type == SystemContractTestType.OUT_OF_GAS_ERROR:
                    # If the test type is OUT_OF_GAS_ERROR, we need to add a
                    # JUMPDEST to the code to ensure that we go over the limit
                    # by one gas.
                    modified_system_contract_code += Op.JUMPDEST
                modified_system_contract_code += Op.STOP
            elif test_type == SystemContractTestType.REVERT_ERROR:
                # Run a simple revert.
                modified_system_contract_code = Op.REVERT(0, 0)
            elif test_type == SystemContractTestType.EXCEPTION_ERROR:
                # Run a simple exception.
                modified_system_contract_code = Op.INVALID()
            else:
                raise ValueError(f"Invalid test type: {test_type}")

            pre[system_contract] = Account(
                code=modified_system_contract_code,
                nonce=1,
                balance=0,
            )

            # Simple test transaction to verify the block failed to modify the
            # state.
            value_receiver = pre.fund_eoa(amount=0)
            test_tx = Transaction(
                to=value_receiver,
                value=1,
                gas_limit=100_000,
                sender=pre.fund_eoa(),
            )
            post = Alloc()
            post[value_receiver] = (
                Account.NONEXISTENT
                if test_type != SystemContractTestType.GAS_LIMIT
                else Account(
                    balance=1,
                )
            )

            blockchain_test(
                pre=pre,
                blocks=[
                    Block(  # Deployment block
                        txs=[test_tx],
                        exception=BlockException.SYSTEM_CONTRACT_CALL_FAILED
                        if test_type != SystemContractTestType.GAS_LIMIT
                        else None,
                    )
                ],
                post=post,
            )

        wrapper.__name__ = func.__name__  # type: ignore
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator


"""Storage addresses for common testing fields"""
_slot = itertools.count()
slot_cold_gas = next(_slot)
slot_warm_gas = next(_slot)
slot_oog_call_result = next(_slot)
slot_sanity_call_result = next(_slot)

LEGACY_CALL_FAILURE = 0
LEGACY_CALL_SUCCESS = 1


def gas_test(
    *,
    fork: Fork,
    state_test: StateTestFiller,
    pre: Alloc,
    setup_code: Bytecode,
    subject_code: Bytecode,
    tear_down_code: Bytecode | None = None,
    cold_gas: int,
    warm_gas: int | None = None,
    subject_address: Address | None = None,
    subject_balance: int = 0,
    oog_difference: int = 1,
    out_of_gas_testing: bool = True,
    prelude_code: Bytecode | None = None,
    tx_gas: int | None = None,
) -> None:
    """
    Create State Test to check the gas cost of a sequence of EOF code.

    `setup_code` and `tear_down_code` are called multiple times during the
    test, and MUST NOT have any side-effects which persist across message
    calls, and in particular, any effects on the gas usage of `subject_code`.
    """
    if fork < Berlin:
        raise ValueError(
            "Gas tests before Berlin are not supported due to CALL gas changes"
        )

    if cold_gas <= 0:
        raise ValueError(
            f"Target gas allocations (cold_gas) must be > 0, got {cold_gas}"
        )
    if warm_gas is None:
        warm_gas = cold_gas

    sender = pre.fund_eoa()
    if tear_down_code is None:
        tear_down_code = Op.STOP
    address_baseline = pre.deploy_contract(setup_code + tear_down_code)
    code_subject = setup_code + subject_code + tear_down_code
    address_subject = pre.deploy_contract(
        code_subject,
        balance=subject_balance,
        address=subject_address,
    )
    # 2 times GAS, POP, CALL, 6 times PUSH1 - instructions charged for at every
    # gas run
    gas_costs = fork.gas_costs()
    OPCODE_GAS_COST = gas_costs.G_BASE
    OPCODE_POP_COST = gas_costs.G_BASE
    OPCODE_PUSH_COST = gas_costs.G_VERY_LOW
    gas_single_gas_run = (
        2 * OPCODE_GAS_COST
        + OPCODE_POP_COST
        + gas_costs.G_WARM_ACCOUNT_ACCESS
        + 6 * OPCODE_PUSH_COST
    )
    address_legacy_harness = pre.deploy_contract(
        code=(
            # warm subject and baseline without executing
            (
                Op.BALANCE(address_subject)
                + Op.POP
                + Op.BALANCE(address_baseline)
                + Op.POP
            )
            # run any "prelude" code that may have universal side effects
            + prelude_code
            # Baseline gas run
            + (
                Op.GAS
                + Op.CALL(address=address_baseline, gas=Op.GAS)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # cold gas run
            + (
                Op.GAS
                + Op.CALL(address=address_subject, gas=Op.GAS)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # warm gas run
            + (
                Op.GAS
                + Op.CALL(address=address_subject, gas=Op.GAS)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # Store warm gas: DUP3 is the gas of the baseline gas run
            + (
                Op.DUP3
                + Op.SWAP1
                + Op.SUB
                + Op.PUSH2(slot_warm_gas)
                + Op.SSTORE
            )
            # store cold gas: DUP2 is the gas of the baseline gas run
            + (
                Op.DUP2
                + Op.SWAP1
                + Op.SUB
                + Op.PUSH2(slot_cold_gas)
                + Op.SSTORE
            )
            + (
                (
                    # do an oog gas run, unless skipped with
                    # `out_of_gas_testing=False`:
                    #
                    # - DUP7 is the gas of the baseline gas run, after other
                    #   CALL args were pushed
                    # - subtract the gas charged by the harness
                    # - add warm gas charged by the subject
                    # - subtract `oog_difference` to cause OOG exception
                    #   (1 by default)
                    Op.SSTORE(
                        slot_oog_call_result,
                        Op.CALL(
                            gas=Op.ADD(
                                warm_gas - gas_single_gas_run - oog_difference,
                                Op.DUP7,
                            ),
                            address=address_subject,
                        ),
                    )
                    # sanity gas run: not subtracting 1 to see if enough gas
                    # makes the call succeed
                    + Op.SSTORE(
                        slot_sanity_call_result,
                        Op.CALL(
                            gas=Op.ADD(warm_gas - gas_single_gas_run, Op.DUP7),
                            address=address_subject,
                        ),
                    )
                    + Op.STOP
                )
                if out_of_gas_testing
                else Op.STOP
            )
        ),
    )

    post = {
        address_legacy_harness: Account(
            storage={
                slot_warm_gas: warm_gas,
                slot_cold_gas: cold_gas,
            },
        ),
    }

    if out_of_gas_testing:
        post[address_legacy_harness].storage[slot_oog_call_result] = (
            LEGACY_CALL_FAILURE
        )
        post[address_legacy_harness].storage[slot_sanity_call_result] = (
            LEGACY_CALL_SUCCESS
        )

    if tx_gas is None:
        tx_gas = gas_single_gas_run + cold_gas + 500_000
    tx = Transaction(
        to=address_legacy_harness, gas_limit=tx_gas, sender=sender
    )

    state_test(pre=pre, tx=tx, post=post)
