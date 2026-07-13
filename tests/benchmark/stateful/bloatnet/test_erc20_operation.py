"""Benchmark storage operations through ERC20 calls on bloatnet contracts."""

import pytest
from execution_testing import (
    AccessList,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Op,
    TestPhaseManager,
    Transaction,
    While,
)

from tests.benchmark.stateful.helpers import (
    APPROVE_SELECTOR,
    BALANCEOF_SELECTOR,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# SLOAD BENCHMARK ARCHITECTURE:
#
#   [Pre-deployed ERC20 Contract] ──── Storage slots for balances
#           │
#           │  balanceOf(address) → SLOAD(keccak256(address || slot))
#           │
#   [Attack Contract] ──CALL──► ERC20.balanceOf(random_address)
#           │
#           └─► Loop(i=0 to N):
#                 1. Generate random address from counter
#                 2. CALL balanceOf(random_address) → forces cold SLOAD
#                 3. Most addresses have zero balance → empty storage slots
#
# WHY IT STRESSES CLIENTS:
#   - Each balanceOf() call forces a cold SLOAD on a likely-empty slot
#   - Storage slot = keccak256(address || balances_slot)
#   - Random addresses ensure maximum cache misses
#   - Tests client's sparse storage handling efficiency


@pytest.mark.stub_parametrize(
    "erc20_stub", "test_sload_empty_erc20_balanceof_"
)
def test_sload_erc20_generic(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    erc20_stub: str,
) -> None:
    """Benchmark SLOAD using ERC20 balanceOf on bloatnet."""
    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=erc20_stub,
    )
    threshold = 100000

    # MEM[0] = function selector
    # MEM[32] = starting address offset
    setup = Op.MSTORE(
        0,
        BALANCEOF_SELECTOR,
        # gas accounting
        old_memory_size=0,
        new_memory_size=32,
    ) + Op.MSTORE(
        32,
        Op.SLOAD(0),  # Address Offset
        # gas accounting
        old_memory_size=32,
        new_memory_size=64,
    )

    call_balance_of = Op.POP(
        Op.CALL(
            address=erc20_address,
            args_offset=32 - 4,
            args_size=32 + 4,
        )
    )

    loop = While(
        body=call_balance_of + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.GT(Op.GAS, threshold),
    )

    teardown = Op.SSTORE(0, Op.MLOAD(32))

    # Contract Deployment
    code = setup + loop + teardown
    attack_contract_address = pre.deploy_contract(code=code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Transaction Loops
    txs = []
    gas_remaining = gas_benchmark_value

    sender = pre.fund_eoa()

    while gas_remaining > intrinsic_gas:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas:
            break

        with TestPhaseManager.execution():
            txs.append(
                Transaction(
                    gas_limit=gas_available,
                    to=attack_contract_address,
                    sender=sender,
                )
            )

        gas_remaining -= gas_available

    blocks = [Block(txs=txs)]
    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )


# SSTORE BENCHMARK ARCHITECTURE:
#
#   [Pre-deployed ERC20 Contract] ──── Storage slots for allowances
#           │
#           │  approve(spender, amount)
#           │    → SSTORE(keccak256(spender || slot), amount)
#           │
#   [Attack Contract]
#       ──CALL──► ERC20.approve(counter_as_spender, counter_as_amount)
#           │
#           └─► Loop(i=0 to N):
#                 1. Use counter as both spender address and amount
#                 2. CALL approve(counter, counter) → forces cold SSTORE
#                 3. Writes to new allowance slots in sparse storage
#
# WHY IT STRESSES CLIENTS:
#   - Each approve() call forces an SSTORE to a new storage slot
#   - Storage slot = keccak256(
#       msg.sender || keccak256(spender || allowances_slot)
#     )
#   - Sequential counter ensures unique storage locations
#   - Tests client's ability to handle many storage writes
#   - Simulates real-world contract state accumulation over time


@pytest.mark.stub_parametrize("erc20_stub", "test_sstore_erc20_approve_")
def test_sstore_erc20_generic(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    erc20_stub: str,
) -> None:
    """Benchmark SSTORE using ERC20 approve."""
    sender = pre.fund_eoa()

    threshold = 100_000

    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=erc20_stub,
    )

    # MEM[0] = function selector
    # MEM[32] = starting address offset
    setup = Op.MSTORE(
        0,
        APPROVE_SELECTOR,
    ) + Op.MSTORE(
        32,
        Op.SLOAD(0),  # Address Offset
    )

    call_approve = Op.MSTORE(
        64,
        Op.ADD(1, Op.MLOAD(32)),
    ) + Op.POP(
        Op.CALL(
            address=erc20_address,
            args_offset=28,
            args_size=68,
        )
    )

    loop = While(
        body=call_approve + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.GT(Op.GAS, threshold),
    )

    teardown = Op.SSTORE(0, Op.MLOAD(32))

    # Contract Deployment
    code = setup + loop + teardown
    attack_contract_address = pre.deploy_contract(code=code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Transaction Loops
    gas_remaining = gas_benchmark_value

    # Collect tx params first, then build Transaction objects
    # so that nonces are allocated contiguously per block.
    tx_gas: list[int] = []
    while gas_remaining > intrinsic_gas:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas:
            break

        tx_gas.append(gas_available)

        gas_remaining -= gas_available

    txs = []
    with TestPhaseManager.execution():
        for gas_available in tx_gas:
            txs.append(
                Transaction(
                    gas_limit=gas_available,
                    to=attack_contract_address,
                    sender=sender,
                )
            )

    blocks = [Block(txs=txs)]

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )


