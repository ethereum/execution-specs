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
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Conditional,
    ExtCallGenerator,
    Fork,
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    RecipientType,
    TestPhaseManager,
    Transaction,
    While,
    WhileGas,
    compute_create_address,
)

from tests.benchmark.helper.enums import StorageAction, TransactionResult


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

    attack_block = Op.TSTORE(Op.DUP2, Op.GAS if not fixed_value else Op.DUP1)
    cleanup = Op.POP + Op.GAS if not fixed_key else Bytecode()

    benchmark_test(
        target_opcode=Op.TSTORE,
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block, cleanup=cleanup
        ),
    )


def create_storage_initializer() -> IteratingBytecode:
    """
    Create a contract that initializes storage slots from calldata parameters.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] slot count (num)

    storage[i] = i for i in [index, index + num).

    Return an IteratingBytecode with the initialization loop.
    """
    prefix = (
        Op.CALLDATALOAD(0)  # [index]
        + Op.DUP1  # [index, index]
        + Op.CALLDATALOAD(32)  # [index, index, num]
        + Op.ADD  # [index, index + num]
    )

    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [index, index + num, 1]
        + Op.SWAP1  # [index, 1, index + num]
        + Op.SUB  # [index, index + num - 1]
        + Op.SSTORE(
            Op.DUP1,
            Op.DUP1,
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP2, Op.DUP2))
    )

    return IteratingBytecode(setup=prefix, iterating=loop)


def create_benchmark_executor(
    storage_action: StorageAction,
    absent_slots: bool,
    tx_result: TransactionResult,
) -> IteratingBytecode:
    """
    Create a contract that executes benchmark operations.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] slot count (num)

    Return an IteratingBytecode with the benchmark execution loop.
    """
    prefix = (
        Op.CALLDATALOAD(0)  # [index]
        + Op.CALLDATALOAD(32)  # [index, num]
    )

    slot_calculation = (
        Op.DUP2  # [index, num, index]
        + Op.DUP2  # [index, num, index, num]
        + Op.ADD  # [index, num, index + num]
        + Op.PUSH1(1)  # [index, num, index + num, 1]
        + Op.SWAP1  # [index, num, 1, index + num]
        + Op.SUB  # [index, num, index + num - 1]
    )

    original = 0 if absent_slots else 1

    # [index, num, index + num - 1]
    match storage_action:
        case StorageAction.READ:
            operation = Op.POP(Op.SLOAD.with_metadata(key_warm=False))
        case StorageAction.WRITE_SAME_VALUE:
            new_value = 1 if absent_slots else original
            operation = (
                Op.SSTORE(
                    Op.DUP1,
                    Op.DUP1,
                    key_warm=False,
                    original_value=original,
                    current_value=original,
                    new_value=new_value,
                )
                + Op.POP
            )
        case StorageAction.WRITE_NEW_VALUE:
            operation = Op.SSTORE(
                Op.SWAP1,
                Op.NOT(0),
                key_warm=False,
                original_value=original,
                current_value=original,
                new_value=2**256 - 1,
            )
        case _:
            raise ValueError

    # [index, num]
    loop_condition = (
        Op.PUSH1(1)  # [index, num, 1]
        + Op.SWAP1  # [index, 1, num]
        + Op.SUB  # [index, num - 1]
        + Op.DUP1  # [index, num - 1, num - 1]
        + Op.ISZERO  # [index, num - 1 == 0]
        + Op.ISZERO  # [index, num - 1 != 0]
    )

    match tx_result:
        case TransactionResult.REVERT:
            suffix = Op.REVERT(0, 0)
        case TransactionResult.OUT_OF_GAS:
            suffix = Bytecode()
        case _:
            suffix = Op.STOP

    loop = (
        Op.JUMPDEST
        + slot_calculation
        + operation
        + Op.JUMPI(len(prefix), loop_condition)
    )

    return IteratingBytecode(setup=prefix, iterating=loop, cleanup=suffix)


