"""
Benchmark storage instructions.

Supported Opcodes:
- SLOAD
- SSTORE
- TLOAD
- TSTORE
"""

import math

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Environment,
    ExtCallGenerator,
    Fork,
    Hash,
    JumpLoopGenerator,
    Op,
    Storage,
    TestPhaseManager,
    Transaction,
    While,
    compute_create_address,
)

from tests.benchmark.compute.helpers import StorageAction, TransactionResult


@pytest.mark.repricing(fixed_key=True, fixed_value=True)
@pytest.mark.parametrize("fixed_key", [True, False])
@pytest.mark.parametrize("fixed_value", [True, False])
def test_tload(
    benchmark_test: BenchmarkTestFiller,
    fixed_key: bool,
    fixed_value: bool,
) -> None:
    """Benchmark TLOAD instruction."""
    setup = Bytecode()
    if not fixed_key and not fixed_value:
        setup = Op.GAS + Op.TSTORE(Op.DUP2, Op.GAS)
        attack_block = Op.TLOAD(Op.DUP1)
    if not fixed_key and fixed_value:
        attack_block = Op.TLOAD(Op.GAS)
    if fixed_key and not fixed_value:
        setup = Op.TSTORE(Op.CALLDATASIZE, Op.GAS)
        attack_block = Op.TLOAD(Op.CALLDATASIZE)
    if fixed_key and fixed_value:
        attack_block = Op.TLOAD(Op.CALLDATASIZE)

    tx_data = b"42" if fixed_key and not fixed_value else b""

    benchmark_test(
        target_opcode=Op.TLOAD,
        code_generator=ExtCallGenerator(
            setup=setup,
            attack_block=attack_block,
            tx_kwargs={"data": tx_data},
        ),
    )


@pytest.mark.repricing(fixed_key=False, fixed_value=False)
@pytest.mark.parametrize("fixed_key", [True, False])
@pytest.mark.parametrize("fixed_value", [True, False])
def test_tstore(
    benchmark_test: BenchmarkTestFiller,
    fixed_key: bool,
    fixed_value: bool,
) -> None:
    """Benchmark TSTORE instruction."""
    init_key = 42
    setup = Op.PUSH1(init_key)

    # If fixed_value is False, we use GAS as a cheap way of always
    # storing a different value than the previous one.
    attack_block = Op.TSTORE(Op.DUP2, Op.GAS if not fixed_value else Op.DUP1)

    # If fixed_key is False, we mutate the key on every iteration of the
    # big loop.
    cleanup = Op.POP + Op.GAS if not fixed_key else Bytecode()

    benchmark_test(
        target_opcode=Op.TSTORE,
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block, cleanup=cleanup
        ),
    )


