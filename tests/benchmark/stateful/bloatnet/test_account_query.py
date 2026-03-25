"""
Benchmark operations that require querying the account state, either on the
current executing account or on a target account.

Supported Opcodes:
- SELFBALANCE
- CODESIZE
- CODECOPY
- EXTCODESIZE
- EXTCODEHASH
- EXTCODECOPY
- BALANCE
"""

from typing import Any, Dict, List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Create2PreimageLayout,
    Fork,
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    ParameterSet,
    TestPhaseManager,
    While,
)

from tests.benchmark.compute.helpers import (
    ContractDeploymentTransaction,
    CustomSizedContractFactory,
)


def generate_account_query_params() -> List[ParameterSet]:
    """
    Generate valid parameter combinations for test_account_query.

    Returns tuples of: (opcode, access_warm, mem_size, code_size, value_sent)
    """
    all_mem_sizes = [0, 32, 256, 1024]
    all_code_sizes = [0, 32, 256, 1024]
    all_access_warm = [True, False]
    all_value_sent = [0, 1]

    params = []

    # BALANCE, EXTCODESIZE, EXTCODEHASH:
    # only mem_size=0, code_size=0, value_sent=0
    for opcode in [Op.BALANCE, Op.EXTCODESIZE, Op.EXTCODEHASH]:
        for access_warm in all_access_warm:
            params.append(pytest.param(opcode, access_warm, 0, 0, 0))

    # EXTCODECOPY: all mem_size, all code_size, value_sent=0
    for access_warm in all_access_warm:
        for mem_size in all_mem_sizes:
            for code_size in all_code_sizes:
                params.append(
                    pytest.param(
                        Op.EXTCODECOPY, access_warm, mem_size, code_size, 0
                    )
                )
            # Add None (max_code_size) separately with custom ID
            params.append(
                pytest.param(
                    Op.EXTCODECOPY,
                    access_warm,
                    mem_size,
                    None,
                    0,
                    id=f"EXTCODECOPY-{access_warm}-{mem_size}-max_code_size-0",
                )
            )

    # CALL, CALLCODE: all mem_size, code_size=0, all value_sent
    for opcode in [Op.CALL, Op.CALLCODE]:
        for access_warm in all_access_warm:
            for mem_size in all_mem_sizes:
                for value_sent in all_value_sent:
                    params.append(
                        pytest.param(
                            opcode, access_warm, mem_size, 0, value_sent
                        )
                    )

    # STATICCALL, DELEGATECALL: all mem_size, code_size=0, value_sent=0
    for opcode in [Op.STATICCALL, Op.DELEGATECALL]:
        for access_warm in all_access_warm:
            for mem_size in all_mem_sizes:
                params.append(
                    pytest.param(opcode, access_warm, mem_size, 0, 0)
                )

    return params


