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

import math

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Create2PreimageLayout,
    Environment,
    ExtCallGenerator,
    Fork,
    Hash,
    JumpLoopGenerator,
    Op,
    TestPhaseManager,
    Transaction,
    While,
    compute_create2_address,
    compute_create_address,
)


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
        # For CREATE2, we provide an initial salt.
        setup += Op.PUSH1(42)

    attack_block = (
        # For CREATE:
        # - DUP2 refers to the EXTOCODESIZE value  pushed in code_prefix.
        # - DUP3 refers to PUSH1(value) above.
        Op.POP(Op.CREATE(value=Op.DUP3, offset=0, size=Op.DUP2))
        if opcode == Op.CREATE
        # For CREATE2: we manually push the arguments because we leverage the
        # return value of previous CREATE2 calls as salt for the next CREATE2
        # call.
        # - DUP4 is targeting the PUSH1(value) from the code_prefix.
        # - DUP3 is targeting the EXTCODESIZE value pushed in code_prefix.
        else Op.DUP3 + Op.PUSH0 + Op.DUP4 + Op.CREATE2
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
    proxy_contract = pre.deploy_contract(
        code=Op.CREATE2(
            value=Op.PUSH0, salt=Op.PUSH0, offset=Op.PUSH0, size=Op.PUSH0
        )
        if opcode == Op.CREATE2
        else Op.CREATE(value=Op.PUSH0, offset=Op.PUSH0, size=Op.PUSH0)
    )

    gas_costs = fork.gas_costs()
    # The CALL to the proxy contract needs at a minimum gas corresponding to
    # the CREATE(2) plus extra required PUSH0s for arguments.
    min_gas_required = gas_costs.G_CREATE + gas_costs.G_BASE * (
        3 if opcode == Op.CREATE else 4
    )
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
        max_contract_count = 2 * gas_benchmark_value // gas_costs.G_CREATE
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
    fork: Fork,
    pre: Alloc,
    value_bearing: bool,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark SELFDESTRUCT instruction for existing contracts.
    contracts.
    """
    attack_gas_limit = gas_benchmark_value
    fee_recipient = pre.fund_eoa(amount=1)

    # Template code that will be used to deploy a large number of contracts.
    selfdestructable_contract_addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(Op.COINBASE)
    )
    initcode = Op.EXTCODECOPY(
        address=selfdestructable_contract_addr,
        dest_offset=0,
        offset=0,
        size=Op.EXTCODESIZE(selfdestructable_contract_addr),
    ) + Op.RETURN(0, Op.EXTCODESIZE(selfdestructable_contract_addr))
    initcode_address = pre.deploy_contract(code=initcode)

    # Calculate the number of contracts that can be deployed with the available
    # gas.
    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    loop_cost = (
        gas_costs.G_KECCAK_256  # KECCAK static cost
        + math.ceil(85 / 32) * gas_costs.G_KECCAK_256_WORD  # KECCAK dynamic
        # cost for CREATE2
        + gas_costs.G_VERY_LOW * 3  # ~MSTOREs+ADDs
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # CALL to self-destructing contract
        + gas_costs.G_BASE
        + gas_costs.G_SELF_DESTRUCT
        + 88  # ~Gluing opcodes
    )
    final_storage_gas = (
        gas_costs.G_VERY_LOW  # ADD
        + gas_costs.G_VERY_LOW * 3  # PUSHs
        + gas_costs.G_COLD_SLOAD  # SSTORE cold
        + gas_costs.G_STORAGE_RESET  # SSTORE new value
    )
    memory_expansion_cost = fork().memory_expansion_gas_calculator()(
        new_bytes=96
    )
    base_costs = (
        intrinsic_gas_cost_calc()
        + (gas_costs.G_VERY_LOW * 12)  # 8 PUSHs + 4 MSTOREs
        + final_storage_gas
        + memory_expansion_cost
    )
    num_contracts = (attack_gas_limit - base_costs) // loop_cost

    # Create a factory that deploys a new SELFDESTRUCT contract instance pre-
    # funded depending on the value_bearing parameter. We use CREATE2 so the
    # caller contract can easily reproduce the addresses in a loop for CALLs.
    factory_code = (
        Op.EXTCODECOPY(
            address=initcode_address,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(initcode_address),
        )
        + Op.MSTORE(
            0,
            Op.CREATE2(
                value=1 if value_bearing else 0,
                offset=0,
                size=Op.EXTCODESIZE(initcode_address),
                salt=Op.SLOAD(0),
            ),
        )
        + Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.RETURN(0, 32)
    )

    required_balance = (
        num_contracts if value_bearing else 0
    )  # 1 wei per contract
    factory_address = pre.deploy_contract(
        code=factory_code, balance=required_balance
    )

    factory_caller_code = Op.CALLDATALOAD(0) + While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )
    factory_caller_address = pre.deploy_contract(code=factory_caller_code)

    # The deployed code length is two-bytes. The dominant factor
    # is the static cost, plus a few glue opcodes/memory-expansion costs.
    estimated_gas_per_creation = gas_costs.G_CREATE + 3_000
    max_creations_per_tx = int(tx_gas_limit // estimated_gas_per_creation)
    num_setup_txs = math.ceil(num_contracts / max_creations_per_tx)

    setup_txs = []
    with TestPhaseManager.setup():
        for i in range(num_setup_txs):
            count = min(
                max_creations_per_tx, num_contracts - i * max_creations_per_tx
            )
            setup_txs.append(
                Transaction(
                    to=factory_caller_address,
                    gas_limit=tx_gas_limit,
                    data=Hash(count),
                    sender=pre.fund_eoa(),
                )
            )

    code = (
        (
            create2_preimage := Create2PreimageLayout(
                factory_address=factory_address,
                salt=Op.CALLDATALOAD(0),
                init_code_hash=initcode.keccak256(),
            )
        )
        # Main loop
        + While(
            body=Op.POP(Op.CALL(address=create2_preimage.address_op()))
            + create2_preimage.increment_salt_op(),
            # Loop while we have enough gas AND within target count
            condition=Op.GT(Op.GAS, final_storage_gas + loop_cost),
        )
        + Op.SSTORE(
            0, Op.ADD(Op.SLOAD(0), 1)
        )  # Done for successful tx execution assertion below.
    )
    assert len(code) <= fork.max_code_size()

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, storage={0: 1})

    # Calculate max targets per execution TX based on effective gas limit
    max_targets_per_tx = (tx_gas_limit - base_costs) // loop_cost
    num_exec_txs = math.ceil(num_contracts / max_targets_per_tx)

    exec_txs = []
    with TestPhaseManager.execution():
        for i in range(num_exec_txs):
            start = i * max_targets_per_tx
            count = min(max_targets_per_tx, num_contracts - start)
            exec_txs.append(
                Transaction(
                    to=code_addr,
                    gas_limit=tx_gas_limit,
                    data=Hash(start),
                    sender=pre.fund_eoa(),
                )
            )

    post = {
        factory_address: Account(storage={0: num_contracts}),
        code_addr: Account(
            storage={0: len(exec_txs) + 1}
        ),  # Check for successful execution.
    }
    deployed_contract_addresses = []
    for i in range(num_contracts):
        deployed_contract_address = compute_create2_address(
            address=factory_address,
            salt=i,
            initcode=initcode,
        )
        post[deployed_contract_address] = Account(nonce=1)
        deployed_contract_addresses.append(deployed_contract_address)

    benchmark_test(
        post=post,
        target_opcode=Op.SELFDESTRUCT,
        blocks=[
            Block(txs=setup_txs),
            Block(txs=exec_txs, fee_recipient=fee_recipient),
        ],
        skip_gas_used_validation=True,
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_created(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark SELFDESTRUCT instruction for deployed contracts within same tx.
    """
    # Avoid account creation costs in the SELFDESTRUCT recipient.
    fee_recipient = pre.fund_eoa(amount=1)
    env.fee_recipient = fee_recipient

    # SELFDESTRUCT(COINBASE) contract deployment
    initcode = (
        Op.MSTORE8(0, Op.COINBASE.int())
        + Op.MSTORE8(1, Op.SELFDESTRUCT.int())
        + Op.RETURN(0, 2)
    )
    gas_costs = fork.gas_costs()
    memory_expansion_calc = fork().memory_expansion_gas_calculator()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()

    initcode_costs = (
        gas_costs.G_VERY_LOW * 8  # MSTOREs, PUSHs
        + memory_expansion_calc(new_bytes=2)  # return into memory
    )
    create_costs = (
        initcode_costs
        + gas_costs.G_CREATE
        + gas_costs.G_VERY_LOW * 3  # Create Parameter PUSHs
        + gas_costs.G_CODE_DEPOSIT_BYTE * 2
        + gas_costs.G_INITCODE_WORD
    )
    call_costs = (
        gas_costs.G_WARM_ACCOUNT_ACCESS
        + gas_costs.G_BASE  # COINBASE
        + gas_costs.G_SELF_DESTRUCT
        + gas_costs.G_VERY_LOW * 5  # CALL Parameter PUSHs
        + gas_costs.G_BASE  #  Parameter GAS
    )
    extra_costs = (
        gas_costs.G_BASE * 2  # POP, GAS
        + gas_costs.G_VERY_LOW * 5  # PUSHs, ADD, DUP, GT
        + gas_costs.G_HIGH  # JUMPI
        + gas_costs.G_JUMPDEST
    )
    loop_cost = create_costs + call_costs + extra_costs

    prefix_cost = (
        gas_costs.G_VERY_LOW * 3
        + gas_costs.G_BASE
        + memory_expansion_calc(new_bytes=32)
    )
    suffix_cost = (
        gas_costs.G_VERY_LOW
        + gas_costs.G_VERY_LOW * 3
        + gas_costs.G_COLD_SLOAD
        + gas_costs.G_STORAGE_RESET
    )

    base_costs = prefix_cost + suffix_cost + intrinsic_gas_cost_calc()

    iterations = (gas_benchmark_value - base_costs) // loop_cost

    code_prefix = Op.MSTORE(0, initcode.hex()) + Op.PUSH0 + Op.JUMPDEST
    code_suffix = (
        Op.SSTORE(
            0, Op.ADD(Op.SLOAD(0), 1)
        )  # Done for successful tx execution assertion below.
        + Op.STOP
    )
    loop_body = (
        Op.POP(
            Op.CALL(
                address=Op.CREATE(
                    value=1 if value_bearing else 0,
                    offset=32 - len(initcode),
                    size=len(initcode),
                )
            )
        )
        + Op.PUSH1[1]
        + Op.ADD
        + Op.JUMPI(
            len(code_prefix) - 1, Op.GT(Op.GAS, suffix_cost + loop_cost)
        )
    )
    code = code_prefix + loop_body + code_suffix

    max_iterations_per_tx = (tx_gas_limit - base_costs) // loop_cost
    num_exec_txs = math.ceil(iterations / max_iterations_per_tx)
    total_expected_iterations = max_iterations_per_tx * num_exec_txs

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(
        code=code,
        balance=total_expected_iterations if value_bearing else 0,
        storage={0: 1},
    )

    exec_txs = []
    with TestPhaseManager.execution():
        for _ in range(num_exec_txs):
            exec_txs.append(
                Transaction(
                    to=code_addr,
                    gas_limit=tx_gas_limit,
                    sender=pre.fund_eoa(),
                )
            )

    post = {
        code_addr: Account(storage={0: len(exec_txs) + 1})
    }  # Check for successful execution.
    benchmark_test(
        post=post,
        blocks=[
            Block(txs=exec_txs, fee_recipient=fee_recipient),
        ],
        expected_benchmark_gas_used=(
            max_iterations_per_tx * loop_cost + base_costs
        )
        * num_exec_txs,
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_initcode(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """Benchmark SELFDESTRUCT instruction executed in initcode."""
    # Avoid account creation costs in the SELFDESTRUCT recipient.
    fee_recipient = pre.fund_eoa(amount=1)
    env.fee_recipient = fee_recipient

    gas_costs = fork.gas_costs()
    memory_expansion_calc = fork().memory_expansion_gas_calculator()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()

    initcode_costs = (
        gas_costs.G_BASE  # COINBASE
        + gas_costs.G_SELF_DESTRUCT
    )
    create_costs = (
        initcode_costs
        + gas_costs.G_CREATE
        + gas_costs.G_VERY_LOW * 3  # Create Parameter PUSHs
        + gas_costs.G_INITCODE_WORD
    )
    extra_costs = (
        gas_costs.G_BASE * 2  # POP, GAS
        + gas_costs.G_VERY_LOW * 5  # PUSHs, ADD, GT
        + gas_costs.G_HIGH  # JUMPI
        + gas_costs.G_JUMPDEST
    )
    loop_cost = create_costs + extra_costs

    prefix_cost = (
        gas_costs.G_VERY_LOW * 3
        + gas_costs.G_BASE
        + memory_expansion_calc(new_bytes=32)
    )
    suffix_cost = (
        gas_costs.G_VERY_LOW
        + gas_costs.G_VERY_LOW * 3
        + gas_costs.G_COLD_SLOAD
        + gas_costs.G_STORAGE_RESET
    )

    base_costs = prefix_cost + suffix_cost + intrinsic_gas_cost_calc()

    initcode = Op.SELFDESTRUCT(Op.COINBASE)
    code_prefix = Op.MSTORE(0, initcode.hex()) + Op.PUSH0 + Op.JUMPDEST
    code_suffix = (
        Op.SSTORE(
            0, Op.ADD(Op.SLOAD(0), 1)
        )  # Done for successful tx execution assertion below.
        + Op.STOP
    )

    loop_body = (
        Op.POP(
            Op.CREATE(
                value=1 if value_bearing else 0,
                offset=32 - len(initcode),
                size=len(initcode),
            )
        )
        + Op.PUSH1[1]
        + Op.ADD
        + Op.JUMPI(
            len(code_prefix) - 1, Op.GT(Op.GAS, suffix_cost + loop_cost)
        )
    )
    code = code_prefix + loop_body + code_suffix

    # The 0 storage slot is initialized to avoid creation
    # costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, balance=100_000, storage={0: 1})

    exec_txs = []
    expected_benchmark_gas_used = 0
    with TestPhaseManager.execution():
        used_gas = 0
        while used_gas < gas_benchmark_value:
            gas_limit = min(tx_gas_limit, gas_benchmark_value - used_gas)
            if gas_limit < intrinsic_gas_cost_calc():
                break
            exec_txs.append(
                Transaction(
                    to=code_addr,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                )
            )
            used_gas += gas_limit
            iterations = (gas_limit - base_costs) // loop_cost
            expected_benchmark_gas_used += iterations * loop_cost + base_costs

    post = {
        code_addr: Account(storage={0: len(exec_txs) + 1})
    }  # Check for successful execution.
    benchmark_test(
        post=post,
        blocks=[
            Block(txs=exec_txs, fee_recipient=fee_recipient),
        ],
        expected_benchmark_gas_used=expected_benchmark_gas_used,
    )
