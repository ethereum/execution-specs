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

import math
from typing import Any

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    ExtCallGenerator,
    Fork,
    Hash,
    JumpLoopGenerator,
    Op,
    TestPhaseManager,
    Transaction,
    While,
)


@pytest.mark.repricing(contract_balance=1)
@pytest.mark.parametrize("contract_balance", [0, 1])
def test_selfbalance(
    benchmark_test: BenchmarkTestFiller,
    contract_balance: int,
) -> None:
    """Benchmark SELFBALANCE instruction."""
    benchmark_test(
        target_opcode=Op.SELFBALANCE,
        code_generator=ExtCallGenerator(
            attack_block=Op.SELFBALANCE,
            contract_balance=contract_balance,
        ),
    )


@pytest.mark.repricing
def test_codesize(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark CODESIZE instruction."""
    benchmark_test(
        target_opcode=Op.CODESIZE,
        code_generator=ExtCallGenerator(
            attack_block=Op.CODESIZE,
            code_padding_opcode=Op.INVALID,
        ),
    )


@pytest.mark.parametrize(
    "max_code_size_ratio",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(0.25, id="0.25x max code size"),
        pytest.param(0.50, id="0.50x max code size"),
        pytest.param(0.75, id="0.75x max code size"),
        pytest.param(1.00, id="max code size"),
    ],
)
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
def test_codecopy(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    max_code_size_ratio: float,
    fixed_src_dst: bool,
) -> None:
    """Benchmark CODECOPY instruction."""
    max_code_size = fork.max_code_size()

    size = int(max_code_size * max_code_size_ratio)

    setup = Op.PUSH32(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CODECOPY(src_dst, src_dst, Op.DUP1)  # DUP1 copies size.

    benchmark_test(
        target_opcode=Op.CODECOPY,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            code_padding_opcode=Op.STOP,
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("mem_size", [0, 32, 256, 1024])
@pytest.mark.parametrize("code_size", [0, 32, 256, 1024, 24576])
def test_codecopy_benchmark(
    benchmark_test: BenchmarkTestFiller,
    mem_size: int,
    code_size: int,
) -> None:
    """Benchmark CODECOPY with varying memory and code size config."""
    setup = Op.MSTORE8(mem_size, 0xFF) if mem_size > 0 else Bytecode()

    attack_block = Op.CODECOPY(Op.PUSH0, Op.PUSH0, code_size)

    benchmark_test(
        target_opcode=Op.CODECOPY,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            code_padding_opcode=Op.INVALID,
        ),
    )


@pytest.mark.repricing(copied_size=512)
@pytest.mark.parametrize(
    "copy_size",
    [0, 32, 256, 512, 1024],
)
def test_extcodecopy_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    copy_size: int,
) -> None:
    """Benchmark EXTCODECOPY instruction."""
    copied_contract_address = pre.deploy_contract(
        code=Op.JUMPDEST * copy_size,
    )

    benchmark_test(
        target_opcode=Op.EXTCODECOPY,
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH10(copy_size) + Op.PUSH20(copied_contract_address),
            attack_block=Op.EXTCODECOPY(Op.DUP4, 0, 0, Op.DUP2),
        ),
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
        target_addr = pre.empty_account()
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


@pytest.mark.repricing(absent_accounts=True)
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
def test_ext_account_query_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_accounts: bool,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    fixed_opcode_count: int,
) -> None:
    """
    Benchmark stateful opcodes accessing cold accounts.
    """
    if fixed_opcode_count:
        pytest.skip("Fixed opcode count is not supported for this test")

    attack_gas_limit = gas_benchmark_value

    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # For calculation robustness, the calculation below ignores "glue" opcodes
    # like  PUSH and POP. It should be considered a worst-case number of
    # accounts, and a few of them might not be targeted before the attacking
    # transaction runs out of gas.
    num_target_accounts = (
        attack_gas_limit - intrinsic_gas_cost_calc()
    ) // gas_costs.G_COLD_ACCOUNT_ACCESS

    blocks = []
    post = {}

    # Setup The target addresses are going to be constructed (in the case of
    # absent=False) and called as addr_offset + i, where i is the index of the
    # account. This is to avoid collisions with the addresses indirectly
    # created by the testing framework.
    addr_offset = int.from_bytes(pre.fund_eoa(amount=0))

    if not absent_accounts:
        account_creation_gas = (
            gas_costs.G_COLD_ACCOUNT_ACCESS
            + gas_costs.G_CALL_VALUE
            + gas_costs.G_NEW_ACCOUNT
        )
        # To avoid brittle/tight gas calculations of glue opcodes, we take
        # 90% of the maximum tx capacity. Even if this calculation fails
        # in the future, it will be caught by the post-state check.
        # Also, this is only for the setup phase, so being optimal is
        # not critical.
        max_creations_per_tx = int(
            (tx_gas_limit * 0.9) // account_creation_gas
        )
        factory_code = (
            Op.CALLDATALOAD(0)  # addr_start
            + Op.PUSH4(max_creations_per_tx)  # counter
            # Stack: [counter, addr_start]
            + While(
                body=Op.POP(
                    Op.CALL(
                        address=Op.ADD(addr_offset, Op.ADD(Op.DUP7, Op.DUP7)),
                        value=10,
                    )
                ),
                condition=Op.PUSH1(1)
                + Op.SWAP1
                + Op.SUB
                + Op.DUP1
                + Op.ISZERO
                + Op.ISZERO,
            )
        )
        factory_address = pre.deploy_contract(
            code=factory_code, balance=10**18
        )

        creation_txs = []
        with TestPhaseManager.setup():
            num_creation_txs = math.ceil(
                num_target_accounts / max_creations_per_tx
            )
            for i in range(num_creation_txs):
                addr_start = i * int(max_creations_per_tx)
                creation_txs.append(
                    Transaction(
                        to=factory_address,
                        data=Hash(addr_start),
                        gas_limit=tx_gas_limit,
                        sender=pre.fund_eoa(),
                    )
                )
        blocks.append(Block(txs=creation_txs))

        for i in range(num_target_accounts):
            addr = Address(i + addr_offset + 1)
            post[addr] = Account(balance=10)

    # Execution
    op_code = (
        Op.CALLDATALOAD(0)  # address_start
        + Op.CALLDATALOAD(32)  # num_to_query
        # Stack: [num_to_query, address_start]
        + While(
            body=Op.POP(opcode(Op.ADD(addr_offset, Op.ADD(Op.DUP2, Op.DUP2)))),
            condition=Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )
    )
    op_address = pre.deploy_contract(code=op_code)

    execution_txs = []
    with TestPhaseManager.execution():
        max_target_per_tx = (
            tx_gas_limit - intrinsic_gas_cost_calc()
        ) // gas_costs.G_COLD_ACCOUNT_ACCESS

        num_execution_txs = math.ceil(num_target_accounts / max_target_per_tx)
        gas_used = 0
        for i in range(num_execution_txs):
            address_start = i * int(max_target_per_tx)
            remaining = num_target_accounts - address_start
            num_to_query = min(int(max_target_per_tx), remaining)
            gas_limit = min(tx_gas_limit, attack_gas_limit - gas_used)
            calldata = Hash(address_start) + Hash(num_to_query)
            if gas_limit < intrinsic_gas_cost_calc(calldata=calldata):
                break
            execution_txs.append(
                Transaction(
                    to=op_address,
                    data=calldata,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                )
            )
            gas_used += gas_limit
    blocks.append(Block(txs=execution_txs))

    benchmark_test(
        target_opcode=opcode,
        post=post,
        blocks=blocks,
    )
