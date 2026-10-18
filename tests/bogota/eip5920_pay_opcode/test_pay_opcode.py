"""
Tests for [EIP-5920: PAY opcode](https://eips.ethereum.org/EIPS/eip-5920).
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalBalanceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import Spec, ref_spec_5920, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_5920.git_path
REFERENCE_SPEC_VERSION = ref_spec_5920.version

pytestmark = pytest.mark.valid_from("Bogota")


@EIPChecklist.Opcode.Test.StackComplexOperations.StackHeights.Odd()
@EIPChecklist.Opcode.Test.StackComplexOperations.StackHeights.Even()
@pytest.mark.parametrize(
    "recipient_exists",
    [True, False],
    ids=["existing_recipient", "nonexistent_recipient"],
)
@pytest.mark.parametrize(
    "transfer_value,expected_success",
    [
        (0, 1),
        (1, 1),
        (1_000, 1),
        (10_000, 1),
        (10_001, 0),
        (2**128, 0),
    ],
    ids=[
        "zero_value",
        "one_wei",
        "partial_balance",
        "full_balance",
        "balance_plus_one",
        "large_insufficient_balance",
    ],
)
def test_pay_basic_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
    recipient_exists: bool,
    transfer_value: int,
    expected_success: int,
) -> None:
    """
    Test basic ether transfer functionality of the `PAY` opcode across
    existing and non-existent recipients, zero/non-zero values, exact full
    balance, and insufficient balance.
    """
    initial_contract_balance = 10_000
    initial_recipient_balance = 500 if recipient_exists else 0
    sender = pre.fund_eoa()
    recipient = (
        pre.fund_eoa(initial_recipient_balance)
        if recipient_exists
        else pre.nonexistent_account()
    )

    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(initial_contract_balance),
                Op.SELFBALANCE,
            )
            + Op.SSTORE(
                storage.store_next(expected_success),
                Op.PAY(recipient, transfer_value),
            )
            + Op.SSTORE(
                storage.store_next(
                    initial_contract_balance - transfer_value
                    if expected_success
                    else initial_contract_balance
                ),
                Op.SELFBALANCE,
            )
            + Op.SSTORE(
                storage.store_next(
                    initial_recipient_balance + transfer_value
                    if expected_success
                    else initial_recipient_balance
                ),
                Op.BALANCE(recipient),
            )
            + Op.STOP
        ),
        balance=initial_contract_balance,
    )

    expected_logs = (
        [transfer_log(contract_address, recipient, transfer_value)]
        if expected_success and transfer_value > 0
        else []
    )

    post: Dict[Address, Account | object] = {
        contract_address: Account(
            balance=(
                initial_contract_balance - transfer_value
                if expected_success
                else initial_contract_balance
            ),
            storage=storage,
        ),
    }
    if recipient_exists or (expected_success and transfer_value > 0):
        post[recipient] = Account(
            balance=(
                initial_recipient_balance + transfer_value
                if expected_success
                else initial_recipient_balance
            )
        )
    else:
        post[recipient] = Account.NONEXISTENT

    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "recipient_code",
    [
        Op.REVERT(0, 0),
        Op.INVALID,
        Op.SSTORE(0, 1) + Op.STOP,
        Op.JUMPDEST + Op.JUMP(0),
    ],
    ids=["revert", "invalid", "sstore", "infinite_loop"],
)
def test_pay_does_not_execute_recipient_code(
    state_test: StateTestFiller,
    pre: Alloc,
    recipient_code: Bytecode,
) -> None:
    """
    Verify `PAY` transfers value to a contract without executing its code
    (even when the recipient code reverts, halts with `INVALID`, writes to
    storage, or loops infinitely).
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=recipient_code, balance=100)

    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(storage.store_next(1), Op.PAY(recipient, 500))
            + Op.SSTORE(storage.store_next(600), Op.BALANCE(recipient))
            + Op.STOP
        ),
        balance=1_000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract_address, recipient, 500)]
        ),
    )

    post = {
        contract_address: Account(balance=500, storage=storage),
        recipient: Account(balance=600, storage={}),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "transfer_amount,expected_success",
    [
        (0, 1),
        (1_000, 1),
        (10_000, 1),
        (10_001, 0),
    ],
    ids=[
        "zero_to_self",
        "partial_to_self",
        "full_balance_to_self",
        "insufficient_balance_to_self",
    ],
)
def test_pay_to_self(
    state_test: StateTestFiller,
    pre: Alloc,
    transfer_amount: int,
    expected_success: int,
) -> None:
    """
    Test `PAY` when a contract transfers to itself (`Op.ADDRESS`).
    Verify balance remains invariant and no EIP-7708 transfer log is emitted.
    """
    initial_balance = 10_000
    sender = pre.fund_eoa()
    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(expected_success),
                Op.PAY(Op.ADDRESS, transfer_amount),
            )
            + Op.SSTORE(storage.store_next(initial_balance), Op.SELFBALANCE)
            + Op.STOP
        ),
        balance=initial_balance,
    )

    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )
    post = {
        contract_address: Account(balance=initial_balance, storage=storage),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.with_all_precompiles
def test_pay_to_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile: Address,
) -> None:
    """
    Verify `PAY` to any active precompile transfers ether without executing
    the precompile.
    """
    sender = pre.fund_eoa()
    transfer_amount = 1_000
    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(1),
                Op.PAY(precompile, transfer_amount),
            )
            + Op.SSTORE(
                storage.store_next(transfer_amount),
                Op.BALANCE(precompile),
            )
            + Op.STOP
        ),
        balance=10_000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract_address, precompile, transfer_amount)]
        ),
    )
    post = {
        contract_address: Account(
            balance=10_000 - transfer_amount,
            storage=storage,
        ),
        precompile: Account(balance=transfer_amount),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.OutOfBounds.Verify.Max()
@pytest.mark.parametrize(
    "special_target",
    ["coinbase", "system_address", "zero_address", "max_valid_address"],
)
def test_pay_to_special_addresses(
    state_test: StateTestFiller,
    pre: Alloc,
    special_target: str,
) -> None:
    """
    Test `PAY` to special addresses (`COINBASE`, `SYSTEM_ADDRESS`, `0x00`,
    and `0xFF..FF` = `2**160 - 1`).
    """
    env = Environment()
    sender = pre.fund_eoa()
    transfer_amount = 500

    target_map: Dict[str, Address] = {
        "coinbase": env.fee_recipient,
        "system_address": Spec.SYSTEM_ADDRESS,
        "zero_address": Address(0),
        "max_valid_address": Address(Spec.MAX_ADDRESS),
    }
    target = target_map[special_target]

    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(storage.store_next(1), Op.PAY(target, transfer_amount))
            + Op.SSTORE(
                storage.store_next(transfer_amount),
                Op.BALANCE(target),
            )
            + Op.STOP
        ),
        balance=5_000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=0,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract_address, target, transfer_amount)]
        ),
    )
    post = {
        contract_address: Account(
            balance=5_000 - transfer_amount,
            storage=storage,
        ),
        target: Account(balance=transfer_amount),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.OutOfBounds.Verify.MaxPlusOne()
@EIPChecklist.Opcode.Test.ExceptionalAbort()
@pytest.mark.parametrize(
    "invalid_addr",
    [
        Spec.INVALID_ADDRESS_MIN,
        Spec.INVALID_ADDRESS_MIN | 0x1234567890ABCDEF1234567890ABCDEF12345678,
        1 << 168,
        1 << 200,
        1 << 248,
        1 << 255,
        2**256 - 1,
    ],
    ids=[
        "min_invalid_2_pow_160",
        "min_invalid_with_low_20_bytes",
        "byte_21_set",
        "byte_25_set",
        "high_byte_lsb_set",
        "msb_set",
        "uint256_max",
    ],
)
@pytest.mark.parametrize("transfer_value", [0, 100])
def test_pay_invalid_address_halts(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    invalid_addr: int,
    transfer_value: int,
) -> None:
    """
    Verify `PAY` exceptionally halts when any of the high 12 bytes of `addr`
    are non-zero (`addr >= 2**160`), even when `val == 0`, without warming
    or recording the masked address in the EIP-7928 Block-Level Access List.
    """
    sender = pre.fund_eoa()
    masked_recipient = Address(invalid_addr & Spec.MAX_ADDRESS)

    callee = pre.deploy_contract(
        code=Op.PAY(invalid_addr, transfer_value) + Op.STOP,
        balance=1_000,
    )
    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(0),
                Op.CALL(100_000, callee, 0, 0, 0, 0, 0),
            )
            + Op.SSTORE(storage.store_next(1_000), Op.BALANCE(callee))
            + Op.STOP
        ),
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                callee: BalAccountExpectation.empty(),
                masked_recipient: None,
            }
        ),
    )
    post = {
        caller: Account(storage=storage),
        callee: Account(balance=1_000),
    }
    blockchain_test(pre=pre, post=post, blocks=[block])