@pytest.mark.parametrize(
    "storage_action,tx_result",
    [
        pytest.param(
            StorageAction.READ, TransactionResult.SUCCESS, id="SSLOAD"
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
@pytest.mark.parametrize("absent_slots", [True, False])
def test_storage_access_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_action: StorageAction,
    absent_slots: bool,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_result: TransactionResult,
) -> None:
    """
    Benchmark cold storage slot accesses using EIP-7702 delegation.

    The authority EOA delegates to:
    - StorageInitializer: storage[i] = i for each slot (absent_slots=False)
    - BenchmarkExecutor: performs the benchmark operation (SLOAD/SSTORE)
    """
    executor_code = create_benchmark_executor(
        storage_action, absent_slots, tx_result
    )
    initializer_code = create_storage_initializer()

    authority = pre.fund_eoa(amount=0)
    initializer_addr = pre.deploy_contract(code=initializer_code)
    executor_addr = pre.deploy_contract(code=executor_code)

    # Calldata generator for both the executor and initializer.
    def calldata_generator(
        iteration_count: int, start_iteration: int
    ) -> bytes:
        return Hash(start_iteration) + Hash(iteration_count)

    # Number of slots that can be processed in the execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata_generator,
            recipient_type=RecipientType.DELEGATION_7702,
            outcome=tx_result,
        )
    )

    blocks = []
    delegation_sender = pre.fund_eoa()

    # Setup phase: initialize storage slots (only if absent_slots=False)
    with TestPhaseManager.setup():
        setup_txs = []
        authority_nonce = 0
        if not absent_slots:
            setup_txs.append(
                Transaction(
                    to=delegation_sender,
                    gas_limit=tx_gas_limit,
                    sender=delegation_sender,
                    authorization_list=[
                        AuthorizationTuple(
                            address=initializer_addr,
                            nonce=authority_nonce,
                            signer=authority,
                        ),
                    ],
                )
            )
            authority_nonce += 1

            setup_txs += list(
                initializer_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=num_target_slots,
                    sender=pre.fund_eoa(),
                    to=authority,
                    start_iteration=1,
                    calldata=calldata_generator,
                    recipient_type=RecipientType.DELEGATION_7702,
                )
            )

        setup_txs.append(
            Transaction(
                to=delegation_sender,
                gas_limit=tx_gas_limit,
                sender=delegation_sender,
                authorization_list=[
                    AuthorizationTuple(
                        address=executor_addr,
                        nonce=authority_nonce,
                        signer=authority,
                    ),
                ],
            )
        )
        blocks.append(Block(txs=setup_txs))

    # Execution phase: run benchmark
    # For absent_slots=False, authority has storage, triggering refund
    expected_gas_used = 0

    with TestPhaseManager.execution():
        # One gas short so the out-of-gas variants cannot terminate cleanly.
        tx_gas_limit_delta = (
            -1 if tx_result == TransactionResult.OUT_OF_GAS else 0
        )
        exec_txs = list(
            executor_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=pre.fund_eoa(),
                to=authority,
                calldata=calldata_generator,
                start_iteration=1,
                recipient_type=RecipientType.DELEGATION_7702,
                tx_gas_limit_delta=tx_gas_limit_delta,
                outcome=tx_result,
            )
        )
        for exec_tx in exec_txs:
            expected_gas_used += exec_tx.gas_cost

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


@pytest.mark.parametrize(
    "storage_action",
    [
        pytest.param(StorageAction.READ, id="SLOAD"),
        pytest.param(StorageAction.WRITE_SAME_VALUE, id="SSTORE_same"),
        pytest.param(StorageAction.WRITE_NEW_VALUE, id="SSTORE_new"),
    ],
)
def test_storage_access_cold_benchmark(
    benchmark_test: BenchmarkTestFiller,
    storage_action: StorageAction,
) -> None:
    """
    Benchmark cold storage slot accesses using code generator.

    Each iteration accesses a different storage slot (incrementing key)
    to ensure cold access costs are measured.
    """
    if storage_action == StorageAction.READ:
        attack_block = Op.SLOAD(Op.GAS)
    elif storage_action == StorageAction.WRITE_SAME_VALUE:
        attack_block = Op.SSTORE(Op.GAS, Op.PUSH0)
    elif storage_action == StorageAction.WRITE_NEW_VALUE:
        attack_block = Op.SSTORE(Op.GAS, Op.GAS)

    benchmark_test(
        target_opcode=Op.SLOAD
        if storage_action == StorageAction.READ
        else Op.SSTORE,
        code_generator=ExtCallGenerator(attack_block=attack_block),
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
    tx_gas_limit: int,
) -> None:
    """Benchmark warm storage slot accesses."""
    blocks = []

    match storage_action:
        case StorageAction.WRITE_SAME_VALUE:
            execution_code_body = Op.SSTORE(0, Op.DUP1)
        case StorageAction.WRITE_NEW_VALUE:
            execution_code_body = Op.SSTORE(0, Op.GAS)
        case StorageAction.READ:
            execution_code_body = Op.POP(Op.SLOAD(0))
        case _:
            raise ValueError("Unspecified storage action")

    execution_code = Op.SLOAD(0) + While(body=execution_code_body)
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
            txs.append(
                Transaction(
                    to=contract_address,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=txs))

    benchmark_test(blocks=blocks)


