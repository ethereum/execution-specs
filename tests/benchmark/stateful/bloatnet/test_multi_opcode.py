"""
abstract: BloatNet bench cases extracted from https://hackmd.io/9icZeLN7R0Sk5mIjKlZAHQ.

   The idea of all these tests is to stress client implementations to find out
   where the limits of processing are focusing specifically on state-related
   operations.
"""

import json
import math
from pathlib import Path

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Create2PreimageLayout,
    Fork,
    Hash,
    Op,
    Transaction,
    While,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# BLOATNET ARCHITECTURE:
#
#   [Initcode Contract]        [Factory Contract]              [24KB Contracts]
#         (9.5KB)                    (116B)                     (N x 24KB each)
#           │                          │                              │
#           │  EXTCODECOPY             │   CREATE2(salt++)            │
#           └──────────────►           ├──────────────────►     Contract_0
#                                      ├──────────────────►     Contract_1
#                                      ├──────────────────►     Contract_2
#                                      └──────────────────►     Contract_N
#
#   [Attack Contract] ──STATICCALL──► [Factory.getConfig()]
#           │                              returns: (N, hash)
#           └─► Loop(i=0 to N):
#                 1. Generate CREATE2 addr: keccak256(0xFF|factory|i|hash)[12:]
#                 2. BALANCE(addr)    → 2600 gas (cold access)
#                 3. EXTCODESIZE(addr) → 100 gas (warm access)
#
# HOW IT WORKS:
#   1. Factory uses EXTCODECOPY to load initcode, avoiding PC-relative jumps
#   2. Each CREATE2 deployment produces unique 24KB bytecode (via ADDRESS)
#   3. All contracts share same initcode hash for deterministic addresses
#   4. Attack rapidly accesses all contracts, stressing client's state handling


@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_extcodesize", "extcodesize_balance"],
)
@pytest.mark.valid_from("Prague")
def test_bloatnet_balance_extcodesize(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """
    BloatNet test using BALANCE + EXTCODESIZE with "on-the-fly" CREATE2
    address generation.

    This test:
    1. Assumes contracts are already deployed via the factory (salt 0 to N-1)
    2. Generates CREATE2 addresses dynamically during execution
    3. Calls BALANCE and EXTCODESIZE (order controlled by balance_first param)
    4. Maximizes cache eviction by accessing many contracts
    """
    # Stub Account
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Contract Construction
    setup = Bytecode()

    setup += Conditional(
        condition=Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
            # gas accounting
            address_warm=False,
            old_memory_size=0,
            new_memory_size=160,
        ),
        if_false=Op.INVALID,
    )

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(32),
        init_code_hash=Op.MLOAD(128),
        old_memory_size=160,
    )

    setup += create2_preimage
    setup += Op.CALLDATALOAD(0)  # [num_contract]

    balance_op = Op.POP(Op.BALANCE)
    extcodesize_op = Op.POP(Op.EXTCODESIZE)
    benchmark_ops = (
        (balance_op + extcodesize_op)
        if balance_first
        else (extcodesize_op + balance_op)
    )

    loop = While(
        body=(
            create2_preimage.address_op()
            + Op.DUP1
            + benchmark_ops
            + create2_preimage.increment_salt_op()
        ),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    salt_offset = 0

    while gas_remaining > intrinsic_gas + setup_cost + loop_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas + setup_cost:
            break

        num_contract = (
            gas_available - intrinsic_gas - setup_cost
        ) // loop_cost

        if num_contract == 0:
            break

        calldata = Hash(num_contract) + Hash(salt_offset)

        txs.append(
            Transaction(
                gas_limit=gas_available,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
            )
        )

        gas_remaining -= gas_available
        salt_offset += num_contract

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
    )


