"""Benchmark call operations with value transfer on target accounts."""

from execution_testing import (
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    While,
    keccak256,
)

from tests.benchmark.helper.loops import DECREMENT_COUNTER_CONDITION


def test_call_value_to_empty(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Benchmark CALL with value transfer to non-existent accounts."""
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
        body=(call_value_op + increment_counter),
        condition=DECREMENT_COUNTER_CONDITION,
    )

    # Contract Deployment — needs balance for value transfers (1 wei each)
    code = IteratingBytecode(
        setup=setup,
        iterating=loop,
    )

    initial_balance = 10**9
    attack_contract_address = pre.deploy_contract(
        code=code,
        balance=initial_balance,
    )

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

    total_iterations = sum(int.from_bytes(tx.data[:32], "big") for tx in txs)

    def new_account_address(counter: int) -> Address:
        return Address(bytes(keccak256(counter.to_bytes(32, "big")))[12:])

    post = {
        new_account_address(counter): Account(balance=1)
        for counter in range(total_iterations)
    }
    post[attack_contract_address] = Account(
        balance=initial_balance - total_iterations
    )

    expected_gas_used = (
        sum(tx.gas_cost for tx in txs)
        - fork.call_value_stipend() * total_iterations
    )

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=expected_gas_used,
    )
