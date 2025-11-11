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
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Hash,
    JumpLoopGenerator,
    Op,
    StateTestFiller,
    Transaction,
    While,
    compute_create2_address,
    compute_create_address,
)

from tests.benchmark.compute.helpers import XOR_TABLE


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
    ],
)
def test_xcall(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """Benchmark a system execution where a single opcode execution."""
    # The attack gas limit is the gas limit which the target tx will use The
    # test will scale the block gas limit to setup the contracts accordingly to
    # be able to pay for the contract deposit. This has to take into account
    # the 200 gas per byte, but also the quadratic memory expansion costs which
    # have to be paid each time the memory is being setup
    attack_gas_limit = gas_benchmark_value
    max_contract_size = fork.max_code_size()

    gas_costs = fork.gas_costs()

    # Calculate the absolute minimum gas costs to deploy the contract This does
    # not take into account setting up the actual memory (using KECCAK256 and
    # XOR) so the actual costs of deploying the contract is higher
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    memory_gas_minimum = memory_expansion_gas_calculator(
        new_bytes=len(bytes(max_contract_size))
    )
    code_deposit_gas_minimum = (
        fork.gas_costs().G_CODE_DEPOSIT_BYTE * max_contract_size
        + memory_gas_minimum
    )

    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # Calculate the loop cost of the attacker to query one address
    loop_cost = (
        gas_costs.G_KECCAK_256  # KECCAK static cost
        + math.ceil(85 / 32) * gas_costs.G_KECCAK_256_WORD  # KECCAK dynamic
        # cost for CREATE2
        + gas_costs.G_VERY_LOW * 3  # ~MSTOREs+ADDs
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Opcode cost
        + 30  # ~Gluing opcodes
    )
    # Calculate the number of contracts to be targeted
    num_contracts = (
        # Base available gas = GAS_LIMIT - intrinsic - (out of loop MSTOREs)
        attack_gas_limit - intrinsic_gas_cost_calc() - gas_costs.G_VERY_LOW * 4
    ) // loop_cost

    # Set the block gas limit to a relative high value to ensure the code
    # deposit tx fits in the block (there is enough gas available in the block
    # to execute this)
    minimum_gas_limit = code_deposit_gas_minimum * 2 * num_contracts
    if env.gas_limit < minimum_gas_limit:
        raise Exception(
            f"`BENCHMARKING_MAX_GAS` ({env.gas_limit}) is no longer enough to"
            f" support this test, which requires {minimum_gas_limit} gas for "
            "its setup. Update the value or consider optimizing gas usage "
            "during the setup phase of this test."
        )

    # The initcode will take its address as a starting point to the input to
    # the keccak hash function. It will reuse the output of the hash function
    # in a loop to create a large amount of seemingly random code, until it
    # reaches the maximum contract size.
    initcode = (
        Op.MSTORE(0, Op.ADDRESS)
        + While(
            body=(
                Op.SHA3(Op.SUB(Op.MSIZE, 32), 32)
                # Use a xor table to avoid having to call the "expensive" sha3
                # opcode as much
                + sum(
                    (
                        Op.PUSH32[xor_value]
                        + Op.XOR
                        + Op.DUP1
                        + Op.MSIZE
                        + Op.MSTORE
                    )
                    for xor_value in XOR_TABLE
                )
                + Op.POP
            ),
            condition=Op.LT(Op.MSIZE, max_contract_size),
        )
        # Despite the whole contract has random bytecode, we make the first
        # opcode be a STOP so CALL-like attacks return as soon as possible,
        # while EXTCODE(HASH|SIZE) work as intended.
        + Op.MSTORE8(0, 0x00)
        + Op.RETURN(0, max_contract_size)
    )
    initcode_address = pre.deploy_contract(code=initcode)

    # The factory contract will simply use the initcode that is already
    # deployed, and create a new contract and return its address if successful.
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
                value=0,
                offset=0,
                size=Op.EXTCODESIZE(initcode_address),
                salt=Op.SLOAD(0),
            ),
        )
        + Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.RETURN(0, 32)
    )
    factory_address = pre.deploy_contract(code=factory_code)

    # The factory caller will call the factory contract N times, creating N new
    # contracts. Calldata should contain the N value.
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

    contracts_deployment_tx = Transaction(
        to=factory_caller_address,
        gas_limit=env.gas_limit,
        gas_price=10**6,
        data=Hash(num_contracts),
        sender=pre.fund_eoa(),
    )

    post = {}
    deployed_contract_addresses = []
    for i in range(num_contracts):
        deployed_contract_address = compute_create2_address(
            address=factory_address,
            salt=i,
            initcode=initcode,
        )
        post[deployed_contract_address] = Account(nonce=1)
        deployed_contract_addresses.append(deployed_contract_address)

    attack_call = Bytecode()
    if opcode == Op.EXTCODECOPY:
        attack_call = Op.EXTCODECOPY(
            address=Op.SHA3(32 - 20 - 1, 85), dest_offset=96, size=1000
        )
    else:
        # For the rest of the opcodes, we can use the same generic attack call
        # since all only minimally need the `address` of the target.
        attack_call = Op.POP(opcode(address=Op.SHA3(32 - 20 - 1, 85)))
    attack_code = (
        # Setup memory for later CREATE2 address generation loop.
        # 0xFF+[Address(20bytes)]+[seed(32bytes)]+[initcode keccak(32bytes)]
        Op.MSTORE(0, factory_address)
        + Op.MSTORE8(32 - 20 - 1, 0xFF)
        + Op.MSTORE(32, 0)
        + Op.MSTORE(64, initcode.keccak256())
        # Main loop
        + While(
            body=attack_call + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        )
    )

    if len(attack_code) > max_contract_size:
        # TODO: A workaround could be to split the opcode code into multiple
        # contracts and call them in sequence.
        raise ValueError(
            f"Code size {len(attack_code)} exceeds maximum "
            f"code size {max_contract_size}"
        )
    opcode_address = pre.deploy_contract(code=attack_code)
    opcode_tx = Transaction(
        to=opcode_address,
        gas_limit=attack_gas_limit,
        gas_price=10**9,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=[contracts_deployment_tx]),
            Block(txs=[opcode_tx]),
        ],
        exclude_full_post_state_in_output=True,
    )


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

    code = JumpLoopGenerator(
        setup=setup, attack_block=attack_block
    ).generate_repeated_code(
        repeated_code=attack_block, setup=setup, fork=fork
    )

    tx = Transaction(
        # Set enough balance in the pre-alloc for `value > 0` configurations.
        to=pre.deploy_contract(
            code=code, balance=1_000_000_000 if value > 0 else 0
        ),
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


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
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    return_size: int,
    return_non_zero_data: bool,
) -> None:
    """Benchmark RETURN and REVERT instructions."""
    max_code_size = fork.max_code_size()

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
    executable_code = mem_preparation + opcode(size=return_size)
    code = executable_code
    if return_non_zero_data:
        code += Op.INVALID * (max_code_size - len(executable_code))
    target_contract_address = pre.deploy_contract(code=code)

    attack_block = Op.POP(Op.STATICCALL(address=target_contract_address))

    benchmark_test(
        code_generator=JumpLoopGenerator(attack_block=attack_block),
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_existing(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    value_bearing: bool,
    env: Environment,
    gas_benchmark_value: int,
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
        + gas_costs.G_SELF_DESTRUCT
        + 63  # ~Gluing opcodes
    )
    final_storage_gas = (
        gas_costs.G_STORAGE_RESET
        + gas_costs.G_COLD_SLOAD
        + (gas_costs.G_VERY_LOW * 2)
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
    expected_benchmark_gas_used = num_contracts * loop_cost + base_costs

    # Create a factory that deployes a new SELFDESTRUCT contract instance pre-
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

    required_balance = num_contracts if value_bearing else 0  # 1 wei per
    # contract
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

    contracts_deployment_tx = Transaction(
        to=factory_caller_address,
        gas_limit=env.gas_limit,
        data=Hash(num_contracts),
        sender=pre.fund_eoa(),
    )

    code = (
        # Setup memory for later CREATE2 address generation loop.
        # 0xFF+[Address(20bytes)]+[seed(32bytes)]+[initcode keccak(32bytes)]
        Op.MSTORE(0, factory_address)
        + Op.MSTORE8(32 - 20 - 1, 0xFF)
        + Op.MSTORE(32, 0)
        + Op.MSTORE(64, initcode.keccak256())
        # Main loop
        + While(
            body=Op.POP(Op.CALL(address=Op.SHA3(32 - 20 - 1, 85)))
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
            # Only loop if we have enough gas to cover another iteration plus
            # the final storage gas.
            condition=Op.GT(Op.GAS, final_storage_gas + loop_cost),
        )
        + Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
    )
    assert len(code) <= fork.max_code_size()

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, storage={0: 1})
    opcode_tx = Transaction(
        to=code_addr,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {
        factory_address: Account(storage={0: num_contracts}),
        code_addr: Account(storage={0: 42}),  # Check for successful execution.
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
        blocks=[
            Block(txs=[contracts_deployment_tx]),
            Block(txs=[opcode_tx], fee_recipient=fee_recipient),
        ],
        expected_benchmark_gas_used=expected_benchmark_gas_used,
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_created(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark SELFDESTRUCT instruction for deployed contracts within same tx.
    """
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
        gas_costs.G_BASE  # POP
        + gas_costs.G_VERY_LOW * 6  # PUSHs, ADD, DUP, GT
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
        gas_costs.G_COLD_SLOAD
        + gas_costs.G_STORAGE_RESET
        + (gas_costs.G_VERY_LOW * 2)
    )

    base_costs = prefix_cost + suffix_cost + intrinsic_gas_cost_calc()

    iterations = (gas_benchmark_value - base_costs) // loop_cost

    code_prefix = Op.MSTORE(0, initcode.hex()) + Op.PUSH0 + Op.JUMPDEST
    code_suffix = (
        Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
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
        + Op.JUMPI(len(code_prefix) - 1, Op.GT(iterations, Op.DUP1))
    )
    code = code_prefix + loop_body + code_suffix
    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(
        code=code,
        balance=iterations if value_bearing else 0,
        storage={0: 1},
    )
    code_tx = Transaction(
        to=code_addr,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    post = {code_addr: Account(storage={0: 42})}  # Check for successful
    # execution.
    state_test(
        pre=pre,
        post=post,
        tx=code_tx,
        expected_benchmark_gas_used=iterations * loop_cost + base_costs,
    )


@pytest.mark.parametrize("value_bearing", [True, False])
def test_selfdestruct_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """Benchmark SELFDESTRUCT instruction executed in initcode."""
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
        gas_costs.G_BASE  # POP
        + gas_costs.G_VERY_LOW * 6  # PUSHs, ADD, DUP, GT
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
        gas_costs.G_COLD_SLOAD
        + gas_costs.G_STORAGE_RESET
        + (gas_costs.G_VERY_LOW * 2)
    )

    base_costs = prefix_cost + suffix_cost + intrinsic_gas_cost_calc()

    iterations = (gas_benchmark_value - base_costs) // loop_cost

    initcode = Op.SELFDESTRUCT(Op.COINBASE)
    code_prefix = Op.MSTORE(0, initcode.hex()) + Op.PUSH0 + Op.JUMPDEST
    code_suffix = (
        Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
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
        + Op.JUMPI(len(code_prefix) - 1, Op.GT(iterations, Op.DUP1))
    )
    code = code_prefix + loop_body + code_suffix

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, balance=100_000, storage={0: 1})
    code_tx = Transaction(
        to=code_addr,
        gas_limit=gas_benchmark_value,
        gas_price=10,
        sender=pre.fund_eoa(),
    )

    post = {code_addr: Account(storage={0: 42})}  # Check for successful
    # execution.
    state_test(
        pre=pre,
        post=post,
        tx=code_tx,
        expected_benchmark_gas_used=iterations * loop_cost + base_costs,
    )