@pytest.mark.stub_parametrize("erc20_stub", "test_mixed_sload_sstore_")
@pytest.mark.parametrize(
    "sload_percent,sstore_percent",
    [
        pytest.param(10, 90, id="10-90"),
        pytest.param(30, 70, id="30-70"),
        pytest.param(50, 50, id="50-50"),
        pytest.param(70, 30, id="70-30"),
        pytest.param(90, 10, id="90-10"),
    ],
)
def test_mixed_sload_sstore(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    erc20_stub: str,
    sload_percent: int,
    sstore_percent: int,
) -> None:
    """Benchmark mixed SLOAD/SSTORE ratios on bloatnet ERC20 contracts."""
    # The gas threshold is the minimum gas reserved to exit the
    # loops and execute cleanup (SSTORE to persist slot offset).
    # 150_000 is conservative: cold approve ~25K + cleanup ~20K.
    gas_threshold = 150_000
    slot_offset_key = 0  # storage slot for persistent offset

    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=erc20_stub,
    )

    # Contract Construction
    # MEM[0]   = function selector
    # MEM[32]  = address/slot offset (incremented each iteration)
    # MEM[64]  = spender/amount for approve (copied from MEM[32])
    # MEM[96]  = initial_gas snapshot
    # MEM[128] = gas_floor for SLOAD phase
    setup = (
        Op.MSTORE(
            0,
            BALANCEOF_SELECTOR,
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.MSTORE(
            32,
            Op.SLOAD(slot_offset_key),
            old_memory_size=32,
            new_memory_size=64,
        )
        + Op.MSTORE(
            96,
            Op.GAS,
            old_memory_size=64,
            new_memory_size=128,
        )
        # gas_floor = initial_gas * sstore_percent / 100
        # This is the gas level at which SLOADs stop and
        # SSTOREs begin, leaving sstore_percent of the
        # initial gas for the SSTORE phase.
        + Op.MSTORE(
            128,
            Op.DIV(Op.MUL(Op.MLOAD(96), sstore_percent), 100),
            old_memory_size=128,
            new_memory_size=160,
        )
    )

    # SLOAD loop — STATICCALL since balanceOf is a view function.
    # Continues while both: gas is above the sload/sstore
    # transition floor AND above the safety threshold.
    sload_loop = While(
        body=Op.POP(
            Op.STATICCALL(
                address=erc20_address,
                args_offset=28,
                args_size=36,
                ret_offset=0,
                ret_size=0,
                address_warm=True,
            )
        )
        + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.AND(
            Op.GT(Op.GAS, Op.MLOAD(128)),
            Op.GT(Op.GAS, gas_threshold),
        ),
    )

    transition = Op.MSTORE(0, APPROVE_SELECTOR)

    # SSTORE loop — runs until gas drops below safety threshold.
    sstore_loop = While(
        body=(
            Op.MSTORE(64, Op.MLOAD(32))
            + Op.POP(
                Op.CALL(
                    address=erc20_address,
                    value=0,
                    args_offset=28,
                    args_size=68,
                    ret_offset=0,
                    ret_size=0,
                    address_warm=True,
                )
            )
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
        ),
        condition=Op.GT(Op.GAS, gas_threshold),
    )

    # Persist the final slot offset so the next tx continues
    # from where this one left off.
    cleanup = Op.SSTORE(slot_offset_key, Op.MLOAD(32))

    # Contract Deployment
    code = setup + sload_loop + transition + sstore_loop + cleanup
    attack_contract_address = pre.deploy_contract(
        code=code,
        storage={slot_offset_key: 0},
    )

    # Transaction Construction — no iteration count math.
    # Each tx gets up to tx_gas_limit gas; the contract
    # self-regulates via the GAS opcode.
    access_list = [AccessList(address=erc20_address, storage_keys=[])]
    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
    )

    gas_remaining = gas_benchmark_value
    txs = []
    while gas_remaining >= intrinsic_gas_cost + gas_threshold:
        gas_limit = min(gas_remaining, tx_gas_limit)
        txs.append(
            Transaction(
                gas_limit=gas_limit,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )
        gas_remaining -= gas_limit

    assert txs, "Gas loop produced zero transactions"
    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )
