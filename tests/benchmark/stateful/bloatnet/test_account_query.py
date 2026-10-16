"""Benchmark operations that query the state of a target account."""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    TestPhaseManager,
    Transaction,
    While,
)
from execution_testing.forks import Amsterdam, Osaka

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)
from tests.benchmark.helper.enums import CacheStrategy
from tests.benchmark.helper.transactions import (
    build_cache_strategy_blocks,
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


def account_access_params() -> list:
    """Generate (opcode, value_sent, account_mode, overhead_baseline)."""
    target_opcodes = [
        Op.BALANCE,
        # CALL*
        Op.CALL,
        Op.CALLCODE,
        Op.STATICCALL,
        Op.DELEGATECALL,
        # EXTCODE*
        Op.EXTCODECOPY,
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
    ]
    value_bearing_opcodes = {Op.CALL, Op.CALLCODE}
    params = []
    for mode in AccountMode:
        for op in target_opcodes:
            values = (0, 1) if op in value_bearing_opcodes else (0,)
            for value_sent in values:
                params.append(pytest.param(op, value_sent, mode, False))
                if AccountCreator(mode).derives_address_via_create2:
                    params.append(pytest.param(op, value_sent, mode, True))
    return params


@pytest.mark.repricing
@pytest.mark.parametrize("cache_strategy", [CacheStrategy.NO_CACHE])
@pytest.mark.parametrize(
    "opcode,value_sent,account_mode,overhead_baseline", account_access_params()
)
@pytest.mark.parametrize(
    "code_size", [Osaka.max_code_size(), Amsterdam.max_code_size()]
)
def test_account_access(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    value_sent: int,
    gas_benchmark_value: int,
    fixed_opcode_count: int | None,
    account_mode: AccountMode,
    overhead_baseline: bool,
    cache_strategy: CacheStrategy,
    code_size: int,
    verified_accounts: dict,
) -> None:
    """Benchmark account access with caching strategies."""
    account_creator = AccountCreator(account_mode, code_size=code_size)
    address_source = account_creator.address_source(Op.CALLDATALOAD(0))
    increment_op = address_source.next_op()

    cache_op = (
        Op.POP(
            Op.BALANCE(
                address=address_source.address_op(),
                # Gas accounting
                address_warm=False,
            )
        )
        if cache_strategy == CacheStrategy.CACHE_TX
        else Bytecode()
    )

    access_warm = cache_strategy == CacheStrategy.CACHE_TX

    setup_code = address_source.setup

    if opcode == Op.EXTCODECOPY:
        copy_size = 1024
        copy_dest = address_source.memory_size
        attack_call = opcode(
            address=address_source.address_op(),
            dest_offset=copy_dest,
            size=copy_size,
            # Gas accounting
            data_size=copy_size,
            address_warm=access_warm,
        )
        # Expand memory during setup so the loop cost is constant.
        setup_code += Op.MSTORE8(
            copy_dest + copy_size - 1,
            0,
            # Gas accounting
            old_memory_size=address_source.memory_size,
            new_memory_size=copy_dest + copy_size,
        )
    elif opcode in (Op.CALL, Op.CALLCODE):
        attack_call = Op.POP(
            opcode(
                address=address_source.address_op(),
                value=value_sent,
                # Gas accounting
                address_warm=access_warm,
                value_transfer=value_sent > 0,
                account_new=(
                    opcode == Op.CALL
                    and value_sent > 0
                    and account_mode == AccountMode.NON_EXISTING_ACCOUNT
                ),
            )
        )
    else:
        # BALANCE, STATICCALL, DELEGATECALL, EXTCODESIZE, EXTCODEHASH
        attack_call = Op.POP(
            opcode(
                address=address_source.address_op(),
                # Gas accounting
                address_warm=access_warm,
            )
        )

    setup_code += Op.ADD(1, Op.CALLDATALOAD(32)) + Op.CALLDATALOAD(0)

    loop_code = While(
        body=cache_op + attack_call + increment_op,
        condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
    )

    call_operations = (Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL)
    executes_contract_code = (
        opcode in call_operations and account_creator.has_execution_code
    )
    iterating_subcall: Bytecode = (
        account_creator.execution_code if executes_contract_code else Op.STOP
    )

    attack_code = IteratingBytecode(
        setup=setup_code,
        iterating=loop_code,
        iterating_subcall=iterating_subcall,
    )

    # Calldata generator for each transaction of the iterating bytecode.
    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        index_end = start_iteration + iteration_count - 1
        return Hash(start_iteration) + Hash(index_end)

    run_code = attack_code
    target_opcode = opcode

    if overhead_baseline:
        keccak_op = Op.POP(address_source.address_op())
        if cache_strategy == CacheStrategy.CACHE_TX:
            keccak_op = keccak_op * 2

        run_code = IteratingBytecode(
            setup=address_source.setup
            + Op.ADD(1, Op.CALLDATALOAD(32))
            + Op.CALLDATALOAD(0),
            iterating=While(
                body=keccak_op + increment_op,
                condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
            ),
        )
        target_opcode = Op.SHA3

    total_iterations = None
    if fixed_opcode_count is not None:
        total_iterations = int(fixed_opcode_count * 1000)
    elif overhead_baseline:
        total_iterations = sum(
            attack_code.tx_iterations_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                calldata=calldata,
            )
        )

    attack_address = pre.deploy_contract(code=run_code, balance=10**21)

    post: dict = {}
    cache_txs = []

    with TestPhaseManager.execution():
        attack_sender = pre.fund_eoa()
        if total_iterations is not None:
            attack_txs = list(
                run_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=total_iterations,
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                )
            )
        else:
            attack_txs = list(
                run_code.transactions_by_gas_limit(
                    fork=fork,
                    gas_limit=gas_benchmark_value,
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                )
            )

    if not overhead_baseline and attack_txs:
        count = 1 + max(
            int.from_bytes(bytes(tx.data)[32:64], "big") for tx in attack_txs
        )
        account_creator.register_targets(
            pre,
            count,
            verified_accounts=verified_accounts,
            label=account_mode.name,
        )

    if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
        with TestPhaseManager.setup():
            cache_sender = pre.fund_eoa()
            for tx in attack_txs:
                cache_txs.append(
                    Transaction(
                        gas_limit=tx.gas_limit,
                        data=tx.data,
                        to=attack_address,
                        sender=cache_sender,
                    )
                )

    blocks = build_cache_strategy_blocks(cache_strategy, attack_txs, cache_txs)

    benchmark_test(
        pre=pre,
        post=post,
        blocks=blocks,
        target_opcode=target_opcode,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
    )