@pytest.mark.repricing(
    storage_action=StorageAction.WRITE_SAME_VALUE, absent_slots=False
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
    with TestPhaseManager.setup():
        setup_tx = Transaction(
            to=None,
            gas_limit=env.gas_limit,
            data=creation_code,
            sender=sender_addr,
        )

    blocks = [Block(txs=[setup_tx])]

    contract_address = compute_create_address(address=sender_addr, nonce=0)

    with TestPhaseManager.execution():
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


@pytest.mark.repricing(storage_action=StorageAction.WRITE_SAME_VALUE)
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
    fork: Fork,
    gas_benchmark_value: int,
    env: Environment,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark warm storage slot accesses.
    """
    blocks = []

    # The warm access is done in storage slot 0.

    # Contract code
    execution_code_body = Bytecode()
    if storage_action == StorageAction.WRITE_SAME_VALUE:
        execution_code_body = Op.SSTORE(0, Op.DUP1)
    elif storage_action == StorageAction.WRITE_NEW_VALUE:
        execution_code_body = Op.SSTORE(0, Op.GAS)
    elif storage_action == StorageAction.READ:
        execution_code_body = Op.POP(Op.SLOAD(0))

    execution_code = Op.SLOAD(0) + While(
        body=execution_code_body,
    )
    execution_code_address = pre.deploy_contract(code=execution_code)

    creation_code = (
        Op.SSTORE(0, 42)
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
            gas_limit=tx_gas_limit,
            data=creation_code,
            sender=sender_addr,
        )
        blocks.append(Block(txs=[setup_tx]))

    contract_address = compute_create_address(address=sender_addr, nonce=0)

    with TestPhaseManager.execution():
        num_exec_txs = math.ceil(gas_benchmark_value / tx_gas_limit)
        txs = []
        for i in range(num_exec_txs):
            gas_limit = min(
                tx_gas_limit, gas_benchmark_value - i * tx_gas_limit
            )
            op_tx = Transaction(
                to=contract_address,
                gas_limit=gas_limit,
                sender=pre.fund_eoa(),
            )
            txs.append(op_tx)
        blocks.append(Block(txs=txs))

    benchmark_test(blocks=blocks)


def storage_contract(sloads_before_sstore: bool) -> Bytecode:
    """
    Storage contract for benchmark slot access.

    # Calldata Layout:
    # - CALLDATA[0..31]: Number of slots to access
    # - CALLDATA[32..63]: Starting slot index
    # - CALLDATA[64..95]: Value to write
    """
    setup = Bytecode()
    loop = Bytecode()
    cleanup = Bytecode()

    start_marker = 10
    end_marker = 30 + (2 if sloads_before_sstore else 0)

    setup += (
        Op.CALLDATALOAD(0)  # num_slots
        + Op.CALLDATALOAD(32)  # start_slot
        + Op.CALLDATALOAD(64)  # value
    )

    setup += Op.PUSH0  # Counter
    setup += Op.JUMPDEST
    # [counter, value, start_slot, num_slots]

    # Loop Condition: Counter < Num Slots
    loop += Op.DUP4
    loop += Op.DUP2
    loop += Op.LT
    loop += Op.ISZERO
    loop += Op.PUSH1(end_marker)
    loop += Op.JUMPI
    # [counter, value, start_slot, num_slots]

    # Loop Body: Store Value at Start Slot + Counter
    loop += Op.DUP1
    loop += Op.DUP4
    loop += Op.ADD
    loop += Op.DUP3
    # [value, start_slot+counter, counter, value, start_slot, num_slots]

    if sloads_before_sstore:
        loop += Op.DUP2
        loop += Op.SSTORE
        loop += Op.SLOAD
        loop += Op.POP
    else:
        loop += Op.SWAP1
        loop += Op.SSTORE  # STORAGE[start_slot + counter] = value
    # [counter, value, start_slot, num_slots]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    loop += Op.PUSH1(start_marker)
    loop += Op.JUMP
    # [counter + 1, value, start_slot, num_slots]

    # Cleanup: Stop
    cleanup += Op.JUMPDEST
    cleanup += Op.STOP

    assert len(setup) - 1 == start_marker
    assert len(setup) + len(loop) == end_marker
    print(f"setup: {len(setup)}, loop: {len(loop)}, cleanup: {len(cleanup)}")
    return setup + loop + cleanup


@pytest.mark.parametrize("slot_count", [50, 100])
@pytest.mark.parametrize("use_access_list", [True, False])
@pytest.mark.parametrize(
    "contract_size",
    [
        pytest.param(0, id="just_created"),
        pytest.param(1024, id="small"),
        pytest.param(12 * 1024, id="medium"),
        pytest.param(24 * 1024, id="xen"),
    ],
)
@pytest.mark.parametrize("sloads_before_sstore", [True, False])
@pytest.mark.parametrize("num_contracts", [1, 5, 10])
@pytest.mark.parametrize(
    "initial_value,write_value",
    [
        pytest.param(0, 0, id="zero_to_zero"),
        pytest.param(0, 0xDEADBEEF, id="zero_to_nonzero"),
        pytest.param(0xDEADBEEF, 0, id="nonzero_to_zero"),
        pytest.param(0xDEADBEEF, 0xBEEFBEEF, id="nonzero_to_nonzero"),
    ],
)
def test_sstore_variants(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
    slot_count: int,
    use_access_list: bool,
    contract_size: int,
    sloads_before_sstore: bool,
    num_contracts: int,
    initial_value: int,
    write_value: int,
) -> None:
    """
    Benchmark SSTORE instruction with various configurations.

    Variants:
    - use_access_list: Warm storage slots via access list
    - contract_size: Contract code size
      (just_created=0, small=1KB, medium=12KB, xen=24KB)
    - sloads_before_sstore: Number of SLOADs per slot before SSTORE
    - num_contracts: Number of contract instances (cold storage writes)
    - initial_value/write_value: Storage transitions
      (zero_to_zero, zero_to_nonzero, nonzero_to_zero, nonzero_to_nonzero)
    """
    base_contract = storage_contract(sloads_before_sstore)
    padded_contract = base_contract

    if len(base_contract) < contract_size:
        padded_contract += Op.INVALID * (contract_size - len(base_contract))

    slots_per_contract = slot_count // num_contracts

    txs = []
    post = {}

    base_gas_per_contract = gas_benchmark_value // num_contracts
    gas_remainder = gas_benchmark_value % num_contracts

    for contract_idx in range(num_contracts):
        initial_storage = Storage()

        start_slot = contract_idx * slot_count
        for i in range(slots_per_contract):
            initial_storage[start_slot + i] = initial_value

        contract_addr = pre.deploy_contract(
            code=padded_contract,
            storage=initial_storage,
        )

        calldata = (
            slots_per_contract.to_bytes(32, "big")
            + start_slot.to_bytes(32, "big")
            + write_value.to_bytes(32, "big")
        )

        access_list = None
        if use_access_list:
            storage_keys = [
                Hash(start_slot + i) for i in range(slots_per_contract)
            ]
            access_list = [
                AccessList(
                    address=contract_addr,
                    storage_keys=storage_keys,
                )
            ]

        contract_gas_limit = base_gas_per_contract
        if contract_idx == 0:
            contract_gas_limit += gas_remainder

        tx = Transaction(
            to=contract_addr,
            data=calldata,
            gas_limit=contract_gas_limit,
            sender=pre.fund_eoa(),
            access_list=access_list,
        )
        txs.append(tx)

        expected_storage = Storage()
        for i in range(slots_per_contract):
            expected_storage[start_slot + i] = write_value

        post[contract_addr] = Account(
            code=padded_contract,
            storage=expected_storage,
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        post=post,
        skip_gas_used_validation=True,
    )
