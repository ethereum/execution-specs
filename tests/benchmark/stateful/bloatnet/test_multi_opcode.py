"""
abstract: BloatNet bench cases extracted from https://hackmd.io/9icZeLN7R0Sk5mIjKlZAHQ.

   The idea of all these tests is to stress client implementations to find out
   where the limits of processing are focusing specifically on state-related
   operations.
"""

import pytest
from execution_testing import (
    AccessList,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Conditional,
    Create2PreimageLayout,
    Fork,
    Hash,
    Op,
    Transaction,
    While,
)

from tests.benchmark.stateful.helpers import (
    APPROVE_SELECTOR,
    BALANCEOF_SELECTOR,
    FACTORY_STUBS,
    MIXED_TOKENS,
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
    "factory_stub",
    FACTORY_STUBS,
    ids=lambda s: s.replace("bloatnet_factory_", "").upper(),
)
@pytest.mark.parametrize(
    "second_opcode",
    ["EXTCODESIZE", "EXTCODECOPY", "EXTCODEHASH", "STATICCALL", "CALL"],
)
@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_first", "opcode_first"],
)
def test_bloatnet_balance_opcode(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
    second_opcode: str,
    factory_stub: str,
) -> None:
    """Benchmark BALANCE paired with a second opcode on bloatnet factory contracts."""
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub=factory_stub,
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

    # Build the second opcode's bytecode
    balance_op = Op.POP(Op.BALANCE)

    if second_opcode == "EXTCODESIZE":
        other_op = Op.POP(Op.EXTCODESIZE)
    elif second_opcode == "EXTCODECOPY":
        max_contract_size = fork.max_code_size()
        other_op = Op.POP(
            Op.EXTCODECOPY(
                address=Op.DUP4,
                dest_offset=Op.ADD(Op.MLOAD(32), 96),
                offset=max_contract_size - 1,
                size=1,
            )
        )
    elif second_opcode == "EXTCODEHASH":
        other_op = Op.POP(Op.EXTCODEHASH)
    elif second_opcode == "STATICCALL":
        # gas=1: forces account/code loading setup, then immediately fails
        other_op = Op.POP(
            Op.STATICCALL(
                gas=1,
                address=Op.DUP2,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            )
        )
    elif second_opcode == "CALL":
        # gas=1: forces account/code loading setup, then immediately fails
        other_op = Op.POP(
            Op.CALL(
                gas=1,
                address=Op.DUP2,
                value=0,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            )
        )
    else:
        raise ValueError(f"Unsupported opcode: {second_opcode}")

    benchmark_ops = (
        (balance_op + other_op) if balance_first else (other_op + balance_op)
    )

    loop = While(
        body=(
            create2_preimage.address_op()
            + Op.DUP1
            + benchmark_ops
            + create2_preimage.increment_salt_op()
        ),
        condition=Op.PUSH1(1)  # [1, num_contract]
        + Op.SWAP1  # [num_contract, 1]
        + Op.SUB  # [num_contract-1]
        + Op.DUP1  # [num_contract-1, num_contract-1]
        + Op.ISZERO  # [num_contract-1==0, num_contract-1]
        + Op.ISZERO,  # [num_contract-1!=0, num_contract-1]
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_intrinsic = intrinsic_cost_calc(calldata=b"\xff" * 64)

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    salt_offset = 0
    total_gas_consumed = 0

    while gas_remaining > max_intrinsic + setup_cost + loop_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < max_intrinsic + setup_cost:
            break

        num_contract = (
            gas_available - max_intrinsic - setup_cost
        ) // loop_cost

        if num_contract == 0:
            break

        calldata = Hash(num_contract) + Hash(salt_offset)
        actual_intrinsic = intrinsic_cost_calc(
            calldata=bytes(calldata),
            return_cost_deducted_prior_execution=True,
        )
        tx_gas = (
            actual_intrinsic + setup_cost
            + num_contract * loop_cost
        )

        txs.append(
            Transaction(
                gas_limit=tx_gas,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
            )
        )

        total_gas_consumed += tx_gas
        gas_remaining -= gas_available
        salt_offset += num_contract

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )


