"""
abstract: Tests that benchmark EVMs for worst-case stateful opcodes.
    Tests that benchmark EVMs for worst-case stateful opcodes.

Tests that benchmark EVMs for worst-case stateful opcodes.
"""

import math

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    While,
    compute_create2_address,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import code_loop_precompile_call

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"


@pytest.mark.valid_from("Cancun")
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
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_accounts: bool,
    env: Environment,
    gas_benchmark_value: int,
):
    """Test running a block with as many stateful opcodes accessing cold accounts."""
    attack_gas_limit = gas_benchmark_value

    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # For calculation robustness, the calculation below ignores "glue" opcodes like  PUSH and POP.
    # It should be considered a worst-case number of accounts, and a few of them might not be
    # targeted before the attacking transaction runs out of gas.
    num_target_accounts = (
        attack_gas_limit - intrinsic_gas_cost_calc()
    ) // gas_costs.G_COLD_ACCOUNT_ACCESS

    blocks = []
    post = {}

    # Setup
    # The target addresses are going to be constructed (in the case of absent=False) and called
    # as addr_offset + i, where i is the index of the account. This is to avoid
    # collisions with the addresses indirectly created by the testing framework.
    addr_offset = int.from_bytes(pre.fund_eoa(amount=0))

    if not absent_accounts:
        factory_code = Op.PUSH4(num_target_accounts) + While(
            body=Op.POP(Op.CALL(address=Op.ADD(addr_offset, Op.DUP6), value=10)),
            condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
        )
        factory_address = pre.deploy_contract(code=factory_code, balance=10**18)

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
        condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
    )
    op_address = pre.deploy_contract(code=op_code)
    op_tx = Transaction(
        to=op_address,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        exclude_full_post_state_in_output=True,
    )


@pytest.mark.valid_from("Cancun")
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
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_target: bool,
    gas_benchmark_value: int,
):
    """Test running a block with as many stateful opcodes doing warm access for an account."""
    max_code_size = fork.max_code_size()
    attack_gas_limit = gas_benchmark_value

    # Setup
    target_addr = Address(100_000)
    post = {}
    if not absent_target:
        code = Op.STOP + Op.JUMPDEST * 100
        target_addr = pre.deploy_contract(balance=100, code=code)
        post[target_addr] = Account(balance=100, code=code)

    # Execution
    prep = Op.MSTORE(0, target_addr)
    jumpdest = Op.JUMPDEST
    jump_back = Op.JUMP(len(prep))
    iter_block = Op.POP(opcode(address=Op.MLOAD(0)))
    max_iters_loop = (max_code_size - len(prep) - len(jumpdest) - len(jump_back)) // len(
        iter_block
    )
    op_code = prep + jumpdest + sum([iter_block] * max_iters_loop) + jump_back
    if len(op_code) > max_code_size:
        # Must never happen, but keep it as a sanity check.
        raise ValueError(f"Code size {len(op_code)} exceeds maximum code size {max_code_size}")
    op_address = pre.deploy_contract(code=op_code)
    tx = Transaction(
        to=op_address,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post=post,
        tx=tx,
    )


class StorageAction:
    """Enum for storage actions."""

    READ = 1
    WRITE_SAME_VALUE = 2
    WRITE_NEW_VALUE = 3


class TransactionResult:
    """Enum for the possible transaction outcomes."""

    SUCCESS = 1
    OUT_OF_GAS = 2
    REVERT = 3


