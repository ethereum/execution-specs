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
    IteratingBytecode,
    Op,
    While,
)

from tests.benchmark.stateful.helpers import (
    DECREMENT_COUNTER_CONDITION,
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
    [Op.EXTCODEHASH, Op.BALANCE, Op.EXTCODECOPY],
)
def test_create2_immediate_access(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    code_size: int,
    access_opcode: Op,
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
    if access_opcode == Op.EXTCODEHASH:
        access_op = Op.POP(Op.EXTCODEHASH(create2_op, address_warm=True))
    elif access_opcode == Op.BALANCE:
        access_op = Op.POP(Op.BALANCE(create2_op, address_warm=True))
    elif access_opcode == Op.EXTCODECOPY:
        # Copy 1 byte from end of deployed code
        access_op = Op.EXTCODECOPY(
            address=create2_op,
            dest_offset=counter_offset + 32,
            offset=max(code_size - 1, 0),
            size=1,
            address_warm=True,
            data_size=1,
            old_memory_size=counter_offset + 32,
            new_memory_size=counter_offset + 33,
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
        condition=DECREMENT_COUNTER_CONDITION,
    )

    subcall_cost = initcode.execution_gas(fork) + initcode.deployment_gas(fork)

    code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        iterating_subcall=subcall_cost,
    )
    attack_contract_address = pre.deploy_contract(code=code)

    def calldata_builder(iteration_count: int, start_iteration: int) -> bytes:
        return bytes(Hash(iteration_count) + Hash(start_iteration))

    txs = list(
        code.transactions_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            sender=pre.fund_eoa(),
            to=attack_contract_address,
            calldata=calldata_builder,
        )
    )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        skip_gas_used_validation=True,
    )
