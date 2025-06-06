"""
abstract: Tests zkEVMs worst-case stateful opcodes.
    Tests zkEVMs worst-case stateful opcodes.

Tests running worst-case stateful opcodes for zkEVMs.
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
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_target: bool,
):
    """Test running a block with as many stateful opcodes doing warm access for an account."""
    env = Environment(gas_limit=100_000_000_000)
    max_code_size = fork.max_code_size()
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
        genesis_environment=env,
        pre=pre,
        post=post,
        tx=tx,
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
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test running a block with as many SELFBALANCE opcodes as possible."""
    env = Environment()

    execution_code = While(
        body=Op.POP(Op.SELFBALANCE),
    )
    execution_code_address = pre.deploy_contract(code=execution_code)
    tx = Transaction(
        to=execution_code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        genesis_environment=env,
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
@pytest.mark.slow()
def test_worst_extcodecopy_warm(
    state_test: StateTestFiller,
    pre: Alloc,
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
    tx = Transaction(
        to=execution_code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        genesis_environment=env,
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
):
    """Test running a block with as many SELFDESTRUCTs as possible for existing contracts."""
    env = Environment(gas_limit=100_000_000_000)
    attack_gas_limit = Environment().gas_limit
    pre.fund_address(env.fee_recipient, 1)

    # Template code that will be used to deploy a large number of contracts.
    selfdestructable_contract_addr = pre.deploy_contract(code=Op.SELFDESTRUCT(Op.COINBASE))
    initcode = Op.EXTCODECOPY(
        address=selfdestructable_contract_addr,
        dest_offset=0,
        offset=0,
        size=Op.EXTCODESIZE(selfdestructable_contract_addr),
    ) + Op.RETURN(0, Op.EXTCODESIZE(selfdestructable_contract_addr))
    initcode_address = pre.deploy_contract(code=initcode)

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
    factory_address = pre.deploy_contract(code=factory_code, balance=10**18)

    factory_caller_code = Op.CALLDATALOAD(0) + While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
    )
    factory_caller_address = pre.deploy_contract(code=factory_caller_code)

    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    loop_cost = (
        gas_costs.G_KECCAK_256  # KECCAK static cost
        + math.ceil(85 / 32) * gas_costs.G_KECCAK_256_WORD  # KECCAK dynamic cost for CREATE2
        + gas_costs.G_VERY_LOW * 3  # ~MSTOREs+ADDs
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # CALL to self-destructing contract
        + gas_costs.G_SELF_DESTRUCT
        + 30  # ~Gluing opcodes
    )
    num_contracts = (
        # Base available gas = GAS_LIMIT - intrinsic - (out of loop MSTOREs)
        attack_gas_limit - intrinsic_gas_cost_calc() - gas_costs.G_VERY_LOW * 4
    ) // loop_cost

    contracts_deployment_tx = Transaction(
        to=factory_caller_address,
        gas_limit=env.gas_limit,
        gas_price=10**9,
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
            # Stop before we run out of gas for the whole tx execution.
            # The value was found by trial-error rounded to the next 1000 multiple.
            condition=Op.GT(Op.GAS, 12_000),
        )
        + Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
    )
    assert len(code) <= fork.max_code_size()

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, storage={0: 1})
    opcode_tx = Transaction(
        to=code_addr,
        gas_limit=attack_gas_limit,
        gas_price=10,
        sender=pre.fund_eoa(),
    )

    post = {
        code_addr: Account(storage={0: 42})  # Check for successful execution.
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
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[
            Block(txs=[contracts_deployment_tx]),
            Block(txs=[opcode_tx]),
        ],
        exclude_full_post_state_in_output=True,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value_bearing", [True, False])
def test_worst_selfdestruct_created(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
):
    """
    Test running a block with as many SELFDESTRUCTs as possible for deployed contracts in
    the same transaction.
    """
    env = Environment()
    pre.fund_address(env.fee_recipient, 1)

    # SELFDESTRUCT(COINBASE) contract deployment
    initcode = Op.MSTORE8(0, 0x41) + Op.MSTORE8(1, 0xFF) + Op.RETURN(0, 2)
    code = (
        Op.MSTORE(0, initcode.hex())
        + While(
            body=Op.POP(
                Op.CALL(
                    address=Op.CREATE(
                        value=1 if value_bearing else 0,
                        offset=32 - len(initcode),
                        size=len(initcode),
                    )
                )
            ),
            # Stop before we run out of gas for the whole tx execution.
            # The value was found by trial-error rounded to the next 1000 multiple.
            condition=Op.GT(Op.GAS, 10_000),
        )
        + Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
    )
    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, balance=100_000, storage={0: 1})
    code_tx = Transaction(
        to=code_addr,
        gas_limit=env.gas_limit,
        gas_price=10,
        sender=pre.fund_eoa(),
    )

    post = {code_addr: Account(storage={0: 42})}  # Check for successful execution.
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=code_tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value_bearing", [True, False])
def test_worst_selfdestruct_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    value_bearing: bool,
):
    """Test running a block with as many SELFDESTRUCTs as possible executed in initcode."""
    env = Environment()
    pre.fund_address(env.fee_recipient, 1)

    initcode = Op.SELFDESTRUCT(Op.COINBASE)
    code = (
        Op.MSTORE(0, initcode.hex())
        + While(
            body=Op.POP(
                Op.CREATE(
                    value=1 if value_bearing else 0,
                    offset=32 - len(initcode),
                    size=len(initcode),
                )
            ),
            # Stop before we run out of gas for the whole tx execution.
            # The value was found by trial-error rounded to the next 1000 multiple.
            condition=Op.GT(Op.GAS, 12_000),
        )
        + Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
    )
    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, balance=100_000, storage={0: 1})
    code_tx = Transaction(
        to=code_addr,
        gas_limit=env.gas_limit,
        gas_price=10,
        sender=pre.fund_eoa(),
    )

    post = {code_addr: Account(storage={0: 42})}  # Check for successful execution.
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=code_tx,
    )