# CALL+VALUE BENCHMARK ARCHITECTURE:
#
#   test_bloatnet_call_value_existing:
#   Same factory pattern as test_bloatnet_balance_opcode, but performs
#   CALL with value=1 wei to each factory contract. The subcall fails
#   (insufficient gas for 24KB bytecode), but GAS_CALL_VALUE (9000 gas)
#   is still charged on top of the cold account access cost.
#
#   test_bloatnet_call_value_new_account:
#   Generates unique addresses from keccak256(counter) and CALLs each with
#   value=1 wei. Since these addresses have no code, the subcall succeeds
#   (via the 2300 gas stipend), transferring value and creating a new account.
#   Each iteration costs ~36,600 gas (cold + value + new_account),
#   stressing trie expansion through massive new account creation.


@pytest.mark.parametrize(
    "factory_stub",
    FACTORY_STUBS,
    ids=lambda s: s.replace("bloatnet_factory_", "").upper(),
)
def test_bloatnet_call_value_existing(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    factory_stub: str,
) -> None:
    """Benchmark CALL with value transfer to cold existing factory contracts.

    Unlike the existing CALL test which uses gas=1 and value=0, this test
    passes value=1 wei per call, adding GAS_CALL_VALUE (9000 gas) to each
    cold account access. The subcall fails (insufficient gas for bytecode
    execution), so value is not actually transferred, but the gas penalty
    is still charged.
    """
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub=factory_stub,
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

    # CALL with value=1 to factory contracts.
    # The address is computed inline via SHA3, avoiding DUP depth issues.
    # gas=1: subcall gets 1 + 2300 stipend, still not enough for 24KB
    # bytecode → subcall fails, but cold + value gas costs are charged.
    call_value_op = Op.POP(
        Op.CALL(
            gas=1,
            address=create2_preimage.address_op(),
            value=1,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
            # gas accounting
            value_transfer=True,
        )
    )

    loop = While(
        body=(
            call_value_op
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
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_intrinsic = intrinsic_cost_calc(calldata=b"\xff" * 64)

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    salt_offset = 0
    total_gas_consumed = 0

    while gas_remaining > max_intrinsic + setup_cost + loop_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < max_intrinsic + setup_cost:
            break

        num_contract = (
            gas_available - max_intrinsic - setup_cost
        ) // loop_cost

        if num_contract == 0:
            break

        calldata = Hash(num_contract) + Hash(salt_offset)
        actual_intrinsic = intrinsic_cost_calc(
            calldata=bytes(calldata),
            return_cost_deducted_prior_execution=True,
        )
        tx_gas = (
            actual_intrinsic + setup_cost
            + num_contract * loop_cost
        )

        txs.append(
            Transaction(
                gas_limit=tx_gas,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
            )
        )

        total_gas_consumed += tx_gas
        gas_remaining -= gas_available
        salt_offset += num_contract

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )


def test_bloatnet_call_value_new_account(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """Benchmark CALL with value transfer to non-existent accounts.

    Generate unique addresses via keccak256(counter) and CALL each with
    value=1 wei. Since these addresses have no code, the subcall succeeds
    (via the 2300 gas stipend), transferring value and creating a new
    account in the trie. Each iteration costs ~36,600 gas:
    - GAS_COLD_ACCOUNT_ACCESS: 2,600
    - GAS_CALL_VALUE: 9,000
    - GAS_NEW_ACCOUNT: 25,000

    This stresses trie expansion through massive new account creation.
    """
    # Memory layout: MEM[0..31] = counter (incremented each iteration)
    setup = (
        Op.MSTORE(
            0,
            Op.CALLDATALOAD(32),  # salt_offset (starting counter)
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.CALLDATALOAD(0)  # [num_calls]
    )

    # CALL with value=1 to keccak256-derived addresses.
    # gas=0: subcall gets 0 + 2300 stipend. No code at target → succeeds.
    # Value is transferred, new account is created in trie.
    call_value_op = Op.POP(
        Op.CALL(
            gas=0,
            address=Op.SHA3(0, 32, data_size=32),
            value=1,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
            # gas accounting
            value_transfer=True,
            account_new=True,
        )
    )

    # Increment counter in memory for next address
    increment_counter = Op.MSTORE(0, Op.ADD(Op.MLOAD(0), 1))

    loop = While(
        body=(
            call_value_op
            + increment_counter
        ),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )

    # Contract Deployment — needs balance for value transfers (1 wei each)
    code = setup + loop
    attack_contract_address = pre.deploy_contract(
        code=code,
        balance=10**18,  # 1 ETH, enough for all iterations
    )

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_intrinsic = intrinsic_cost_calc(calldata=b"\xff" * 64)

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    salt_offset = 0
    total_gas_consumed = 0

    while gas_remaining > max_intrinsic + setup_cost + loop_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < max_intrinsic + setup_cost:
            break

        num_calls = (
            gas_available - max_intrinsic - setup_cost
        ) // loop_cost

        if num_calls == 0:
            break

        calldata = Hash(num_calls) + Hash(salt_offset)
        actual_intrinsic = intrinsic_cost_calc(
            calldata=bytes(calldata),
            return_cost_deducted_prior_execution=True,
        )
        tx_gas = (
            actual_intrinsic + setup_cost
            + num_calls * loop_cost
        )

        txs.append(
            Transaction(
                gas_limit=tx_gas,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
            )
        )

        total_gas_consumed += tx_gas
        gas_remaining -= gas_available
        salt_offset += num_calls

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )


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
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    sload_percent: int,
    sstore_percent: int,
) -> None:
    """Benchmark mixed SLOAD/SSTORE on bloatnet."""
    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=f"test_mixed_sload_sstore_{token_name}",
    )

    # Contract Construction
    # MEM[0] = function selector
    # MEM[32] = address/slot offset (incremented each iteration)
    # MEM[64] = spender/amount for approve (copied from MEM[32])
    setup = (
        Op.MSTORE(
            0,
            BALANCEOF_SELECTOR,
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.MSTORE(
            32,
            Op.CALLDATALOAD(64),  # Slot Offset
            # gas accounting
            old_memory_size=32,
            new_memory_size=64,
        )
        + Op.CALLDATALOAD(0)  # [num_sload_calls]
    )

    sload_loop = While(
        body=Op.POP(
            Op.CALL(
                address=erc20_address,
                value=0,
                args_offset=28,
                args_size=36,
                ret_offset=0,
                ret_size=0,
                # gas accounting
                address_warm=True,
            )
        )
        + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.PUSH1(1)  # [1, num_sload]
        + Op.SWAP1  # [num_sload, 1]
        + Op.SUB  # [num_sload-1]
        + Op.DUP1  # [num_sload-1, num_sload-1]
        + Op.ISZERO  # [num_sload-1==0, num_sload-1]
        + Op.ISZERO,  # [num_sload-1!=0, num_sload-1]
    )

    transition = (
        Op.POP  # remove 0 counter from sload loop
        + Op.MSTORE(0, APPROVE_SELECTOR)
        + Op.CALLDATALOAD(32)  # [num_sstore_calls]
    )

    sstore_loop = While(
        body=(
            Op.MSTORE(64, Op.MLOAD(32))
            + Op.POP(
                Op.CALL(
                    address=erc20_address,
                    value=0,
                    args_offset=28,
                    args_size=68,
                    ret_offset=0,
                    ret_size=0,
                    # gas accounting
                    address_warm=True,
                )
            )
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
        ),
        condition=Op.PUSH1(1)  # [1, num_sstore]
        + Op.SWAP1  # [num_sstore, 1]
        + Op.SUB  # [num_sstore-1]
        + Op.DUP1  # [num_sstore-1, num_sstore-1]
        + Op.ISZERO  # [num_sstore-1==0, num_sstore-1]
        + Op.ISZERO,  # [num_sstore-1!=0, num_sstore-1]
    )

    # Contract Deployment
    code = setup + sload_loop + transition + sstore_loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    sload_loop_cost = sload_loop.gas_cost(fork)
    transition_cost = transition.gas_cost(fork)
    sstore_loop_cost = sstore_loop.gas_cost(fork)

    access_list = [AccessList(address=erc20_address, storage_keys=[])]
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_intrinsic = intrinsic_cost_calc(
        access_list=access_list,
        calldata=b"\xff" * 96,
    )

    # ERC20 balanceOf bytecode structure (gas cost model):
    sload_dispatch = (
        # Selector dispatch
        Op.PUSH4(BALANCEOF_SELECTOR)
        + Op.EQ
        + Op.JUMPI
        # Function body
        + Op.JUMPDEST
        + Op.MSTORE(0, Op.CALLDATALOAD(4))
        + Op.MSTORE(32, 0)
        + Op.MSTORE(
            0,
            Op.SLOAD(
                Op.SHA3(
                    0,
                    64,
                    # gas accounting
                    data_size=64,
                    old_memory_size=0,
                    new_memory_size=64,
                )
            ),
        )
        + Op.RETURN(0, 32)
    )

    sload_dispatch_cost = sload_dispatch.gas_cost(fork)

    # ERC20 approve bytecode structure (gas cost model):
    sstore_dispatch = (
        # Selector dispatch
        Op.PUSH4(APPROVE_SELECTOR)
        + Op.EQ
        + Op.JUMPI
        # Function body
        + Op.JUMPDEST
        + Op.CALLDATALOAD(4)
        + Op.CALLDATALOAD(36)
        + Op.MSTORE(0, Op.CALLER)
        + Op.MSTORE(32, 1)
        + Op.MSTORE(
            32,
            Op.SHA3(
                0,
                64,
                # gas accounting
                data_size=64,
                old_memory_size=0,
                new_memory_size=64,
            ),
        )
        + Op.MSTORE(0, Op.CALLDATALOAD(4))
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
        )
        + Op.DUP1
        + Op.SLOAD.with_metadata(key_warm=False)
        + Op.POP
        + Op.SSTORE
        # Return true
        + Op.MSTORE(0, 1)
        + Op.RETURN(0, 32)
    )

    sstore_dispatch_cost = sstore_dispatch.gas_cost(fork)

    sload_iter_cost = sload_loop_cost + sload_dispatch_cost
    sstore_iter_cost = sstore_loop_cost + sstore_dispatch_cost
    fixed_overhead = max_intrinsic + setup_cost + transition_cost

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    slot_offset = 0
    total_gas_consumed = 0

    while gas_remaining > fixed_overhead + sload_iter_cost + sstore_iter_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < fixed_overhead + sload_iter_cost + sstore_iter_cost:
            break

        available = gas_available - fixed_overhead
        sload_gas = (available * sload_percent) // 100
        sstore_gas = (available * sstore_percent) // 100

        num_sload = sload_gas // sload_iter_cost
        num_sstore = sstore_gas // sstore_iter_cost

        if num_sload == 0 or num_sstore == 0:
            break

        calldata = (
            Hash(num_sload) + Hash(num_sstore) + Hash(slot_offset)
        )
        actual_intrinsic = intrinsic_cost_calc(
            access_list=access_list,
            calldata=bytes(calldata),
            return_cost_deducted_prior_execution=True,
        )
        tx_gas = (
            actual_intrinsic + setup_cost + transition_cost
            + num_sload * sload_iter_cost
            + num_sstore * sstore_iter_cost
        )

        txs.append(
            Transaction(
                gas_limit=tx_gas,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )

        total_gas_consumed += tx_gas
        gas_remaining -= gas_available
        slot_offset += num_sload + num_sstore

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )
