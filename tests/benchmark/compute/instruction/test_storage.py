"""
Benchmark storage instructions.

Supported Opcodes:
- SLOAD
- SSTORE
- TLOAD
- TSTORE
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Environment,
    Fork,
    JumpLoopGenerator,
    Op,
    TestPhaseManager,
    Transaction,
    While,
    compute_create_address,
)

from tests.benchmark.compute.helpers import StorageAction, TransactionResult


# `key_mut` indicates the key isn't fixed.
@pytest.mark.parametrize("key_mut", [True, False])
# `val_mut` indicates that at the end of each big-loop, the value of the target
# key changes.
@pytest.mark.parametrize("val_mut", [True, False])
def test_tload(
    benchmark_test: BenchmarkTestFiller,
    key_mut: bool,
    val_mut: bool,
) -> None:
    """Benchmark TLOAD instruction."""
    start_key = 41
    code_key_mut = Bytecode()
    code_val_mut = Bytecode()
    setup = Bytecode()
    if key_mut and val_mut:
        setup = Op.PUSH1(start_key)
        attack_block = Op.POP(Op.TLOAD(Op.DUP1))
        code_key_mut = Op.POP + Op.GAS
        code_val_mut = Op.TSTORE(Op.DUP2, Op.GAS)
    if key_mut and not val_mut:
        attack_block = Op.POP(Op.TLOAD(Op.GAS))
    if not key_mut and val_mut:
        attack_block = Op.POP(Op.TLOAD(Op.CALLVALUE))
        code_val_mut = Op.TSTORE(
            Op.CALLVALUE, Op.GAS
        )  # CALLVALUE configured in the tx
    if not key_mut and not val_mut:
        attack_block = Op.POP(Op.TLOAD(Op.CALLVALUE))

    cleanup = code_key_mut + code_val_mut
    tx_value = start_key if not key_mut and val_mut else 0

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
            tx_kwargs={
                "value": tx_value,
            },
        ),
    )


@pytest.mark.parametrize("key_mut", [True, False])
@pytest.mark.parametrize("dense_val_mut", [True, False])
def test_tstore(
    benchmark_test: BenchmarkTestFiller,
    key_mut: bool,
    dense_val_mut: bool,
) -> None:
    """Benchmark TSTORE instruction."""
    init_key = 42
    setup = Op.PUSH1(init_key)

    # If `dense_val_mut` is set, we use GAS as a cheap way of always
    # storing a different value than
    # the previous one.
    attack_block = Op.TSTORE(Op.DUP2, Op.GAS if dense_val_mut else Op.DUP1)

    # If `key_mut` is True, we mutate the key on every iteration of the
    # big loop.
    cleanup = Op.POP + Op.GAS if key_mut else Bytecode()

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block, cleanup=cleanup
        ),
    )


@pytest.mark.parametrize(
    "storage_action,tx_result",
    [
        pytest.param(
            StorageAction.READ,
            TransactionResult.SUCCESS,
            id="SSLOAD",
        ),
        pytest.param(
            StorageAction.WRITE_SAME_VALUE,
            TransactionResult.SUCCESS,
            id="SSTORE same value",
        ),
        pytest.param(
            StorageAction.WRITE_SAME_VALUE,
            TransactionResult.REVERT,
            id="SSTORE same value, revert",
        ),
        pytest.param(
            StorageAction.WRITE_SAME_VALUE,
            TransactionResult.OUT_OF_GAS,
            id="SSTORE same value, out of gas",
        ),
        pytest.param(
            StorageAction.WRITE_NEW_VALUE,
            TransactionResult.SUCCESS,
            id="SSTORE new value",
        ),
        pytest.param(
            StorageAction.WRITE_NEW_VALUE,
            TransactionResult.REVERT,
            id="SSTORE new value, revert",
        ),
        pytest.param(
            StorageAction.WRITE_NEW_VALUE,
            TransactionResult.OUT_OF_GAS,
            id="SSTORE new value, out of gas",
        ),
    ],
)
@pytest.mark.parametrize(
    "absent_slots",
    [
        True,
        False,
    ],
)
def test_storage_access_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_action: StorageAction,
    absent_slots: bool,
    env: Environment,
    gas_benchmark_value: int,
    tx_result: TransactionResult,
) -> None:
    """
    Benchmark cold storage slot accesses.
    """
    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()

    loop_cost = gas_costs.G_COLD_SLOAD  # All accesses are always cold
    if storage_action == StorageAction.WRITE_NEW_VALUE:
        if not absent_slots:
            loop_cost += gas_costs.G_STORAGE_RESET
        else:
            loop_cost += gas_costs.G_STORAGE_SET
    elif storage_action == StorageAction.WRITE_SAME_VALUE:
        if absent_slots:
            loop_cost += gas_costs.G_STORAGE_SET
        else:
            loop_cost += gas_costs.G_WARM_SLOAD
    elif storage_action == StorageAction.READ:
        loop_cost += 0  # Only G_COLD_SLOAD is charged

    # Contract code
    execution_code_body = Bytecode()
    if storage_action == StorageAction.WRITE_SAME_VALUE:
        # All the storage slots in the contract are initialized to their index.
        # That is, storage slot `i` is initialized to `i`.
        execution_code_body = Op.SSTORE(Op.DUP1, Op.DUP1)
        loop_cost += gas_costs.G_VERY_LOW * 2
    elif storage_action == StorageAction.WRITE_NEW_VALUE:
        # The new value 2^256-1 is guaranteed to be different from the initial
        # value.
        execution_code_body = Op.SSTORE(Op.DUP2, Op.NOT(0))
        loop_cost += gas_costs.G_VERY_LOW * 3
    elif storage_action == StorageAction.READ:
        execution_code_body = Op.POP(Op.SLOAD(Op.DUP1))
        loop_cost += gas_costs.G_VERY_LOW + gas_costs.G_BASE

    # Add costs jump-logic costs
    loop_cost += (
        gas_costs.G_JUMPDEST  # Prefix Jumpdest
        + gas_costs.G_VERY_LOW * 7  # ISZEROs, PUSHs, SWAPs, SUB, DUP
        + gas_costs.G_HIGH  # JUMPI
    )

    prefix_cost = (
        gas_costs.G_VERY_LOW  # Target slots push
    )

    suffix_cost = 0
    if tx_result == TransactionResult.REVERT:
        suffix_cost = (
            gas_costs.G_VERY_LOW * 2  # Revert PUSHs
        )

    num_target_slots = (
        gas_benchmark_value
        - intrinsic_gas_cost_calc()
        - prefix_cost
        - suffix_cost
    ) // loop_cost
    if tx_result == TransactionResult.OUT_OF_GAS:
        # Add an extra slot to make it run out-of-gas
        num_target_slots += 1

    code_prefix = Op.PUSH4(num_target_slots) + Op.JUMPDEST
    code_loop = execution_code_body + Op.JUMPI(
        len(code_prefix) - 1,
        Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
    )
    execution_code = code_prefix + code_loop

    if tx_result == TransactionResult.REVERT:
        execution_code += Op.REVERT(0, 0)
    else:
        execution_code += Op.STOP

    execution_code_address = pre.deploy_contract(code=execution_code)

    total_gas_used = (
        num_target_slots * loop_cost
        + intrinsic_gas_cost_calc()
        + prefix_cost
        + suffix_cost
    )

    # Contract creation
    slots_init = Bytecode()
    if not absent_slots:
        slots_init = Op.PUSH4(num_target_slots) + While(
            body=Op.SSTORE(Op.DUP1, Op.DUP1),
            condition=Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )

    # To create the contract, we apply the slots_init code to initialize the
    # storage slots (int the case of absent_slots=False) and then copy the
    # execution code to the contract.
    creation_code = (
        slots_init
        + Op.EXTCODECOPY(
            address=execution_code_address,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(execution_code_address),
        )
        + Op.RETURN(0, Op.MSIZE)
    )
    sender_addr = pre.fund_eoa()
    setup_tx = Transaction(
        to=None,
        gas_limit=env.gas_limit,
        data=creation_code,
        sender=sender_addr,
    )

    blocks = [Block(txs=[setup_tx])]

    contract_address = compute_create_address(address=sender_addr, nonce=0)

    op_tx = Transaction(
        to=contract_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    benchmark_test(
        blocks=blocks,
        expected_benchmark_gas_used=(
            total_gas_used
            if tx_result != TransactionResult.OUT_OF_GAS
            else gas_benchmark_value
        ),
    )


@pytest.mark.parametrize(
    "storage_action",
    [
        pytest.param(StorageAction.READ, id="SLOAD"),
        pytest.param(StorageAction.WRITE_SAME_VALUE, id="SSTORE same value"),
        pytest.param(StorageAction.WRITE_NEW_VALUE, id="SSTORE new value"),
    ],
)
def test_storage_access_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    storage_action: StorageAction,
    gas_benchmark_value: int,
    env: Environment,
) -> None:
    """
    Benchmark warm storage slot accesses.
    """
    blocks = []

    # The target storage slot for the warm access is storage slot 0.
    storage_slot_initial_value = 10

    # Contract code
    execution_code_body = Bytecode()
    if storage_action == StorageAction.WRITE_SAME_VALUE:
        execution_code_body = Op.SSTORE(0, Op.DUP1)
    elif storage_action == StorageAction.WRITE_NEW_VALUE:
        execution_code_body = Op.PUSH1(1) + Op.ADD + Op.SSTORE(0, Op.DUP1)
    elif storage_action == StorageAction.READ:
        execution_code_body = Op.POP(Op.SLOAD(0))

    execution_code = Op.PUSH1(storage_slot_initial_value) + While(
        body=execution_code_body,
    )
    execution_code_address = pre.deploy_contract(code=execution_code)

    creation_code = (
        Op.SSTORE(0, storage_slot_initial_value)
        + Op.EXTCODECOPY(
            address=execution_code_address,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(execution_code_address),
        )
        + Op.RETURN(0, Op.MSIZE)
    )

    with TestPhaseManager.setup():
        sender_addr = pre.fund_eoa()
        setup_tx = Transaction(
            to=None,
            gas_limit=env.gas_limit,
            data=creation_code,
            sender=sender_addr,
        )
        blocks.append(Block(txs=[setup_tx]))

    contract_address = compute_create_address(address=sender_addr, nonce=0)

    with TestPhaseManager.execution():
        op_tx = Transaction(
            to=contract_address,
            gas_limit=gas_benchmark_value,
            sender=pre.fund_eoa(),
        )
        blocks.append(Block(txs=[op_tx]))

    benchmark_test(blocks=blocks)