@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall()
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.BanCheck()
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.BanNoModification()
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.SubCalls()
@pytest.mark.parametrize(
    "transfer_value",
    [0, 1, 1_000],
    ids=["zero_value", "one_wei", "non_zero_value"],
)
def test_pay_static_context_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    transfer_value: int,
) -> None:
    """
    Verify `PAY` halts exceptionally in a `STATICCALL` frame, even when
    `val == 0` (no state modification), and when called in a `CALL` nested
    inside a `STATICCALL`.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(100)

    pay_callee = pre.deploy_contract(
        code=Op.PAY(recipient, transfer_value) + Op.STOP,
        balance=10_000,
    )
    intermediate = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(100_000, pay_callee, 0, 0, 0, 0, 0))
        + Op.STOP,
    )
    # Direct STATICCALL to pay_callee and STATICCALL -> CALL to pay_callee
    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(0),
                Op.STATICCALL(100_000, pay_callee, 0, 0, 0, 0),
            )
            + Op.SSTORE(
                storage.store_next(0),
                Op.STATICCALL(100_000, intermediate, 0, 0, 0, 0),
            )
            + Op.SSTORE(storage.store_next(10_000), Op.BALANCE(pay_callee))
            + Op.SSTORE(storage.store_next(100), Op.BALANCE(recipient))
            + Op.STOP
        ),
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )
    post = {
        caller: Account(storage=storage),
        pay_callee: Account(balance=10_000),
        recipient: Account(balance=100),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.GasUsage.Normal()
@pytest.mark.parametrize("address_warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "recipient_exists", [True, False], ids=["existing", "nonexistent"]
)
@pytest.mark.parametrize(
    "transfer_value,sufficient_balance",
    [
        (0, True),
        (100, True),
        (20_000, False),
    ],
    ids=["zero_val", "nonzero_val", "insufficient_balance"],
)
def test_pay_gas_table(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    address_warm: bool,
    recipient_exists: bool,
    transfer_value: int,
    sufficient_balance: bool,
) -> None:
    """
    Verify exact execution-gas and state-gas consumption of `PAY` across all
    combinations of cold/warm target, existing/non-existent target, and
    zero/non-zero/insufficient-balance value transfer.
    """
    initial_balance = 1_000
    sender = pre.fund_eoa()
    recipient = (
        pre.fund_eoa(500) if recipient_exists else pre.nonexistent_account()
    )

    pay_op = Op.PAY(
        address_warm=address_warm,
        value_transfer=transfer_value > 0,
        account_new=(not recipient_exists and transfer_value > 0),
    )
    expected_exec_gas = pay_op.execution_cost(fork)
    # Overhead between the two GAS opcodes:
    # PUSH recipient (21) + PUSH value (1..3) -> 3 + 3 = 6, plus GAS (2) = 8
    push_overhead = 3 + 3 + fork.gas_costs().BASE

    warm_setup = Op.POP(Op.BALANCE(recipient)) if address_warm else Bytecode()

    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            warm_setup
            + Op.GAS
            + Op.PUSH2(transfer_value)
            + Op.PUSH20(recipient)
            + Op.PAY
            + Op.GAS
            # Stack: [gas_before, pay_result, gas_after]
            + Op.SWAP1
            + Op.PUSH1(storage.store_next(1 if sufficient_balance else 0))
            + Op.SSTORE
            # Stack: [gas_before, gas_after] -> SWAP1 -> SUB
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1(storage.store_next(expected_exec_gas + push_overhead))
            + Op.SSTORE
            + Op.STOP
        ),
        balance=initial_balance,
    )

    # Set gas_limit above the execution gas cap so state gas is drawn from
    # the state gas reservoir and Op.GAS measures purely execution gas.
    exec_cap = fork.transaction_gas_limit_cap() or 16_777_216
    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=exec_cap + 1_000_000,
    )

    post: Dict[Address, Account | object] = {
        contract_address: Account(
            balance=(
                initial_balance - transfer_value
                if sufficient_balance
                else initial_balance
            ),
            storage=storage,
        ),
    }
    if recipient_exists:
        post[recipient] = Account(
            balance=500 + (transfer_value if sufficient_balance else 0)
        )
    elif sufficient_balance and transfer_value > 0:
        post[recipient] = Account(balance=transfer_value)
    else:
        post[recipient] = Account.NONEXISTENT

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.GasUsage.OutOfGasExecution()
@EIPChecklist.Opcode.Test.GasUsage.ExtraGas()
@pytest.mark.parametrize("address_warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize("transfer_value", [0, 100], ids=["zero", "nonzero"])
@pytest.mark.parametrize(
    "gas_delta", [-1, 0, 1], ids=["oog_minus_1", "exact", "extra_plus_1"]
)
def test_pay_pre_state_execution_gas_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    address_warm: bool,
    transfer_value: int,
    gas_delta: int,
) -> None:
    """
    Test two-sided execution-gas boundary (`exact - 1`, `exact`, `exact + 1`)
    for `PAY`. Verify that on pre-state execution OOG (`exact - 1`), `addr`
    is neither warmed nor added to the EIP-7928 Block-Level Access List.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(500)

    pay_op = Op.PAY(
        address_warm=address_warm,
        value_transfer=transfer_value > 0,
        account_new=False,
    )
    # Callee code: PUSH1(transfer_value) (3) + PUSH20(recipient) (3) + PAY
    callee_code = Op.PUSH1(transfer_value) + Op.PUSH20(recipient) + Op.PAY
    exact_callee_gas = 6 + pay_op.execution_cost(fork)
    subcall_gas = exact_callee_gas + gas_delta
    expected_call_success = 1 if gas_delta >= 0 else 0

    callee = pre.deploy_contract(code=callee_code, balance=1_000)

    warm_setup = Op.POP(Op.BALANCE(recipient)) if address_warm else Bytecode()
    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            warm_setup
            + Op.SSTORE(
                storage.store_next(expected_call_success),
                Op.CALL(subcall_gas, callee, 0, 0, 0, 0, 0),
            )
            + Op.STOP
        ),
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=500_000,
    )

    # When address_warm is False and gas_delta < 0 (pre-state OOG),
    # recipient was never accessed so it must NOT appear in the BAL!
    recipient_bal = (
        None
        if (not address_warm and gas_delta < 0)
        else (
            BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=500 + transfer_value
                    )
                ]
            )
            if (expected_call_success and transfer_value > 0)
            else BalAccountExpectation.empty()
        )
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                recipient: recipient_bal,
            }
        ),
    )

    post = {
        caller: Account(storage=storage),
        callee: Account(
            balance=1_000 - (transfer_value if expected_call_success else 0)
        ),
        recipient: Account(
            balance=500 + (transfer_value if expected_call_success else 0)
        ),
    }
    blockchain_test(pre=pre, post=post, blocks=[block])