@pytest.mark.parametrize(
    "opcode,access_warm,mem_size,code_size,value_sent",
    generate_account_query_params(),
)
def test_account_query(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    access_warm: bool,
    mem_size: int,
    code_size: int,
    value_sent: int,
    gas_benchmark_value: int,
    fixed_opcode_count: int | None,
) -> None:
    """Benchmark scenario of accessing max-code size bytecode."""
    attack_gas_limit = gas_benchmark_value

    # Create the max-sized fork-dependent contract factory.
    custom_sized_contract_factory = CustomSizedContractFactory(
        pre=pre, fork=fork, contract_size=code_size
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

    if mem_size > 96:
        setup_code += Op.MSTORE8(
            mem_size - 1,
            0,
            # Gas accounting
            old_memory_size=96,
            new_memory_size=mem_size,
        )

    if opcode == Op.EXTCODECOPY:
        attack_call = Op.EXTCODECOPY(
            address=create2_preimage.address_op(),
            dest_offset=0,
            size=mem_size,
            # Gas accounting
            data_size=mem_size,
            address_warm=access_warm,
        )
    elif opcode in (Op.CALL, Op.CALLCODE):
        # CALL and CALLCODE accept value parameter
        attack_call = Op.POP(
            opcode(
                address=create2_preimage.address_op(),
                value=value_sent,
                args_size=mem_size,
                # Gas accounting
                address_warm=access_warm,
                new_memory_size=max(mem_size, 96),
                value_transfer=value_sent > 0,
            )
        )
    elif opcode in (Op.STATICCALL, Op.DELEGATECALL):
        # STATICCALL and DELEGATECALL don't have value parameter
        attack_call = Op.POP(
            opcode(
                address=create2_preimage.address_op(),
                args_size=mem_size,
                # Gas accounting
                address_warm=access_warm,
                new_memory_size=max(mem_size, 96),
            )
        )
    else:
        # BALANCE, EXTCODESIZE, EXTCODEHASH
        attack_call = Op.POP(
            opcode(
                address=create2_preimage.address_op(),
                # Gas accounting
                address_warm=access_warm,
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

    # Access list generator for warm access tests.
    # When access_warm=True, include all contract addresses that will be
    # accessed in each transaction to warm them up via access list.
    # Note: This access list generation is very expensive due to the binary
    # search, which builds different access lists using the same elements
    # over and over. Caching the elements helps a bit.
    access_list_cache: Dict[int, AccessList] = {}

    def access_list_generator(
        iteration_count: int, start_iteration: int
    ) -> list[AccessList] | None:
        if not access_warm:
            return None
        return [
            access_list_cache.setdefault(
                i,
                AccessList(
                    address=custom_sized_contract_factory.created_contract_address(
                        salt=i
                    ),
                    storage_keys=[],
                ),
            )
            for i in range(start_iteration, start_iteration + iteration_count)
        ]

    attack_address = pre.deploy_contract(code=attack_code, balance=10**21)

    # Calculate the number of contracts to be targeted.
    if fixed_opcode_count is not None:
        # Fixed opcode count mode
        num_contracts = int(fixed_opcode_count * 1000)
    else:
        # Gas limit mode
        num_contracts = sum(
            attack_code.tx_iterations_by_gas_limit(
                fork=fork,
                gas_limit=attack_gas_limit,
                calldata=calldata,
                access_list=access_list_generator,
            )
        )

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
            attack_txs = list(
                attack_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=int(fixed_opcode_count * 1000),
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                    access_list=access_list_generator,
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
                    access_list=access_list_generator,
                )
            )
        total_gas_cost = sum(tx.gas_cost for tx in attack_txs)

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


@pytest.mark.repricing(
    empty_code=True,
    initial_balance=True,
    initial_storage=True,
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
    "empty_code",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_balance",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_storage",
    [
        True,
        False,
    ],
)
def test_ext_account_query_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
    empty_code: bool,
    initial_balance: bool,
    initial_storage: bool,
) -> None:
    """
    Test running a block with as many stateful opcodes doing warm access
    for an account.
    """
    # Setup
    post = {}

    # Case 1: Completely empty account (no balance, no storage, no code)
    if not initial_balance and not initial_storage and empty_code:
        target_addr = pre.nonexistent_account()
    # Case 2: EOA with optional balance and storage
    elif empty_code:
        eoa_kwargs: dict[str, Any] = {}
        if initial_balance:
            eoa_kwargs["amount"] = 100
        if initial_storage:
            eoa_kwargs["storage"] = {0: 0x1337}
        target_addr = pre.fund_eoa(**eoa_kwargs)
    # Case 3: Contract with optional balance and storage
    else:
        contract_kwargs: dict[str, Any] = {"code": Op.STOP + Op.JUMPDEST * 100}
        if initial_balance:
            contract_kwargs["balance"] = 100
        if initial_storage:
            contract_kwargs["storage"] = {0: 0x1337}
        target_addr = pre.deploy_contract(**contract_kwargs)
        post[target_addr] = Account(**contract_kwargs)

    benchmark_test(
        target_opcode=opcode,
        post=post,
        code_generator=JumpLoopGenerator(
            setup=Op.MSTORE(0, target_addr),
            attack_block=Op.POP(opcode(address=Op.MLOAD(0))),
        ),
    )
