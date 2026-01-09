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
- Verifies attack success via a verification transaction at block end

Test parameters:
- storage_depth: Depth of storage slots (e.g., 10, 11)
- account_depth: Account address prefix sharing depth (e.g., 6, 7)
- NUM_CONTRACTS: Dynamically computed based on gas_benchmark_value
- Gas per attack call: ~8,050 gas (~2,742 overhead + 5,300 forwarded)

Contract sources:
- Pre-mined assets (depth_*.sol, s*_acc*.json):
  https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets
"""

from pathlib import Path
from typing import Any, List, Self

import pytest
from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Fork,
    Hash,
    Initcode,
    Op,
    Transaction,
    While,
    compute_deterministic_create2_address,
)
from pydantic import BaseModel, Field

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
    Model to load information about a contract mined using using
    https://github.com/CPerezz/worst_case_miner.
    """

    deployer: Address
    initcode_hash: Hash = Field(..., alias="init_code_hash")
    initcode: Bytes = Field(..., alias="init_code")
    deploy_code: Bytes
    storage_keys: List[Address]
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
                f"Number of storage keys ({len(self.storage_keys)}) does "
                f"not match number of contracts ({self.num_contracts})"
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


def attack_orchestrator_bytecode(fork: Fork) -> Bytecode:
    """
    Return the bytecode of the attack orchestrator, depending on the fork.
    """
    factory_address = (
        fork.deterministic_factory_predeploy_address()
        or DETERMINISTIC_FACTORY_ADDRESS
    )
    return (
        # - Prepare CREATE2 Address Keccak, Mem[0:85]
        # Mem[0:21] = 0xff + DETERMINISTIC_FACTORY_ADDRESS
        Op.MSTORE(
            0,
            Hash(
                b"\xff" + factory_address,
                right_padding=True,
            ),
        )
        # Mem[21:53] = salt (Batch start)
        + Op.MSTORE(1 + 20, Op.CALLDATALOAD(32))
        # Mem[53:85] = Initcode hash
        + Op.MSTORE(1 + 20 + 32, Op.CALLDATALOAD(96))
        # - Prepare ERC20 Calldata, Mem[85:121]
        # Mem[85:89] = 0x64dd891a (ABI `attack(uint256)`)
        + Op.MSTORE(
            1 + 20 + 32 + 32,
            Hash(bytes.fromhex("64dd891a"), right_padding=True),
        )
        # Mem[89:121] = value
        + Op.MSTORE(1 + 20 + 32 + 32 + 4, Op.CALLDATALOAD(0))
        + While(
            body=Op.POP(
                Op.CALL(
                    address=Op.AND(2 ** (20 * 8) - 1, Op.SHA3(0, 85)),
                    args_offset=1 + 20 + 32 + 32,
                    args_size=4 + 32,
                )
            )
            # Increment salt in memory by one
            + Op.MSTORE(1 + 20, Op.ADD(1, Op.MLOAD(1 + 20))),
            # Check that current salt is less than or equal to batch end
            condition=Op.LT(Op.MLOAD(1 + 20), Op.ADD(1, Op.CALLDATALOAD(64))),
        )
        + Op.STOP
    )