@EIPChecklist.Opcode.Test.GasUsage.OrderOfOperations.Exact()
@EIPChecklist.Opcode.Test.GasUsage.OrderOfOperations.Oog()
@pytest.mark.parametrize("funding", ["reservoir", "spill"])
@pytest.mark.parametrize(
    "outcome",
    ["sufficient", "insufficient_state_gas", "insufficient_balance_refund"],
)
def test_pay_new_account_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    funding: str,
    outcome: str,
) -> None:
    """
    Test `PAY` state-gas charging (`GAS_NEW_ACCOUNT` = 183,600) when funding a
    non-existent account:
    1. `sufficient`: succeeds drawing from `state_gas_reservoir` or spilling
       into `gas_left`.
    2. `insufficient_state_gas`: halts with OOG when state-gas cannot be
       covered, while still recording `addr` in the EIP-7928 BAL (since the
       pre-state execution-gas succeeded and `addr` was checked for liveness).
    3. `insufficient_balance_refund`: when sender balance < `val`, `0` is
       pushed and the `GAS_NEW_ACCOUNT` state-gas charge is refilled in LIFO
       order so a subsequent `PAY` to a new account succeeds without needing
       an extra `GAS_NEW_ACCOUNT` grant.
    """
    sender = pre.fund_eoa()
    recipient_1 = pre.nonexistent_account()
    recipient_2 = pre.nonexistent_account()

    pay_op = Op.PAY(
        address_warm=False,
        value_transfer=True,
        account_new=True,
    )
    exec_cost = pay_op.execution_cost(fork)
    state_cost = pay_op.state_cost(fork)

    if outcome == "insufficient_balance_refund":
        # First PAY attempts to transfer 2_000 (> balance 1_000) to
        # recipient_1: charges NEW_ACCOUNT state gas, then refills it on
        # insufficient balance. Second PAY transfers 500 to recipient_2:
        # uses the refilled NEW_ACCOUNT state gas!
        callee_code = (
            Op.PUSH2(2_000)
            + Op.PUSH20(recipient_1)
            + Op.PAY
            + Op.POP
            + Op.PUSH2(500)
            + Op.PUSH20(recipient_2)
            + Op.PAY
            + Op.POP
            + Op.STOP
        )
        # Only 1x state_cost is provided, proving the first PAY refilled its
        # state gas!
        needed_exec = 2 * (6 + exec_cost + 2) + 100
        needed_state = state_cost
    else:
        callee_code = (
            Op.PUSH2(500) + Op.PUSH20(recipient_1) + Op.PAY + Op.POP + Op.STOP
        )
        needed_exec = 6 + exec_cost + 2
        needed_state = (
            state_cost - 1
            if outcome == "insufficient_state_gas"
            else state_cost
        )

    callee = pre.deploy_contract(code=callee_code, balance=1_000)

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    if funding == "spill":
        # Set tx gas_limit below execution_gas_cap so reservoir == 0 and state
        # gas spills into gas_left.
        subcall_gas = needed_exec + needed_state
        tx_gas_limit = intrinsic + subcall_gas + 200_000
    else:
        subcall_gas = needed_exec + (
            0 if outcome == "insufficient_state_gas" else 100
        )
        exec_cap = fork.transaction_gas_limit_cap() or 16_777_216
        tx_gas_limit = exec_cap + needed_state

    expected_call_success = 0 if outcome == "insufficient_state_gas" else 1
    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(expected_call_success),
                Op.CALL(subcall_gas, callee, 0, 0, 0, 0, 0),
            )
            + Op.STOP
        ),
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=tx_gas_limit,
    )

    # Even on insufficient_state_gas, recipient_1 was accessed during the
    # liveness check after pre-state execution gas succeeded, so it appears in
    # the BAL as an empty read!
    expected_bal = {
        recipient_1: (
            BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=500)
                ]
            )
            if outcome == "sufficient"
            else BalAccountExpectation.empty()
        ),
    }
    if outcome == "insufficient_balance_refund":
        expected_bal[recipient_2] = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=500)
            ]
        )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=expected_bal,
        ),
    )

    post: Dict[Address, Account | object] = {
        caller: Account(storage=storage),
        callee: Account(
            balance=1_000 if outcome == "insufficient_state_gas" else 500
        ),
        recipient_1: (
            Account(balance=500)
            if outcome == "sufficient"
            else Account.NONEXISTENT
        ),
    }
    if outcome == "insufficient_balance_refund":
        post[recipient_2] = Account(balance=500)

    blockchain_test(pre=pre, post=post, blocks=[block])


