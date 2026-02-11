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
    "balance_first",
    [True, False],
    ids=["balance_extcodesize", "extcodesize_balance"],
)
def test_bloatnet_balance_extcodesize(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """Benchmark BALANACE and EXTCODESIZE combination on bloatnet."""
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
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 64
    )

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
def test_bloatnet_balance_extcodecopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """Benchmark BALANACE and EXTCODECOPY combination on bloatnet."""
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
    extcodecopy_op = Op.POP(
        Op.EXTCODECOPY(
            address=Op.DUP4,
            destOffset=Op.ADD(Op.MLOAD(32), 96),
            offset=max_contract_size - 1,
            size=1,
        )
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
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 64
    )

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
def test_bloatnet_balance_extcodehash(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """Benchmark BALANACE and EXTCODEHASH combination on bloatnet."""
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
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 64
    )

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
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        calldata=b"\xff" * 96,
    )

    # ERC20 balanceOf bytecode structure:
    sload_dispatch = (
        # Selector dispatch
        Op.PUSH4(BALANCEOF_SELECTOR)
        + Op.EQ
        + Op.JUMPI
        # Function body
        + Op.JUMPDEST
        + Op.CALLDATALOAD(4)
        + Op.MSTORE(0)
        + Op.MSTORE(32, 0)
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
            old_memory_size=0,
            new_memory_size=64,
        )
        + Op.SLOAD
        # Return value
        + Op.MSTORE(0)
        + Op.RETURN(0, 32)
    )

    sload_dispatch_cost = sload_dispatch.gas_cost(fork)

    # ERC20 approve bytecode structure:
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
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
            old_memory_size=0,
            new_memory_size=64,
        )
        + Op.MSTORE(32)
        + Op.MSTORE(0, Op.CALLDATALOAD(4))
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
        )
        + Op.DUP1
        + Op.SLOAD.with_metadata(access_warm=False)
        + Op.POP
        + Op.SSTORE
        # Return true
        + Op.PUSH1(1)
        + Op.MSTORE(0)
        + Op.PUSH1(32)
        + Op.PUSH1(0)
        + Op.RETURN(0, 32)
    )

    sstore_dispatch_cost = sstore_dispatch.gas_cost(fork)

    sload_iter_cost = sload_loop_cost + sload_dispatch_cost
    sstore_iter_cost = sstore_loop_cost + sstore_dispatch_cost
    fixed_overhead = intrinsic_gas + setup_cost + transition_cost

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    slot_offset = 0

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

        calldata = Hash(num_sload) + Hash(num_sstore) + Hash(slot_offset)

        txs.append(
            Transaction(
                gas_limit=gas_available,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )

        gas_remaining -= gas_available
        slot_offset += num_sload + num_sstore

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
    )