@pytest.mark.parametrize(
    "storage_action",
    [
        pytest.param(StorageAction.READ, id="SLOAD"),
        pytest.param(StorageAction.WRITE_SAME_VALUE, id="SSTORE same value"),
        pytest.param(StorageAction.WRITE_NEW_VALUE, id="SSTORE new value"),
    ],
)
def test_storage_access_warm_benchmark(
    benchmark_test: BenchmarkTestFiller,
    storage_action: StorageAction,
) -> None:
    """
    Benchmark warm storage slot accesses using code generator.

    Each iteration accesses a different storage slot (incrementing key)
    to ensure warm access costs are measured.
    """
    match storage_action:
        case StorageAction.WRITE_SAME_VALUE:
            # Timestamp is nonzero (no txs run in Genesis block),
            # Always writes to the zero key a nonzero, constant value
            attack_block = Op.SSTORE(Op.PUSH0, Op.TIMESTAMP)
        case StorageAction.WRITE_NEW_VALUE:
            attack_block = Op.SSTORE(Op.PUSH0, Op.GAS)
        case StorageAction.READ:
            attack_block = Op.SLOAD(Op.PUSH0)
        case _:
            raise ValueError("Unspecified storage action")

    benchmark_test(
        target_opcode=Op.SLOAD
        if storage_action == StorageAction.READ
        else Op.SSTORE,
        code_generator=ExtCallGenerator(attack_block=attack_block),
    )


@pytest.mark.parametrize("revert", [True, False])
@pytest.mark.parametrize("depth", [1, pytest.param(None, id="max")])
@pytest.mark.parametrize(
    "opcode",
    [
        Op.SLOAD,
        Op.SSTORE,
        Op.TLOAD,
        Op.TSTORE,
    ],
)
def test_nested_frame_state_access(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    depth: int | None,
    opcode: Op,
    revert: bool,
) -> None:
    """Benchmark warm state access from the bottom of a deep frame stack."""
    match opcode:
        case Op.SLOAD:
            body = Op.POP(Op.SLOAD(Op.PUSH0))
        case Op.SSTORE:
            body = Op.SSTORE(Op.GAS, Op.GAS)
        case Op.TLOAD:
            body = Op.POP(Op.TLOAD(Op.GAS))
        case Op.TSTORE:
            body = Op.TSTORE(Op.GAS, Op.GAS)
        case _:
            raise ValueError(f"Unsupported opcode: {opcode}")

    # A leaf that runs out of gas returns no data, unlike one that reverts.
    epilogue = (
        Op.REVERT(
            0,
            32,
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        if revert
        else Op.RETURN(
            0,
            32,
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
    )
    leaf_code = (
        WhileGas(body=body, fork=fork, extra_gas=epilogue.gas_cost(fork))
        + epilogue
    )
    leaf_address = pre.deploy_contract(code=leaf_code)

    descend = Op.MSTORE(0, Op.SUB(Op.CALLDATALOAD(0), 1)) + Conditional(
        condition=Op.CALL(
            gas=Op.GAS,
            address=Op.ADDRESS,
            args_offset=0,
            args_size=32,
            address_warm=True,
        ),
        if_false=Op.REVERT(0, 0),
    )
    invoke_leaf = Op.CALL(
        gas=Op.GAS, address=leaf_address, address_warm=True
    ) + Conditional(
        condition=Op.RETURNDATASIZE, if_false=Op.REVERT(Op.PUSH0, Op.PUSH0)
    )

    frame_code = Conditional(
        condition=Op.CALLDATALOAD(0),
        if_true=descend,
        if_false=invoke_leaf,
    )
    entry_address = pre.deploy_contract(code=frame_code)

    frame_gas = frame_code.execution_cost(fork)
    leaf_gas = leaf_code.gas_cost(fork)
    leaf_state_gas = leaf_code.state_cost(fork)

    def deepest_frame(execution_gas: int, reservoir_gas: int) -> int:
        """Return the deepest frame that can still afford the leaf call."""
        leaf_call_gas = frame_gas + math.ceil(
            (leaf_gas - reservoir_gas) * 64 / 63
        )
        frames = 0
        while True:
            forwarded_gas = execution_gas - frame_gas
            forwarded_gas -= forwarded_gas // 64
            if forwarded_gas < leaf_call_gas:
                return frames
            execution_gas = forwarded_gas
            frames += 1

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 32,
        return_cost_deducted_prior_execution=True,
    )

    txs = []
    remaining_gas = gas_benchmark_value
    while remaining_gas > 0:
        execution_gas = min(tx_gas_limit, remaining_gas)
        remaining_gas -= execution_gas
        reservoir_gas = (
            leaf_state_gas
            if fork.state_gas_reservoir_enabled()
            and execution_gas == tx_gas_limit
            else 0
        )
        txs.append(
            Transaction(
                to=entry_address,
                gas_limit=execution_gas + reservoir_gas,
                data=Hash(
                    deepest_frame(execution_gas - intrinsic_gas, reservoir_gas)
                    if depth is None
                    else depth
                ),
                sender=pre.fund_eoa(),
            )
        )

    benchmark_test(
        target_opcode=opcode,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
    )
