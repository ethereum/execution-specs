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
from typing import Any

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Conditional,
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
    WhileGas,
    compute_create2_address,
    compute_create_address,
)
from execution_testing import Macros as Om

from tests.frontier.identity_precompile.spec import Spec as IdentitySpec


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
    fixed_opcode_count: float | None,
) -> None:
    """Benchmark a contract that calls many distinct addresses."""
    start_addr = 2**80 - 1

    value_transfer = transfer_amount > 0
    # Only CALL creates accounts on value transfer (CALLCODE doesn't).
    account_creation = value_transfer and opcode == Op.CALL

    setup = (
        Op.ADD(1, Op.CALLDATALOAD(32))  # [end+1 = limit]
        + Op.CALLDATALOAD(0)  # [start = index, limit]
    )

    iterating = While(
        body=Op.POP(
            opcode(
                address=Op.ADD(start_addr, Op.DUP6),
                value=transfer_amount,
                # gas accounting
                address_warm=access_warm,
                value_transfer=value_transfer,
                account_new=account_creation,
            )
        ),
        condition=Op.PUSH1(1)  # [1, index, limit]
        + Op.ADD  # [index+1, limit]
        + Op.DUP1  # [index+1, index+1, limit]
        + Op.DUP3  # [limit, index+1, index+1, limit]
        + Op.GT,  # [limit > index+1, index+1, limit]
    )
    code = IteratingBytecode(
        setup=setup,
        iterating=iterating,
        cleanup=Op.STOP,
    )

    contract_address = pre.deploy_contract(
        code=code,
        balance=10**9 if value_transfer else 0,
    )

    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        index_end = start_iteration + iteration_count - 1
        return Hash(start_iteration) + Hash(index_end)

    def access_list(
        iteration_count: int, start_iteration: int
    ) -> list[AccessList]:
        return [
            AccessList(address=Address(start_addr + i), storage_keys=[])
            for i in range(start_iteration, start_iteration + iteration_count)
        ]

    tx_kwargs: dict = {
        "calldata": calldata,
        "access_list": access_list if access_warm else None,
    }

    total_iterations = (
        sum(
            code.tx_iterations_by_gas_limit(
                fork=fork, gas_limit=gas_benchmark_value, **tx_kwargs
            )
        )
        if fixed_opcode_count is None
        else int(fixed_opcode_count * 1000)
    )

    if total_iterations == 0:
        pytest.skip(
            "Benchmark gas value cannot cover a single call to the contract."
        )

    with TestPhaseManager.execution():
        sender = pre.fund_eoa()
        if fixed_opcode_count is not None:
            exec_txs = list(
                code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=total_iterations,
                    sender=sender,
                    to=contract_address,
                    **tx_kwargs,
                )
            )
        else:
            exec_txs = list(
                code.transactions_by_gas_limit(
                    fork=fork,
                    gas_limit=gas_benchmark_value,
                    sender=sender,
                    to=contract_address,
                    **tx_kwargs,
                )
            )
        total_gas_cost = sum(tx.gas_cost for tx in exec_txs)
        if value_transfer:
            total_gas_cost -= fork.gas_costs().CALL_STIPEND * total_iterations

    post = {
        Address(start_addr + i): Account(balance=transfer_amount)
        for i in range(total_iterations)
        if account_creation
    }

    benchmark_test(
        post=post,
        blocks=[Block(txs=exec_txs)],
        expected_benchmark_gas_used=total_gas_cost,
    )


@pytest.mark.parametrize("opcode", [Op.DELEGATECALL, Op.STATICCALL])
@pytest.mark.parametrize(
    "warm_access",
    [True, False],
)
def test_delegatecall_staticcall(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
    warm_access: bool,
) -> None:
    """Benchmark a contract that STATICCALL/DELEGATECALL accounts."""
    target = pre.deploy_contract(code=Op.STOP)
    address = target if warm_access else Op.GAS

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(
                opcode(
                    gas=Op.GAS,
                    address=address,
                )
            ),
        ),
    )


