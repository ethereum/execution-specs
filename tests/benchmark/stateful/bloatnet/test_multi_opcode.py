"""
abstract: BloatNet bench cases extracted from https://hackmd.io/9icZeLN7R0Sk5mIjKlZAHQ.

   The idea of all these tests is to stress client implementations to find out
   where the limits of processing are focusing specifically on state-related
   operations.
"""

import pytest
from execution_testing import (
    AccessList,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Conditional,
    Create2PreimageLayout,
    Fork,
    Op,
    Transaction,
    While,
)

from tests.benchmark.stateful.helpers import (
    APPROVE_SELECTOR,
    BALANCEOF_SELECTOR,
    DECREMENT_COUNTER_CONDITION,
    build_benchmark_txs,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# BLOATNET ARCHITECTURE:
#
#   [Initcode Contract]        [Factory Contract]        [Deployed Contracts]
#     (varies by stub)           (varies by stub)          (N x each)
#           │                          │                        │
#           │  EXTCODECOPY             │   CREATE2(salt++)      │
#           └──────────────►           ├────────────────►  Contract_0
#                                      ├────────────────►  Contract_1
#                                      └────────────────►  Contract_N
#
#   [Attack Contract] ──STATICCALL──► [Factory.getConfig()]
#           │                              returns: (N, hash)
#           └─► Loop(i=0 to N):
#                 1. Compute CREATE2 addr from factory|salt|hash
#                 2. BALANCE(addr)        → 2600 gas (cold)
#                 3. <second_opcode>(addr) → varies (warm)
#
# HOW IT WORKS:
#   1. Factory uses EXTCODECOPY to load initcode
#   2. Each CREATE2 produces unique bytecode (via ADDRESS)
#   3. Shared initcode hash enables deterministic addresses
#   4. Attack rapidly accesses all contracts per factory stub


@pytest.mark.stub_parametrize("factory_stub", "bloatnet_factory_")
@pytest.mark.parametrize(
    "second_opcode",
    [Op.EXTCODESIZE, Op.EXTCODECOPY, Op.EXTCODEHASH, Op.STATICCALL, Op.CALL],
)
@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_first", "opcode_first"],
)
def test_bloatnet_balance_opcode(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
    second_opcode: Op,
    factory_stub: str,
) -> None:
    """
    Benchmark BALANCE paired with a second opcode on bloatnet
    factory contracts.
    """
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub=factory_stub,
    )

    # Contract Construction
    setup = Bytecode()

    setup += Conditional(
        condition=Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
            # gas accounting
            address_warm=False,
            old_memory_size=0,
            new_memory_size=160,
        ),
        if_false=Op.INVALID,
    )

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(32),
        init_code_hash=Op.MLOAD(128),
        old_memory_size=160,
    )

    setup += create2_preimage
    setup += Op.CALLDATALOAD(0)  # [num_contract]

    # Build the second opcode's bytecode
    balance_op = Op.POP(Op.BALANCE)

    if second_opcode == Op.EXTCODESIZE:
        other_op = Op.POP(Op.EXTCODESIZE)
    elif second_opcode == Op.EXTCODECOPY:
        max_contract_size = fork.max_code_size()
        other_op = Op.POP(
            Op.EXTCODECOPY(
                address=Op.DUP4,
                dest_offset=Op.ADD(Op.MLOAD(32), 96),
                offset=max_contract_size - 1,
                size=1,
                data_size=1,
            )
        )
    elif second_opcode == Op.EXTCODEHASH:
        other_op = Op.POP(Op.EXTCODEHASH)
    elif second_opcode == Op.STATICCALL:
        # gas=1: forces account/code loading, then fails
        other_op = (
            Op.POP(
                Op.STATICCALL(
                    gas=1,
                    address=Op.DUP5,
                    args_offset=0,
                    args_size=0,
                    ret_offset=0,
                    ret_size=0,
                )
            )
            + Op.POP
        )
    elif second_opcode == Op.CALL:
        # gas=1: forces account/code loading, then fails
        other_op = (
            Op.POP(
                Op.CALL(
                    gas=1,
                    address=Op.DUP6,
                    value=0,
                    args_offset=0,
                    args_size=0,
                    ret_offset=0,
                    ret_size=0,
                )
            )
            + Op.POP
        )
    else:
        raise ValueError(f"Unsupported opcode: {second_opcode}")

    benchmark_ops = (
        (balance_op + other_op) if balance_first else (other_op + balance_op)
    )

    loop = While(
        body=(
            create2_preimage.address_op()
            + Op.DUP1
            + benchmark_ops
            + create2_preimage.increment_salt_op()
        ),
        condition=DECREMENT_COUNTER_CONDITION,
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    txs, total_gas_consumed = build_benchmark_txs(
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        attack_contract_address=attack_contract_address,
        setup_cost=setup.gas_cost(fork),
        iteration_cost=loop.gas_cost(fork),
    )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )


