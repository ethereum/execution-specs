"""
Benchmark operations that force the inclusion of max size bytecodes.
This scenario is relevant in forks that have unchunkified bytecode.

Each target contract carries unique, address-seeded code, so clients
cannot deduplicate the reads by code hash. The distinct-target set is
bounded: every byte of unique code must exist in the fixture (in the
pre-allocation or, for on-chain deployment, in the EIP-7928 block access
list), so an unbounded set produces gigabyte fixtures. The bounded set
benchmarks the per-access mechanics (cold account access plus a full
unchunkified code read); sustained cache-busting reads over state larger
than client caches are covered by the bloatnet stateful benchmarks.
"""

from typing import List

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

from ..helpers import ContractDeploymentTransaction, CustomSizedContractFactory

DISTINCT_TARGET_CONTRACTS = 64
"""
Number of distinct max-size target contracts. Transactions cycle through
the set, so every access stays cold (EIP-2929 warmth resets per
transaction) while the fixture carries only this many unique code blobs
(~131KB each in the EIP-7928 block access list).
"""


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
@pytest.mark.execute(
    pytest.mark.skip(
        reason="deployment transactions exceed devnet block state gas"
    )
)
def test_unchunkified_bytecode(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    gas_benchmark_value: int,
    fixed_opcode_count: float | None,
) -> None:
    """Benchmark cold accesses to max-code-size, unique-code contracts."""
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

    # CALLDATA[0:32] = start salt, CALLDATA[32:64] = end salt.
    setup_code += Op.ADD(1, Op.CALLDATALOAD(32)) + Op.CALLDATALOAD(0)

    loop_code = While(
        body=attack_call + create2_preimage.increment_salt_op(),
        condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
    )

    attack_code = IteratingBytecode(
        setup=setup_code,
        iterating=loop_code,
        # Since the target contract is guaranteed to have a STOP as the first
        # instruction, we can use a STOP as the iterating subcall code.
        iterating_subcall=Op.STOP,
        cleanup=Op.STOP,
    )

    # Every transaction cycles through the same target set from salt zero;
    # warmth resets per transaction, so each access stays cold.
    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        del start_iteration
        return Hash(0) + Hash(iteration_count - 1)

    attack_address = pre.deploy_contract(code=attack_code)

    num_contracts = DISTINCT_TARGET_CONTRACTS

    # Deploy num_contracts via multiple txs (each capped by tx gas limit).
    post = {}
    with TestPhaseManager.setup():
        setup_sender = pre.fund_eoa()
        contracts_deployment_txs: List[ContractDeploymentTransaction] = []
        for contract_creating_tx in (
            custom_sized_contract_factory.transactions_by_total_contract_count(
                fork=fork,
                sender=setup_sender,
                contract_count=num_contracts,
            )
        ):
            contracts_deployment_txs.append(contract_creating_tx)
            if custom_sized_contract_factory.contract_size > 0:
                post[contract_creating_tx.deployed_contracts[-1]] = Account(
                    nonce=1
                )

    with TestPhaseManager.execution():
        attack_sender = pre.fund_eoa()
        if fixed_opcode_count is not None:
            # Fixed opcode count mode.
            attack_txs = list(
                attack_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=int(fixed_opcode_count * 1000),
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                    max_iterations_per_tx=num_contracts,
                )
            )
        else:
            attack_txs = list(
                attack_code.transactions_by_gas_limit(
                    fork=fork,
                    gas_limit=attack_gas_limit,
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                    max_iterations_per_tx=num_contracts,
                )
            )
        total_gas_cost = sum(tx.gas_cost for tx in attack_txs)

    if not attack_txs:
        pytest.skip("Benchmark gas value cannot cover a single target access.")

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=contracts_deployment_txs),
            Block(txs=attack_txs),
        ],
        target_opcode=opcode,
        expected_benchmark_gas_used=total_gas_cost,
    )
