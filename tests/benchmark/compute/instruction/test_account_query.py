"""
Benchmark operations that require querying the account state, either on the
current executing account or on a target account.

Supported Opcodes:
- SELFBALANCE
- CODESIZE
- CODECOPY
- EXTCODESIZE
- EXTCODEHASH
- EXTCODECOPY
- BALANCE
"""

import math
from typing import Any

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    BlockchainTestFiller,
    Bytecode,
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
)

from tests.benchmark.compute.helpers import (
    XOR_TABLE,
)


@pytest.mark.repricing(contract_balance=0)
@pytest.mark.parametrize("contract_balance", [0, 1])
def test_selfbalance(
    benchmark_test: BenchmarkTestFiller,
    contract_balance: int,
) -> None:
    """Benchmark SELFBALANCE instruction."""
    benchmark_test(
        code_generator=ExtCallGenerator(
            attack_block=Op.SELFBALANCE,
            contract_balance=contract_balance,
        ),
    )


@pytest.mark.repricing
def test_codesize(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark CODESIZE instruction."""
    benchmark_test(
        code_generator=ExtCallGenerator(attack_block=Op.CODESIZE),
    )


@pytest.mark.parametrize(
    "max_code_size_ratio",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(0.25, id="0.25x max code size"),
        pytest.param(0.50, id="0.50x max code size"),
        pytest.param(0.75, id="0.75x max code size"),
        pytest.param(1.00, id="max code size"),
    ],
)
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
def test_codecopy(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    max_code_size_ratio: float,
    fixed_src_dst: bool,
) -> None:
    """Benchmark CODECOPY instruction."""
    max_code_size = fork.max_code_size()

    size = int(max_code_size * max_code_size_ratio)

    setup = Op.PUSH32(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CODECOPY(src_dst, src_dst, Op.DUP1)  # DUP1 copies size.

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            code_padding_opcode=Op.STOP,
        )
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
        Op.EXTCODECOPY,
    ],
)
def test_extcode_ops(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark a block execution where a single opcode execution.
    """
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

    with TestPhaseManager.setup():
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

    with TestPhaseManager.execution():
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
    "copied_size",
    [
        pytest.param(512, id="512"),
        pytest.param(1024, id="1KiB"),
        pytest.param(5 * 1024, id="5KiB"),
    ],
)
def test_extcodecopy_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    copied_size: int,
) -> None:
    """Benchmark EXTCODECOPY instruction."""
    copied_contract_address = pre.deploy_contract(
        code=Op.JUMPDEST * copied_size,
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH10(copied_size) + Op.PUSH20(copied_contract_address),
            attack_block=Op.EXTCODECOPY(Op.DUP4, 0, 0, Op.DUP2),
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.BALANCE,
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
    ],
)
@pytest.mark.parametrize(
    "empty_code",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_balance",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_storage",
    [
        True,
        False,
    ],
)
def test_ext_account_query_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
    empty_code: bool,
    initial_balance: bool,
    initial_storage: bool,
) -> None:
    """
    Test running a block with as many stateful opcodes doing warm access
    for an account.
    """
    # Setup
    post = {}

    # Case 1: Completely empty account (no balance, no storage, no code)
    if not initial_balance and not initial_storage and empty_code:
        target_addr = pre.empty_account()
    # Case 2: EOA with optional balance and storage
    elif empty_code:
        eoa_kwargs: dict[str, Any] = {}
        if initial_balance:
            eoa_kwargs["amount"] = 100
        if initial_storage:
            eoa_kwargs["storage"] = {0: 0x1337}
        target_addr = pre.fund_eoa(**eoa_kwargs)
    # Case 3: Contract with optional balance and storage
    else:
        contract_kwargs: dict[str, Any] = {"code": Op.STOP + Op.JUMPDEST * 100}
        if initial_balance:
            contract_kwargs["balance"] = 100
        if initial_storage:
            contract_kwargs["storage"] = {0: 0x1337}
        target_addr = pre.deploy_contract(**contract_kwargs)
        post[target_addr] = Account(**contract_kwargs)

    benchmark_test(
        post=post,
        code_generator=JumpLoopGenerator(
            setup=Op.MSTORE(0, target_addr),
            attack_block=Op.POP(opcode(address=Op.MLOAD(0))),
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.BALANCE,
    ],
)
@pytest.mark.parametrize(
    "absent_accounts",
    [
        True,
        False,
    ],
)
def test_ext_account_query_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_accounts: bool,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark stateful opcodes accessing cold accounts.
    """
    attack_gas_limit = gas_benchmark_value

    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # For calculation robustness, the calculation below ignores "glue" opcodes
    # like  PUSH and POP. It should be considered a worst-case number of
    # accounts, and a few of them might not be targeted before the attacking
    # transaction runs out of gas.
    num_target_accounts = (
        attack_gas_limit - intrinsic_gas_cost_calc()
    ) // gas_costs.G_COLD_ACCOUNT_ACCESS

    blocks = []
    post = {}

    # Setup The target addresses are going to be constructed (in the case of
    # absent=False) and called as addr_offset + i, where i is the index of the
    # account. This is to avoid collisions with the addresses indirectly
    # created by the testing framework.
    addr_offset = int.from_bytes(pre.fund_eoa(amount=0))

    if not absent_accounts:
        factory_code = Op.PUSH4(num_target_accounts) + While(
            body=Op.POP(
                Op.CALL(address=Op.ADD(addr_offset, Op.DUP6), value=10)
            ),
            condition=Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )
        factory_address = pre.deploy_contract(
            code=factory_code, balance=10**18
        )

        with TestPhaseManager.setup():
            setup_tx = Transaction(
                to=factory_address,
                gas_limit=env.gas_limit,
                sender=pre.fund_eoa(),
            )
        blocks.append(Block(txs=[setup_tx]))

        for i in range(num_target_accounts):
            addr = Address(i + addr_offset + 1)
            post[addr] = Account(balance=10)

    # Execution
    op_code = Op.PUSH4(num_target_accounts) + While(
        body=Op.POP(opcode(Op.ADD(addr_offset, Op.DUP1))),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )
    op_address = pre.deploy_contract(code=op_code)

    with TestPhaseManager.execution():
        op_tx = Transaction(
            to=op_address,
            gas_limit=attack_gas_limit,
            sender=pre.fund_eoa(),
        )
    blocks.append(Block(txs=[op_tx]))

    benchmark_test(
        post=post,
        blocks=blocks,
    )