def test_pay_revert_undoes_account_creation_and_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify that when a child frame executes `PAY` to create a new account and
    subsequently `REVERT`s, both the account creation and its `GAS_NEW_ACCOUNT`
    state-gas charge are rolled back.
    """
    sender = pre.fund_eoa()
    recipient_reverted = pre.nonexistent_account()
    recipient_committed = pre.nonexistent_account()

    reverting_callee = pre.deploy_contract(
        code=(Op.POP(Op.PAY(recipient_reverted, 500)) + Op.REVERT(0, 0)),
        balance=1_000,
    )

    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(0),
                Op.CALL(100_000, reverting_callee, 0, 0, 0, 0, 0),
            )
            + Op.SSTORE(
                storage.store_next(1),
                Op.PAY(recipient_committed, 500),
            )
            + Op.STOP
        ),
        balance=1_000,
    )

    # Provide only 1x NEW_ACCOUNT in the state gas reservoir so the second PAY
    # can only succeed if the reverted child frame's NEW_ACCOUNT charge was
    # restored to the reservoir.
    state_cost = fork.gas_costs().NEW_ACCOUNT
    exec_cap = fork.transaction_gas_limit_cap() or 16_777_216
    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=exec_cap + state_cost,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(caller, recipient_committed, 500)]
        ),
    )

    post = {
        caller: Account(balance=500, storage=storage),
        reverting_callee: Account(balance=1_000),
        recipient_reverted: Account.NONEXISTENT,
        recipient_committed: Account(balance=500),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.ReturnData.Buffer.Current()
@EIPChecklist.Opcode.Test.ReturnData.Buffer.Parent()
@pytest.mark.parametrize(
    "pay_transfer_value,expected_pay_status",
    [(100, 1), (10_000, 0)],
    ids=["pay_success", "pay_insufficient_balance"],
)
def test_pay_preserves_returndata(
    state_test: StateTestFiller,
    pre: Alloc,
    pay_transfer_value: int,
    expected_pay_status: int,
) -> None:
    """
    Verify that `PAY` (unlike `CALL*`) does not clear or overwrite the
    current frame's `returndata` buffer on either success or failure.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(50)
    return_word = (
        0xCAFEBABEDEADBEEF11223344556677889900AABBCCDDEEFF0011223344556677
    )

    echo_callee = pre.deploy_contract(
        code=Op.MSTORE(0, return_word) + Op.RETURN(0, 32),
    )

    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(1),
                Op.CALL(100_000, echo_callee, 0, 0, 0, 0, 0),
            )
            + Op.SSTORE(storage.store_next(32), Op.RETURNDATASIZE)
            + Op.SSTORE(
                storage.store_next(expected_pay_status),
                Op.PAY(recipient, pay_transfer_value),
            )
            + Op.SSTORE(storage.store_next(32), Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(0, 0, 32)
            + Op.SSTORE(storage.store_next(return_word), Op.MLOAD(0))
            + Op.STOP
        ),
        balance=1_000,
    )

    tx = Transaction(sender=sender, to=caller, gas_limit=1_000_000)
    post = {
        caller: Account(
            balance=1_000 - (pay_transfer_value if expected_pay_status else 0),
            storage=storage,
        ),
        recipient: Account(
            balance=50 + (pay_transfer_value if expected_pay_status else 0)
        ),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.StackUnderflow()
@EIPChecklist.Opcode.Test.StackComplexOperations.StackHeights.Zero()
@pytest.mark.parametrize(
    "stack_items", [0, 1], ids=["empty_stack", "one_item"]
)
def test_pay_stack_underflow(
    state_test: StateTestFiller,
    pre: Alloc,
    stack_items: int,
) -> None:
    """Test `PAY` halts with `StackUnderflowError` with < 2 stack items."""
    sender = pre.fund_eoa()
    callee = pre.deploy_contract(
        code=(Op.PUSH0 * stack_items) + Op.PAY + Op.STOP,
        balance=1_000,
    )
    storage = Storage()
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(0),
            Op.CALL(100_000, callee, 0, 0, 0, 0, 0),
        )
        + Op.STOP,
    )
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)
    state_test(
        env=Environment(),
        pre=pre,
        post={
            caller: Account(storage=storage),
            callee: Account(balance=1_000),
        },
        tx=tx,
    )