@pytest.mark.parametrize(
    "opcode,value",
    [
        pytest.param(Op.CALL, 0, id="CALL"),
        pytest.param(Op.CALL, 1, id="CALL with value"),
        pytest.param(Op.CALLCODE, 0, id="CALLCODE"),
        pytest.param(Op.CALLCODE, 1, id="CALLCODE with value"),
        pytest.param(Op.DELEGATECALL, None, id="DELEGATECALL"),
        pytest.param(Op.STATICCALL, None, id="STATICCALL"),
    ],
)
def test_call_opcodes_to_precompile(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    value: int | None,
) -> None:
    """Benchmark every call opcode dispatching to a precompile."""
    value_kwarg: dict[str, Any] = {}
    if value is not None:
        value_kwarg = {"value": value}

    attack_block = Op.POP(
        opcode(
            gas=Op.GAS,
            address=IdentitySpec.IDENTITY,
            args_offset=Op.PUSH0,
            args_size=Op.PUSH0,
            ret_offset=Op.PUSH0,
            ret_size=Op.PUSH0,
            **value_kwarg,
        )
    )

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            attack_block=attack_block,
            contract_balance=10**9 if value else 0,
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
)
def test_nested_calls(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """Benchmark chains of nested call frames."""
    chain_address = pre.deploy_contract(
        code=Op.POP(opcode(gas=Op.GAS, address=Op.ADDRESS))
    )

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(Op.CALL(gas=Op.GAS, address=chain_address))
        ),
    )