# CALL+VALUE BENCHMARK ARCHITECTURE:
#
#   test_bloatnet_call_value_existing:
#   Same factory pattern as test_bloatnet_balance_opcode, but performs
#   CALL with value=1 wei to each factory contract. The subcall fails
#   (insufficient gas for 24KB bytecode), but GAS_CALL_VALUE (9000 gas)
#   is still charged on top of the cold account access cost.
#
#   test_bloatnet_call_value_new_account:
#   Generates unique addresses from keccak256(counter) and CALLs each with
#   value=1 wei. Since these addresses have no code, the subcall succeeds
#   (via the 2300 gas stipend), transferring value and creating a new account.
#   Each iteration costs ~36,600 gas (cold + value + new_account),
#   stressing trie expansion through massive new account creation.


@pytest.mark.stub_parametrize("factory_stub", "bloatnet_factory_")
def test_bloatnet_call_value_existing(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    factory_stub: str,
) -> None:
    """
    Benchmark CALL with value transfer to cold existing factory contracts.

    Unlike the existing CALL test which uses gas=1 and value=0, this test
    passes value=1 wei per call, adding GAS_CALL_VALUE (9000 gas) to each
    cold account access. The subcall fails (insufficient gas for bytecode
    execution), so value is not actually transferred, but the gas penalty
    is still charged.
    """
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub=factory_stub,
    )

    # Contract Construction
    setup = Bytecode()

    setup += Conditional(
        condition=Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
            # gas accounting
            address_warm=False,
            old_memory_size=0,
            new_memory_size=160,
        ),
        if_false=Op.INVALID,
    )

    create2_preimage = Create2PreimageLayout(
        factory_address=factory_address,
        salt=Op.CALLDATALOAD(32),
        init_code_hash=Op.MLOAD(128),
        old_memory_size=160,
    )

    setup += create2_preimage
    setup += Op.CALLDATALOAD(0)  # [num_contract]

    # CALL with value=1 to factory contracts.
    # The address is computed inline via SHA3, avoiding DUP depth issues.
    # gas=1: subcall gets 1 + 2300 stipend, still not enough for 24KB
    # bytecode → subcall fails, but cold + value gas costs are charged.
    call_value_op = Op.POP(
        Op.CALL(
            gas=1,
            address=create2_preimage.address_op(),
            value=1,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
            # gas accounting
            value_transfer=True,
        )
    )

    loop = While(
        body=(call_value_op + create2_preimage.increment_salt_op()),
        condition=DECREMENT_COUNTER_CONDITION,
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    txs, total_gas_consumed = build_benchmark_txs(
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        attack_contract_address=attack_contract_address,
        setup_cost=setup.gas_cost(fork),
        iteration_cost=loop.gas_cost(fork),
    )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
    )


def test_bloatnet_call_value_new_account(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark CALL with value transfer to non-existent accounts.

    Generate unique addresses via keccak256(counter) and CALL each with
    value=1 wei. Since these addresses have no code, the subcall succeeds
    (via the 2300 gas stipend), transferring value and creating a new
    account in the trie. Each iteration costs ~36,600 gas:
    - GAS_COLD_ACCOUNT_ACCESS: 2,600
    - GAS_CALL_VALUE: 9,000
    - GAS_NEW_ACCOUNT: 25,000

    This stresses trie expansion through massive new account creation.
    """
    # Memory layout: MEM[0..31] = counter (incremented each iteration)
    setup = (
        Op.MSTORE(
            0,
            Op.CALLDATALOAD(32),  # salt_offset (starting counter)
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.CALLDATALOAD(0)  # [num_calls]
    )

    # CALL with value=1 to keccak256-derived addresses.
    # gas=0: subcall gets 0 + 2300 stipend. No code at target → succeeds.
    # Value is transferred, new account is created in trie.
    call_value_op = Op.POP(
        Op.CALL(
            gas=0,
            address=Op.SHA3(0, 32, data_size=32),
            value=1,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
            # gas accounting
            value_transfer=True,
            account_new=True,
        )
    )

    # Increment counter in memory for next address
    increment_counter = Op.MSTORE(0, Op.ADD(Op.MLOAD(0), 1))

    loop = While(
        body=(call_value_op + increment_counter),
        condition=DECREMENT_COUNTER_CONDITION,
    )

    # Contract Deployment — needs balance for value transfers (1 wei each)
    code = setup + loop
    attack_contract_address = pre.deploy_contract(
        code=code,
        balance=10**18,  # 1 ETH, enough for all iterations
    )

    # Gas Accounting
    txs, total_gas_consumed = build_benchmark_txs(
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        attack_contract_address=attack_contract_address,
        setup_cost=setup.gas_cost(fork),
        iteration_cost=loop.gas_cost(fork),
    )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
        skip_gas_used_validation=True,
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
    """
    Benchmark mixed SLOAD/SSTORE on bloatnet.

    Uses runtime gas checking instead of pre-calculated iteration
    counts.  Each ERC20 contract has its own implementation with
    different per-call gas costs, so a single gas model cannot
    predict the right iteration count.  Instead the contract
    checks remaining gas via the GAS opcode each iteration and
    splits the budget between SLOAD and SSTORE phases using a
    pre-computed gas floor.
    """
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
