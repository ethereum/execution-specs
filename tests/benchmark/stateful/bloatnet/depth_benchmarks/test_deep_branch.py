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

from pathlib import Path
from typing import Any, Callable, List, Self

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
    Op,
    Transaction,
    While,
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
    fork: Fork
    mined_contract_file: MinedContractFile
    attack_orchestrator_address: Address

    def next(self) -> Self:
        """Create a copy of the instance with the next salt as the new end."""
        return self.__class__(
            value=self.value,
            start=self.start,
            end=self.end + 1,
            fork=self.fork,
            mined_contract_file=self.mined_contract_file,
            attack_orchestrator_address=self.attack_orchestrator_address,
        )

    def calldata(self) -> bytes:
        """Return the calldata that needs to be passed to the orchestrator."""
        return Bytes(
            self.value.to_bytes(32, "big")
            + self.start.to_bytes(32, "big")
            + self.end.to_bytes(32, "big")
            + self.mined_contract_file.initcode_hash
        )

    def calculate_inner_call_cost(self) -> int:
        """Calculate the exact gas this inner call would use."""
        gas_costs = self.fork.gas_costs()
        mem_expand_calc = self.fork.memory_expansion_gas_calculator()
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

    def calculate_gas(self) -> int:
        """Calculate the exact gas this attack transaction will use."""
        tx_intrinsic_gas_calc = (
            self.fork.transaction_intrinsic_cost_calculator()
        )
        gas_costs = self.fork.gas_costs()
        mem_expand_calc = self.fork.memory_expansion_gas_calculator()
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
        inner_call_cost = self.calculate_inner_call_cost()
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

    def calculate_tx_gas_limit(self) -> int:
        """Calculate the gas limit required for the transaction."""
        gas_cost = self.calculate_gas()
        # Add the 63/64 margin for the last inner call.
        inner_call_cost = self.calculate_inner_call_cost()
        return gas_cost + ((inner_call_cost * 64 // 63) - inner_call_cost)

    def generate_transaction(self, *, sender: EOA) -> Transaction:
        """Generate the transaction to perform the attack."""
        return Transaction(
            to=self.attack_orchestrator_address,
            gas_limit=self.calculate_tx_gas_limit(),
            sender=sender,
            data=self.calldata(),
        )

    def add_post_verification(self, *, post: Alloc) -> None:
        """Add the post-verification transaction to the post-state."""
        contract = self.mined_contract_file.contracts[self.end]
        storage = dict.fromkeys(self.mined_contract_file.storage_keys, 1)
        storage[self.mined_contract_file.storage_keys[-1]] = self.value
        post[contract.contract_address] = Account(storage=storage)


@pytest.fixture
def mined_contract_file(
    storage_depth: int,
    account_depth: int,
) -> MinedContractFile:
    """Return the correct file for the given test."""
    mined_contract_file = MinedContractFile.load(storage_depth, account_depth)
    # Verify we have contracts in the JSON
    available_contracts = len(mined_contract_file.contracts)
    if available_contracts == 0:
        json_name = f"s{storage_depth}_acc{account_depth}.json"
        raise ValueError(f"No contracts available in {json_name}")
    return mined_contract_file


@pytest.fixture
def mined_contract_deployer(
    pre: Alloc,
    mined_contract_file: MinedContractFile,
) -> Callable[[int], None]:
    """Return a helper to deploy a contract for a given salt when needed."""

    def _mined_contract_deployer(salt: int) -> None:
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

    return _mined_contract_deployer


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
    mined_contract_file: MinedContractFile,
    mined_contract_deployer: Callable[[int], None],
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
        mined_contract_file: The mined contract file
        mined_contract_deployer: A function to deploy a mined contract

    """
    # Deploy orchestrator to deterministic address
    attack_orchestrator_address = pre.deterministic_deploy_contract(
        deploy_code=attack_orchestrator_bytecode(fork)
    )
    print(f"  Orchestrator will be deployed at: {attack_orchestrator_address}")

    # Create an EOA with funds for the deployer
    sender = pre.fund_eoa()

    # Build attack transactions
    attack_txs: list[Transaction] = []
    accrued_tx_gas_usage = 0
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    post = Alloc({})

    # Create the starting attack
    current_attack_batch = Attack(
        value=DEFAULT_ATTACK_VALUE,
        start=0,
        end=0,
        fork=fork,
        mined_contract_file=mined_contract_file,
        attack_orchestrator_address=attack_orchestrator_address,
    )

    # Deploy the starting contract
    mined_contract_deployer(current_attack_batch.start)

    while True:
        next_attack_batch = current_attack_batch.next()
        next_batch_cost = next_attack_batch.calculate_tx_gas_limit()

        if next_batch_cost + accrued_tx_gas_usage > gas_benchmark_value:
            # Next contract cost would go above benchmark limit, we are done.
            attack_txs.append(
                current_attack_batch.generate_transaction(sender=sender)
            )
            current_attack_batch.add_post_verification(post=post)
            accrued_tx_gas_usage += current_attack_batch.calculate_gas()
            break

        # Next contract would not go above limit, but we need to check
        # whether we have gone above the tx limit.

        # We are going to use the next contract regardless
        mined_contract_deployer(next_attack_batch.end)

        if tx_gas_limit_cap is not None and next_batch_cost > tx_gas_limit_cap:
            # Adding a contract would go above the transaction gas limit cap,
            # make the cut here.
            attack_txs.append(
                current_attack_batch.generate_transaction(sender=sender)
            )
            current_attack_batch.add_post_verification(post=post)
            accrued_tx_gas_usage += current_attack_batch.calculate_gas()

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