@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_extcodecopy", "extcodecopy_balance"],
)
@pytest.mark.valid_from("Prague")
def test_bloatnet_balance_extcodecopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """
    BloatNet test using BALANCE + EXTCODECOPY with on-the-fly CREATE2
    address generation.

    This test forces actual bytecode reads from disk by:
    1. Assumes contracts are already deployed via the factory
    2. Generating CREATE2 addresses dynamically during execution
    3. Using BALANCE and EXTCODECOPY (order controlled by balance_first param)
    4. Reading 1 byte from the END of the bytecode to force full contract load
    """
    # Stub Account
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Contract Construction
    setup = Bytecode()

    setup += Conditional(
        condition=Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
            # gas accounting
            address_warm=False,
            old_memory_size=0,
            new_memory_size=160,
        ),
        if_false=Op.INVALID,
    )

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(32),
        init_code_hash=Op.MLOAD(128),
        old_memory_size=160,
    )

    setup += create2_preimage
    setup += Op.CALLDATALOAD(0)  # [num_contract]

    max_contract_size = fork.max_code_size()

    balance_op = Op.POP(Op.BALANCE)
    extcodecopy_op = (
        Op.PUSH1(1)
        + Op.PUSH2(max_contract_size - 1)
        + Op.ADD(Op.MLOAD(32), 96)
        + Op.DUP4
        + Op.EXTCODECOPY
        + Op.POP
    )
    benchmark_ops = (
        (balance_op + extcodecopy_op)
        if balance_first
        else (extcodecopy_op + balance_op)
    )

    loop = While(
        body=(
            create2_preimage.address_op()
            + Op.DUP1
            + benchmark_ops
            + create2_preimage.increment_salt_op()
        ),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    salt_offset = 0

    while gas_remaining > intrinsic_gas + setup_cost + loop_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas + setup_cost:
            break

        num_contract = (
            gas_available - intrinsic_gas - setup_cost
        ) // loop_cost

        if num_contract == 0:
            break

        calldata = Hash(num_contract) + Hash(salt_offset)

        txs.append(
            Transaction(
                gas_limit=gas_available,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
            )
        )

        gas_remaining -= gas_available
        salt_offset += num_contract

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
    )


@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_extcodehash", "extcodehash_balance"],
)
@pytest.mark.valid_from("Prague")
def test_bloatnet_balance_extcodehash(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """
    BloatNet test using BALANCE + EXTCODEHASH with on-the-fly CREATE2
    address generation.

    This test:
    1. Assumes contracts are already deployed via the factory
    2. Generates CREATE2 addresses dynamically during execution
    3. Calls BALANCE and EXTCODEHASH (order controlled by balance_first param)
    4. Forces client to compute code hash for 24KB bytecode
    """
    # Stub Account
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Contract Construction
    setup = Bytecode()

    setup += Conditional(
        condition=Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
            # gas accounting
            address_warm=False,
            old_memory_size=0,
            new_memory_size=160,
        ),
        if_false=Op.INVALID,
    )

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(32),
        init_code_hash=Op.MLOAD(128),
        old_memory_size=160,
    )

    setup += create2_preimage
    setup += Op.CALLDATALOAD(0)  # [num_contract]

    balance_op = Op.POP(Op.BALANCE)
    extcodehash_op = Op.POP(Op.EXTCODEHASH)
    benchmark_ops = (
        (balance_op + extcodehash_op)
        if balance_first
        else (extcodehash_op + balance_op)
    )

    loop = While(
        body=(
            create2_preimage.address_op()
            + Op.DUP1
            + benchmark_ops
            + create2_preimage.increment_salt_op()
        ),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    salt_offset = 0

    while gas_remaining > intrinsic_gas + setup_cost + loop_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas + setup_cost:
            break

        num_contract = (
            gas_available - intrinsic_gas - setup_cost
        ) // loop_cost

        if num_contract == 0:
            break

        calldata = Hash(num_contract) + Hash(salt_offset)

        txs.append(
            Transaction(
                gas_limit=gas_available,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
            )
        )

        gas_remaining -= gas_available
        salt_offset += num_contract

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
    )


# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)

# Load token names from stubs.json for test parametrization
_STUBS_FILE = Path(__file__).parent / "stubs_bloatnet.json"
with open(_STUBS_FILE) as f:
    _STUBS = json.load(f)