@pytest.mark.valid_from("Cancun")
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
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_action: StorageAction,
    absent_slots: bool,
    env: Environment,
    gas_benchmark_value: int,
    tx_result: TransactionResult,
):
    """Test running a block with as many cold storage slot accesses as possible."""
    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    attack_gas_limit = gas_benchmark_value

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
        # The new value 2^256-1 is guaranteed to be different from the initial value.
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
        attack_gas_limit - intrinsic_gas_cost_calc() - prefix_cost - suffix_cost
    ) // loop_cost
    if tx_result == TransactionResult.OUT_OF_GAS:
        # Add an extra slot to make it run out-of-gas
        num_target_slots += 1

    code_prefix = Op.PUSH4(num_target_slots) + Op.JUMPDEST
    code_loop = execution_code_body + Op.JUMPI(
        len(code_prefix) - 1, Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO
    )
    execution_code = code_prefix + code_loop

    if tx_result == TransactionResult.REVERT:
        execution_code += Op.REVERT(0, 0)
    else:
        execution_code += Op.STOP

    execution_code_address = pre.deploy_contract(code=execution_code)

    total_gas_used = (
        num_target_slots * loop_cost + intrinsic_gas_cost_calc() + prefix_cost + suffix_cost
    )

    # Contract creation
    slots_init = Bytecode()
    if not absent_slots:
        slots_init = Op.PUSH4(num_target_slots) + While(
            body=Op.SSTORE(Op.DUP1, Op.DUP1),
            condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
        )

    # To create the contract, we apply the slots_init code to initialize the storage slots
    # (int the case of absent_slots=False) and then copy the execution code to the contract.
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
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        exclude_full_post_state_in_output=True,
        expected_benchmark_gas_used=(
            total_gas_used if tx_result != TransactionResult.OUT_OF_GAS else attack_gas_limit
        ),
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "storage_action",
    [
        pytest.param(StorageAction.READ, id="SLOAD"),
        pytest.param(StorageAction.WRITE_SAME_VALUE, id="SSTORE same value"),
        pytest.param(StorageAction.WRITE_NEW_VALUE, id="SSTORE new value"),
    ],
)
def test_worst_storage_access_warm(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    storage_action: StorageAction,
    env: Environment,
    gas_benchmark_value: int,
):
    """Test running a block with as many warm storage slot accesses as possible."""
    attack_gas_limit = gas_benchmark_value

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
    sender_addr = pre.fund_eoa()
    setup_tx = Transaction(
        to=None,
        gas_limit=env.gas_limit,
        data=creation_code,
        sender=sender_addr,
    )
    blocks.append(Block(txs=[setup_tx]))

    contract_address = compute_create_address(address=sender_addr, nonce=0)

    op_tx = Transaction(
        to=contract_address,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_blockhash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
):
    """Test running a block with as many blockhash accessing oldest allowed block as possible."""
    # Create 256 dummy blocks to fill the blockhash window.
    blocks = [Block()] * 256

    # Always ask for the oldest allowed BLOCKHASH block.
    execution_code = Op.PUSH1(1) + While(
        body=Op.POP(Op.BLOCKHASH(Op.DUP1)),
    )
    execution_code_address = pre.deploy_contract(code=execution_code)
    op_tx = Transaction(
        to=execution_code_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_selfbalance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test running a block with as many SELFBALANCE opcodes as possible."""
    max_stack_height = fork.max_stack_height()

    code_sequence = Op.SELFBALANCE * max_stack_height
    target_address = pre.deploy_contract(code=code_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_address, 0, 0, 0, 0))

    code = code_loop_precompile_call(calldata, attack_block, fork)
    assert len(code) <= fork.max_code_size()

    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "copied_size",
    [
        pytest.param(512, id="512"),
        pytest.param(1024, id="1KiB"),
        pytest.param(5 * 1024, id="5KiB"),
    ],
)
def test_worst_extcodecopy_warm(
    state_test: StateTestFiller,
    pre: Alloc,
    copied_size: int,
    gas_benchmark_value: int,
):
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

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value_bearing", [True, False])
def test_worst_selfdestruct_existing(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    pre: Alloc,
    value_bearing: bool,
    env: Environment,
    gas_benchmark_value: int,
):
    """Test running a block with as many SELFDESTRUCTs as possible for existing contracts."""
    attack_gas_limit = gas_benchmark_value
    fee_recipient = pre.fund_eoa(amount=1)

    # Template code that will be used to deploy a large number of contracts.
    selfdestructable_contract_addr = pre.deploy_contract(code=Op.SELFDESTRUCT(Op.COINBASE))
    initcode = Op.EXTCODECOPY(
        address=selfdestructable_contract_addr,
        dest_offset=0,
        offset=0,
        size=Op.EXTCODESIZE(selfdestructable_contract_addr),
    ) + Op.RETURN(0, Op.EXTCODESIZE(selfdestructable_contract_addr))
    initcode_address = pre.deploy_contract(code=initcode)

    # Calculate the number of contracts that can be deployed with the available gas.
    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    loop_cost = (
        gas_costs.G_KECCAK_256  # KECCAK static cost
        + math.ceil(85 / 32) * gas_costs.G_KECCAK_256_WORD  # KECCAK dynamic cost for CREATE2
        + gas_costs.G_VERY_LOW * 3  # ~MSTOREs+ADDs
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # CALL to self-destructing contract
        + gas_costs.G_SELF_DESTRUCT
        + 63  # ~Gluing opcodes
    )
    final_storage_gas = (
        gas_costs.G_STORAGE_RESET + gas_costs.G_COLD_SLOAD + (gas_costs.G_VERY_LOW * 2)
    )
    memory_expansion_cost = fork().memory_expansion_gas_calculator()(new_bytes=96)
    base_costs = (
        intrinsic_gas_cost_calc()
        + (gas_costs.G_VERY_LOW * 12)  # 8 PUSHs + 4 MSTOREs
        + final_storage_gas
        + memory_expansion_cost
    )
    num_contracts = (attack_gas_limit - base_costs) // loop_cost
    expected_benchmark_gas_used = num_contracts * loop_cost + base_costs

    # Create a factory that deployes a new SELFDESTRUCT contract instance pre-funded depending on
    # the value_bearing parameter. We use CREATE2 so the caller contract can easily reproduce
    # the addresses in a loop for CALLs.
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

    required_balance = num_contracts if value_bearing else 0  # 1 wei per contract
    factory_address = pre.deploy_contract(code=factory_code, balance=required_balance)

    factory_caller_code = Op.CALLDATALOAD(0) + While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
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
            # Only loop if we have enough gas to cover another iteration plus the
            # final storage gas.
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

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=[contracts_deployment_tx]),
            Block(txs=[opcode_tx], fee_recipient=fee_recipient),
        ],
        exclude_full_post_state_in_output=True,
        expected_benchmark_gas_used=expected_benchmark_gas_used,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value_bearing", [True, False])
def test_worst_selfdestruct_created(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
):
    """
    Test running a block with as many SELFDESTRUCTs as possible for deployed contracts in
    the same transaction.
    """
    fee_recipient = pre.fund_eoa(amount=1)
    env.fee_recipient = fee_recipient

    # SELFDESTRUCT(COINBASE) contract deployment
    initcode = (
        Op.MSTORE8(0, Op.COINBASE.int()) + Op.MSTORE8(1, Op.SELFDESTRUCT.int()) + Op.RETURN(0, 2)
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

    prefix_cost = gas_costs.G_VERY_LOW * 3 + gas_costs.G_BASE + memory_expansion_calc(new_bytes=32)
    suffix_cost = gas_costs.G_COLD_SLOAD + gas_costs.G_STORAGE_RESET + (gas_costs.G_VERY_LOW * 2)

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

    post = {code_addr: Account(storage={0: 42})}  # Check for successful execution.
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=code_tx,
        expected_benchmark_gas_used=iterations * loop_cost + base_costs,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value_bearing", [True, False])
def test_worst_selfdestruct_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
    fork: Fork,
    env: Environment,
    gas_benchmark_value: int,
):
    """Test running a block with as many SELFDESTRUCTs as possible executed in initcode."""
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

    prefix_cost = gas_costs.G_VERY_LOW * 3 + gas_costs.G_BASE + memory_expansion_calc(new_bytes=32)
    suffix_cost = gas_costs.G_COLD_SLOAD + gas_costs.G_STORAGE_RESET + (gas_costs.G_VERY_LOW * 2)

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

    post = {code_addr: Account(storage={0: 42})}  # Check for successful execution.
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=code_tx,
        expected_benchmark_gas_used=iterations * loop_cost + base_costs,
    )
