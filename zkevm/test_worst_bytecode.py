"""
abstract: Tests for zkEVMs
    Tests for zkEVMs.

Tests for zkEVMs worst-cases scenarios.
"""

import math

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
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
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"

XOR_TABLE_SIZE = 256
XOR_TABLE = [Hash(i).sha256() for i in range(XOR_TABLE_SIZE)]


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
        Op.EXTCODECOPY,
    ],
)
@pytest.mark.slow()
@pytest.mark.valid_from("Cancun")
def test_worst_bytecode_single_opcode(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
):
    """
    Test a block execution where a single opcode execution maxes out the gas limit,
    and the opcodes access a huge amount of contract code.

    We first use a single block to deploy a factory contract that will be used to deploy
    a large number of contracts.

    This is done to avoid having a big pre-allocation size for the test.

    The test is performed in the last block of the test, and the entire block gas limit is
    consumed by repeated opcode executions.
    """
    # The attack gas limit is the gas limit which the target tx will use
    # The test will scale the block gas limit to setup the contracts accordingly to be
    # able to pay for the contract deposit. This has to take into account the 200 gas per byte,
    # but also the quadratic memory expansion costs which have to be paid each time the
    # memory is being setup
    attack_gas_limit = Environment().gas_limit
    max_contract_size = fork.max_code_size()

    gas_costs = fork.gas_costs()

    # Calculate the absolute minimum gas costs to deploy the contract
    # This does not take into account setting up the actual memory (using KECCAK256 and XOR)
    # so the actual costs of deploying the contract is higher
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    memory_gas_minimum = memory_expansion_gas_calculator(new_bytes=len(bytes(max_contract_size)))
    code_deposit_gas_minimum = (
        fork.gas_costs().G_CODE_DEPOSIT_BYTE * max_contract_size + memory_gas_minimum
    )

    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # Calculate the loop cost of the attacker to query one address
    loop_cost = (
        gas_costs.G_KECCAK_256  # KECCAK static cost
        + math.ceil(85 / 32) * gas_costs.G_KECCAK_256_WORD  # KECCAK dynamic cost for CREATE2
        + gas_costs.G_VERY_LOW * 3  # ~MSTOREs+ADDs
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Opcode cost
        + 30  # ~Gluing opcodes
    )
    # Calculate the number of contracts to be targeted
    num_contracts = (
        # Base available gas = GAS_LIMIT - intrinsic - (out of loop MSTOREs)
        attack_gas_limit - intrinsic_gas_cost_calc() - gas_costs.G_VERY_LOW * 4
    ) // loop_cost

    # Set the block gas limit to a relative high value to ensure the code deposit tx
    # fits in the block (there is enough gas available in the block to execute this)
    env = Environment(gas_limit=code_deposit_gas_minimum * 2 * num_contracts)

    # The initcode will take its address as a starting point to the input to the keccak
    # hash function.
    # It will reuse the output of the hash function in a loop to create a large amount of
    # seemingly random code, until it reaches the maximum contract size.
    initcode = (
        Op.MSTORE(0, Op.ADDRESS)
        + While(
            body=(
                Op.SHA3(Op.SUB(Op.MSIZE, 32), 32)
                # Use a xor table to avoid having to call the "expensive" sha3 opcode as much
                + sum(
                    (Op.PUSH32[xor_value] + Op.XOR + Op.DUP1 + Op.MSIZE + Op.MSTORE)
                    for xor_value in XOR_TABLE
                )
                + Op.POP
            ),
            condition=Op.LT(Op.MSIZE, max_contract_size),
        )
        # Despite the whole contract has random bytecode, we make the first opcode be a STOP
        # so CALL-like attacks return as soon as possible, while EXTCODE(HASH|SIZE) work as
        # intended.
        + Op.MSTORE8(0, 0x00)
        + Op.RETURN(0, max_contract_size)
    )
    initcode_address = pre.deploy_contract(code=initcode)

    # The factory contract will simply use the initcode that is already deployed,
    # and create a new contract and return its address if successful.
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

    # The factory caller will call the factory contract N times, creating N new contracts.
    # Calldata should contain the N value.
    factory_caller_code = Op.CALLDATALOAD(0) + While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO,
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
        attack_call = Op.EXTCODECOPY(address=Op.SHA3(32 - 20 - 1, 85), dest_offset=85, size=1000)
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
        # TODO: A workaround could be to split the opcode code into multiple contracts
        # and call them in sequence.
        raise ValueError(
            f"Code size {len(attack_code)} exceeds maximum code size {max_contract_size}"
        )
    opcode_address = pre.deploy_contract(code=attack_code)
    opcode_tx = Transaction(
        to=opcode_address,
        gas_limit=attack_gas_limit,
        gas_price=10**9,
        sender=pre.fund_eoa(),
    )

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
@pytest.mark.parametrize(
    "pattern",
    [
        Op.STOP,
        Op.JUMPDEST,
        Op.PUSH1[bytes(Op.JUMPDEST)],
        Op.PUSH2[bytes(Op.JUMPDEST + Op.JUMPDEST)],
        Op.PUSH1[bytes(Op.JUMPDEST)] + Op.JUMPDEST,
        Op.PUSH2[bytes(Op.JUMPDEST + Op.JUMPDEST)] + Op.JUMPDEST,
    ],
    ids=lambda x: x.hex(),
)
def test_worst_initcode_jumpdest_analysis(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    pattern: Bytecode,
):
    """
    Test the jumpdest analysis performance of the initcode.

    This benchmark places a very long initcode in the memory and then invoke CREATE instructions
    with this initcode up to the block gas limit. The initcode itself has minimal execution time
    but forces the EVM to perform the full jumpdest analysis on the parametrized byte pattern.
    The initicode is modified by mixing-in the returned create address between CREATE invocations
    to prevent caching.
    """
    max_code_size = fork.max_code_size()
    initcode_size = fork.max_initcode_size()

    # Expand the initcode pattern to the transaction data so it can be used in CALLDATACOPY
    # in the main contract. TODO: tune the tx_data_len param.
    tx_data_len = 1024
    tx_data = pattern * (tx_data_len // len(pattern))
    tx_data += (tx_data_len - len(tx_data)) * bytes(Op.JUMPDEST)
    assert len(tx_data) == tx_data_len
    assert initcode_size % len(tx_data) == 0

    # Prepare the initcode in memory.
    code_prepare_initcode = sum(
        (
            Op.CALLDATACOPY(dest_offset=i * len(tx_data), offset=0, size=Op.CALLDATASIZE)
            for i in range(initcode_size // len(tx_data))
        ),
        Bytecode(),
    )

    # At the start of the initcode execution, jump to the last opcode.
    # This forces EVM to do the full jumpdest analysis.
    initcode_prefix = Op.JUMP(initcode_size - 1)
    code_prepare_initcode += Op.MSTORE(
        0, Op.PUSH32[bytes(initcode_prefix).ljust(32, bytes(Op.JUMPDEST))]
    )

    # Make sure the last opcode in the initcode is JUMPDEST.
    code_prepare_initcode += Op.MSTORE(initcode_size - 32, Op.PUSH32[bytes(Op.JUMPDEST) * 32])

    code_invoke_create = (
        Op.PUSH1[len(initcode_prefix)]
        + Op.MSTORE
        + Op.CREATE(value=Op.PUSH0, offset=Op.PUSH0, size=Op.MSIZE)
    )

    initial_random = Op.PUSH0
    code_prefix = code_prepare_initcode + initial_random
    code_loop_header = Op.JUMPDEST
    code_loop_footer = Op.JUMP(len(code_prefix))
    code_loop_body_len = (
        max_code_size - len(code_prefix) - len(code_loop_header) - len(code_loop_footer)
    )

    code_loop_body = (code_loop_body_len // len(code_invoke_create)) * bytes(code_invoke_create)
    code = code_prefix + code_loop_header + code_loop_body + code_loop_footer
    assert (max_code_size - len(code_invoke_create)) < len(code) <= max_code_size

    env = Environment()

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=tx_data,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )
