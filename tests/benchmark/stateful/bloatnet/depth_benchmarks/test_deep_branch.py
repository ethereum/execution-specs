"""
abstract: BloatNet worst-case attack benchmark for maximum SSTORE stress.

This test implements a worst-case scenario for Ethereum block processing
that exploits the computational complexity of Patricia Merkle Trie
operations. It uses CREATE2 to deploy contracts at pre-mined addresses
with shared prefixes, maximizing trie traversal depth.

Key features:
- Attacks pre-deployed contracts via CREATE2 address derivation
- Each contract has deep storage slots with configurable trie depth
- Executes optimized attack bytecode with multiple SSTORE operations
- Respects Fusaka tx gas limit (16M gas) and fills blocks fully
- Verifies attack success via a storage check in each of the attack contracts

Test parameters:
- storage_depth: Depth of storage slots (e.g., 10, 11)
- account_depth: Account address prefix sharing depth (e.g., 6, 7)

Contract sources:
- Pre-mined assets (depth_*.sol, s*_acc*.json):
  https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets
"""

import time
from pathlib import Path
from typing import Annotated, Any, List, Self

import pytest
from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Bytes,
    Create2PreimageLayout,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    TransactionWithCost,
    While,
)
from pydantic import BaseModel, BeforeValidator, Field

# Folder path to the submodule and mined assets
WORST_CASE_MINER_SUBMODULE_PATH = Path(__file__).parent / ".worst_case_miner"
MINED_ASSETS_PATH = WORST_CASE_MINER_SUBMODULE_PATH / "mined_assets"

# Arbitrary value written to storage slots during attack
DEFAULT_ATTACK_VALUE = 42


def get_mined_asset(filename: str) -> str:
    """
    Get the contents of the mined asset.

    Requires `git submodule update --init --recursive` if the repository
    was not cloned using submodules initially.

    Args:
        filename: Name of the file (e.g., "s9_acc5.json" or "depth_9.sol")

    Returns:
        str: Content of the file

    """
    asset_path = MINED_ASSETS_PATH / filename

    if not asset_path.exists():
        raise RuntimeError(
            f"""
            File {filename} not found in {MINED_ASSETS_PATH}.
            Please run `git submodule update --init --recursive` to download
            the submodule before running the test.
            """
        )

    return asset_path.read_text()


class SaltedContractInstance(BaseModel):
    """
    Represents a single instance of a contract deployed using the given salt.
    """

    salt: int
    contract_address: Address
    auxiliary_accounts: List[Address]


class MinedContractFile(BaseModel):
    """
    Model to load information about a contract mined using
    https://github.com/CPerezz/worst_case_miner.
    """

    deployer: Address
    initcode_hash: Hash = Field(..., alias="init_code_hash")
    initcode: Bytes = Field(..., alias="init_code")
    deploy_code: Bytes
    storage_keys: List[
        Annotated[Hash, BeforeValidator(lambda v: Hash(v, left_padding=True))]
    ]
    target_depth: int
    num_contracts: int
    total_time: float
    contracts: List[SaltedContractInstance]

    def model_post_init(self, __context: Any) -> None:
        """
        Perform post-initialization checks.
        """
        if len(self.contracts) != self.num_contracts:
            raise ValueError(
                f"Number of contracts specified in the `num_contracts` field, "
                f"({self.num_contracts})does not match number of "
                f"contracts ({len(self.contracts)})."
            )
        if self.initcode_hash != self.initcode.keccak256():
            raise ValueError(
                f"init code hash ({self.initcode_hash}) does not match "
                f"calculated hash ({self.initcode.keccak256()})"
            )

    @classmethod
    def load(cls, storage_depth: int, account_depth: int) -> Self:
        """
        Load the pre-mined CREATE2 data for given depth parameters.

        Args:
            storage_depth: Depth of storage slots in the contract (e.g., 9)
            account_depth: Depth of account address prefix sharing (e.g., 5)

        Returns dict with:
            - initcode_hash: Expected hash for reproducible compilation
            - deployer: Nick's deployer address
            - contracts: List of dicts with 'salt' and 'auxiliary_accounts'

        """
        json_filename = f"s{storage_depth}_acc{account_depth}.json"
        return cls.model_validate_json(get_mined_asset(json_filename))


