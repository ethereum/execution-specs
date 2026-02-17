"""
abstract: CREATE2 deploy + immediate access benchmark cases.

   These tests benchmark the deploy-then-access pattern: CREATE2 a
   contract, then immediately query it with EXTCODEHASH, BALANCE, or
   EXTCODECOPY in the same transaction. This tests whether clients
   efficiently serve state that was just written to the trie.
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Hash,
    Initcode,
    Op,
    Transaction,
    While,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# CREATE2 + ACCESS BENCHMARK ARCHITECTURE:
#
#   [Init Code Holder Contract] ──── Runtime code = init code bytes
#           │
#           │  EXTCODECOPY by attack contract during setup
#           │
#   [Attack Contract]
#       │ Setup:
#       │   1. EXTCODECOPY init code from holder into MEM[0..N]
#       │   2. Store starting counter at MEM[N..N+32]
#       │
#       │ Loop(i=0 to M):
#       │   1. CREATE2(value=0, offset=0, size=N, salt=counter)
#       │      → deploys new contract, returns address
#       │   2. EXTCODEHASH / BALANCE / EXTCODECOPY on address
#       │   3. Increment counter
#
# WHY IT STRESSES CLIENTS:
#   - Each CREATE2 inserts a new account + code into the trie
#   - Immediate access tests if the just-written data is efficiently
#     served from write caches vs requiring a trie re-read
#   - Code deposit cost (200 gas/byte) dominates: larger code =
#     fewer iterations but more trie data per cycle


@pytest.mark.parametrize(
    "code_size",
    [32, 256, 1024],
    ids=["32B", "256B", "1KB"],
)
@pytest.mark.parametrize(
    "access_opcode",
    ["EXTCODEHASH", "BALANCE", "EXTCODECOPY"],
)
def test_create2_immediate_access(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    code_size: int,
    access_opcode: str,
) -> None:
    """
    Benchmark CREATE2 followed by immediate opcode access.

    Deploy a contract via CREATE2, then immediately query it with the
    specified access opcode. Each iteration creates a new trie entry
    and reads from it, stressing the deploy-then-access path.
    """
    # Build init code that deploys `code_size` bytes of zeros
    deploy_code = bytes(code_size)
    initcode = Initcode(deploy_code=deploy_code)
    init_code_bytes = bytes(initcode)
    init_code_size = len(init_code_bytes)

    # Deploy holder contract whose runtime code IS the init code
    init_holder = pre.deploy_contract(
        code=Bytecode(
            init_code_bytes,
            popped_stack_items=0,
            pushed_stack_items=0,
        ),
    )

    # Memory layout:
    #   MEM[0 .. init_code_size-1]     = init code (for CREATE2)
    #   MEM[init_code_size .. +31]     = counter (salt)
    counter_offset = init_code_size

    # Setup: load init code + starting counter
    setup = (
        Op.EXTCODECOPY(
            address=init_holder,
            dest_offset=0,
            offset=0,
            size=init_code_size,
            address_warm=False,
            data_size=init_code_size,
            old_memory_size=0,
            new_memory_size=init_code_size,
        )
        + Op.MSTORE(
            counter_offset,
            Op.CALLDATALOAD(32),
            old_memory_size=init_code_size,
            new_memory_size=counter_offset + 32,
        )
        + Op.CALLDATALOAD(0)  # [num_iters]
    )

    # CREATE2 — deploys new contract each iteration
    create2_op = Op.CREATE2(
        value=0,
        offset=0,
        size=init_code_size,
        salt=Op.MLOAD(counter_offset),
        init_code_size=init_code_size,
        old_memory_size=counter_offset + 32,
        new_memory_size=counter_offset + 32,
    )

    # Access the just-deployed contract
    if access_opcode == "EXTCODEHASH":
        access_op = Op.POP(
            Op.EXTCODEHASH(create2_op, address_warm=True)
        )
    elif access_opcode == "BALANCE":
        access_op = Op.POP(
            Op.BALANCE(create2_op, address_warm=True)
        )
    elif access_opcode == "EXTCODECOPY":
        # Copy 1 byte from end of deployed code
        access_op = Op.EXTCODECOPY(
            address=create2_op,
            dest_offset=counter_offset + 32,
            offset=max(code_size - 1, 0),
            size=1,
            address_warm=True,
            data_size=1,
            old_memory_size=counter_offset + 32,
            new_memory_size=counter_offset + 64,
        )
    else:
        raise ValueError(f"Unsupported opcode: {access_opcode}")

    # Increment counter
    increment = Op.MSTORE(
        counter_offset,
        Op.ADD(Op.MLOAD(counter_offset), 1),
    )

    loop = While(
        body=access_op + increment,
        condition=(
            Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO
        ),
    )

    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting — CREATE2 subcall costs (init execution + code
    # deposit) are not captured by loop.gas_cost(), so add them.
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)

    init_exec_gas = initcode.execution_gas(fork)
    code_deposit_gas = initcode.deployment_gas(fork)
    full_iteration_cost = (
        loop_cost + init_exec_gas + code_deposit_gas
    )

    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_intrinsic = intrinsic_cost_calc(calldata=b"\xff" * 64)

    # Attack Loop
    gas_remaining = gas_benchmark_value
    txs = []
    counter_start = 0
    total_gas_consumed = 0

    while gas_remaining > max_intrinsic + setup_cost + full_iteration_cost:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < max_intrinsic + setup_cost:
            break

        num_iters = (
            gas_available - max_intrinsic - setup_cost
        ) // full_iteration_cost

        if num_iters == 0:
            break

        calldata = Hash(num_iters) + Hash(counter_start)
        actual_intrinsic = intrinsic_cost_calc(
            calldata=bytes(calldata),
            return_cost_deducted_prior_execution=True,
        )
        tx_gas = (
            actual_intrinsic + setup_cost
            + num_iters * full_iteration_cost
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
        counter_start += num_iters

    assert txs, "Gas loop produced zero transactions"
    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )
