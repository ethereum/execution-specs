"""
abstract: Tests zkEVMs worst-case stateful opcodes.
    Tests zkEVMs worst-case stateful opcodes.

Tests running worst-case stateful opcodes for zkEVMs.
"""

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
    Transaction,
    While,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"

MAX_CODE_SIZE = 24 * 1024


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
@pytest.mark.slow()
def test_worst_address_state_cold(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_accounts: bool,
):
    """Test running a block with as many stateful opcodes accessing cold accounts."""
    env = Environment(gas_limit=100_000_000_000)
    attack_gas_limit = Environment().gas_limit

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
        genesis_environment=env,
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
@pytest.mark.slow()
def test_worst_address_state_warm(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_target: bool,
):
    """Test running a block with as many stateful opcodes doing warm access for an account."""
    env = Environment(gas_limit=100_000_000_000)
    attack_gas_limit = Environment().gas_limit

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
    max_iters_loop = (MAX_CODE_SIZE - len(prep) - len(jumpdest) - len(jump_back)) // len(
        iter_block
    )
    op_code = prep + jumpdest + sum([iter_block] * max_iters_loop) + jump_back
    if len(op_code) > MAX_CODE_SIZE:
        # Must never happen, but keep it as a sanity check.
        raise ValueError(f"Code size {len(op_code)} exceeds maximum code size {MAX_CODE_SIZE}")
    op_address = pre.deploy_contract(code=op_code)
    op_tx = Transaction(
        to=op_address,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[Block(txs=[op_tx])],
    )


class StorageAction:
    """Enum for storage actions."""

    READ = 1
    WRITE_SAME_VALUE = 2
    WRITE_NEW_VALUE = 3


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "storage_action",
    [
        pytest.param(StorageAction.READ, id="SSLOAD"),
        pytest.param(StorageAction.WRITE_SAME_VALUE, id="SSTORE same value"),
        pytest.param(StorageAction.WRITE_NEW_VALUE, id="SSTORE new value"),
    ],
)
@pytest.mark.parametrize(
    "absent_slots",
    [
        True,
        False,
    ],
)
@pytest.mark.slow()
def test_worst_storage_access_cold(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_action: StorageAction,
    absent_slots: bool,
):
    """Test running a block with as many cold storage slot accesses as possible."""
    env = Environment(gas_limit=100_000_000_000)
    gas_costs = fork.gas_costs()
    attack_gas_limit = Environment().gas_limit

    cost = gas_costs.G_COLD_SLOAD  # All accesses are always cold
    if storage_action == StorageAction.WRITE_NEW_VALUE:
        if not absent_slots:
            cost += gas_costs.G_STORAGE_RESET
        else:
            cost += gas_costs.G_STORAGE_SET
    elif storage_action == StorageAction.WRITE_SAME_VALUE:
        if absent_slots:
            cost += gas_costs.G_STORAGE_SET
        else:
            cost += gas_costs.G_WARM_SLOAD
    elif storage_action == StorageAction.READ:
        cost += gas_costs.G_WARM_SLOAD

    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    num_target_slots = (attack_gas_limit - intrinsic_gas_cost_calc()) // cost

    blocks = []

    # Contract code
    execution_code_body = Bytecode()
    if storage_action == StorageAction.WRITE_SAME_VALUE:
        # All the storage slots in the contract are initialized to their index.
        # That is, storage slot `i` is initialized to `i`.
        execution_code_body = Op.SSTORE(Op.DUP1, Op.DUP1)
    elif storage_action == StorageAction.WRITE_NEW_VALUE:
        # The new value 2^256-1 is guaranteed to be different from the initial value.
        execution_code_body = Op.SSTORE(Op.DUP2, Op.NOT(0))
    elif storage_action == StorageAction.READ:
        execution_code_body = Op.POP(Op.SLOAD(Op.DUP1))

    execution_code = Op.PUSH4(num_target_slots) + While(
        body=execution_code_body,
        condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
    )
    execution_code_address = pre.deploy_contract(code=execution_code)

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
    blocks.append(Block(txs=[setup_tx]))

    contract_address = compute_create_address(address=sender_addr, nonce=0)

    op_tx = Transaction(
        to=contract_address,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=blocks,
        exclude_full_post_state_in_output=True,
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
@pytest.mark.slow()
def test_worst_storage_access_warm(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    storage_action: StorageAction,
):
    """Test running a block with as many warm storage slot accesses as possible."""
    env = Environment(gas_limit=100_000_000_000)
    attack_gas_limit = Environment().gas_limit

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
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.slow()
def test_worst_blockhash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a block with as many blockhash accessing oldest allowed block as possible."""
    env = Environment()

    # Create 256 dummy blocks to fill the blockhash window.
    blocks = [Block()] * 256

    # Always ask for the oldest allowed BLOCKHASH block.
    execution_code = Op.PUSH1(1) + While(
        body=Op.POP(Op.BLOCKHASH(Op.DUP1)),
    )
    execution_code_address = pre.deploy_contract(code=execution_code)
    op_tx = Transaction(
        to=execution_code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.slow()
def test_worst_selfbalance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a block with as many SELFBALANCE opcodes as possible."""
    env = Environment()

    execution_code = While(
        body=Op.POP(Op.SELFBALANCE),
    )
    execution_code_address = pre.deploy_contract(code=execution_code)
    op_tx = Transaction(
        to=execution_code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[op_tx])],
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
@pytest.mark.slow()
def test_worst_extcodecopy_warm(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    copied_size: int,
):
    """Test running a block with as many wamr EXTCODECOPY work as possible."""
    env = Environment()

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
    op_tx = Transaction(
        to=execution_code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[op_tx])],
    )
