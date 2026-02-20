"""
Benchmark system instructions.

Supported Opcodes:
- CREATE
- CREATE2
- RETURN
- REVERT
- CALL
- CALLCODE
- DELEGATECALL
- STATICCALL
- SELFDESTRUCT
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Create2PreimageLayout,
    ExtCallGenerator,
    Fork,
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    TestPhaseManager,
    Transaction,
    While,
    compute_create2_address,
    compute_create_address,
)


@pytest.mark.parametrize("transfer_amount", [0, 1])
@pytest.mark.parametrize("opcode", [Op.CALL, Op.CALLCODE])
@pytest.mark.parametrize("access_warm", [True, False])
def test_contract_calling_many_addresses(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    transfer_amount: int,
    opcode: Op,
    access_warm: bool,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """Benchmark a contract that calls many addresses."""
    warm_start_addr = 2**80 - 1
    setup = Op.PUSH20(warm_start_addr) if access_warm else Op.GAS

    def loop(threshold: int) -> Bytecode:
        return (
            Op.JUMPDEST
            + opcode(address=Op.DUP6, value=transfer_amount)
            + Op.SWAP1
            + Op.SUB
            + Op.JUMPI(Op.GT(Op.GAS, threshold), len(setup))
        )

    cost = loop(0xFFFF).gas_cost(fork)
    code = setup + loop(cost)

    contract_addr = pre.deploy_contract(
        code=code,
        balance=10**18 if transfer_amount > 0 else 0,
    )

    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_cost = intrinsic_cost_calc()
    access_list_addr_cost = fork.gas_costs().GAS_TX_ACCESS_LIST_ADDRESS

    txs = []
    remaining_gas = gas_benchmark_value
    while remaining_gas > intrinsic_cost:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        remaining_gas -= per_tx_gas

        access_list = None
        if access_warm:
            iterations = (per_tx_gas - intrinsic_cost) // (
                access_list_addr_cost + cost
            )
            if iterations <= 0:
                break
            access_list = [
                AccessList(
                    address=Address(warm_start_addr - i),
                    storage_keys=[],
                )
                for i in range(iterations)
            ]

        txs.append(
            Transaction(
                to=contract_addr,
                sender=pre.fund_eoa(),
                gas_limit=per_tx_gas,
                access_list=access_list,
            )
        )

    benchmark_test(blocks=[Block(txs=txs)])


@pytest.mark.repricing(max_code_size_ratio=0)
@pytest.mark.parametrize(
    "opcode",
    [
        Op.CREATE,
        Op.CREATE2,
    ],
)
@pytest.mark.parametrize(
    "max_code_size_ratio, non_zero_data, value",
    [
        # To avoid a blowup of combinations, the value dimension is only
        # explored for the non-zero data case, so isn't affected by code size
        # influence.
        pytest.param(0, False, 0, id="0 bytes without value"),
        pytest.param(0, False, 1, id="0 bytes with value"),
        pytest.param(
            0.25, True, 0, id="0.25x max code size with non-zero data"
        ),
        pytest.param(0.25, False, 0, id="0.25x max code size with zero data"),
        pytest.param(
            0.50, True, 0, id="0.50x max code size with non-zero data"
        ),
        pytest.param(0.50, False, 0, id="0.50x max code size with zero data"),
        pytest.param(
            0.75, True, 0, id="0.75x max code size with non-zero data"
        ),
        pytest.param(0.75, False, 0, id="0.75x max code size with zero data"),
        pytest.param(1.00, True, 0, id="max code size with non-zero data"),
        pytest.param(1.00, False, 0, id="max code size with zero data"),
    ],
)
def test_create(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    max_code_size_ratio: float,
    non_zero_data: bool,
    value: int,
) -> None:
    """Benchmark CREATE and CREATE2 instructions."""
    max_code_size = fork.max_code_size()

    code_size = int(max_code_size * max_code_size_ratio)

    # Deploy the initcode template which has following design:
    # ```
    # PUSH3(code_size)
    # [CODECOPY(DUP1) -- Conditional that non_zero_data is True]
    # RETURN(0, DUP1)
    # [<pad to code_size>] -- Conditional that non_zero_data is True]
    # ```
    code = (
        Op.PUSH3(code_size)
        + (Op.CODECOPY(size=Op.DUP1) if non_zero_data else Bytecode())
        + Op.RETURN(0, Op.DUP1)
    )
    if non_zero_data:  # Pad to code_size.
        code += bytes([i % 256 for i in range(code_size - len(code))])

    initcode_template_contract = pre.deploy_contract(code=code)

    # Create the benchmark contract which has the following design:
    # ```
    # PUSH(value)
    # [EXTCODECOPY(full initcode_template_contract)
    # -> Conditional that non_zero_data is True]
    #
    # JUMPDEST (#)
    # (CREATE|CREATE2)
    # (CREATE|CREATE2)
    # ...
    # JUMP(#)
    # ```
    setup = (
        Op.PUSH3(code_size)
        + Op.PUSH1(value)
        + Op.EXTCODECOPY(
            address=initcode_template_contract,
            size=Op.DUP2,  # DUP2 refers to the EXTCODESIZE value above.
        )
    )

    if opcode == Op.CREATE2:
        # For CREATE2, load salt from storage (persist across outer loop calls)
        # If storage is 0 (first call), use initial salt of 42.
        # Stack after setup: [..., value, code_size, salt]
        setup += (
            Op.SLOAD(0)  # Load saved salt
            + Op.DUP1  # Duplicate for check
            + Op.ISZERO  # Check if zero
            + Op.PUSH1(42)  # Default salt
            + Op.MUL  # 42 if zero, 0 if not
            + Op.ADD  # Add to get final salt (saved or 42)
        )

    attack_block = (
        # For CREATE:
        # - DUP2 refers to the EXTOCODESIZE value  pushed in code_prefix.
        # - DUP3 refers to PUSH1(value) above.
        Op.POP(Op.CREATE(value=Op.DUP3, offset=0, size=Op.DUP2))
        if opcode == Op.CREATE
        # For CREATE2: we manually push the arguments because we leverage the
        # return value of previous CREATE2 calls as salt for the next CREATE2
        # call. After CREATE2, save result to storage for next outer loop call.
        # - DUP4 is targeting the PUSH1(value) from the code_prefix.
        # - DUP3 is targeting the EXTCODESIZE value pushed in code_prefix.
        else Op.DUP3
        + Op.PUSH0
        + Op.DUP4
        + Op.CREATE2
        + Op.DUP1
        + Op.PUSH0
        + Op.SSTORE
    )

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            contract_balance=1_000_000_000 if value > 0 else 0,
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CREATE,
        Op.CREATE2,
    ],
)
@pytest.mark.pre_alloc_mutable
def test_creates_collisions(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    gas_benchmark_value: int,
) -> None:
    """Benchmark CREATE and CREATE2 instructions with collisions."""
    # We deploy a "proxy contract" which is the contract that will be called in
    # a loop using all the gas in the block. This "proxy contract" is the one
    # executing CREATE2 failing with a collision. The reason why we need a
    # "proxy contract" is that CREATE(2) failing with a collision will consume
    # all the available gas. If we try to execute the CREATE(2) directly
    # without being wrapped **and capped in gas** in a previous CALL, we would
    # run out of gas very fast!
    # The proxy contract calls CREATE(2) with empty initcode. The current call
    # frame gas will be exhausted because of the collision. For this reason the
    # caller will carefully give us the minimal gas necessary to execute the
    # CREATE(2) and not waste any extra gas in the CREATE(2)-failure.
    # Note that these CREATE(2) calls will fail because in (**) below we pre-
    # alloc contracts with the same address as the ones that CREATE(2) will try
    # to create.
    proxy_contract_code = (
        Op.CREATE2(
            value=Op.PUSH0, salt=Op.PUSH0, offset=Op.PUSH0, size=Op.PUSH0
        )
        if opcode == Op.CREATE2
        else Op.CREATE(value=Op.PUSH0, offset=Op.PUSH0, size=Op.PUSH0)
    )
    proxy_contract = pre.deploy_contract(code=proxy_contract_code)

    # The CALL to the proxy contract needs at a minimum gas corresponding to
    # the CREATE(2) plus extra required PUSH0s for arguments.
    min_gas_required = proxy_contract_code.gas_cost(fork)
    setup = Op.PUSH20(proxy_contract) + Op.PUSH3(min_gas_required)
    attack_block = Op.POP(
        # DUP7 refers to the PUSH3 above.
        # DUP7 refers to the proxy contract address.
        Op.CALL(gas=Op.DUP7, address=Op.DUP7)
    )

    # (**) We deploy the contract that CREATE(2) will attempt to create so any
    # attempt will fail.
    if opcode == Op.CREATE2:
        addr = compute_create2_address(
            address=proxy_contract, salt=0, initcode=[]
        )
        pre.deploy_contract(address=addr, code=Op.INVALID)
    else:
        # Heuristic to have an upper bound.
        creation_cost = proxy_contract_code.gas_cost(fork)
        max_contract_count = 2 * gas_benchmark_value // creation_cost
        for nonce in range(max_contract_count):
            addr = compute_create_address(address=proxy_contract, nonce=nonce)
            pre.deploy_contract(address=addr, code=Op.INVALID)

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    [Op.RETURN, Op.REVERT],
)
@pytest.mark.parametrize(
    "return_size, return_non_zero_data",
    [
        pytest.param(0, False, id="empty"),
        pytest.param(1024, True, id="1KiB of non-zero data"),
        pytest.param(1024, False, id="1KiB of zero data"),
        pytest.param(1024 * 1024, True, id="1MiB of non-zero data"),
        pytest.param(1024 * 1024, False, id="1MiB of zero data"),
    ],
)
def test_return_revert(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    return_size: int,
    return_non_zero_data: bool,
) -> None:
    """Benchmark RETURN and REVERT instructions."""
    # Create the contract that will be called repeatedly.
    # The bytecode of the contract is:
    # ```
    # [CODECOPY(returned_size) -- Conditional if return_non_zero_data]
    # opcode(returned_size)
    # <Fill with INVALID opcodes up to the max contract size>
    # ```
    # Filling the contract up to the max size is a cheap way of leveraging
    # CODECOPY to return non-zero bytes if requested. Note that since this
    # is a pre-deploy this cost isn't
    # relevant for the benchmark.
    mem_preparation = (
        Op.CODECOPY(size=return_size) if return_non_zero_data else Bytecode()
    )
    benchmark_test(
        target_opcode=opcode,
        code_generator=ExtCallGenerator(
            setup=mem_preparation,
            attack_block=opcode(size=return_size),
            code_padding_opcode=Op.INVALID,
        ),
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_existing(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Benchmark SELFDESTRUCT instruction for existing contracts."""
    selfdestructable_contract = Op.SELFDESTRUCT(Op.CALLER, address_warm=True)

    # Initcode
    initcode = (
        Op.MSTORE8(
            0,
            Op.CALLER.int(),
            # gas accounting
            old_memory_size=0,
            new_memory_size=2,
        )
        + Op.MSTORE8(1, Op.SELFDESTRUCT.int())
        + Op.RETURN(0, 2, code_deposit_size=2)
    )

    # Factory Contract Setup
    # CALLDATA[0:32] = start index
    # CALLDATA[32:64] = end index
    factory_setup = (
        Op.MSTORE(
            0,
            initcode.hex(),
            # Gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.ADD(1, Op.CALLDATALOAD(32))
        + Op.CALLDATALOAD(0)
    )

    factory_iterating = While(
        body=Op.POP(
            Op.CREATE2(
                value=1 if value_bearing else 0,
                offset=32 - len(initcode),
                size=len(initcode),
                salt=Op.DUP1,
                # gas accounting
                init_code_size=len(initcode),
            )
        ),
        condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
    )

    factory_code = IteratingBytecode(
        setup=factory_setup,
        iterating=factory_iterating,
        iterating_subcall=initcode,
        cleanup=Op.STOP,
    )

    factory_address = pre.deploy_contract(
        code=factory_code,
        balance=10**18,
    )

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(0),
        init_code_hash=initcode.keccak256(),
    )

    # Attack Contract Setup
    # CALLDATA[0:32] = start index
    # CALLDATA[32:64] = end index
    attack_setup = (
        create2_preimage + Op.ADD(1, Op.CALLDATALOAD(32)) + Op.CALLDATALOAD(0)
    )

    loop = While(
        body=Op.POP(
            Op.CALL(
                address=create2_preimage.address_op(),
                address_warm=False,
            )
        )
        + create2_preimage.increment_salt_op(),
        condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
    )

    attack_code = IteratingBytecode(
        setup=attack_setup,
        iterating=loop,
        iterating_subcall=selfdestructable_contract,
        cleanup=Op.STOP,
    )

    attack_code_address = pre.deploy_contract(code=attack_code)

    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        index_end = iteration_count + start_iteration - 1
        return Hash(start_iteration) + Hash(index_end)

    # Compute iteration counts and expected gas from the gas model.
    iteration_counts = list(
        attack_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata,
        )
    )
    num_contracts = sum(iteration_counts)

    start = 0
    total_gas_cost = 0
    for iters in iteration_counts:
        total_gas_cost += attack_code.tx_gas_cost_by_iteration_count(
            fork=fork,
            iteration_count=iters,
            start_iteration=start,
            calldata=calldata,
        )
        start += iters

    def factory_calldata(iteration_count: int, start_iteration: int) -> bytes:
        index_end = iteration_count + start_iteration - 1
        return Hash(start_iteration) + Hash(index_end)

    with TestPhaseManager.setup():
        setup_sender = pre.fund_eoa()
        setup_txs = list(
            factory_code.transactions_by_total_iteration_count(
                fork=fork,
                total_iterations=num_contracts,
                sender=setup_sender,
                to=factory_address,
                calldata=factory_calldata,
            )
        )

    with TestPhaseManager.execution():
        attack_sender = pre.fund_eoa()
        exec_txs = list(
            attack_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=attack_sender,
                to=attack_code_address,
                calldata=calldata,
            )
        )

    post = {}
    for i in range(num_contracts):
        deployed_contract_address = compute_create2_address(
            address=factory_address,
            salt=i,
            initcode=initcode,
        )
        post[deployed_contract_address] = Account(nonce=1)

    post[attack_code_address] = Account(
        balance=num_contracts if value_bearing else 0
    )

    benchmark_test(
        post=post,
        target_opcode=Op.SELFDESTRUCT,
        blocks=[
            Block(txs=setup_txs),
            Block(txs=exec_txs),
        ],
        expected_benchmark_gas_used=total_gas_cost,
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_created(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Benchmark SELFDESTRUCT instruction for contracts created in same tx."""
    selfdestructable_contract = Op.SELFDESTRUCT(Op.CALLER, address_warm=True)

    # Initcode
    initcode = (
        Op.MSTORE8(
            0,
            Op.CALLER.int(),
            # gas accounting
            old_memory_size=0,
            new_memory_size=2,
        )
        + Op.MSTORE8(1, Op.SELFDESTRUCT.int())
        + Op.RETURN(0, 2, code_deposit_size=2)
    )

    # CALLDATA[0:32] = iteration_count
    setup = (
        Op.MSTORE(
            0,
            initcode.hex(),
            # Gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.CALLDATALOAD(0)
        + Op.PUSH0
    )

    loop = While(
        body=Op.POP(
            Op.CALL(
                address=Op.CREATE(
                    value=1 if value_bearing else 0,
                    offset=32 - len(initcode),
                    size=len(initcode),
                    init_code_size=len(initcode),
                ),
                address_warm=True,
            )
        ),
        condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
    )

    attack_code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        iterating_subcall=selfdestructable_contract.gas_cost(fork)
        + initcode.gas_cost(fork),
        cleanup=Op.STOP,
    )

    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        del start_iteration
        return Hash(iteration_count)

    iteration_counts = list(
        attack_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata,
        )
    )
    num_iterations = sum(iteration_counts)

    total_gas_cost = sum(
        attack_code.tx_gas_cost_by_iteration_count(
            fork=fork,
            iteration_count=iters,
            calldata=calldata,
        )
        for iters in iteration_counts
    )

    attack_code_address = pre.deploy_contract(
        code=attack_code,
        balance=num_iterations if value_bearing else 0,
    )

    with TestPhaseManager.execution():
        sender = pre.fund_eoa()
        exec_txs = list(
            attack_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=sender,
                to=attack_code_address,
                calldata=calldata,
            )
        )

    post = {
        attack_code_address: Account(
            balance=num_iterations if value_bearing else 0
        )
    }

    benchmark_test(
        post=post,
        target_opcode=Op.SELFDESTRUCT,
        blocks=[
            Block(txs=exec_txs),
        ],
        expected_benchmark_gas_used=total_gas_cost,
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_initcode(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Benchmark SELFDESTRUCT instruction executed in initcode."""
    initcode = Op.SELFDESTRUCT(Op.CALLER, address_warm=True)

    # CALLDATA[0:32] = iteration_count
    setup = (
        Op.MSTORE(
            0,
            initcode.hex(),
            # Gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.CALLDATALOAD(0)
        + Op.PUSH0
    )

    loop = While(
        body=Op.POP(
            Op.CREATE(
                value=1 if value_bearing else 0,
                offset=32 - len(initcode),
                size=len(initcode),
                init_code_size=len(initcode),
            )
        ),
        condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
    )

    attack_code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        iterating_subcall=initcode,
        cleanup=Op.STOP,
    )

    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        del start_iteration
        return Hash(iteration_count)

    iteration_counts = list(
        attack_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata,
        )
    )
    num_iterations = sum(iteration_counts)

    total_gas_cost = sum(
        attack_code.tx_gas_cost_by_iteration_count(
            fork=fork,
            iteration_count=iters,
            calldata=calldata,
        )
        for iters in iteration_counts
    )

    attack_code_address = pre.deploy_contract(
        code=attack_code,
        balance=num_iterations if value_bearing else 0,
    )

    with TestPhaseManager.execution():
        sender = pre.fund_eoa()
        exec_txs = list(
            attack_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=sender,
                to=attack_code_address,
                calldata=calldata,
            )
        )

    post = {
        attack_code_address: Account(
            balance=num_iterations if value_bearing else 0
        )
    }

    benchmark_test(
        post=post,
        target_opcode=Op.SELFDESTRUCT,
        blocks=[
            Block(txs=exec_txs),
        ],
        expected_benchmark_gas_used=total_gas_cost,
    )
