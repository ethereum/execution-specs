"""
abstract: Tests for zkEVMs
    Tests for zkEVMs.

Tests for zkEVMs worst-cases scenarios.
"""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Hash,
    Transaction,
    While,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"

MAX_CONTRACT_SIZE = 24 * 1024  # TODO: This could be a fork property
BLOCK_GAS_LIMIT = 36_000_000  # TODO: Parametrize using the (yet to be implemented) block gas limit
# OPCODE_GAS_LIMIT = BLOCK_GAS_LIMIT  # TODO: Reduced in order to run the test in a reasonable time
OPCODE_GAS_LIMIT = 100_000

XOR_TABLE_SIZE = 256
XOR_TABLE = [Hash(i).sha256() for i in range(XOR_TABLE_SIZE)]


# TODO: Parametrize for EOF
@pytest.mark.zkevm
@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCODESIZE,
    ],
)
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
    env = Environment(gas_limit=BLOCK_GAS_LIMIT)

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
            condition=Op.LT(Op.MSIZE, MAX_CONTRACT_SIZE),
        )
        + Op.RETURN(0, MAX_CONTRACT_SIZE)
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
            Op.CREATE(
                value=0,
                offset=0,
                size=Op.MSIZE,
            ),
        )
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

    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_number_of_contract_calls = (OPCODE_GAS_LIMIT - intrinsic_gas_cost_calc()) // (
        gas_costs.G_VERY_LOW + gas_costs.G_BASE + gas_costs.G_COLD_ACCOUNT_ACCESS
    )
    total_contracts_to_deploy = max_number_of_contract_calls
    approximate_gas_per_deployment = 4_970_000  # Obtained from evm tracing
    contracts_deployed_per_tx = BLOCK_GAS_LIMIT // approximate_gas_per_deployment

    deploy_txs = []

    def generate_deploy_tx(contracts_to_deploy: int):
        return Transaction(
            to=factory_caller_address,
            gas_limit=BLOCK_GAS_LIMIT,
            gas_price=10**9,  # Bump required due to the amount of full blocks
            data=Hash(contracts_deployed_per_tx),
            sender=pre.fund_eoa(),
        )

    for _ in range(total_contracts_to_deploy // contracts_deployed_per_tx):
        deploy_txs.append(generate_deploy_tx(contracts_deployed_per_tx))

    if total_contracts_to_deploy % contracts_deployed_per_tx != 0:
        deploy_txs.append(
            generate_deploy_tx(total_contracts_to_deploy % contracts_deployed_per_tx)
        )

    post = {}
    deployed_contract_addresses = []
    for i in range(total_contracts_to_deploy):
        deployed_contract_address = compute_create_address(
            address=factory_address,
            nonce=i + 1,
        )
        post[deployed_contract_address] = Account(nonce=1)
        deployed_contract_addresses.append(deployed_contract_address)

    opcode_code = (
        sum(Op.POP(opcode(address=address)) for address in deployed_contract_addresses) + Op.STOP
    )
    if len(opcode_code) > MAX_CONTRACT_SIZE:
        # TODO: A workaround could be to split the opcode code into multiple contracts
        # and call them in sequence.
        raise ValueError(
            f"Code size {len(opcode_code)} exceeds maximum code size {MAX_CONTRACT_SIZE}"
        )
    opcode_address = pre.deploy_contract(code=opcode_code)
    opcode_tx = Transaction(
        to=opcode_address,
        gas_limit=OPCODE_GAS_LIMIT,
        gas_price=10**9,  # Bump required due to the amount of full blocks
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[
            *[Block(txs=[deploy_tx]) for deploy_tx in deploy_txs],
            Block(txs=[opcode_tx]),
        ],
    )
