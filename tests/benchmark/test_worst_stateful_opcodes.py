"""
Tests that benchmark EVMs for worst-case stateful opcodes.
"""

import math
from enum import auto

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Environment,
    ExtCallGenerator,
    Fork,
    Hash,
    JumpLoopGenerator,
    Op,
    StateTestFiller,
    TestPhaseManager,
    Transaction,
    While,
    compute_create2_address,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"


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
def test_worst_address_state_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_accounts: bool,
    gas_benchmark_value: int,
    tx_gas_limit_cap: int,
) -> None:
    """
    Test running a block with as many stateful opcodes accessing cold accounts.
    """
    # Gas Costs
    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()

    # Constants
    num_contracts = (
        2 * gas_benchmark_value
    ) // gas_costs.G_COLD_ACCOUNT_ACCESS

    # Setup The target addresses are going to be constructed (in the case of
    # absent=False) and called as addr_offset + i, where i is the index of the
    # account. This is to avoid collisions with the addresses indirectly
    # created by the testing framework.
    addr_offset = int.from_bytes(pre.fund_eoa(amount=0))

    # Variables
    blocks = []
    post = {}

    if not absent_accounts:
        setup = Op.JUMPDEST
        loop = Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.ADD(addr_offset, Op.SELFBALANCE),
                value=1,
                args_offset=Op.PUSH0,
                args_size=Op.PUSH0,
                ret_offset=Op.PUSH0,
                ret_size=Op.PUSH0,
            )
        )
        cleanup = (
            Op.JUMPI(0, Op.ISZERO(Op.EQ(Op.SELFBALANCE, Op.CALLDATALOAD(0))))
            + Op.STOP
        )
        factory_code = setup + loop + cleanup

        factory_address = pre.deploy_contract(
            code=factory_code, balance=num_contracts
        )

        loop_cost = 37_000
        gas_available = tx_gas_limit_cap - intrinsic_gas_cost_calc()
        loop_count_per_iter = gas_available // loop_cost
        tx_count = gas_benchmark_value // tx_gas_limit_cap

        setup_txs = []
        for i in range(tx_count * 2):
            tx = Transaction(
                to=factory_address,
                data=Hash(num_contracts - (i + 1) * loop_count_per_iter),
                gas_limit=tx_gas_limit_cap,
                sender=pre.fund_eoa(),
            )
            setup_txs.append(tx)

        blocks.append(Block(txs=setup_txs[:tx_count]))
        blocks.append(Block(txs=setup_txs[tx_count:]))

        for i in range(tx_count * 2 * loop_count_per_iter):
            addr = Address(addr_offset + num_contracts - i)
            post[addr] = Account(balance=1)

    # Execution
    attack_address = pre.deploy_contract(
        code=Op.CALLDATALOAD(0)
        + While(
            body=Op.POP(opcode(address=Op.ADD(addr_offset, Op.DUP1))),
            condition=Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.CALLVALUE
            + Op.GT,
        )
    )

    loop_cost = gas_costs.G_COLD_ACCOUNT_ACCESS + 25 * gas_costs.G_VERY_LOW

    attack_txs = []
    gas_remaining = gas_benchmark_value
    total_iteration = 0
    while gas_remaining > 0:
        gas_available = min(gas_remaining, tx_gas_limit_cap)
        iteration_count = gas_available // loop_cost

        if gas_available < intrinsic_gas_cost_calc():
            break

        tx = Transaction(
            to=attack_address,
            data=Hash(num_contracts - total_iteration),
            value=num_contracts - total_iteration - iteration_count,
            gas_limit=gas_available,
            sender=pre.fund_eoa(),
        )

        attack_txs.append(tx)
        gas_remaining -= gas_available
        total_iteration += iteration_count

    blocks.append(Block(txs=attack_txs))

    benchmark_test(
        post=post,
        blocks=blocks,
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
    "absent_target",
    [
        True,
        False,
    ],
)
def test_worst_address_state_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
    absent_target: bool,
) -> None:
    """
    Test running a block with as many stateful opcodes doing warm access
    for an account.
    """
    # Setup
    target_addr = Address(100_000)
    post = {}
    if not absent_target:
        code = Op.STOP + Op.JUMPDEST * 100
        target_addr = pre.deploy_contract(balance=100, code=code)
        post[target_addr] = Account(balance=100, code=code)

    # Execution
    setup = Op.MSTORE(0, target_addr)
    attack_block = Op.POP(opcode(address=Op.MLOAD(0)))
    benchmark_test(
        post=post,
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block
        ),
    )


