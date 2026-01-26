"""
Benchmark operations that force the inclusion of max size bytecodes.
This scenario is relevant in forks that have unchunkified bytecode.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Create2PreimageLayout,
    Fork,
    Hash,
    Op,
    TestPhaseManager,
    Transaction,
    While,
)

from tests.benchmark.compute.helpers import (
    IteratingBytecode,
    MaxSizedContractFactory,
)


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

    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()

    # Create the max-sized fork-dependent contract factory.
    max_sized_contract_factory = MaxSizedContractFactory(pre=pre, fork=fork)
    factory_address = max_sized_contract_factory.address(fork=fork)
    initcode = max_sized_contract_factory.initcode

    # Prepare the attack iterating bytecode.
    # Setup is just placing the CREATE2 Preimage in memory.
    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(0),
        init_code_hash=initcode.keccak256(),
    )
    setup_code = create2_preimage

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

    attack_address = pre.deploy_contract(code=attack_code)

    # Calculate an upper bound of the number of contracts to be targeted
    num_contracts = (
        # Base available gas = GAS_LIMIT - intrinsic - (out of loop MSTOREs)
        attack_gas_limit
        - intrinsic_gas_cost_calc()
        - attack_code.setup.gas_cost(fork)
    ) // attack_code.iterating.gas_cost(fork)

    # Deploy num_contracts via multiple txs (each capped by tx gas limit).
    with TestPhaseManager.setup():
        setup_sender = pre.fund_eoa()
        contracts_deployment_txs = (
            max_sized_contract_factory.txs_with_gas_limit_cap(
                fork=fork,
                sender=setup_sender,
                index_start=0,
                index_end=num_contracts - 1,
                gas_limit_cap=fork.transaction_gas_limit_cap(),
            )
        )

    with TestPhaseManager.execution():
        attack_sender = pre.fund_eoa()
        full_txs = attack_gas_limit // tx_gas_limit
        remainder = attack_gas_limit % tx_gas_limit

        num_targeted_contracts_per_full_tx = (
            # Base available gas:
            # TX_GAS_LIMIT - intrinsic - (out of loop MSTOREs)
            tx_gas_limit
            - intrinsic_gas_cost_calc()
            - attack_code.setup.gas_cost(fork)
        ) // attack_code.iterating.gas_cost(fork)
        contract_start_index = 0
        opcode_txs = []
        for _ in range(full_txs):
            opcode_txs.append(
                Transaction(
                    to=attack_address,
                    gas_limit=tx_gas_limit,
                    data=Hash(contract_start_index),
                    sender=attack_sender,
                )
            )
            contract_start_index += num_targeted_contracts_per_full_tx
        if remainder > intrinsic_gas_cost_calc(calldata=bytes(32)):
            opcode_txs.append(
                Transaction(
                    to=attack_address,
                    gas_limit=remainder,
                    data=Hash(contract_start_index),
                    sender=attack_sender,
                )
            )

    post = {}
    for i in range(num_contracts):
        deployed_contract_address = (
            max_sized_contract_factory.created_contract_address(
                fork=fork, salt=i
            )
        )
        post[deployed_contract_address] = Account(nonce=1)

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=contracts_deployment_txs),
            Block(txs=opcode_txs),
        ],
        exclude_full_post_state_in_output=True,
    )
