"""
Benchmark operations that force the inclusion of max size bytecodes.
This scenario is relevant in forks that have unchunkified bytecode.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Create2PreimageLayout,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    TestPhaseManager,
    While,
)

from tests.benchmark.compute.helpers import CustomSizedContractFactory


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
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    gas_benchmark_value: int,
) -> None:
    """Benchmark scenario of accessing max-code size bytecode."""
    # The attack gas limit represents the transaction gas limit cap or
    # the block gas limit. If eip-7825 is applied, the test will create
    # multiple transactions for contract deployment. It should account
    # for the 200 gas per byte cost and the quadratic memory-expansion
    # costs, which must be paid each time memory is initialized.
    attack_gas_limit = gas_benchmark_value

    # Create the max-sized fork-dependent contract factory.
    custom_sized_contract_factory = CustomSizedContractFactory(
        pre=pre, fork=fork
    )
    factory_address = custom_sized_contract_factory.address()
    initcode = custom_sized_contract_factory.initcode

    # Prepare the attack iterating bytecode.
    # Setup is just placing the CREATE2 Preimage in memory.
    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(0),
        init_code_hash=initcode.keccak256(),
    )
    setup_code: Bytecode = create2_preimage

    if opcode == Op.EXTCODECOPY:
        copy_size = 1000
        attack_call = Op.EXTCODECOPY(
            address=create2_preimage.address_op(),
            dest_offset=96,
            size=copy_size,
            # Gas accounting
            data_size=copy_size,
            address_warm=False,
        )
        # Also, expand memory during setup so the loop cost is constant.
        setup_code += Op.MSTORE8(
            96 + copy_size - 1,
            0,
            # Gas accounting
            old_memory_size=96,
            new_memory_size=96 + copy_size,
        )
    else:
        # For the rest of the opcodes, we can use the same generic attack call
        # since all only minimally need the `address` of the target.
        attack_call = Op.POP(
            opcode(
                address=create2_preimage.address_op(),
                # Gas accounting
                address_warm=False,
            )
        )

    loop_code = While(
        body=attack_call + create2_preimage.increment_salt_op(),
    )

    attack_code = IteratingBytecode(
        setup=setup_code,
        iterating=loop_code,
        # Since the target contract is guaranteed to have a STOP as the first
        # instruction, we can use a STOP as the iterating subcall code.
        iterating_subcall=Op.STOP,
    )

    # Calldata generator for each transaction of the iterating bytecode.
    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        del iteration_count
        # We only pass the start iteration index as calldata for this bytecode
        return Hash(start_iteration)

    attack_address = pre.deploy_contract(code=attack_code)

    # Calculate the number of contracts to be targeted.
    num_contracts = sum(
        attack_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=attack_gas_limit,
            calldata=calldata,
        )
    )

    # Deploy num_contracts via multiple txs (each capped by tx gas limit).
    with TestPhaseManager.setup():
        setup_sender = pre.fund_eoa()
        contracts_deployment_txs = list(
            custom_sized_contract_factory.transactions_by_total_contract_count(
                fork=fork,
                sender=setup_sender,
                contract_count=num_contracts,
            )
        )

    with TestPhaseManager.execution():
        attack_sender = pre.fund_eoa()
        attack_txs = list(
            attack_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=attack_gas_limit,
                sender=attack_sender,
                to=attack_address,
                calldata=calldata,
            )
        )
        total_gas_cost = sum(tx.gas_cost for tx in attack_txs)

    post = {}
    for i in range(num_contracts):
        deployed_contract_address = (
            custom_sized_contract_factory.created_contract_address(salt=i)
        )
        post[deployed_contract_address] = Account(nonce=1)

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=contracts_deployment_txs),
            Block(txs=attack_txs),
        ],
        expected_benchmark_gas_used=total_gas_cost,
    )