@pytest.fixture
def attack_value(request: pytest.FixtureRequest) -> int:
    """
    Value to set in storage to trigger the update.

    During test fill, it's desirable to use a constant so the filled fixtures
    are always the same.

    However during execute we should use a random value to guarantee the
    storage update that's required for the attack.
    """
    if request.config.pluginmanager.has_plugin(
        "execution_testing.cli.pytest_commands.plugins.execute.execute"
    ):
        return int(time.time())
    return DEFAULT_ATTACK_VALUE


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "storage_depth,account_depth",
    [
        # From .worst_case_miner/mined_assets
        (10, 3),
        (10, 4),
        (10, 5),
        (10, 6),
        (10, 7),
        (11, 3),
        (11, 4),
        (11, 5),
        (11, 6),
        (11, 7),
        (12, 3),
        (12, 4),
        (12, 5),
    ],
)
def test_worst_depth_stateroot_recomp(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    gas_benchmark_value: int,
    storage_depth: int,
    account_depth: int,
    attack_value: int,
) -> None:
    """
    BloatNet worst-case SSTORE attack benchmark with pre-deployed contracts.

    This test:
    1. Derives CREATE2 addresses from initcode_hash + Nick's deployer
    2. Deploys AttackOrchestrator that calls attack() on each target
    3. Fills blocks with 16M gas transactions attacking contracts
    4. Adds a verification transaction at the end to confirm success

    Args:
        benchmark_test: The benchmark test filler
        fork: The fork to test on
        pre: Pre-state allocation
        gas_benchmark_value: Gas budget for benchmark
        storage_depth: Depth of storage slots in the contract (e.g., 9)
        account_depth: Depth of account address prefix sharing (e.g., 5)
        attack_value: The value to be written to storage in each attack

    """
    # Load the mined contract file
    mined_contract_file = MinedContractFile.load(storage_depth, account_depth)

    # Generate the attack orchestrator
    factory_address = (
        fork.deterministic_factory_predeploy_address()
        or DETERMINISTIC_FACTORY_ADDRESS
    )

    # Prepare attack contract
    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(32),
        init_code_hash=Op.CALLDATALOAD(96),
    )
    args_offset = 96
    setup: Bytecode = (
        create2_preimage
        # Place ABI (`attack(uint256)`) in memory
        + Op.MSTORE(
            args_offset,
            Hash(bytes.fromhex("64dd891a"), right_padding=True),
            old_memory_size=args_offset,
            new_memory_size=args_offset + 32,
        )
        # Place attack value in memory
        + Op.MSTORE(
            args_offset + 4,
            Op.CALLDATALOAD(0),
            old_memory_size=args_offset + 32,
            new_memory_size=args_offset + 32 + 4,
        )
        # Place end index in stack
        + Op.CALLDATALOAD(64)
    )
    iterating = While(
        body=Op.POP(
            Op.CALL(
                address=create2_preimage.address_op(),
                args_offset=args_offset,
                args_size=4 + 32,
            )
        )
        # Increment salt in memory by one
        + create2_preimage.increment_salt_op(),
        # Check that current salt is less than the batch end
        # Salt + 1 < End Index
        condition=Op.LT(
            Op.MLOAD(create2_preimage.salt_offset),
            Op.DUP1,
        ),
    )
    cleanup = Op.STOP

    # The code was compiled by solidity, so these opcode counts were obtained
    # from the traces.
    # The purpose of this bytecode definition is to calculate the gas cost of
    # the inner call, not to deploy it, hence the unsorted opcodes.
    # This collection of opcodes represents Solidity's function dispatching
    # logic, and the `attack(uint256 value)` function that can be seen in
    # `depth_N.sol` files.
    inner_call_bytecode = (
        # Attack sstore
        Op.SSTORE(key_warm=False, original_value=1, new_value=2)
        # Rest of the opcodes
        + Op.CALLDATALOAD * 2
        + Op.CALLDATASIZE * 2
        + Op.CALLVALUE
        + Op.DUP1 * 5
        + Op.EQ
        + Op.GT
        + Op.ISZERO * 2
        + Op.JUMP * 3
        + Op.JUMPDEST * 6
        + Op.JUMPI * 5
        + Op.LT
        + Op.MSTORE(new_memory_size=96)
        + Op.POP * 3
        + Op.PUSH0 * 2
        + Op.PUSH1 * 17
        + Op.SHR
        + Op.SLT
        + Op.SUB
        + Op.SWAP1 * 2
    )

    attack_orchestrator_bytecode = IteratingBytecode(
        setup=setup,
        iterating=iterating,
        cleanup=cleanup,
        iterating_subcall=inner_call_bytecode,
    )

    # Deploy orchestrator to deterministic address
    attack_orchestrator_address = pre.deterministic_deploy_contract(
        deploy_code=attack_orchestrator_bytecode
    )
    print(f"  Orchestrator will be deployed at: {attack_orchestrator_address}")

    # Calldata generator for each transaction of the iterating bytecode.
    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        end_iteration = start_iteration + iteration_count
        return (
            Hash(attack_value)
            + Hash(start_iteration)
            + Hash(end_iteration)
            + mined_contract_file.initcode_hash
        )

    # Get the number of contracts to deploy
    contracts_required = sum(
        attack_orchestrator_bytecode.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            start_iteration=0,
            calldata=calldata,
        )
    )

    # Deploy all contracts required.
    post = Alloc({})
    for salt in range(contracts_required):
        if salt >= len(mined_contract_file.contracts):
            raise RuntimeError(
                f"Requested salt {salt} but only "
                f"{len(mined_contract_file.contracts)} available"
            )
        salted_contract_info = mined_contract_file.contracts[salt]
        assert salted_contract_info.salt == salt, (
            f"Salt out of order: {salted_contract_info.salt} != {salt}"
        )
        deployed_contract_address = pre.deterministic_deploy_contract(
            deploy_code=mined_contract_file.deploy_code,
            salt=Hash(salt),
            initcode=mined_contract_file.initcode,
            storage=dict.fromkeys(mined_contract_file.storage_keys, 1),
        )
        assert (
            deployed_contract_address == salted_contract_info.contract_address
        ), (
            f"Contract address mismatch: {deployed_contract_address} != "
            f"{salted_contract_info.contract_address}, salt: {salt}"
        )
        for auxiliary_account in salted_contract_info.auxiliary_accounts:
            # Ensure the account exists in the state trie
            pre.fund_address(
                address=auxiliary_account, amount=1, minimum_balance=True
            )

        # Set the post expectations
        storage = dict.fromkeys(mined_contract_file.storage_keys, 1)
        storage[mined_contract_file.storage_keys[-1]] = attack_value
        post[salted_contract_info.contract_address] = Account(storage=storage)

    # Create an EOA with funds for the deployer
    sender = pre.fund_eoa()

    # Build attack transactions
    attack_txs: list[TransactionWithCost] = list(
        attack_orchestrator_bytecode.transactions_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            start_iteration=0,
            sender=sender,
            to=attack_orchestrator_address,
            calldata=calldata,
        )
    )

    total_gas_cost = sum(tx.gas_cost for tx in attack_txs)

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=attack_txs)],
        post=post,
        expected_benchmark_gas_used=total_gas_cost,
    )