class StorageAction:
    """Enum for storage actions."""

    READ = auto()
    WRITE_SAME_VALUE = auto()
    WRITE_NEW_VALUE = auto()


class TransactionResult:
    """Enum for the possible transaction outcomes."""

    SUCCESS = auto()
    OUT_OF_GAS = auto()
    REVERT = auto()


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
def test_worst_storage_access_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_action: StorageAction,
    absent_slots: bool,
    tx_gas_limit_cap: int,
    gas_benchmark_value: int,
    tx_result: TransactionResult,
) -> None:
    """
    Test running a block with as many cold storage slot accesses as possible.
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
        + gas_costs.G_VERY_LOW * 5  # GT, PUSHs, SWAPs, SUB, DUP
        + gas_costs.G_MID  # SELFBALANCE
        + gas_costs.G_HIGH  # JUMPI
    )

    prefix_cost = (
        gas_costs.G_VERY_LOW * 2  # CALLDATALOAD(0)
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

    code_prefix = Op.CALLDATALOAD(0) + Op.JUMPDEST
    code_loop = execution_code_body + Op.JUMPI(
        len(code_prefix) - 1,
        Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.SELFBALANCE + Op.GT,
    )
    execution_code = code_prefix + code_loop

    if tx_result == TransactionResult.REVERT:
        execution_code += Op.REVERT(0, 0)
    else:
        execution_code += Op.STOP

    execution_code_address = pre.deploy_contract(code=execution_code)

    blocks = []
    target_addr = execution_code_address

    # Setup the target address
    if not absent_slots:
        init_prefix = Op.CALLDATALOAD(0) + Op.JUMPDEST
        init_loop = Op.SSTORE(Op.DUP1, Op.DUP1)
        init_condition = Op.JUMPI(
            len(init_prefix) - 1,
            Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.SELFBALANCE + Op.GT,
        )
        init_contract = init_prefix + init_loop + init_condition

        target_addr = pre.fund_eoa(
            amount=0, delegation=pre.deploy_contract(code=init_contract)
        )

        init_prefix_overhead = gas_costs.G_VERY_LOW * 2 + gas_costs.G_JUMPDEST
        init_loop_overhead = (
            gas_costs.G_VERY_LOW * 2 + gas_costs.G_WARM_ACCOUNT_ACCESS
        )
        init_condition_overhead = (
            gas_costs.G_VERY_LOW * 5 + gas_costs.G_MID + gas_costs.G_HIGH
        )
        init_total_overhead = (
            init_prefix_overhead + init_loop_overhead + init_condition_overhead
        )
        iteration_count = (
            gas_benchmark_value - intrinsic_gas_cost_calc()
        ) // init_total_overhead

        tx_count = gas_benchmark_value // tx_gas_limit_cap
        total_txs = []
        for i in range(tx_count * 2):
            tx = Transaction(
                to=target_addr,
                data=Hash(i * iteration_count),
                value=iteration_count,
                gas_limit=tx_gas_limit_cap,
                sender=pre.fund_eoa(),
            )
            total_txs.append(tx)
        blocks.append(Block(txs=total_txs[:tx_count]))
        blocks.append(Block(txs=total_txs[tx_count:]))

        tx = Transaction(
            to=execution_code_address,
            gas_limit=tx_gas_limit_cap,
            sender=pre.fund_eoa(),
            authorization_list=[
                AuthorizationTuple(
                    address=execution_code_address,
                    nonce=target_addr.nonce,
                    signer=target_addr,
                )
            ],
        )
        blocks.append(Block(txs=[tx]))

    attack_txs = []
    gas_remaining = gas_benchmark_value
    total_iteration = 0
    total_gas_used = 0
    while gas_remaining > 0:
        gas_available = min(gas_remaining, tx_gas_limit_cap)

        # Calculate minimum gas needed for at least one iteration
        min_gas_needed = (
            intrinsic_gas_cost_calc() + prefix_cost + loop_cost + suffix_cost
        )
        if gas_available < min_gas_needed:
            break

        # Calculate iterations accounting for all overhead costs
        if tx_result == TransactionResult.OUT_OF_GAS:
            # For OUT_OF_GAS, add an extra iteration to run out of gas
            iterations = (
                (
                    gas_available
                    - intrinsic_gas_cost_calc()
                    - prefix_cost
                    - suffix_cost
                )
                // loop_cost
            ) + 1
            tx_gas_used = (
                gas_available  # Transaction will use all available gas
            )
        else:
            # For SUCCESS and REVERT, calculate iterations properly
            iterations = (
                gas_available
                - intrinsic_gas_cost_calc()
                - prefix_cost
                - suffix_cost
            ) // loop_cost
            tx_gas_used = (
                intrinsic_gas_cost_calc()
                + prefix_cost
                + loop_cost * iterations
                + suffix_cost
            )

        attack_txs.append(
            Transaction(
                to=execution_code_address,
                data=Hash(total_iteration),
                value=iterations,
                gas_limit=gas_available,
                sender=pre.fund_eoa(),
            )
        )
        gas_remaining -= gas_available
        total_iteration += iterations
        total_gas_used += tx_gas_used

    blocks.append(Block(txs=attack_txs))

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
def test_worst_storage_access_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    storage_action: StorageAction,
    gas_benchmark_value: int,
    env: Environment,
) -> None:
    """
    Test running a block with as many warm storage slot accesses as
    possible.
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


