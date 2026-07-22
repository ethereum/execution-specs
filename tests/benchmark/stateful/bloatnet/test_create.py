"""Benchmark CREATE2 deployment with immediate access to the new account."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Hash,
    Header,
    Initcode,
    IteratingBytecode,
    Op,
    While,
    compute_create2_address,
)

from tests.benchmark.helper.loops import DECREMENT_COUNTER_CONDITION


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
    """Benchmark CREATE2 followed by immediate opcode access."""
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

    code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        iterating_subcall=initcode,
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

    # Salts are contiguous from 0: calldata[0:32] holds each tx's
    # iteration count.
    total_iterations = sum(int.from_bytes(tx.data[:32], "big") for tx in txs)

    post: dict[Address, Account | None] = {
        compute_create2_address(
            address=attack_contract_address, salt=salt, initcode=initcode
        ): Account(nonce=1, code=deploy_code)
        for salt in range(total_iterations)
    }
    post[
        compute_create2_address(
            address=attack_contract_address,
            salt=total_iterations,
            initcode=initcode,
        )
    ] = Account.NONEXISTENT

    expected_block_gas_used = sum(tx.block_gas_cost for tx in txs)
    expected_benchmark_gas_used = sum(tx.gas_cost for tx in txs)

    block = Block(
        txs=txs,
        header_verify=Header(gas_used=expected_block_gas_used),
    )

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[block],
        expected_benchmark_gas_used=expected_benchmark_gas_used,
    )