# Extract unique token names for mixed sload/sstore tests
MIXED_TOKENS = [
    k.replace("test_mixed_sload_sstore_", "")
    for k in _STUBS.keys()
    if k.startswith("test_mixed_sload_sstore_")
]


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("token_name", MIXED_TOKENS)
@pytest.mark.parametrize(
    "sload_percent,sstore_percent",
    [
        pytest.param(10, 90, id="10-90"),
        pytest.param(30, 70, id="30-70"),
        pytest.param(50, 50, id="50-50"),
        pytest.param(70, 30, id="70-30"),
        pytest.param(90, 10, id="90-10"),
    ],
)
def test_mixed_sload_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    sload_percent: int,
    sstore_percent: int,
) -> None:
    """
    BloatNet mixed SLOAD/SSTORE benchmark with configurable operation ratios.

    This test:
    1. Uses a single ERC20 contract specified by token_name parameter
    2. Allocates full gas budget to that contract
    3. Divides gas into SLOAD and SSTORE portions by percentage
    4. Executes balanceOf (SLOAD) and approve (SSTORE) calls per the ratio
    5. Stresses clients with combined read/write operations on large contracts
    """
    stub_name = f"test_mixed_sload_sstore_{token_name}"
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Fixed overhead for SLOAD loop
    sload_loop_overhead = (
        # Attack contract loop overhead
        gas_costs.G_VERY_LOW * 2  # MLOAD counter (3*2)
        + gas_costs.G_VERY_LOW * 2  # MSTORE selector (3*2)
        + gas_costs.G_VERY_LOW * 3  # MLOAD + MSTORE address (3*3)
        + gas_costs.G_BASE  # POP (2)
        + gas_costs.G_BASE * 3  # SUB + MLOAD + MSTORE counter decrement
        + gas_costs.G_BASE * 2  # ISZERO * 2 for loop condition (2*2)
        + gas_costs.G_MID  # JUMPI (8)
    )

    # ERC20 balanceOf internal gas
    sload_erc20_internal = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_MID  # JUMPI to function (8)
        + gas_costs.G_JUMPDEST  # JUMPDEST at function start (1)
        + gas_costs.G_VERY_LOW * 2  # CALLDATALOAD arg (3*2)
        + gas_costs.G_KECCAK_256  # keccak256 static (30)
        + gas_costs.G_KECCAK_256_WORD * 2  # keccak256 dynamic 64 bytes
        + gas_costs.G_COLD_SLOAD  # Cold SLOAD - always cold
        + gas_costs.G_VERY_LOW * 3  # MSTORE result + RETURN setup (3*3)
    )

    # Fixed overhead for SSTORE loop
    sstore_loop_overhead = (
        # Attack contract loop body operations
        gas_costs.G_VERY_LOW  # MSTORE selector at memory[32] (3)
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_VERY_LOW  # MSTORE spender at memory[64] (3)
        + gas_costs.G_BASE  # POP call result (2)
        # Counter decrement
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_VERY_LOW  # PUSH1 1 (3)
        + gas_costs.G_VERY_LOW  # SUB (3)
        + gas_costs.G_VERY_LOW  # MSTORE counter back (3)
        # While loop condition check
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_BASE  # ISZERO (2)
        + gas_costs.G_BASE  # ISZERO (2)
        + gas_costs.G_MID  # JUMPI back to loop start (8)
    )

    # ERC20 approve internal gas
    # Cold SSTORE: 22100 = 20000 base + 2100 cold access
    sstore_erc20_internal = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_MID  # JUMPI to function (8)
        + gas_costs.G_JUMPDEST  # JUMPDEST at function start (1)
        + gas_costs.G_VERY_LOW  # CALLDATALOAD spender (3)
        + gas_costs.G_VERY_LOW  # CALLDATALOAD amount (3)
        + gas_costs.G_KECCAK_256  # keccak256 static (30)
        + gas_costs.G_KECCAK_256_WORD * 2  # keccak256 dynamic 64 bytes
        + gas_costs.G_COLD_SLOAD  # Cold SLOAD for allowance check (2100)
        + gas_costs.G_STORAGE_SET  # SSTORE base cost (20000)
        + gas_costs.G_COLD_SLOAD  # Additional cold storage access (2100)
        + gas_costs.G_VERY_LOW  # PUSH1 1 for return value (3)
        + gas_costs.G_VERY_LOW  # MSTORE return value (3)
        + gas_costs.G_VERY_LOW  # PUSH1 32 for return size (3)
        + gas_costs.G_VERY_LOW  # PUSH1 0 for return offset (3)
    )

    # Account for cold/warm transitions in CALL costs
    # First SLOAD call is COLD (2600), rest are WARM (100)
    sload_warm_cost = (
        sload_loop_overhead
        + gas_costs.G_WARM_ACCOUNT_ACCESS
        + sload_erc20_internal
    )
    cold_warm_diff = (
        gas_costs.G_COLD_ACCOUNT_ACCESS - gas_costs.G_WARM_ACCOUNT_ACCESS
    )

    # First SSTORE call is COLD (2600), rest are WARM (100)
    sstore_warm_cost = (
        sstore_loop_overhead
        + gas_costs.G_WARM_ACCOUNT_ACCESS
        + sstore_erc20_internal
    )

    # Deploy ERC20 contract using stub
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=stub_name,
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate total available gas and split by percentage
    total_available_gas = gas_benchmark_value - (intrinsic_gas * num_txs)
    sload_gas = (total_available_gas * sload_percent) // 100
    sstore_gas = (total_available_gas * sstore_percent) // 100

    # Calculate total calls for each operation type
    total_sload_calls = int((sload_gas - cold_warm_diff) // sload_warm_cost)
    total_sstore_calls = int((sstore_gas - cold_warm_diff) // sstore_warm_cost)

    # Distribute calls across transactions
    sload_calls_per_tx = total_sload_calls // num_txs
    sstore_calls_per_tx = total_sstore_calls // num_txs

    # Log test requirements
    print(
        f"Token: {token_name}, "
        f"Total gas budget: {gas_benchmark_value / 1_000_000:.1f}M gas "
        f"({sload_percent}% SLOAD, {sstore_percent}% SSTORE). "
        f"{total_sload_calls} balanceOf, {total_sstore_calls} approve "
        f"across {num_txs} tx(s)."
    )

    # Build transactions
    txs = []
    post = {}
    sload_remaining = total_sload_calls
    sstore_remaining = total_sstore_calls

    for i in range(num_txs):
        # Last tx gets remaining calls
        tx_sload_calls = (
            sload_calls_per_tx if i < num_txs - 1 else sload_remaining
        )
        tx_sstore_calls = (
            sstore_calls_per_tx if i < num_txs - 1 else sstore_remaining
        )
        sload_remaining -= tx_sload_calls
        sstore_remaining -= tx_sstore_calls

        # Build attack code for this transaction
        attack_code: Bytecode = (
            Op.JUMPDEST  # Entry point
            + Op.MSTORE(offset=0, value=BALANCEOF_SELECTOR)
            # SLOAD operations (balanceOf)
            + Op.MSTORE(offset=32, value=tx_sload_calls)
            + While(
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    Op.CALL(
                        address=erc20_address,
                        value=0,
                        args_offset=28,
                        args_size=36,
                        ret_offset=0,
                        ret_size=0,
                    )
                    + Op.POP
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
            # SSTORE operations (approve)
            + Op.MSTORE(offset=0, value=APPROVE_SELECTOR)
            + Op.MSTORE(offset=32, value=tx_sstore_calls)
            + While(
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    Op.MSTORE(offset=64, value=Op.MLOAD(32))
                    + Op.CALL(
                        address=erc20_address,
                        value=0,
                        args_offset=28,
                        args_size=68,
                        ret_offset=0,
                        ret_size=0,
                    )
                    + Op.POP
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
        )

        # Deploy attack contract for this tx
        attack_address = pre.deploy_contract(code=attack_code)

        # Calculate gas for this transaction
        this_tx_gas = min(
            tx_gas_limit, gas_benchmark_value - (i * tx_gas_limit)
        )

        txs.append(
            Transaction(
                to=attack_address,
                gas_limit=this_tx_gas,
                sender=pre.fund_eoa(),
            )
        )

        # Add to post-state
        post[attack_address] = Account(storage={})

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post=post,
    )