def test_nested_call_chain(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    gas_benchmark_value: int,
) -> None:
    """Benchmark nested call frames that each enter a different contract."""
    # Overwriting the slot keeps the tail cheaper than filling a fresh one.
    tail = Op.SSTORE(0, 2, original_value=1, current_value=1, new_value=2)
    tail_address = pre.deploy_contract(code=tail, storage={0: 1})

    # Every level is a distinct account, so the first traversal pays cold
    # access all the way down.
    address = tail_address
    link = Op.POP(Op.CALL(gas=Op.GAS, address=address, address_warm=False))
    tail_call_gas = link.gas_cost(fork) + math.ceil(
        tail.gas_cost(fork) * 64 / 63
    )

    gas = min(tx_gas_limit, gas_benchmark_value)
    gas -= fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    while True:
        forwarded_gas = gas - link.gas_cost(fork)
        forwarded_gas -= forwarded_gas // 64
        if forwarded_gas < tail_call_gas:
            break
        gas = forwarded_gas
        address = pre.deploy_contract(code=link)
        link = Op.POP(Op.CALL(gas=Op.GAS, address=address, address_warm=False))

    benchmark_test(
        target_opcode=Op.CALL,
        skip_gas_used_validation=True,
        post={tail_address: Account(storage={0: 2})},
        tx=Transaction(
            to=pre.deploy_contract(code=WhileGas(body=link, fork=fork)),
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.parametrize("out_of_gas", [True, False])
def test_nested_creates(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    out_of_gas: bool,
) -> None:
    """Benchmark chains of nested CREATE frames."""
    initcode_size = 32

    copy_self = Op.CODECOPY(
        dest_offset=0,
        offset=0,
        size=Op.CODESIZE,
        # gas accounting
        data_size=initcode_size,
        old_memory_size=0,
        new_memory_size=initcode_size,
    )

    create_self = Op.POP(
        Op.CREATE(
            value=0,
            offset=0,
            size=Op.CODESIZE,
            # gas accounting
            init_code_size=initcode_size,
            old_memory_size=initcode_size,
            new_memory_size=initcode_size,
        )
    )

    initcode = copy_self + create_self
    if not out_of_gas:
        initcode = copy_self + Conditional(
            condition=Op.GT(Op.GAS, 2 * initcode.gas_cost(fork)),
            if_true=create_self,
        )

    assert len(initcode) <= initcode_size, "initcode outgrew its padding"
    initcode += Op.STOP * (initcode_size - len(initcode))

    setup = Om.MSTORE(bytes(initcode), 0)
    launch = Op.POP(
        Op.CREATE(
            value=0,
            offset=0,
            size=initcode_size,
            # gas accounting
            init_code_size=initcode_size,
            old_memory_size=initcode_size,
            new_memory_size=initcode_size,
        )
    )

    if out_of_gas:
        benchmark_test(
            target_opcode=Op.CREATE,
            code_generator=JumpLoopGenerator(setup=setup, attack_block=launch),
        )
    else:
        driver_address = pre.deploy_contract(
            code=setup + WhileGas(body=launch, fork=fork)
        )
        # Every level spends fifteen times more state gas than execution
        # gas, so a single transaction asking for the whole budget goes
        # deeper than several could: the state gas the chain spends counts
        # against the budget whether a reservoir or execution gas paid it.
        gas_limit = min(tx_gas_limit, gas_benchmark_value)
        if fork.state_gas_reservoir_enabled():
            gas_limit = gas_benchmark_value

        benchmark_test(
            target_opcode=Op.CREATE,
            skip_gas_used_validation=True,
            post={
                compute_create_address(
                    address=driver_address, nonce=1
                ): Account(nonce=2, code=b""),
            },
            blocks=[
                Block(
                    txs=[
                        Transaction(
                            to=driver_address,
                            gas_limit=gas_limit,
                            sender=pre.fund_eoa(),
                        )
                    ]
                )
            ],
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
    gas_benchmark_value: int,
    fixed_opcode_count: float | None,
) -> None:
    """Benchmark CREATE and CREATE2 instructions."""
    max_code_size = fork.max_code_size()

    code_size = int(max_code_size * max_code_size_ratio)

    copy = (
        Op.CODECOPY(
            dest_offset=0,
            offset=0,
            size=code_size,
            # gas accounting
            data_size=code_size,
            new_memory_size=code_size,
        )
        if non_zero_data
        else Bytecode()
    )

    initcode_body = copy + Op.RETURN(
        0,
        code_size,
        # gas accounting
        code_deposit_size=code_size,
        new_memory_size=0 if non_zero_data else code_size,
    )

    initcode = initcode_body

    if non_zero_data:  # Pad to code_size so CODECOPY has code_size bytes.
        initcode += bytes(
            [i % 256 for i in range(code_size - len(initcode_body))]
        )

    initcode_template_contract = pre.deploy_contract(code=initcode)

    # CALLDATA[0:32] = start index
    # CALLDATA[32:64] = end index
    setup = (
        Op.EXTCODECOPY(
            address=initcode_template_contract,
            dest_offset=0,
            offset=0,
            size=len(initcode),
            # gas accounting
            data_size=len(initcode),
            new_memory_size=len(initcode),
        )
        + Op.ADD(1, Op.CALLDATALOAD(32))  # [end+1 = limit]
        + Op.CALLDATALOAD(0)  # [start = index, limit]
    )

    # CREATE2 takes the loop index (stack top) as its salt;
    salt_kwarg: dict[str, Any] = {}
    if opcode == Op.CREATE2:
        salt_kwarg = {"salt": Op.DUP1}

    create_op = opcode(
        value=value,
        offset=0,
        size=len(initcode),
        init_code_size=len(initcode),
        **salt_kwarg,
    )

    loop = While(
        body=Op.POP(create_op),  # [index, limit]
        condition=Op.PUSH1(1)  # [1, index, limit]
        + Op.ADD  # [index+1, limit]
        + Op.DUP1  # [index+1, index+1, limit]
        + Op.DUP3  # [limit, index+1, index+1, limit]
        + Op.GT,  # [limit > index+1, index+1, limit]
    )

    code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        iterating_subcall=initcode_body,
        cleanup=Op.STOP,
    )

    contract_address = pre.deploy_contract(
        code=code,
        balance=10**9 if value > 0 else 0,
    )

    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        index_end = iteration_count + start_iteration - 1
        return Hash(start_iteration) + Hash(index_end)

    num_contracts = (
        sum(
            code.tx_iterations_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                calldata=calldata,
            )
        )
        if fixed_opcode_count is None
        else int(fixed_opcode_count * 1000)
    )

    if num_contracts == 0:
        pytest.skip(
            "Benchmark gas value cannot cover a single contract creation."
        )

    with TestPhaseManager.execution():
        sender = pre.fund_eoa()
        if fixed_opcode_count is not None:
            exec_txs = list(
                code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=num_contracts,
                    sender=sender,
                    to=contract_address,
                    calldata=calldata,
                )
            )
        else:
            exec_txs = list(
                code.transactions_by_gas_limit(
                    fork=fork,
                    gas_limit=gas_benchmark_value,
                    sender=sender,
                    to=contract_address,
                    calldata=calldata,
                )
            )
        total_gas_cost = sum(tx.gas_cost for tx in exec_txs)

    post = {
        compute_create_address(
            address=contract_address,
            nonce=1 + i,
            salt=i,
            initcode=initcode,
            opcode=opcode,
        ): Account(nonce=1)
        for i in range(num_contracts)
    }

    benchmark_test(
        post=post,
        target_opcode=opcode,
        blocks=[Block(txs=exec_txs)],
        expected_benchmark_gas_used=total_gas_cost,
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
    fixed_opcode_count: float | None,
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
    # The collision targets pre-exist (**), so per EIP-8037 the
    # CREATE(2) never charges NEW_ACCOUNT state gas.
    proxy_contract_code = (
        Op.CREATE2(
            value=Op.PUSH0,
            salt=Op.PUSH0,
            offset=Op.PUSH0,
            size=Op.PUSH0,
            # gas accounting
            account_new=False,
        )
        if opcode == Op.CREATE2
        else Op.CREATE(
            value=Op.PUSH0,
            offset=Op.PUSH0,
            size=Op.PUSH0,
            # gas accounting
            account_new=False,
        )
    )
    proxy_contract = pre.deploy_contract(code=proxy_contract_code)

    min_gas_required = proxy_contract_code.execution_cost(
        fork
    ) + proxy_contract_code.state_cost(fork)
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
        creation_cost = proxy_contract_code.execution_cost(fork)
        max_contract_count = (
            2 * gas_benchmark_value // creation_cost
            if fixed_opcode_count is None
            else int(fixed_opcode_count * 1000)
        )
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
    [
        Op.CREATE,
        Op.CREATE2,
    ],
)
@pytest.mark.parametrize(
    "revert_size",
    [
        pytest.param(0, id="empty revert data"),
        pytest.param(32, id="32 bytes of revert data"),
        pytest.param(1024, id="1KiB of revert data"),
    ],
)
def test_creates_reverting_initcode(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    revert_size: int,
) -> None:
    """Benchmark CREATE and CREATE2 whose initcode reverts."""
    initcode = Op.REVERT(0, revert_size)

    salt_kwarg: dict[str, Any] = {}
    if opcode == Op.CREATE2:
        salt_kwarg = {"salt": 0}

    attack_block = Op.POP(
        opcode(
            value=0,
            offset=32 - len(initcode),
            size=len(initcode),
            **salt_kwarg,
        )
    )

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=Op.MSTORE(0, initcode.hex()),
            attack_block=attack_block,
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

    total_gas_cost = sum(tx.gas_cost for tx in exec_txs)

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
        iterating_subcall=initcode + selfdestructable_contract,
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

    total_gas_cost = sum(tx.gas_cost for tx in exec_txs)

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


@pytest.mark.parametrize(
    "value_bearing,beneficiary_is_self",
    [
        pytest.param(False, False, id="without value"),
        pytest.param(True, False, id="with value moved to the creator"),
        pytest.param(True, True, id="with value burnt to self"),
    ],
)
def test_selfdestruct_initcode(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    value_bearing: bool,
    beneficiary_is_self: bool,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Benchmark SELFDESTRUCT instruction executed in initcode."""
    beneficiary = Op.ADDRESS if beneficiary_is_self else Op.CALLER
    initcode = Op.SELFDESTRUCT(beneficiary, address_warm=True)

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

    total_gas_cost = sum(tx.gas_cost for tx in exec_txs)

    returned_to_creator = value_bearing and not beneficiary_is_self
    post = {
        attack_code_address: Account(
            balance=num_iterations if returned_to_creator else 0
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