class Attack(BaseModel):
    """Describe one attack round using the orchestrator."""

    value: int
    start: int
    end: int
    initcode_hash: Hash

    def calldata(self) -> bytes:
        """Return the calldata that needs to be passed to the orchestrator."""
        return Bytes(
            self.value.to_bytes(32, "big")
            + self.start.to_bytes(32, "big")
            + self.end.to_bytes(32, "big")
            + self.initcode_hash
        )

    def calculate_inner_call_cost(self, fork: Fork) -> int:
        """Calculate the exact gas this inner call would use."""
        gas_costs = fork.gas_costs()
        mem_expand_calc = fork.memory_expansion_gas_calculator()
        inner_call_cost = (
            mem_expand_calc(new_bytes=96)
            + 17 * gas_costs.G_VERY_LOW  # PUSHN operations
            + 1 * gas_costs.G_VERY_LOW  # MSTORE operations
            + 5 * gas_costs.G_VERY_LOW  # DUP operations
            + 1 * gas_costs.G_VERY_LOW  # LT operations
            + 1 * gas_costs.G_VERY_LOW  # GT operations
            + 1 * gas_costs.G_VERY_LOW  # EQ operations
            + 2 * gas_costs.G_VERY_LOW  # CALLDATALOAD operations
            + 1 * gas_costs.G_VERY_LOW  # SHR operations
            + 1 * gas_costs.G_VERY_LOW  # SUB operations
            + 1 * gas_costs.G_VERY_LOW  # SLT operations
            + 2 * gas_costs.G_VERY_LOW  # SWAP operations
            + 2 * gas_costs.G_VERY_LOW  # ISZERO operations
            + 5 * gas_costs.G_HIGH  # JUMPI operations
            + 3 * gas_costs.G_MID  # JUMP operations
            + 3 * gas_costs.G_BASE  # POP operations
            + 1 * gas_costs.G_BASE  # CALLVALUE operations
            + 2 * gas_costs.G_BASE  # CALLDATASIZE operations
            + 6 * gas_costs.G_JUMPDEST  # JUMPDEST operations
            + 2 * gas_costs.G_BASE  # PUSH0 operations
            + 1
            * (
                gas_costs.G_COLD_SLOAD + gas_costs.G_STORAGE_RESET
            )  # SSTORE operations
        )
        return inner_call_cost

    def calculate_gas(self, fork: Fork) -> int:
        """Calculate the exact gas this attack transaction will use."""
        tx_intrinsic_gas_calc = fork.transaction_intrinsic_cost_calculator()
        gas_costs = fork.gas_costs()
        mem_expand_calc = fork.memory_expansion_gas_calculator()
        tx_overhead = tx_intrinsic_gas_calc(
            calldata=self.calldata(),
            return_cost_deducted_prior_execution=True,
        )
        setup_gas = (
            mem_expand_calc(new_bytes=121)
            + 5 * gas_costs.G_VERY_LOW  # MSTORE operations
            + 10 * gas_costs.G_VERY_LOW  # PUSH operations
            + 3 * gas_costs.G_VERY_LOW  # CALLDATALOAD operations
        )
        inner_call_cost = self.calculate_inner_call_cost(fork)
        gas_per_attack = (
            1 * gas_costs.G_JUMPDEST  # JUMPDEST operations
            + 15 * gas_costs.G_VERY_LOW  # PUSH operations
            + 2 * gas_costs.G_VERY_LOW  # MLOAD operations
            + 2 * gas_costs.G_VERY_LOW  # ADD operations
            + 1 * gas_costs.G_VERY_LOW  # AND operations
            + 1 * gas_costs.G_VERY_LOW  # MSTORE operations
            + 1 * gas_costs.G_VERY_LOW  # CALLDATALOAD operations
            + 1 * gas_costs.G_VERY_LOW  # LT operations
            + 1 * gas_costs.G_VERY_LOW  # SUB operations
            + 1 * gas_costs.G_BASE  # PC operations
            + 1 * gas_costs.G_BASE  # GAS operations
            + 1 * gas_costs.G_BASE  # POP operations
            + 1 * gas_costs.G_HIGH  # JUMPI operations
            + gas_costs.G_KECCAK_256
            + 3 * gas_costs.G_KECCAK_256_WORD
            + 1 * gas_costs.G_COLD_ACCOUNT_ACCESS
            + inner_call_cost
        )
        call_count = (self.end - self.start) + 1
        assert call_count > 0, (
            f"Batch end ({self.end}) must be greater or equal "
            f"to batch start ({self.start})"
        )
        return call_count * gas_per_attack + setup_gas + tx_overhead

    def calculate_tx_gas_limit(self, fork: Fork) -> int:
        """Calculate the gas limit required for the transaction."""
        gas_cost = self.calculate_gas(fork)
        # Add the 63/64 margin for the last inner call.
        inner_call_cost = self.calculate_inner_call_cost(fork)
        return gas_cost + ((inner_call_cost * 64 // 63) - inner_call_cost)

    def generate_transaction(self, fork: Fork, sender: EOA) -> Transaction:
        """Generate the transaction to perform the attack."""
        attack_orchestrator_address = compute_deterministic_create2_address(
            salt=Hash(0),
            initcode=Initcode(deploy_code=attack_orchestrator_bytecode(fork)),
            fork=fork,
        )
        return Transaction(
            to=attack_orchestrator_address,
            gas_limit=self.calculate_tx_gas_limit(fork),
            sender=sender,
            data=self.calldata(),
        )

    def add_post_verification(
        self, post: Alloc, mined_contract_file: MinedContractFile
    ) -> None:
        """Add the post-verification transaction to the post-state."""
        contract = mined_contract_file.contracts[self.end]
        storage = dict.fromkeys(mined_contract_file.storage_keys, 1)
        storage[mined_contract_file.storage_keys[-1]] = self.value
        post[contract.contract_address] = Account(storage=storage)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "storage_depth,account_depth",
    [
        (10, 6),  # From .worst_case_miner/mined_assets
    ],
)
def test_worst_depth_stateroot_recomp(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    storage_depth: int,
    account_depth: int,
) -> None:
    """
    BloatNet worst-case SSTORE attack benchmark with pre-deployed contracts.

    This test:
    1. Derives CREATE2 addresses from initcode_hash + Nick's deployer
    2. Deploys AttackOrchestrator that calls attack() on each target
    3. Fills blocks with 16M gas transactions attacking contracts
    4. Adds a verification transaction at the end to confirm success

    Args:
        blockchain_test: The blockchain test filler
        pre: Pre-state allocation
        fork: The fork to test on
        env: Environment object that will be used to fill/execute
        gas_benchmark_value: Gas budget for benchmark
        storage_depth: Depth of storage slots in the contract
        account_depth: Account address prefix sharing depth

    """
    # Dynamically calculate number of contracts based on gas budget
    print("\nTesting with pre-deployed contracts:")
    print(f"  Storage depth: {storage_depth}")
    print(f"  Account depth: {account_depth}")
    print(f"  Gas benchmark value: {gas_benchmark_value:,}")

    # Load the CREATE2 data to get the init code hash
    mined_contract_file = MinedContractFile.load(storage_depth, account_depth)
    initcode_hash = mined_contract_file.initcode_hash

    # Verify we have enough contracts in the JSON
    available_contracts = len(mined_contract_file.contracts)
    if available_contracts == 0:
        json_name = f"s{storage_depth}_acc{account_depth}.json"
        raise ValueError(f"No contracts available in {json_name}")

    # Create an EOA with funds for the deployer
    sender = pre.fund_eoa()

    # Deploy orchestrator to deterministic address
    orchestrator_address = pre.deterministic_deploy_contract(
        deploy_code=attack_orchestrator_bytecode(fork)
    )
    print(f"  Orchestrator will be deployed at: {orchestrator_address}")

    # Build attack transactions
    attack_txs: list[Transaction] = []
    attack_value = DEFAULT_ATTACK_VALUE
    accrued_tx_gas_usage = 0
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    post = Alloc({})

    current_attack_batch = Attack(
        value=attack_value,
        start=0,
        end=0,
        initcode_hash=initcode_hash,
    )

    # Create a helper to deploy a contract for a given salt when needed.
    def deploy_mined_contract(salt: int) -> None:
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

    # Deploy the starting contract
    deploy_mined_contract(current_attack_batch.start)

    while True:
        next_attack_batch = Attack(
            value=attack_value,
            start=current_attack_batch.start,
            end=current_attack_batch.end + 1,
            initcode_hash=initcode_hash,
        )
        next_batch_cost = next_attack_batch.calculate_tx_gas_limit(fork=fork)

        if next_batch_cost + accrued_tx_gas_usage > gas_benchmark_value:
            # Next contract cost would go above benchmark limit, we are done.
            attack_txs.append(
                current_attack_batch.generate_transaction(fork, sender)
            )
            current_attack_batch.add_post_verification(
                post, mined_contract_file
            )
            accrued_tx_gas_usage += current_attack_batch.calculate_gas(fork)
            break

        # Next contract would not go above limit, but we need to check
        # whether we have gone above the tx limit.

        # We are going to use the next contract regardless
        if next_attack_batch.end > available_contracts:
            raise RuntimeError(
                f"Requested {next_attack_batch.end} contracts but only "
                f"{available_contracts} available, using {available_contracts}"
            )
        deploy_mined_contract(next_attack_batch.end)

        if tx_gas_limit_cap is not None and next_batch_cost > tx_gas_limit_cap:
            # Adding a contract would go above the transaction gas limit cap,
            # make the cut here.
            attack_txs.append(
                current_attack_batch.generate_transaction(fork, sender)
            )
            current_attack_batch.add_post_verification(
                post, mined_contract_file
            )
            accrued_tx_gas_usage += current_attack_batch.calculate_gas(fork)

            next_attack_batch.start = next_attack_batch.end

        current_attack_batch = next_attack_batch

    print(f"  Created {len(attack_txs)} attack transactions")
    if accrued_tx_gas_usage > gas_benchmark_value:
        raise ValueError(
            f"Accrued tx gas usage ({accrued_tx_gas_usage:,} gas) "
            f"exceeds gas benchmark value ({gas_benchmark_value:,} gas)"
        )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=attack_txs)],
        post=post,
        expected_benchmark_gas_used=accrued_tx_gas_usage,
    )
