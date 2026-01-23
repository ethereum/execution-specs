"""
Benchmark operations that force the inclusion of max size bytecodes.
This scenario is relevant in forks that have unchunkified bytecode.
"""

import math

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Create2PreimageLayout,
    Fork,
    Hash,
    Op,
    TestPhaseManager,
    Transaction,
    While,
    compute_create2_address,
)

from tests.benchmark.compute.helpers import XOR_TABLE


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
        Op.EXTCODECOPY,
    ],
)
def test_unchunkified_bytecode(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """Benchmark scenario of accessing max-code size bytecode."""
    # The attack gas limit represents the transaction gas limit cap or
    # the block gas limit. If eip-7825 is applied, the test will create
    # multiple transactions for contract deployment. It should account
    # for the 200 gas per byte cost and the quadratic memory-expansion
    # costs, which must be paid each time memory is initialized.
    attack_gas_limit = gas_benchmark_value
    max_contract_size = fork.max_code_size()

    gas_costs = fork.gas_costs()

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
    # Calculate an upper bound of the number of contracts to be targeted
    num_contracts = (
        # Base available gas = GAS_LIMIT - intrinsic - (out of loop MSTOREs)
        attack_gas_limit - intrinsic_gas_cost_calc() - gas_costs.G_VERY_LOW * 4
    ) // loop_cost

    initcode, factory_address, factory_caller_address = (
        _deploy_max_contract_factory(pre, fork)
    )

    # Deploy num_contracts via multiple txs (each capped by tx gas limit).
    with TestPhaseManager.setup():
        # Rough estimate (rounded down) of contracts per tx based on dominant
        # cost factor only, and up to 90% of the block gas limit.
        # The goal is to involve the minimum amount of gas pricing to avoid
        # complexity and potential brittleness.
        num_contracts_per_tx = int(tx_gas_limit * 0.9) // (
            gas_costs.G_CODE_DEPOSIT_BYTE * max_contract_size
        )
        if num_contracts_per_tx == 0:
            pytest.skip("tx_gas_limit too low to deploy max-size contract")
        setup_txs = math.ceil(num_contracts / num_contracts_per_tx)

        contracts_deployment_txs = []
        for _ in range(setup_txs):
            contracts_deployment_txs.append(
                Transaction(
                    to=factory_caller_address,
                    gas_limit=tx_gas_limit,
                    data=Hash(num_contracts_per_tx),
                    sender=pre.fund_eoa(),
                )
            )

    post = {}
    for i in range(num_contracts):
        deployed_contract_address = compute_create2_address(
            address=factory_address,
            salt=i,
            initcode=initcode,
        )
        post[deployed_contract_address] = Account(nonce=1)

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(0),
        init_code_hash=initcode.keccak256(),
    )
    attack_call = Bytecode()
    if opcode == Op.EXTCODECOPY:
        attack_call = Op.EXTCODECOPY(
            address=create2_preimage.address_op(), dest_offset=96, size=1000
        )
    else:
        # For the rest of the opcodes, we can use the same generic attack call
        # since all only minimally need the `address` of the target.
        attack_call = Op.POP(opcode(address=create2_preimage.address_op()))
    attack_code = (
        create2_preimage
        # Main loop
        + While(
            body=attack_call + create2_preimage.increment_salt_op(),
        )
    )

    attack_address = pre.deploy_contract(code=attack_code)

    with TestPhaseManager.execution():
        full_txs = attack_gas_limit // tx_gas_limit
        remainder = attack_gas_limit % tx_gas_limit

        num_targeted_contracts_per_full_tx = (
            # Base available gas:
            # TX_GAS_LIMIT - intrinsic - (out of loop MSTOREs)
            tx_gas_limit - intrinsic_gas_cost_calc() - gas_costs.G_VERY_LOW * 4
        ) // loop_cost
        contract_start_index = 0
        opcode_txs = []
        for _ in range(full_txs):
            opcode_txs.append(
                Transaction(
                    to=attack_address,
                    gas_limit=tx_gas_limit,
                    data=Hash(contract_start_index),
                    sender=pre.fund_eoa(),
                )
            )
            contract_start_index += num_targeted_contracts_per_full_tx
        if remainder > intrinsic_gas_cost_calc(calldata=bytes(32)):
            opcode_txs.append(
                Transaction(
                    to=attack_address,
                    gas_limit=remainder,
                    data=Hash(contract_start_index),
                    sender=pre.fund_eoa(),
                )
            )

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=contracts_deployment_txs),
            Block(txs=opcode_txs),
        ],
        exclude_full_post_state_in_output=True,
    )


def _deploy_max_contract_factory(
    pre: Alloc,
    fork: Fork,
) -> tuple[Bytecode, Address, Address]:
    max_contract_size = fork.max_code_size()

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

    return initcode, factory_address, factory_caller_address