@EIPChecklist.Opcode.Test.StackOverflow()
def test_pay_max_stack(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that `PAY` succeeds when the operand stack is at its maximum height
    of 1024 items (pops 2, pushes 1 -> 1023 items on stack).
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(100)
    storage = Storage()
    contract_address = pre.deploy_contract(
        code=(
            Op.PUSH0 * 1022
            + Op.PUSH1(250)
            + Op.PUSH20(recipient)
            + Op.PAY
            + Op.PUSH1(storage.store_next(1))
            + Op.SSTORE
            + Op.STOP
        ),
        balance=1_000,
    )
    tx = Transaction(sender=sender, to=contract_address, gas_limit=1_000_000)
    post = {
        contract_address: Account(balance=750, storage=storage),
        recipient: Account(balance=350),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.ExecutionContext.Call()
@EIPChecklist.Opcode.Test.ExecutionContext.Callcode()
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall()
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall.Balance()
@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
    ids=["call", "callcode", "delegatecall"],
)
def test_pay_execution_contexts(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Verify `PAY` deducts balance from `evm.current_target` across `CALL`
    (deducts from callee) and `CALLCODE` / `DELEGATECALL` (deducts from
    caller).
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(100)

    pay_target = pre.deploy_contract(
        code=Op.MSTORE(0, Op.PAY(recipient, 300)) + Op.RETURN(0, 32),
        balance=1_000,
    )

    storage = Storage()
    caller_call = (
        call_opcode(100_000, pay_target, 0, 0, 0, 0, 32)
        if call_opcode in (Op.CALL, Op.CALLCODE)
        else call_opcode(100_000, pay_target, 0, 0, 0, 32)
    )
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(storage.store_next(1), caller_call)
            + Op.SSTORE(storage.store_next(1), Op.MLOAD(0))
            + Op.STOP
        ),
        balance=2_000,
    )

    deducts_from_caller = call_opcode in (Op.CALLCODE, Op.DELEGATECALL)
    effective_payer = caller if deducts_from_caller else pay_target

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(effective_payer, recipient, 300)]
        ),
    )
    post = {
        caller: Account(
            balance=1_700 if deducts_from_caller else 2_000,
            storage=storage,
        ),
        pay_target: Account(
            balance=1_000 if deducts_from_caller else 700,
        ),
        recipient: Account(balance=400),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Tx()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Opcode()
@pytest.mark.parametrize("mode", ["tx_create", "create", "create2"])
def test_pay_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    mode: str,
) -> None:
    """
    Verify `PAY` inside contract creation initcode (`tx_create`, `CREATE`,
    `CREATE2`) transfers from the newly created contract's endowment balance.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(100)

    deployed_code = Op.STOP
    initcode = Initcode(
        deploy_code=deployed_code,
        initcode_prefix=Op.SSTORE(0, Op.PAY(recipient, 400)),
    )

    if mode == "tx_create":
        created_address = compute_create_address(address=sender, nonce=0)
        tx = Transaction(
            sender=sender,
            to=None,
            value=1_000,
            data=initcode,
            gas_limit=1_000_000,
            expected_receipt=TransactionReceipt(
                logs=[
                    transfer_log(sender, created_address, 1_000),
                    transfer_log(created_address, recipient, 400),
                ]
            ),
        )
        post = {
            created_address: Account(
                balance=600,
                code=deployed_code,
                storage={0: 1},
            ),
            recipient: Account(balance=500),
        }
    else:
        create_call = (
            Op.CREATE(1_000, 0, Op.CALLDATASIZE)
            if mode == "create"
            else Op.CREATE2(1_000, 0, Op.CALLDATASIZE, 0x42)
        )
        storage = Storage()
        factory = pre.deploy_contract(
            code=(
                Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                + Op.SSTORE(1, create_call)
                + Op.STOP
            ),
            balance=2_000,
        )
        created_address = compute_create_address(
            address=factory,
            nonce=1,
            salt=0x42,
            initcode=initcode,
            opcode=Op.CREATE2 if mode == "create2" else Op.CREATE,
        )
        storage[1] = created_address
        tx = Transaction(
            sender=sender,
            to=factory,
            data=initcode,
            gas_limit=1_000_000,
            expected_receipt=TransactionReceipt(
                logs=[
                    transfer_log(factory, created_address, 1_000),
                    transfer_log(created_address, recipient, 400),
                ]
            ),
        )
        post = {
            factory: Account(balance=1_000, storage=storage),
            created_address: Account(
                balance=600,
                code=deployed_code,
                storage={0: 1},
            ),
            recipient: Account(balance=500),
        }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.ExecutionContext.SetCode()
def test_pay_to_and_from_eip7702_delegated_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test `PAY` interaction with EIP-7702 delegated accounts:
    1. Paying TO an EIP-7702 delegated EOA does not resolve its delegation,
       does not execute the delegate's code, does not charge delegation-target
       access gas, and does not include the delegation target in the EIP-7928
       Block-Level Access List.
    2. Executing `PAY` FROM an EIP-7702 delegated EOA transfers from the
       delegated EOA's balance.
    """
    sender = pre.fund_eoa()

    # Recipient is an EOA delegated to `forbidden_delegate` (which reverts if
    # executed).
    forbidden_delegate = pre.deploy_contract(code=Op.REVERT(0, 0))
    delegated_recipient = pre.fund_eoa(
        amount=200, delegation=forbidden_delegate
    )

    # Payer is an EOA delegated to `payer_delegate` via type-4 authorization.
    pay_op = Op.PAY(
        address_warm=False,
        value_transfer=True,
        account_new=False,
    )
    expected_exec_gas = pay_op.execution_cost(fork)
    push_overhead = 3 + 3 + fork.gas_costs().BASE

    storage = Storage()
    payer_delegate = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.PUSH2(300)
            + Op.PUSH20(delegated_recipient)
            + Op.PAY
            + Op.GAS
            + Op.SWAP1
            + Op.PUSH1(storage.store_next(1))
            + Op.SSTORE
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1(storage.store_next(expected_exec_gas + push_overhead))
            + Op.SSTORE
            + Op.STOP
        ),
    )
    delegated_payer = pre.fund_eoa(amount=1_000)

    exec_cap = fork.transaction_gas_limit_cap() or 16_777_216
    tx = Transaction(
        sender=sender,
        to=delegated_payer,
        gas_limit=exec_cap + 1_000_000,
        authorization_list=[
            AuthorizationTuple(
                address=payer_delegate,
                nonce=0,
                signer=delegated_payer,
            )
        ],
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(delegated_payer, delegated_recipient, 300)]
        ),
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                delegated_recipient: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=500
                        )
                    ]
                ),
                # forbidden_delegate must NOT be accessed or in the BAL!
                forbidden_delegate: None,
            }
        ),
    )

    post = {
        delegated_payer: Account(
            balance=700,
            nonce=1,
            code=b"\xef\x01\x00" + bytes(payer_delegate),
            storage=storage,
        ),
        delegated_recipient: Account(
            balance=500,
            code=b"\xef\x01\x00" + bytes(forbidden_delegate),
        ),
    }
    blockchain_test(pre=pre, post=post, blocks=[block])