def test_worst_blockhash(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit_cap: int,
) -> None:
    """
    Test running a block with as many blockhash accessing oldest allowed block
    as possible.
    """
    # Create 256 dummy blocks to fill the blockhash window.
    blocks = [Block()] * 256

    benchmark_test(
        setup_blocks=blocks,
        code_generator=ExtCallGenerator(attack_block=Op.BLOCKHASH(1)),
        expected_benchmark_gas_used=gas_benchmark_value,
    )


@pytest.mark.parametrize("contract_balance", [0, 1])
def test_worst_selfbalance(
    benchmark_test: BenchmarkTestFiller,
    contract_balance: int,
) -> None:
    """Test running a block with as many SELFBALANCE opcodes as possible."""
    benchmark_test(
        code_generator=ExtCallGenerator(
            attack_block=Op.SELFBALANCE,
            contract_balance=contract_balance,
        ),
    )


@pytest.mark.parametrize(
    "copied_size",
    [
        pytest.param(512, id="512"),
        pytest.param(1024, id="1KiB"),
        pytest.param(5 * 1024, id="5KiB"),
    ],
)
def test_worst_extcodecopy_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    copied_size: int,
    gas_benchmark_value: int,
) -> None:
    """Test running a block with as many wamr EXTCODECOPY work as possible."""
    copied_contract_address = pre.deploy_contract(
        code=Op.JUMPDEST * copied_size,
    )

    execution_code = (
        Op.PUSH10(copied_size)
        + Op.PUSH20(copied_contract_address)
        + While(
            body=Op.EXTCODECOPY(Op.DUP4, 0, 0, Op.DUP2),
        )
    )
    execution_code_address = pre.deploy_contract(code=execution_code)
    tx = Transaction(
        to=execution_code_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


@pytest.mark.parametrize("value_bearing", [True, False])
def test_worst_selfdestruct_existing(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    value_bearing: bool,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Test running a block with as many SELFDESTRUCTs as possible for existing
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
def test_worst_selfdestruct_created(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Test running a block with as many SELFDESTRUCTs as possible for deployed
    contracts in the same transaction.
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
def test_worst_selfdestruct_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Test running a block with as many SELFDESTRUCTs as possible executed in
    initcode.
    """
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
