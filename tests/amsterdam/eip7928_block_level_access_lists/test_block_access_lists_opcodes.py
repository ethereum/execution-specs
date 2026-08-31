"""
Tests for EIP-7928 Block Access Lists with single-opcode success and OOG
scenarios.

Block access lists (BAL) are generated via a client's state tracing journal.
Residual journal entries may persist when opcodes run out of gas, resulting
in a bloated BAL payload.

Issues identified in:
https://github.com/paradigmxyz/reth/issues/17765
https://github.com/bluealloy/revm/pull/2903

These tests ensure out-of-gas operations are not recorded in BAL,
preventing consensus issues.
"""

from enum import Enum
from typing import Callable, Dict

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Fork,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing import Macros as Om

from .spec import ref_spec_7928
from .test_block_access_lists_eip4788 import SYSTEM_ADDRESS

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version


pytestmark = pytest.mark.valid_from("Amsterdam")


class OutOfGasAt(Enum):
    """
    Enumeration of specific gas boundaries where OOG can occur.
    """

    EIP_2200_STIPEND = "oog_at_eip2200_stipend"
    EIP_2200_STIPEND_PLUS_1 = "oog_at_eip2200_stipend_plus_1"
    ABOVE_STIPEND_BELOW_ACCESS = "oog_above_stipend_below_access"
    ACCESS_COVERED_OOG_ON_WRITE = "access_covered_oog_on_write"
    EXACT_GAS_MINUS_1 = "oog_at_exact_gas_minus_1"


class OutOfGasBoundary(Enum):
    """
    OOG boundary scenarios for call-type opcodes with 7702 delegation.

    For 7702 targets, there's ALWAYS a gap between static gas check and
    second check (delegation_cost). All 4 scenarios test
    distinct boundaries.

    Gas check order:
    1. oog_before_target_access: access + transfer (if applicable) + memory.
       OOG with not enough for this check - no state access.
    2. oog_after_target_access: only enough for static check, state access
       reads target into BAL, not enough for anything else.
    3. oog_success_minus_1: exact gas minus 1. OOG here means target is in
       BAL, but we have enough information to calculate delegation cost
       AND the message call gas and not read if we don't have enough for
       both - delegation target NOT in BAL.
    4. success: target and delegation target both in BAL.

    OOG_SUCCESS_MINUS_1 tests that even when we have enough for delegation
    access cost, if we don't have enough for the total (missing subcall_gas),
    we don't read the delegation.
    """

    OOG_BEFORE_TARGET_ACCESS = "oog_before_target_access"
    OOG_AFTER_TARGET_ACCESS = "oog_after_target_access"
    OOG_SUCCESS_MINUS_1 = "oog_success_minus_1"
    SUCCESS = "success"


@pytest.mark.parametrize(
    "out_of_gas_at",
    [
        OutOfGasAt.EIP_2200_STIPEND,
        OutOfGasAt.EIP_2200_STIPEND_PLUS_1,
        OutOfGasAt.ABOVE_STIPEND_BELOW_ACCESS,
        OutOfGasAt.ACCESS_COVERED_OOG_ON_WRITE,
        OutOfGasAt.EXACT_GAS_MINUS_1,
        None,  # no oog, successful sstore
    ],
    ids=lambda x: x.value if x else "successful_sstore",
)
def test_bal_sstore_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    out_of_gas_at: OutOfGasAt | None,
) -> None:
    """
    Test BAL recording with SSTORE at various OOG boundaries and success.

    ``SSTORE`` clears two gates before the write cost: the EIP-2200
    stipend sentry (``gas_left`` must exceed ``CALL_STIPEND``) and the
    cold access charge (``COLD_STORAGE_ACCESS``). The slot read is
    recorded in the BAL only once both are cleared, so the recording
    gate is the higher of the two — which one dominates depends on the
    fork's schedule, and the expectations below are derived from that
    relation rather than assuming it.

    1. OOG at the stipend -> sentry fires, no BAL changes
    2. OOG at stipend + 1 -> sentry cleared by one; the read is
       recorded only if this also covers the access cost
    3. OOG at access cost - 1 -> below one of the two gates, no BAL
       changes
    4. OOG at the recording gate, write unaffordable -> storage read in
       BAL
    5. OOG at exact gas minus 1 -> storage read in BAL
    6. exact gas (success) -> storage write in BAL
    """
    alice = pre.fund_eoa()

    # Create contract that attempts SSTORE to cold storage slot 0x01
    storage_contract_code = Op.SSTORE(
        0x01, 0x42, key_warm=False, original_value=0, new_value=0x42
    )

    storage_contract = pre.deploy_contract(code=storage_contract_code)

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()()

    # Full cost: PUSHes + SSTORE (COLD_STORAGE_ACCESS + STORAGE_SET)
    full_cost = storage_contract_code.gas_cost(fork)

    # Push cost for the gas-boundary calculations below.
    push_code = Op.PUSH1(0x42) + Op.PUSH1(0x01)
    push_cost = push_code.gas_cost(fork)

    # CALL_STIPEND is a threshold check, not a gas cost. The read is
    # recorded once the sentry is cleared and the access cost is
    # affordable, so the recording gate is the higher of the two.
    stipend = fork.gas_costs().CALL_STIPEND
    cold_access = fork.gas_costs().COLD_STORAGE_ACCESS
    read_gate = max(cold_access, stipend + 1)

    if out_of_gas_at == OutOfGasAt.EIP_2200_STIPEND:
        # gas_left == stipend: fails the sentry check outright.
        tx_gas_limit = intrinsic_gas_cost + push_cost + stipend
    elif out_of_gas_at == OutOfGasAt.EIP_2200_STIPEND_PLUS_1:
        # gas_left == stipend + 1: clears the stipend sentry by one;
        # whether the access is then affordable depends on the schedule.
        tx_gas_limit = intrinsic_gas_cost + push_cost + stipend + 1
    elif out_of_gas_at == OutOfGasAt.ABOVE_STIPEND_BELOW_ACCESS:
        # gas_left == access cost - 1: cannot afford the access (when
        # the stipend dominates, the sentry fires first instead), so
        # OOG before the read either way.
        tx_gas_limit = intrinsic_gas_cost + push_cost + cold_access - 1
    elif out_of_gas_at == OutOfGasAt.ACCESS_COVERED_OOG_ON_WRITE:
        # gas_left == read gate: sentry cleared and access affordable
        # (read recorded), then OOG on the write cost.
        tx_gas_limit = intrinsic_gas_cost + push_cost + read_gate
    elif out_of_gas_at == OutOfGasAt.EXACT_GAS_MINUS_1:
        # fail at the final charge at exact gas - 1 (boundary condition).
        tx_gas_limit = intrinsic_gas_cost + full_cost - 1
    else:
        # exact gas for successful SSTORE
        tx_gas_limit = intrinsic_gas_cost + full_cost

    tx = Transaction(
        sender=alice,
        to=storage_contract,
        gas_limit=tx_gas_limit,
    )

    # The read is recorded only once the recording gate is covered: the
    # frame reaches the implicit SLOAD before any later OOG.
    expect_storage_read = out_of_gas_at in (
        OutOfGasAt.ACCESS_COVERED_OOG_ON_WRITE,
        OutOfGasAt.EXACT_GAS_MINUS_1,
    ) or (
        out_of_gas_at == OutOfGasAt.EIP_2200_STIPEND_PLUS_1
        and stipend + 1 >= cold_access
    )
    expect_storage_write = out_of_gas_at is None

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                storage_contract: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        ),
                    ]
                    if expect_storage_write
                    else [],
                    storage_reads=[0x01] if expect_storage_read else [],
                )
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            storage_contract: Account(
                storage={0x01: 0x42} if expect_storage_write else {}
            ),
        },
    )


@pytest.mark.parametrize(
    "fails_at_sload",
    [True, False],
    ids=["oog_at_sload", "successful_sload"],
)
def test_bal_sload_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    fails_at_sload: bool,
) -> None:
    """
    Ensure BAL handles SLOAD and OOG during SLOAD appropriately.
    """
    alice = pre.fund_eoa()

    # Create contract that attempts SLOAD from cold storage slot 0x01
    storage_contract_code = (
        Op.PUSH1(0x01)  # Storage slot (cold)
        + Op.SLOAD(key_warm=False)  # Load value from slot - this will OOG
        + Op.STOP
    )

    storage_contract = pre.deploy_contract(code=storage_contract_code)

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()()

    tx_gas_limit = intrinsic_gas_cost + storage_contract_code.gas_cost(fork)

    if fails_at_sload:
        # subtract 1 gas to ensure OOG at SLOAD
        tx_gas_limit -= 1

    tx = Transaction(
        sender=alice,
        to=storage_contract,
        gas_limit=tx_gas_limit,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                storage_contract: BalAccountExpectation(
                    storage_reads=[] if fails_at_sload else [0x01],
                )
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            storage_contract: Account(storage={}),
        },
    )


@pytest.mark.parametrize(
    "fails_at_balance",
    [True, False],
    ids=["oog_at_balance", "successful_balance"],
)
def test_bal_balance_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    fails_at_balance: bool,
) -> None:
    """Ensure BAL handles BALANCE and OOG during BALANCE appropriately."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    # Create contract that attempts to check Bob's balance
    balance_checker_code = (
        Op.PUSH20(bob)  # Bob's address
        + Op.BALANCE(address_warm=False)  # Check balance (cold access)
        + Op.STOP
    )

    balance_checker = pre.deploy_contract(code=balance_checker_code)

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()()

    tx_gas_limit = intrinsic_gas_cost + balance_checker_code.gas_cost(fork)

    if fails_at_balance:
        # subtract 1 gas to ensure OOG at BALANCE
        tx_gas_limit -= 1

    tx = Transaction(
        sender=alice,
        to=balance_checker,
        gas_limit=tx_gas_limit,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                balance_checker: BalAccountExpectation.empty(),
                # Bob should only appear in BAL if BALANCE succeeded
                **(
                    {bob: None}
                    if fails_at_balance
                    else {bob: BalAccountExpectation.empty()}
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(),
            balance_checker: Account(),
        },
    )


@pytest.mark.parametrize(
    "access_opcode",
    [
        pytest.param(lambda target: Op.BALANCE(target), id="balance"),
        pytest.param(lambda target: Op.EXTCODESIZE(target), id="extcodesize"),
        pytest.param(lambda target: Op.EXTCODEHASH(target), id="extcodehash"),
        pytest.param(
            lambda target: Op.EXTCODECOPY(target, 0, 0, 0),
            id="extcodecopy",
        ),
        pytest.param(lambda target: Op.CALL(address=target), id="call"),
        pytest.param(
            lambda target: Op.STATICCALL(address=target),
            id="staticcall",
        ),
    ],
)
def test_bal_account_touch_system_address(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    access_opcode: Callable[[Address], Bytecode],
) -> None:
    """
    Ensure a normal transaction that explicitly touches SYSTEM_ADDRESS via
    an account-accessing opcode includes SYSTEM_ADDRESS as an account-only
    BAL entry.

    This confirms that SYSTEM_ADDRESS is only excluded from the BAL when it
    appears as the synthetic caller of a pre-execution system call; a real
    EVM state access from user code MUST still land in the BAL.
    """
    alice = pre.fund_eoa()
    pre.fund_address(SYSTEM_ADDRESS, amount=1)

    toucher = pre.deploy_contract(code=access_opcode(SYSTEM_ADDRESS) + Op.STOP)

    tx = Transaction(sender=alice, to=toucher)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                toucher: BalAccountExpectation.empty(),
                SYSTEM_ADDRESS: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            toucher: Account(),
            SYSTEM_ADDRESS: Account(balance=1),
        },
    )


def test_bal_selfdestruct_to_system_address_zero_balance(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure `SYSTEM_ADDRESS` is in BAL when accessed via `SELFDESTRUCT`,
    even with zero balance transferred. Companion to
    `test_bal_account_touch_system_address`, which covers the
    `BALANCE`/`EXTCODE*`/`CALL`/`STATICCALL` opcodes.
    """
    alice = pre.fund_eoa()

    init_code = Op.SELFDESTRUCT(SYSTEM_ADDRESS)
    new_contract = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,  # CREATE
        value=0,  # zero contract balance at SELFDESTRUCT time
        data=init_code,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                    ],
                ),
                SYSTEM_ADDRESS: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            new_contract: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "fails_at_extcodesize",
    [True, False],
    ids=["oog_at_extcodesize", "successful_extcodesize"],
)
def test_bal_extcodesize_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    fails_at_extcodesize: bool,
) -> None:
    """
    Ensure BAL handles EXTCODESIZE and OOG during EXTCODESIZE appropriately.
    """
    alice = pre.fund_eoa()

    # Create target contract with some code
    target_contract = pre.deploy_contract(code=Op.STOP)

    # Create contract that checks target's code size
    codesize_checker_code = (
        Op.PUSH20(target_contract)  # Target contract address
        + Op.EXTCODESIZE(address_warm=False)  # Check code size (cold access)
        + Op.STOP
    )

    codesize_checker = pre.deploy_contract(code=codesize_checker_code)

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()()

    tx_gas_limit = intrinsic_gas_cost + codesize_checker_code.gas_cost(fork)
    if fails_at_extcodesize:
        # subtract 1 gas to ensure OOG at EXTCODESIZE
        tx_gas_limit -= 1

    tx = Transaction(
        sender=alice,
        to=codesize_checker,
        gas_limit=tx_gas_limit,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                codesize_checker: BalAccountExpectation.empty(),
                # Target should only appear if EXTCODESIZE succeeded
                **(
                    {target_contract: None}
                    if fails_at_extcodesize
                    else {target_contract: BalAccountExpectation.empty()}
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            codesize_checker: Account(),
            target_contract: Account(),
        },
    )


@pytest.mark.parametrize(
    "oog_boundary",
    [OutOfGasBoundary.SUCCESS, OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS],
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "target_is_empty", [False, True], ids=["existing_target", "empty_target"]
)
@pytest.mark.parametrize("value", [0, 1], ids=["no_value", "with_value"])
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_call_no_delegation_and_oog_before_target_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    target_is_empty: bool,
    value: int,
    args_size: int,
    ret_size: int,
) -> None:
    """
    CALL without 7702 delegation - test SUCCESS and OOG before target access.

    When target_is_warm=True, we use EIP-2930 tx access list to warm the
    target. Access list warming does NOT add to BAL - only EVM access does.

    Memory expansion is parametrized independently for args (insize) and
    ret (outsize) per #1910, surfacing client-impl asymmetry bugs in the
    memory-cost calculator.
    """
    alice = pre.fund_eoa()

    target = (
        pre.nonexistent_account()
        if target_is_empty
        else pre.deploy_contract(code=Op.STOP)
    )

    new_memory_size = max(args_size, ret_size)

    # Full gas metadata: includes create_cost when applicable
    call_code = Op.CALL(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=value > 0,
        account_new=value > 0 and target_is_empty,
        new_memory_size=new_memory_size,
    )
    caller = pre.deploy_contract(code=call_code, balance=value)

    access_list = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # Static gas (before state access): no create_cost
        call_static = Op.CALL(
            gas=0,
            address=target,
            value=value,
            args_size=args_size,
            args_offset=0,
            ret_size=ret_size,
            ret_offset=0,
            address_warm=target_is_warm,
            value_transfer=value > 0,
            account_new=False,
            new_memory_size=new_memory_size,
        )
        gas_limit = intrinsic_cost + call_static.gas_cost(fork) - 1
    else:  # SUCCESS
        gas_limit = intrinsic_cost + call_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # BAL expectations
    account_expectations: Dict[Address, BalAccountExpectation | None]
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # Target NOT in BAL - we OOG before state access
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: None,
        }
    elif value > 0:
        account_expectations = {
            caller: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=0)
                ]
            ),
            target: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=value)
                ]
            ),
        }
    else:
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: BalAccountExpectation.empty(),
        }

    value_transferred = value > 0 and oog_boundary == OutOfGasBoundary.SUCCESS

    post_state: Dict[Address, Account | None] = {alice: Account(nonce=1)}

    if value_transferred:
        post_state[target] = Account(balance=value)
        post_state[caller] = Account(balance=0)
    else:
        post_state[caller] = Account(balance=value)
        post_state[target] = (
            Account.NONEXISTENT
            if target_is_empty
            else Account(balance=0, code=Op.STOP)
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post_state,
    )


@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
@pytest.mark.eels_base_coverage
def test_bal_call_no_delegation_oog_after_target_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    target_is_warm: bool,
    args_size: int,
    ret_size: int,
) -> None:
    """
    CALL without 7702 delegation - OOG after state access.

    When target_is_warm=True, uses EIP-2930 tx access list to warm the target.
    Access list warming does NOT add targets to BAL - only EVM access does.

    This test is only meaningful when there's a gap between gas check before
    state access and after state access. This only happens if create cost
    (empty target) and value transfer cost are both non-zero.

    Note:
        - target is always empty - required for create cost
        - value=1 (greater than 0) - required for create cost

    The create_cost (NEW_ACCOUNT = 25000) is charged only for value
    transfers to empty accounts, creating the gap tested here.

    Memory expansion is parametrized independently for args (insize) and
    ret (outsize) per #1910.

    """
    alice = pre.fund_eoa()

    # empty target required for create_cost gap
    target = pre.nonexistent_account()
    # value > 0 required for create_cost
    value = 1

    new_memory_size = max(args_size, ret_size)

    # Static gas (before state access): no create_cost
    # Pass static check, fail at second check due to create cost
    call_code = Op.CALL(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=True,
        account_new=False,
        new_memory_size=new_memory_size,
    )
    caller = pre.deploy_contract(code=call_code, balance=value)

    # Access list for warming target (if needed)
    access_list = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    gas_limit = intrinsic_cost + call_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # Target is always in BAL after state access but value transfer fails
    # (no balance changes)
    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        caller: BalAccountExpectation.empty(),
        target: BalAccountExpectation.empty(),
    }

    post_state = {
        alice: Account(nonce=1),
        caller: Account(balance=value),
        target: Account.NONEXISTENT,
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post_state,
    )


@pytest.mark.parametrize(
    "oog_boundary",
    list(OutOfGasBoundary),
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "delegation_is_warm",
    [False, True],
    ids=["cold_delegation", "warm_delegation"],
)
@pytest.mark.parametrize("value", [0, 1], ids=["no_value", "with_value"])
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_call_7702_delegation_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    delegation_is_warm: bool,
    value: int,
    args_size: int,
    ret_size: int,
) -> None:
    """
    CALL with 7702 delegation - test all OOG boundaries.

    When target_is_warm or delegation_is_warm, we use EIP-2930 tx access list.
    Access list warming does NOT add targets to BAL - only EVM access does.

    Memory expansion is parametrized independently for args and ret per #1910.
    """
    alice = pre.fund_eoa()

    delegation_target = pre.deploy_contract(code=Op.STOP)
    target = pre.fund_eoa(amount=0, delegation=delegation_target)

    new_memory_size = max(args_size, ret_size)

    # Full gas metadata: includes delegation cost
    call_code = Op.CALL(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=value > 0,
        account_new=False,
        new_memory_size=new_memory_size,
        delegated_address=True,
        delegated_address_warm=delegation_is_warm,
    )
    caller = pre.deploy_contract(code=call_code, balance=value)

    # Build access list for warming
    access_list: list[AccessList] = []
    if target_is_warm:
        access_list.append(AccessList(address=target, storage_keys=[]))
    if delegation_is_warm:
        access_list.append(
            AccessList(address=delegation_target, storage_keys=[])
        )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    # Static gas (before state access): no delegation
    call_static = Op.CALL(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=value > 0,
        account_new=False,
        new_memory_size=new_memory_size,
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + call_static.gas_cost(fork) - 1
    elif oog_boundary == OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS:
        # Enough for static_gas only - not enough for delegation_cost
        gas_limit = intrinsic_cost + call_static.gas_cost(fork)
    elif oog_boundary == OutOfGasBoundary.OOG_SUCCESS_MINUS_1:
        # One less than full cost - not enough for full call
        gas_limit = intrinsic_cost + call_code.gas_cost(fork) - 1
    else:
        gas_limit = intrinsic_cost + call_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # Access list warming does NOT add to BAL - only EVM execution does
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        target_in_bal = False
        delegation_in_bal = False
    elif oog_boundary in (
        OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS,
        OutOfGasBoundary.OOG_SUCCESS_MINUS_1,
    ):
        # Both cases: target accessed but not enough gas for full call
        # so delegation is NOT read (static check optimization)
        target_in_bal = True
        delegation_in_bal = False
    else:
        target_in_bal = True
        delegation_in_bal = True

    value_transferred = value > 0 and oog_boundary == OutOfGasBoundary.SUCCESS

    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        caller: (
            BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=0)
                ]
            )
            if value_transferred
            else BalAccountExpectation.empty()
        ),
        delegation_target: (
            BalAccountExpectation.empty() if delegation_in_bal else None
        ),
    }

    if target_in_bal:
        if value_transferred:
            account_expectations[target] = BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=value)
                ]
            )
        else:
            account_expectations[target] = BalAccountExpectation.empty()
    else:
        account_expectations[target] = None

    # Post-state balance checks verify value transfer only happened on success
    post_state: Dict[Address, Account] = {alice: Account(nonce=1)}
    if value > 0:
        post_state[target] = Account(balance=value if value_transferred else 0)
        post_state[caller] = Account(balance=0 if value_transferred else value)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post_state,
    )


@pytest.mark.parametrize(
    "oog_boundary",
    [OutOfGasBoundary.SUCCESS, OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS],
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_delegatecall_no_delegation_and_oog_before_target_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    args_size: int,
    ret_size: int,
) -> None:
    """
    DELEGATECALL without 7702 delegation - test SUCCESS and OOG boundaries.

    When target_is_warm=True, we use EIP-2930 tx access list to warm the
    target. Access list warming does NOT add to BAL - only EVM access does.

    Memory expansion is parametrized independently for args and ret per #1910.
    """
    alice = pre.fund_eoa()

    target = pre.deploy_contract(code=Op.STOP)

    new_memory_size = max(args_size, ret_size)

    delegatecall_code = Op.DELEGATECALL(
        address=target,
        gas=0,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        new_memory_size=new_memory_size,
    )

    caller = pre.deploy_contract(code=delegatecall_code)

    access_list = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + delegatecall_code.gas_cost(fork) - 1
    else:  # SUCCESS
        gas_limit = intrinsic_cost + delegatecall_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # BAL expectations
    account_expectations: Dict[Address, BalAccountExpectation | None]
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # Target NOT in BAL - we OOG before state access
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: None,
        }
    else:  # SUCCESS - target in BAL
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: BalAccountExpectation.empty(),
        }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={alice: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "oog_boundary",
    list(OutOfGasBoundary),
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "delegation_is_warm",
    [False, True],
    ids=["cold_delegation", "warm_delegation"],
)
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_delegatecall_7702_delegation_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    delegation_is_warm: bool,
    args_size: int,
    ret_size: int,
) -> None:
    """
    DELEGATECALL with 7702 delegation - test all OOG boundaries.

    When target_is_warm or delegation_is_warm, we use EIP-2930 tx access list.
    Access list warming does NOT add targets to BAL - only EVM access does.

    For 7702 delegation, there's ALWAYS a gap between static gas and
    second check (delegation_cost) - all 3 scenarios produce distinct
    behaviors.

    Memory expansion is parametrized independently for args and ret per #1910.
    """
    alice = pre.fund_eoa()

    delegation_target = pre.deploy_contract(code=Op.STOP)
    target = pre.fund_eoa(amount=0, delegation=delegation_target)

    new_memory_size = max(args_size, ret_size)

    # Full gas metadata: includes delegation cost
    delegatecall_code = Op.DELEGATECALL(
        gas=0,
        address=target,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        new_memory_size=new_memory_size,
        delegated_address=True,
        delegated_address_warm=delegation_is_warm,
    )

    caller = pre.deploy_contract(code=delegatecall_code)

    # Build access list for warming
    access_list: list[AccessList] = []
    if target_is_warm:
        access_list.append(AccessList(address=target, storage_keys=[]))
    if delegation_is_warm:
        access_list.append(
            AccessList(address=delegation_target, storage_keys=[])
        )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    # Static gas (before state access): no delegation
    delegatecall_static = Op.DELEGATECALL(
        gas=0,
        address=target,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        new_memory_size=new_memory_size,
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + delegatecall_static.gas_cost(fork) - 1
    elif oog_boundary == OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS:
        # Enough for static_gas only - not enough for delegation_cost
        gas_limit = intrinsic_cost + delegatecall_static.gas_cost(fork)
    elif oog_boundary == OutOfGasBoundary.OOG_SUCCESS_MINUS_1:
        # One less than full cost - not enough for full call
        gas_limit = intrinsic_cost + delegatecall_code.gas_cost(fork) - 1
    else:
        gas_limit = intrinsic_cost + delegatecall_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # Access list warming does NOT add to BAL - only EVM execution does
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        target_in_bal = False
        delegation_in_bal = False
    elif oog_boundary in (
        OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS,
        OutOfGasBoundary.OOG_SUCCESS_MINUS_1,
    ):
        # Both cases: target accessed but not enough gas for full call
        # so delegation is NOT read (static check optimization)
        target_in_bal = True
        delegation_in_bal = False
    else:
        target_in_bal = True
        delegation_in_bal = True

    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        caller: BalAccountExpectation.empty(),
        delegation_target: (
            BalAccountExpectation.empty() if delegation_in_bal else None
        ),
    }

    if target_in_bal:
        account_expectations[target] = BalAccountExpectation.empty()
    else:
        account_expectations[target] = None

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={alice: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "oog_boundary",
    [OutOfGasBoundary.SUCCESS, OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS],
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize("value", [0, 1], ids=["no_value", "with_value"])
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_callcode_no_delegation_and_oog_before_target_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    value: int,
    args_size: int,
    ret_size: int,
) -> None:
    """
    CALLCODE without 7702 delegation - test SUCCESS and OOG boundaries.

    When target_is_warm=True, we use EIP-2930 tx access list to warm the
    target. Access list warming does NOT add to BAL - only EVM access does.
    CALLCODE has no balance transfer to target (runs in caller's context).

    Memory expansion is parametrized independently for args and ret per #1910.
    """
    alice = pre.fund_eoa()

    target = pre.deploy_contract(code=Op.STOP)

    new_memory_size = max(args_size, ret_size)

    callcode_code = Op.CALLCODE(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=value > 0,
        account_new=False,
        new_memory_size=new_memory_size,
    )
    caller = pre.deploy_contract(code=callcode_code, balance=value)

    access_list = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + callcode_code.gas_cost(fork) - 1
    else:  # SUCCESS
        gas_limit = intrinsic_cost + callcode_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # BAL expectations
    account_expectations: Dict[Address, BalAccountExpectation | None]
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # Target NOT in BAL - we OOG before state access
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: None,
        }
    else:  # SUCCESS - target in BAL (no balance changes, CALLCODE no transfer)
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: BalAccountExpectation.empty(),
        }

    # Post-state: CALLCODE runs in caller's context, so value transfer is
    # caller-to-caller (net-zero). Caller keeps its balance regardless.
    post_state: Dict[Address, Account] = {
        alice: Account(nonce=1),
        caller: Account(balance=value),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post_state,
    )


@pytest.mark.parametrize(
    "oog_boundary",
    list(OutOfGasBoundary),
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "delegation_is_warm",
    [False, True],
    ids=["cold_delegation", "warm_delegation"],
)
@pytest.mark.parametrize("value", [0, 1], ids=["no_value", "with_value"])
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_callcode_7702_delegation_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    delegation_is_warm: bool,
    value: int,
    args_size: int,
    ret_size: int,
) -> None:
    """
    CALLCODE with 7702 delegation - test all OOG boundaries.

    When target_is_warm or delegation_is_warm, we use EIP-2930 tx access list.
    Access list warming does NOT add targets to BAL - only EVM access does.

    For 7702 delegation, there's ALWAYS a gap between static gas and
    second check (delegation_cost) - all 3 scenarios produce distinct
    behaviors.

    Memory expansion is parametrized independently for args and ret per #1910.
    """
    alice = pre.fund_eoa()

    delegation_target = pre.deploy_contract(code=Op.STOP)
    target = pre.fund_eoa(amount=0, delegation=delegation_target)

    new_memory_size = max(args_size, ret_size)

    # Full gas metadata: includes delegation cost
    callcode_code = Op.CALLCODE(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=value > 0,
        account_new=False,
        new_memory_size=new_memory_size,
        delegated_address=True,
        delegated_address_warm=delegation_is_warm,
    )
    caller = pre.deploy_contract(code=callcode_code, balance=value)

    # Build access list for warming
    access_list: list[AccessList] = []
    if target_is_warm:
        access_list.append(AccessList(address=target, storage_keys=[]))
    if delegation_is_warm:
        access_list.append(
            AccessList(address=delegation_target, storage_keys=[])
        )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    # Static gas (before state access): no delegation
    callcode_static = Op.CALLCODE(
        gas=0,
        address=target,
        value=value,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        value_transfer=value > 0,
        account_new=False,
        new_memory_size=new_memory_size,
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + callcode_static.gas_cost(fork) - 1
    elif oog_boundary == OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS:
        # Enough for static_gas only - not enough for delegation_cost
        gas_limit = intrinsic_cost + callcode_static.gas_cost(fork)
    elif oog_boundary == OutOfGasBoundary.OOG_SUCCESS_MINUS_1:
        # One less than full cost - not enough for full call
        gas_limit = intrinsic_cost + callcode_code.gas_cost(fork) - 1
    else:
        gas_limit = intrinsic_cost + callcode_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # Access list warming does NOT add to BAL - only EVM execution does
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        target_in_bal = False
        delegation_in_bal = False
    elif oog_boundary in (
        OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS,
        OutOfGasBoundary.OOG_SUCCESS_MINUS_1,
    ):
        # Both cases: target accessed but not enough gas for full call
        # so delegation is NOT read (static check optimization)
        target_in_bal = True
        delegation_in_bal = False
    else:
        target_in_bal = True
        delegation_in_bal = True

    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        caller: BalAccountExpectation.empty(),
        delegation_target: (
            BalAccountExpectation.empty() if delegation_in_bal else None
        ),
    }

    if target_in_bal:
        account_expectations[target] = BalAccountExpectation.empty()
    else:
        account_expectations[target] = None

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={alice: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "oog_boundary",
    [OutOfGasBoundary.SUCCESS, OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS],
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_staticcall_no_delegation_and_oog_before_target_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    args_size: int,
    ret_size: int,
) -> None:
    """
    STATICCALL without 7702 delegation - test SUCCESS and OOG boundaries.

    When target_is_warm=True, we use EIP-2930 tx access list to warm the
    target. Access list warming does NOT add to BAL - only EVM access does.
    """
    alice = pre.fund_eoa()

    target = pre.deploy_contract(code=Op.STOP)

    new_memory_size = max(args_size, ret_size)

    staticcall_code = Op.STATICCALL(
        address=target,
        gas=0,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        new_memory_size=new_memory_size,
    )

    caller = pre.deploy_contract(code=staticcall_code)

    access_list = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + staticcall_code.gas_cost(fork) - 1
    else:  # SUCCESS
        gas_limit = intrinsic_cost + staticcall_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # BAL expectations
    account_expectations: Dict[Address, BalAccountExpectation | None]
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # Target NOT in BAL - we OOG before state access
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: None,
        }
    else:  # SUCCESS - target in BAL
        account_expectations = {
            caller: BalAccountExpectation.empty(),
            target: BalAccountExpectation.empty(),
        }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={alice: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "oog_boundary",
    list(OutOfGasBoundary),
    ids=lambda x: x.value,
)
@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "delegation_is_warm",
    [False, True],
    ids=["cold_delegation", "warm_delegation"],
)
@pytest.mark.parametrize(
    "args_size,ret_size",
    [
        pytest.param(0, 0, id="no_memory"),
        pytest.param(4096, 0, id="args_large"),
        pytest.param(0, 4096, id="ret_large"),
        pytest.param(32, 32, id="both_small"),
    ],
)
def test_bal_staticcall_7702_delegation_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_boundary: OutOfGasBoundary,
    target_is_warm: bool,
    delegation_is_warm: bool,
    args_size: int,
    ret_size: int,
) -> None:
    """
    STATICCALL with 7702 delegation - test all OOG boundaries.

    When target_is_warm or delegation_is_warm, we use EIP-2930 tx access list.
    Access list warming does NOT add targets to BAL - only EVM access does.

    For 7702 delegation, there's ALWAYS a gap between static gas and
    second check (delegation_cost) - all 3 scenarios produce distinct
    behaviors.
    """
    alice = pre.fund_eoa()

    delegation_target = pre.deploy_contract(code=Op.STOP)
    target = pre.fund_eoa(amount=0, delegation=delegation_target)

    new_memory_size = max(args_size, ret_size)

    staticcall_code = Op.STATICCALL(
        gas=0,
        address=target,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        new_memory_size=new_memory_size,
        delegated_address=True,
        delegated_address_warm=delegation_is_warm,
    )

    caller = pre.deploy_contract(code=staticcall_code)

    access_list: list[AccessList] = []
    if target_is_warm:
        access_list.append(AccessList(address=target, storage_keys=[]))
    if delegation_is_warm:
        access_list.append(
            AccessList(address=delegation_target, storage_keys=[])
        )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    staticcall_static = Op.STATICCALL(
        gas=0,
        address=target,
        args_size=args_size,
        args_offset=0,
        ret_size=ret_size,
        ret_offset=0,
        address_warm=target_is_warm,
        new_memory_size=new_memory_size,
    )

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        gas_limit = intrinsic_cost + staticcall_static.gas_cost(fork) - 1
    elif oog_boundary == OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS:
        # Enough for static_gas only - not enough for delegation_cost
        gas_limit = intrinsic_cost + staticcall_static.gas_cost(fork)
    elif oog_boundary == OutOfGasBoundary.OOG_SUCCESS_MINUS_1:
        # One less than full cost - not enough for full call
        gas_limit = intrinsic_cost + staticcall_code.gas_cost(fork) - 1
    else:
        gas_limit = intrinsic_cost + staticcall_code.gas_cost(fork)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    # Access list warming does NOT add to BAL - only EVM execution does
    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        target_in_bal = False
        delegation_in_bal = False
    elif oog_boundary in (
        OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS,
        OutOfGasBoundary.OOG_SUCCESS_MINUS_1,
    ):
        # Both cases: target accessed but not enough gas for full call
        # so delegation is NOT read (static check optimization)
        target_in_bal = True
        delegation_in_bal = False
    else:
        target_in_bal = True
        delegation_in_bal = True

    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        caller: BalAccountExpectation.empty(),
        delegation_target: (
            BalAccountExpectation.empty() if delegation_in_bal else None
        ),
    }

    if target_in_bal:
        account_expectations[target] = BalAccountExpectation.empty()
    else:
        account_expectations[target] = None

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={alice: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "oog_scenario,memory_offset,copy_size",
    [
        pytest.param("success", 0, 0, id="successful_extcodecopy"),
        pytest.param("oog_at_cold_access", 0, 0, id="oog_at_cold_access"),
        pytest.param(
            "oog_at_memory_large_offset",
            0x10000,
            32,
            id="oog_at_memory_large_offset",
        ),
        pytest.param(
            "oog_at_memory_boundary",
            256,
            32,
            id="oog_at_memory_boundary",
        ),
    ],
)
def test_bal_extcodecopy_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    oog_scenario: str,
    memory_offset: int,
    copy_size: int,
) -> None:
    """
    Ensure BAL handles EXTCODECOPY and OOG during EXTCODECOPY appropriately.

    Tests various OOG scenarios:
    - success: EXTCODECOPY completes, target appears in BAL
    - oog_at_cold_access: OOG before cold access, target NOT in BAL
    - oog_at_memory_large_offset: OOG at memory expansion (large offset),
      target NOT in BAL
    - oog_at_memory_boundary: OOG at memory expansion (boundary case),
      target NOT in BAL

    Gas for all components (cold access + copy + memory expansion) must be
    checked BEFORE recording account access.
    """
    alice = pre.fund_eoa()

    # Create target contract with some code
    target_contract = pre.deploy_contract(code=Op.PUSH1(0x42) + Op.STOP)

    # Full EXTCODECOPY: access + copy + memory expansion
    extcodecopy_code = Op.EXTCODECOPY(
        address=target_contract,
        dest_offset=memory_offset,
        offset=0,
        size=copy_size,
        address_warm=False,
        data_size=copy_size,
        new_memory_size=memory_offset + copy_size,
    )

    extcodecopy_contract = pre.deploy_contract(code=extcodecopy_code + Op.STOP)

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()()

    if oog_scenario == "success":
        # Provide enough gas for everything including memory expansion
        tx_gas_limit = intrinsic_gas_cost + extcodecopy_code.gas_cost(fork)
        target_in_bal = True
    elif oog_scenario == "oog_at_cold_access":
        # Provide gas for pushes but 1 less than cold access
        extcodecopy_access_only = Op.EXTCODECOPY(
            address=target_contract,
            dest_offset=memory_offset,
            offset=0,
            size=copy_size,
            address_warm=False,
            data_size=0,
            new_memory_size=0,
        )
        tx_gas_limit = (
            intrinsic_gas_cost + extcodecopy_access_only.gas_cost(fork) - 1
        )
        target_in_bal = False
    elif oog_scenario == "oog_at_memory_large_offset":
        # Provide gas for push + cold access + copy, but NOT memory expansion
        extcodecopy_no_mem = Op.EXTCODECOPY(
            address=target_contract,
            dest_offset=memory_offset,
            offset=0,
            size=copy_size,
            address_warm=False,
            data_size=copy_size,
            new_memory_size=0,
        )
        tx_gas_limit = intrinsic_gas_cost + extcodecopy_no_mem.gas_cost(fork)
        target_in_bal = False
    elif oog_scenario == "oog_at_memory_boundary":
        # Calculate full cost and provide exactly 1 less than needed
        tx_gas_limit = intrinsic_gas_cost + extcodecopy_code.gas_cost(fork) - 1
        target_in_bal = False
    else:
        raise ValueError(f"Invariant: unknown oog_scenario {oog_scenario}")

    tx = Transaction(
        sender=alice,
        to=extcodecopy_contract,
        gas_limit=tx_gas_limit,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                extcodecopy_contract: BalAccountExpectation.empty(),
                **(
                    {target_contract: BalAccountExpectation.empty()}
                    if target_in_bal
                    else {target_contract: None}
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            extcodecopy_contract: Account(),
            target_contract: Account(),
        },
    )


def test_bal_storage_write_read_same_frame(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures write precedence over read in same call frame.

    Oracle writes to slot 0x01, then reads from slot 0x01 in same call.
    The write shadows the read - only the write appears in BAL.
    """
    alice = pre.fund_eoa()

    oracle_code = (
        Op.SSTORE(0x01, 0x42)  # Write 0x42 to slot 0x01
        + Op.SLOAD(0x01)  # Read from slot 0x01
        + Op.STOP
    )
    oracle = pre.deploy_contract(code=oracle_code, storage={0x01: 0x99})

    tx = Transaction(sender=alice, to=oracle)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        )
                    ],
                    storage_reads=[],  # Empty! Write shadows the read
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            oracle: Account(storage={0x01: 0x42}),
        },
    )


@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(
            lambda target: Op.CALL(100_000, target, 0, 0, 0, 0, 0), id="call"
        ),
        pytest.param(
            lambda target: Op.DELEGATECALL(100_000, target, 0, 0, 0, 0),
            id="delegatecall",
        ),
        pytest.param(
            lambda target: Op.CALLCODE(100_000, target, 0, 0, 0, 0, 0),
            id="callcode",
        ),
    ],
)
def test_bal_storage_write_read_cross_frame(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    call_opcode: Callable[[Bytecode], Bytecode],
) -> None:
    """
    Ensure BAL captures write precedence over read across call frames.

    Frame 1: Read slot 0x01 (0x99), write 0x42, then call itself.
    Frame 2: Read slot 0x01 (0x42), see it's 0x42 and return.
    Both reads are shadowed by the write - only write appears in BAL.
    """
    alice = pre.fund_eoa()

    # Oracle code:
    # 1. Read slot 0x01 (initial: 0x99, recursive: 0x42)
    # 2. If value == 0x42, return (exit recursion)
    # 3. Write 0x42 to slot 0x01
    # 4. Call itself recursively
    oracle_code = (
        Op.SLOAD(0x01)  # Load value from slot 0x01
        + Op.PUSH1(0x42)  # Push 0x42 for comparison
        + Op.EQ  # Check if loaded value == 0x42
        + Op.PUSH1(0x1D)  # Jump destination (after SSTORE + CALL)
        + Op.JUMPI  # If equal, jump to end (exit recursion)
        + Op.PUSH1(0x42)  # Value to write
        + Op.PUSH1(0x01)  # Slot 0x01
        + Op.SSTORE  # Write 0x42 to slot 0x01
        + call_opcode(Op.ADDRESS)  # Call itself
        + Op.JUMPDEST  # Jump destination for exit
        + Op.STOP
    )

    oracle = pre.deploy_contract(code=oracle_code, storage={0x01: 0x99})

    tx = Transaction(sender=alice, to=oracle)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        )
                    ],
                    storage_reads=[],  # Empty! Write shadows both reads
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            oracle: Account(storage={0x01: 0x42}),
        },
    )


@pytest.mark.parametrize(
    "sufficient_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
def test_bal_create_oog_code_deposit(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    sufficient_gas: bool,
) -> None:
    """
    Ensure BAL correctly handles CREATE that runs out of gas during code
    deposit. The contract address should appear with empty changes (read
    during collision check) but no nonce or code changes (rolled back).
    """
    alice = pre.fund_eoa()

    # create init code that returns a very large contract to force OOG
    deposited_len = 10_000
    initcode = Op.RETURN(
        0,
        deposited_len,
        old_memory_size=0,
        new_memory_size=deposited_len,
        code_deposit_size=deposited_len,
    )

    create_code = Op.MSTORE(
        0,
        Op.PUSH32(bytes(initcode)),
        new_memory_size=len(initcode),
    ) + Op.CREATE(
        offset=32 - len(initcode),
        size=len(initcode),
        init_code_size=len(initcode),
    )
    return_code = Op.PUSH1[0] + Op.MSTORE + Op.RETURN(0, 32)
    factory_code = create_code + return_code

    factory = pre.deploy_contract(code=factory_code)

    contract_address = compute_create_address(address=factory, nonce=1)

    initcode_cost = initcode.gas_cost(fork)
    gas = (initcode_cost * 64 // 63) + create_code.gas_cost(fork)
    if not sufficient_gas:
        gas -= 1

    entry_code = Op.SSTORE(
        0, Op.CALL(gas=gas, address=factory, ret_size=32)
    ) + Op.SSTORE(1, Op.MLOAD(0))
    entry = pre.deploy_contract(
        entry_code, storage={0: 0xDEADBEEF, 1: 0xDEADBEEF}
    )

    tx = Transaction(
        sender=alice,
        to=entry,
        gas_limit=fork.transaction_gas_limit_cap(),  # No state reservoir
    )

    # BAL expectations:
    # - Alice: nonce change (tx sender)
    # - Factory: nonce change (CREATE increments factory nonce)
    # - Contract address: empty changes (read during collision check,
    #   nonce/code changes rolled back on OOG)
    if sufficient_gas:
        entry_storage_changes = [
            BalStorageSlot(
                slot=0,
                slot_changes=[
                    BalStorageChange(block_access_index=1, post_value=1),
                ],
            ),
            BalStorageSlot(
                slot=1,
                slot_changes=[
                    # SSTORE saves address (CREATE succeeded)
                    BalStorageChange(
                        block_access_index=1, post_value=contract_address
                    ),
                ],
            ),
        ]
    else:
        entry_storage_changes = [
            BalStorageSlot(
                slot=0,
                slot_changes=[
                    BalStorageChange(block_access_index=1, post_value=1),
                ],
            ),
            BalStorageSlot(
                slot=1,
                slot_changes=[
                    # SSTORE saves 0 (CREATE failed)
                    BalStorageChange(block_access_index=1, post_value=0),
                ],
            ),
        ]

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        factory: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
        ),
        entry: BalAccountExpectation(
            storage_changes=entry_storage_changes,
        ),
        contract_address: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        )
        if sufficient_gas
        else BalAccountExpectation.empty(),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            factory: Account(nonce=2),
            entry: Account(
                nonce=1,
                storage={0: 1, 1: contract_address if sufficient_gas else 0},
            ),
            contract_address: Account(nonce=1)
            if sufficient_gas
            else Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "original_value", [0, 0x42], ids=["zero_original", "nonzero_original"]
)
def test_bal_sstore_static_context(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    original_value: int,
) -> None:
    """
    SSTORE in static context must not leak storage reads into BAL.

    Contract A STATICCALLs Contract B which attempts SSTORE. Contract B
    IS in BAL (accessed via STATICCALL) but MUST NOT have storage_reads
    — the static check must fire before any implicit SLOAD.
    """
    alice = pre.fund_eoa()

    contract_b = pre.deploy_contract(
        code=Op.SSTORE(0, 5),
        storage={0: original_value} if original_value else {},
    )

    contract_a = pre.deploy_contract(
        code=Op.SSTORE(0, Op.STATICCALL(gas=1_000_000, address=contract_b))
        + Op.SSTORE(1, 1),  # proves execution continued
        storage={0: 0xDEAD},  # non-zero so STATICCALL result (0) is detectable
    )

    tx = Transaction(sender=alice, to=contract_a)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        contract_a: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x00,
                                    slot_changes=[
                                        # STATICCALL returns 0 (inner SSTORE
                                        # failed in static context)
                                        BalStorageChange(
                                            block_access_index=1, post_value=0
                                        ),
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x01,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1, post_value=1
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        # Contract B is in BAL (accessed via STATICCALL)
                        # but MUST NOT have any state touches
                        contract_b: BalAccountExpectation.empty(),
                    }
                ),
            )
        ],
        post={
            contract_a: Account(storage={0: 0, 1: 1}),
            contract_b: Account(
                storage={0: original_value} if original_value else {}
            ),
        },
    )


def blockchain_test_under_static_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    *,
    static_call_target: Address,
    bal_expectations: Dict[Address, BalAccountExpectation | None],
    post: Dict[Address, Account | None] | None = None,
    tx_access_list: list[AccessList] | None = None,
) -> None:
    """
    Run a blockchain_test that STATICCALLs static_call_target and
    verifies BAL expectations. Stores the STATICCALL result to detect
    silent failures.
    """
    alice = pre.fund_eoa()

    # Slot 0: STATICCALL result, pre-set to non-zero so writes are
    # detectable regardless of return value (0 or 1).
    static_caller = pre.deploy_contract(
        code=Op.SSTORE(
            0, Op.STATICCALL(gas=1_000_000, address=static_call_target)
        )
        + Op.SSTORE(1, 1),
        storage={0: 0xDEAD},
    )

    tx = Transaction(
        sender=alice, to=static_caller, access_list=tx_access_list
    )

    # Inner call fails (returns 0) when forbidden opcodes are tested
    # (None values in bal_expectations), succeeds (returns 1) otherwise.
    staticcall_result = (
        0 if any(v is None for v in bal_expectations.values()) else 1
    )

    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        static_caller: BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=0x00,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1,
                            post_value=staticcall_result,
                        ),
                    ],
                ),
                BalStorageSlot(
                    slot=0x01,
                    slot_changes=[
                        BalStorageChange(block_access_index=1, post_value=1),
                    ],
                ),
            ],
        ),
        static_call_target: BalAccountExpectation.empty(),
    }
    account_expectations.update(bal_expectations)

    _post: Dict[Address, Account | None] = {
        static_caller: Account(storage={0: staticcall_result, 1: 1}),
    }
    if post:
        _post.update(post)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=_post,
    )


@pytest.mark.parametrize(
    "target_is_warm", [False, True], ids=["cold_target", "warm_target"]
)
@pytest.mark.parametrize(
    "target_has_code", [False, True], ids=["eoa_target", "contract_target"]
)
def test_bal_call_with_value_in_static_context(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    target_is_warm: bool,
    target_has_code: bool,
) -> None:
    """
    CALL with nonzero value in static context: target NOT in BAL.

    Static check must fire before account access (warm/cold lookup,
    code loading).
    """
    target_starting_balance = 1022
    if target_has_code:
        target = pre.deploy_contract(
            code=Op.STOP, balance=target_starting_balance
        )
    else:
        target = pre.fund_eoa(amount=target_starting_balance)

    caller_starting_balance = 10**18
    caller = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=target, value=1) + Op.STOP,
        balance=caller_starting_balance,
    )

    access_list = (
        [AccessList(address=target, storage_keys=[])]
        if target_is_warm
        else None
    )

    blockchain_test_under_static_call(
        pre,
        blockchain_test,
        static_call_target=caller,
        bal_expectations={target: None},
        post={
            caller: Account(balance=caller_starting_balance),
            target: Account(balance=target_starting_balance),
        },
        tx_access_list=access_list,
    )


@pytest.mark.parametrize("value", [0, 1], ids=["no_value", "with_value"])
@pytest.mark.with_all_create_opcodes
def test_bal_create_in_static_context(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    create_opcode: Op,
    value: int,
) -> None:
    """
    CREATE/CREATE2 in static context: created address NOT in BAL.

    Static check must fire before balance check, address computation,
    or nonce increment.
    """
    init_code = Initcode(deploy_code=Op.STOP)
    init_code_bytes = bytes(init_code)

    caller = pre.deploy_contract(
        code=Op.MSTORE(0, Op.PUSH32(init_code_bytes))
        + create_opcode(
            value=value,
            offset=32 - len(init_code_bytes),
            size=len(init_code_bytes),
        )
        + Op.STOP,
        balance=value,
    )

    would_be_address = compute_create_address(
        address=caller,
        nonce=1,
        salt=0,
        initcode=init_code_bytes,
        opcode=create_opcode,
    )

    blockchain_test_under_static_call(
        pre,
        blockchain_test,
        static_call_target=caller,
        bal_expectations={would_be_address: None},
        post={
            caller: Account(nonce=1, balance=value),
            would_be_address: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "beneficiary_is_warm",
    [False, True],
    ids=["cold_beneficiary", "warm_beneficiary"],
)
@pytest.mark.parametrize(
    "caller_balance", [0, 100], ids=["no_balance", "with_balance"]
)
def test_bal_selfdestruct_in_static_context(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    beneficiary_is_warm: bool,
    caller_balance: int,
) -> None:
    """
    SELFDESTRUCT in static context: beneficiary NOT in BAL.

    Static check must fire before beneficiary access (warm/cold lookup)
    or balance transfer.
    """
    beneficiary_balance = 1
    beneficiary = pre.fund_eoa(amount=beneficiary_balance)
    caller = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=beneficiary),
        balance=caller_balance,
    )

    access_list = (
        [AccessList(address=beneficiary, storage_keys=[])]
        if beneficiary_is_warm
        else None
    )

    blockchain_test_under_static_call(
        pre,
        blockchain_test,
        static_call_target=caller,
        bal_expectations={beneficiary: None},
        post={
            caller: Account(balance=caller_balance),
            beneficiary: Account(balance=beneficiary_balance),
        },
        tx_access_list=access_list,
    )


@pytest.mark.with_all_call_opcodes
def test_bal_call_opcode_succeeds_in_static_context(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    call_opcode: Op,
) -> None:
    """
    All call opcodes (without value) succeed in static context.

    Target IS in BAL. Ensures clients don't over-restrict call opcodes
    beyond what EIP-214 forbids (only CALL with nonzero value).
    """
    target = pre.deploy_contract(code=Op.STOP)

    caller = pre.deploy_contract(
        code=call_opcode(address=target) + Op.STOP,
    )

    blockchain_test_under_static_call(
        pre,
        blockchain_test,
        static_call_target=caller,
        bal_expectations={
            target: BalAccountExpectation.empty(),
        },
    )


def test_bal_callcode_with_value_in_static_context(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    CALLCODE with nonzero value succeeds in static context.

    EIP-214 explicitly excludes CALLCODE from write-protection.
    """
    target = pre.deploy_contract(code=Op.STOP)

    caller = pre.deploy_contract(
        code=Op.CALLCODE(gas=100_000, address=target, value=1) + Op.STOP,
        balance=10**18,
    )

    blockchain_test_under_static_call(
        pre,
        blockchain_test,
        static_call_target=caller,
        bal_expectations={
            target: BalAccountExpectation.empty(),
        },
    )


def test_bal_create_contract_init_revert(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that BAL does not include nonce/code changes when CREATE happens
    in a call that then REVERTs.
    """
    alice = pre.fund_eoa(amount=10**18)

    # Simple init code that returns STOP as deployed code
    init_code_bytes = bytes(Op.RETURN(0, 1) + Op.STOP)

    # Factory that does CREATE then REVERTs
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, Op.PUSH32(init_code_bytes))
        + Op.POP(Op.CREATE(0, 32 - len(init_code_bytes), len(init_code_bytes)))
        + Op.REVERT(0, 0)
    )

    # A caller that CALLs factory to CREATE then REVERT
    caller = pre.deploy_contract(code=Op.CALL(address=factory))

    created_address = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=alice, to=caller)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        caller: BalAccountExpectation.empty(),
                        factory: BalAccountExpectation.empty(),
                        created_address: BalAccountExpectation.empty(),
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            caller: Account(nonce=1),
            factory: Account(nonce=1),
            created_address: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "delegated,target_is_warm,delegation_is_warm",
    [
        pytest.param(False, False, False, id="no_delegation-cold_target"),
        pytest.param(False, True, False, id="no_delegation-warm_target"),
        pytest.param(
            True, False, False, id="delegated-cold_target-cold_delegation"
        ),
        pytest.param(
            True, True, False, id="delegated-warm_target-cold_delegation"
        ),
        pytest.param(
            True, False, True, id="delegated-cold_target-warm_delegation"
        ),
        pytest.param(
            True, True, True, id="delegated-warm_target-warm_delegation"
        ),
    ],
)
@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode in (Op.CALL, Op.CALLCODE)
)
def test_bal_call_revert_insufficient_funds(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    call_opcode: Op,
    delegated: bool,
    target_is_warm: bool,
    delegation_is_warm: bool,
) -> None:
    """
    Test BAL with CALL/CALLCODE failure due to insufficient balance
    (not OOG), with and without 7702 delegation.

    Caller (balance=100): SLOAD(0x01) → call_opcode(target, value=1000)
    → SSTORE(0x02, result). The call fails because 1000 > 100. The
    failure happens after delegation resolution. Under EIP-8037 the
    call family reads the delegation target's code before the balance
    check fails, so both the target and the delegation target appear in
    the BAL. Pre-8037 forks defer that read, so only the target appears.

    Access-list warming does NOT add to BAL on its own — only EVM
    access does — so the BAL is identical across warm/cold variants.
    """
    alice = pre.fund_eoa()

    caller_balance = 100
    transfer_amount = 1000  # > caller_balance, transfer must fail
    target_balance = 1  # non-zero balance keeps non-delegated target non-empty

    delegation_target: Address | None = None
    if delegated:
        delegation_target = pre.deploy_contract(code=Op.STOP)
        target = pre.fund_eoa(
            amount=target_balance, delegation=delegation_target
        )
    else:
        target = pre.fund_eoa(amount=target_balance)

    caller_code = (
        Op.SLOAD(0x01)
        + Op.POP
        + call_opcode(100_000, target, transfer_amount, 0, 0, 0, 0)
        + Op.PUSH1(0x02)
        + Op.SSTORE
        + Op.STOP
    )

    caller = pre.deploy_contract(
        code=caller_code,
        balance=caller_balance,
        storage={0x02: 0xDEAD},  # non-zero so SSTORE(0) is a change
    )

    access_list: list[AccessList] = []
    if target_is_warm:
        access_list.append(AccessList(address=target, storage_keys=[]))
    if delegated and delegation_is_warm:
        assert delegation_target is not None
        access_list.append(
            AccessList(address=delegation_target, storage_keys=[])
        )

    tx = Transaction(sender=alice, to=caller, access_list=access_list)

    account_expectations: Dict[Address, BalAccountExpectation | None] = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        caller: BalAccountExpectation(
            storage_reads=[0x01],
            storage_changes=[
                BalStorageSlot(
                    slot=0x02,
                    slot_changes=[
                        BalStorageChange(block_access_index=1, post_value=0)
                    ],
                )
            ],
        ),
        # Target accessed before balance check fails.
        target: BalAccountExpectation.empty(),
    }

    if delegated:
        assert delegation_target is not None
        # Under EIP-8037 the call family reads the delegation target's
        # code before the balance check fails, so it appears in the
        # BAL. Pre-8037 forks defer that read and it stays out.
        # TODO: drop this fork split once #2473 (defer get_code into
        # generic_call) is consolidated into amsterdam.
        if fork.is_eip_enabled(8037):
            account_expectations[delegation_target] = (
                BalAccountExpectation.empty()
            )
        else:
            account_expectations[delegation_target] = None

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            caller: Account(
                balance=caller_balance,  # unchanged - transfer failed
                storage={0x02: 0},  # Failed call returned 0
            ),
            target: Account(balance=target_balance),  # unchanged
        },
    )


def test_bal_create_selfdestruct_to_self_with_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL with init code that CALLs Oracle, writes storage, then
    SELFDESTRUCTs to self.

    Factory CREATE2(endowment=100).
    Init: CALL(Oracle)→SSTORE(0x01)→SELFDESTRUCT(SELF).

    Expected BAL:
    - Factory: nonce_changes, balance_changes (loses 100)
    - Oracle: storage_changes slot 0x01
    - Created address: storage_reads [0x01] (aborted write→read),
      MUST NOT have nonce/code/storage/balance changes (ephemeral)
    """
    alice = pre.fund_eoa()
    factory_balance = 1000

    # Oracle contract that writes to slot 0x01 when called
    oracle_code = Op.SSTORE(0x01, 0x42) + Op.STOP
    oracle = pre.deploy_contract(code=oracle_code)

    endowment = 100

    # Init code that:
    # 1. Calls Oracle (which writes to its slot 0x01)
    # 2. Writes 0x42 to own slot 0x01
    # 3. Selfdestructs to self
    initcode_runtime = (
        Op.CALL(address=oracle)
        + Op.POP
        # Write to own storage slot 0x01
        + Op.SSTORE(0x01, 0x42)
        # SELFDESTRUCT to self (ADDRESS returns own address)
        + Op.SELFDESTRUCT(Op.ADDRESS)
    )
    init_code = Initcode(deploy_code=Op.STOP, initcode_prefix=initcode_runtime)
    init_code_bytes = bytes(init_code)
    init_code_size = len(init_code_bytes)

    # Factory code with embedded initcode (no template contract needed)
    # Structure: [execution code] [initcode bytes]
    # CODECOPY copies initcode from factory's own code to memory
    #
    # Two-pass approach: build with placeholder, measure, rebuild
    placeholder_offset = 0xFF  # Placeholder (same byte size as final value)
    factory_execution_template = (
        Op.CODECOPY(0, placeholder_offset, init_code_size)
        + Op.SSTORE(
            0x00,
            Op.CREATE2(
                value=endowment,
                offset=0,
                size=init_code_size,
                salt=0,
            ),
        )
        + Op.STOP
    )
    # Measure execution code size
    execution_code_size = len(bytes(factory_execution_template))

    # Rebuild with actual offset value
    factory_execution = (
        Op.CODECOPY(0, execution_code_size, init_code_size)
        + Op.SSTORE(
            0x00,
            Op.CREATE2(
                value=endowment,
                offset=0,
                size=init_code_size,
                salt=0,
            ),
        )
        + Op.STOP
    )
    # Combine execution code with embedded initcode
    factory_code = bytes(factory_execution) + init_code_bytes

    factory = pre.deploy_contract(code=factory_code, balance=factory_balance)

    # Calculate the CREATE2 target address
    created_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code_bytes,
        opcode=Op.CREATE2,
    )

    tx = Transaction(sender=alice, to=factory)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                factory: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                    # Balance changes: loses endowment (100)
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=factory_balance - endowment,
                        )
                    ],
                ),
                # Oracle: storage changes for slot 0x01
                oracle: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        )
                    ],
                ),
                # Created address: ephemeral (created and destroyed same tx)
                # - storage_reads for slot 0x01 (aborted write becomes read)
                # - NO nonce/code/storage changes
                # - Balance remains per eip-8246
                created_address: BalAccountExpectation(
                    storage_reads=[0x01],
                    storage_changes=[],
                    nonce_changes=[],
                    code_changes=[],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=endowment
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            factory: Account(nonce=2, balance=factory_balance - endowment),
            oracle: Account(storage={0x01: 0x42}),
            created_address: Account(
                balance=endowment, nonce=0, code=b"", storage={}
            ),
        },
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize(
    "modification",
    ["collision_only", "then_nonce_change", "then_storage_change"],
)
@pytest.mark.pre_alloc_mutable()
def test_bal_create_collision(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    create_opcode: Op,
    modification: str,
) -> None:
    """
    BAL with CREATE/CREATE2 collision against pre-existing contract X,
    optionally followed by a tx that modifies X via call (closes #2914
    nonce/storage axes). Balance axis is already covered by the suite's
    existing collision-then-value-transfer tests. The `code_changes`
    axis isn't reachable in forward order — see
    `test_bal_create2_deploy_then_collision`.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    # Storage-touching init: a client that wrongly runs init on the
    # collision leaks a slot-0 access into X's BAL.
    init_code = Initcode(
        deploy_code=Op.STOP,
        initcode_prefix=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)),
    )
    init_code_bytes = bytes(init_code)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(init_code_bytes))
        + Op.SSTORE(
            0x00,
            create_opcode(
                value=0,
                offset=32 - len(init_code_bytes),
                size=len(init_code_bytes),
            ),
        )
        + Op.STOP
    )
    factory = pre.deploy_contract(
        code=factory_code,
        storage={0x00: 0xDEAD},
    )

    collision_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code_bytes,
        opcode=create_opcode,
    )

    if modification == "collision_only":
        x_code: Bytecode = Op.STOP
    elif modification == "then_nonce_change":
        inner_init = Initcode(deploy_code=Op.STOP)
        x_code = (
            Op.MSTORE(0, Op.PUSH32(bytes(inner_init)))
            + Op.CREATE(0, 32 - len(inner_init), len(inner_init))
            + Op.STOP
        )
    elif modification == "then_storage_change":
        x_code = Op.SSTORE(0x01, 0xCAFE) + Op.STOP
    else:
        raise ValueError(f"unknown modification: {modification}")

    pre[collision_address] = Account(code=x_code, nonce=1)

    tx_gas_limit = fork.transaction_gas_limit_cap()
    txs = [Transaction(sender=alice, to=factory, gas_limit=tx_gas_limit)]

    account_expectations: dict = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        # Factory's nonce bumps even on failed CREATE/CREATE2; slot 0
        # records the failure return value (0).
        factory: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
            storage_changes=[
                BalStorageSlot(
                    slot=0x00,
                    slot_changes=[
                        BalStorageChange(block_access_index=1, post_value=0)
                    ],
                )
            ],
        ),
    }

    post: dict = {
        alice: Account(nonce=1),
        factory: Account(nonce=2, storage={0x00: 0}),
    }

    if modification == "collision_only":
        account_expectations[collision_address] = BalAccountExpectation.empty()
        post[collision_address] = Account(
            code=x_code, nonce=1, balance=0, storage={}
        )
    elif modification == "then_nonce_change":
        txs.append(
            Transaction(
                sender=bob, to=collision_address, gas_limit=tx_gas_limit
            )
        )
        account_expectations[bob] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=2, post_nonce=1)],
        )
        # Strict: only the inner-CREATE nonce bump appears; no spurious
        # code/storage/balance entries from the index-1 collision touch.
        account_expectations[collision_address] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=2, post_nonce=2)],
            balance_changes=[],
            code_changes=[],
            storage_changes=[],
            storage_reads=[],
        )
        # Inner CREATE deploys at addr(X, 1).
        inner_created = compute_create_address(
            address=collision_address, nonce=1
        )
        account_expectations[inner_created] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=2, post_nonce=1)],
            code_changes=[
                BalCodeChange(block_access_index=2, new_code=bytes(Op.STOP))
            ],
            balance_changes=[],
            storage_changes=[],
            storage_reads=[],
        )
        post[bob] = Account(nonce=1)
        post[collision_address] = Account(
            code=x_code, nonce=2, balance=0, storage={}
        )
        post[inner_created] = Account(
            nonce=1, code=bytes(Op.STOP), balance=0, storage={}
        )
    elif modification == "then_storage_change":
        txs.append(
            Transaction(
                sender=bob, to=collision_address, gas_limit=tx_gas_limit
            )
        )
        account_expectations[bob] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=2, post_nonce=1)],
        )
        # Strict: only the SSTORE slot appears; no spurious other entries.
        account_expectations[collision_address] = BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=0x01,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=2, post_value=0xCAFE
                        )
                    ],
                )
            ],
            nonce_changes=[],
            balance_changes=[],
            code_changes=[],
            storage_reads=[],
        )
        post[bob] = Account(nonce=1)
        post[collision_address] = Account(
            code=x_code, nonce=1, balance=0, storage={0x01: 0xCAFE}
        )
    else:
        raise ValueError(f"unknown modification: {modification}")

    block = Block(
        txs=txs,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations,
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post=post)


def test_bal_transient_storage_not_tracked(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL excludes EIP-1153 transient storage (TSTORE/TLOAD).

    Contract: TSTORE(0x01, 0x42)→TLOAD(0x01)→SSTORE(0x02, result).

    Expected BAL:
    - storage_changes: slot 0x02 (persistent)
    - MUST NOT include slot 0x01 (transient storage not persisted)
    """
    alice = pre.fund_eoa()

    # Contract that uses transient storage then persists to execution storage
    contract_code = (
        # TSTORE slot 0x01 with value 0x42 (transient storage)
        Op.TSTORE(0x01, 0x42)
        # TLOAD slot 0x01 (transient storage read)
        + Op.TLOAD(0x01)
        # Result (0x42) is on stack, store it in persistent slot 0x02
        + Op.PUSH1(0x02)
        + Op.SSTORE  # SSTORE pops slot (0x02), then value (0x42)
        + Op.STOP
    )

    contract = pre.deploy_contract(code=contract_code)

    tx = Transaction(sender=alice, to=contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                contract: BalAccountExpectation(
                    # Persistent storage change for slot 0x02
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        )
                    ],
                    # MUST NOT include slot 0x01 in storage_reads
                    # Transient storage operations don't pollute BAL
                    storage_reads=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            contract: Account(storage={0x02: 0x42}),
        },
    )


def test_bal_create2_deploy_then_collision(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Reverse-order companion to `test_bal_create_collision`: tx1 deploys X
    via CREATE2, tx2 retries the same CREATE2 → collision. Covers the
    `code_changes` axis of #2914 (forward order would need 7702 +
    signable EOA at a deterministic CREATE address, infeasible).

    Init increments X's slot 0, so post-state slot 0 == 1 proves it ran
    once (tx1); the tx2 collision must not re-run it (else a demoted
    read leaks into X's `storage_reads`).

    CREATE2-only: CREATE auto-increments factory.nonce between txs, so
    the second attempt targets a different address.
    """
    alice = pre.fund_eoa()

    init_code = Initcode(
        deploy_code=Op.STOP,
        initcode_prefix=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)),
    )
    init_code_bytes = bytes(init_code)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(init_code_bytes))
        + Op.SSTORE(
            0x00,
            Op.CREATE2(
                value=0,
                offset=32 - len(init_code_bytes),
                size=len(init_code_bytes),
                salt=0,
            ),
        )
        + Op.STOP
    )
    factory = pre.deploy_contract(
        code=factory_code,
        storage={0x00: 0xDEAD},
    )

    target = compute_create_address(
        address=factory,
        salt=0,
        initcode=init_code_bytes,
        opcode=Op.CREATE2,
    )

    tx_gas_limit = fork.transaction_gas_limit_cap()
    tx_deploy = Transaction(sender=alice, to=factory, gas_limit=tx_gas_limit)
    tx_collide = Transaction(sender=alice, to=factory, gas_limit=tx_gas_limit)

    block = Block(
        txs=[tx_deploy, tx_collide],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                        BalNonceChange(block_access_index=2, post_nonce=2),
                    ],
                ),
                factory: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2),
                        BalNonceChange(block_access_index=2, post_nonce=3),
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=target
                                ),
                                BalStorageChange(
                                    block_access_index=2, post_value=0
                                ),
                            ],
                        )
                    ],
                ),
                # Index-1 deployment entries must survive the
                # index-2 collision touch. Init ran once (tx1), writing
                # slot 0 = 1. The tx2 collision must add nothing — in
                # particular `storage_reads` MUST stay empty (a client
                # that runs init then reverts on collision would leak
                # slot 0 here as a demoted read).
                target: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=bytes(Op.STOP)
                        ),
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=1
                                )
                            ],
                        )
                    ],
                    balance_changes=[],
                    storage_reads=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=2),
            factory: Account(nonce=3, storage={0x00: 0}),
            # slot 0 == 1 proves init ran exactly once (tx2 collided).
            target: Account(
                nonce=1, code=bytes(Op.STOP), balance=0, storage={0x00: 1}
            ),
        },
    )


@pytest.mark.parametrize(
    "oog_boundary",
    [
        OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS,
        OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS,
        OutOfGasBoundary.SUCCESS,
    ],
    ids=lambda x: x.value,
)
@pytest.mark.with_all_create_opcodes
def test_bal_create_and_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    create_opcode: Op,
    oog_boundary: OutOfGasBoundary,
) -> None:
    """
    CREATE/CREATE2 OOG boundary test at three gas levels.

    OOG_BEFORE_TARGET_ACCESS and OOG_AFTER_TARGET_ACCESS differ by
    exactly 1 gas, proving the static cost boundary: below it the
    created address is NOT in BAL, at it the address IS in BAL.
    """
    alice = pre.fund_eoa()

    init_code = Initcode(deploy_code=Op.STOP)
    init_code_bytes = bytes(init_code)

    factory_mstore = Op.MSTORE(
        0, Op.PUSH32(init_code_bytes), new_memory_size=32
    )
    factory_create = create_opcode(
        value=0,
        offset=32 - len(init_code_bytes),
        size=len(init_code_bytes),
        init_code_size=len(init_code_bytes),
        account_new=False,
    )
    factory_sstore = Op.SSTORE(0x00, 1)
    oog_sink_memory_size = 10000 * 32
    factory_oog_sink = Op.MSTORE(
        oog_sink_memory_size - 32,
        0,
        old_memory_size=32,
        new_memory_size=oog_sink_memory_size,
    )
    factory_code = (
        factory_mstore + factory_create + factory_oog_sink + factory_sstore
    )

    factory = pre.deploy_contract(
        code=factory_code,
        storage={0x00: 0xDEAD},
    )

    created_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code_bytes,
        opcode=create_opcode,
    )
    # Pre-fund the address so no new account is created
    pre.fund_address(created_address, 1)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    create_static_cost = factory_mstore.gas_cost(
        fork
    ) + factory_create.gas_cost(fork)

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # 1 gas short of CREATE static cost — no state access
        gas_limit = intrinsic_cost + create_static_cost - 1
    elif oog_boundary == OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS:
        # Exactly the CREATE static cost — address accessed, child
        # frame gets 0 gas, CREATE fails, sink forces OOG after access
        gas_limit = intrinsic_cost + create_static_cost
    else:
        # Full success: static cost + child frame (63/64 rule) +
        # SSTORE + gas sink.
        child_gas = init_code.gas_cost(fork)
        remaining_needed = (child_gas * 64 + 62) // 63
        gas_limit = (
            intrinsic_cost
            + create_static_cost
            + remaining_needed
            + factory_sstore.gas_cost(fork)
            + factory_oog_sink.gas_cost(fork)
        )

    tx = Transaction(
        sender=alice,
        to=factory,
        gas_limit=gas_limit,
    )

    account_expectations: Dict[Address, BalAccountExpectation | None]
    post: Dict[Address, Account | None]

    if oog_boundary == OutOfGasBoundary.OOG_BEFORE_TARGET_ACCESS:
        # Created address NOT in BAL — static check failed before access
        account_expectations = {
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            ),
            factory: BalAccountExpectation.empty(),
            created_address: None,
        }
        post = {
            alice: Account(nonce=1),
            factory: Account(nonce=1, storage={0x00: 0xDEAD}),
            created_address: Account(balance=1, code=b"", nonce=0),
        }
    elif oog_boundary == OutOfGasBoundary.OOG_AFTER_TARGET_ACCESS:
        # Created address IS in BAL (accessed during collision check),
        # but tx OOGs so all state changes revert — only access is
        # recorded, no nonce/code/storage changes.
        account_expectations = {
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            ),
            factory: BalAccountExpectation.empty(),
            created_address: BalAccountExpectation.empty(),
        }
        post = {
            alice: Account(nonce=1),
            factory: Account(nonce=1, storage={0x00: 0xDEAD}),
            created_address: Account(balance=1, code=b"", nonce=0),
        }
    else:
        # SUCCESS: created address in BAL with nonce and code changes
        account_expectations = {
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            ),
            factory: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=2)
                ],
                storage_changes=[
                    BalStorageSlot(
                        slot=0x00,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=1
                            )
                        ],
                    )
                ],
            ),
            created_address: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
                code_changes=[
                    BalCodeChange(
                        block_access_index=1,
                        new_code=bytes(Op.STOP),
                    )
                ],
            ),
        }
        post = {
            alice: Account(nonce=1),
            factory: Account(nonce=2, storage={0x00: 1}),
            created_address: Account(balance=1, code=Op.STOP, nonce=1),
        }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post,
    )


@pytest.mark.with_all_create_opcodes
def test_bal_create_early_failure(
    pre: Alloc, blockchain_test: BlockchainTestFiller, create_opcode: Op
) -> None:
    """
    Test BAL with CREATE/CREATE2 failure due to insufficient endowment.

    Factory (balance=50) attempts CREATE/CREATE2(value=100).
    Fails before nonce increment (before track_address).
    Distinct from collision where address IS accessed.

    Expected BAL:
    - Alice: nonce_changes
    - Factory: storage_changes slot 0 (0xDEAD→0), NO nonce_changes
    - Contract address: MUST NOT appear (never accessed)
    """
    alice = pre.fund_eoa()

    factory_balance = 50
    endowment = 100

    init_code = Initcode(deploy_code=Op.STOP)
    init_code_bytes = bytes(init_code)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(init_code_bytes))
        + Op.SSTORE(
            0x00,
            create_opcode(
                value=endowment,
                offset=32 - len(init_code_bytes),
                size=len(init_code_bytes),
            ),
        )
        + Op.STOP
    )

    factory = pre.deploy_contract(
        code=factory_code,
        balance=factory_balance,
        storage={0x00: 0xDEAD},
    )

    would_be_contract_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code_bytes,
        opcode=create_opcode,
    )

    tx = Transaction(sender=alice, to=factory)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                factory: BalAccountExpectation(
                    nonce_changes=[],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0
                                )
                            ],
                        )
                    ],
                ),
                would_be_contract_address: None,
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            factory: Account(
                nonce=1, balance=factory_balance, storage={0x00: 0}
            ),
            would_be_contract_address: Account.NONEXISTENT,
        },
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize("creation_outcome", ["pre_frame_failure", "success"])
def test_bal_create_existing_target(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    create_opcode: Op,
    creation_outcome: str,
) -> None:
    """
    Test BAL for CREATE/CREATE2 into a pre-existing balance-only target.

    Under EIP-8037 the account-creation charge is unconditional, so the
    target's existence is never read to decide it. On a pre-frame failure
    (insufficient endowment) the pre-existing target is never accessed and
    stays absent from the BAL; on success it appears with the deployed
    nonce and code.
    """
    alice = pre.fund_eoa()

    init_code = Initcode(deploy_code=Op.STOP)
    init_code_bytes = bytes(init_code)

    if creation_outcome == "pre_frame_failure":
        factory_balance, endowment = 50, 100
    else:
        factory_balance, endowment = 0, 0

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(init_code_bytes))
        + Op.SSTORE(
            0x00,
            Op.GT(
                create_opcode(
                    value=endowment,
                    offset=32 - len(init_code_bytes),
                    size=len(init_code_bytes),
                ),
                0,
            ),
        )
        + Op.STOP
    )

    factory = pre.deploy_contract(
        code=factory_code,
        balance=factory_balance,
        storage={0x00: 0xDEAD},
    )

    target = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code_bytes,
        opcode=create_opcode,
    )
    # Pre-existing balance-only leaf (balance, no code, zero nonce).
    pre.fund_address(target, amount=1)

    tx = Transaction(sender=alice, to=factory)

    if creation_outcome == "pre_frame_failure":
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                factory: BalAccountExpectation(
                    nonce_changes=[],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0
                                )
                            ],
                        )
                    ],
                ),
                # Never accessed despite pre-existing: absent from the BAL.
                target: None,
            }
        )
        post = {
            alice: Account(nonce=1),
            factory: Account(
                nonce=1, balance=factory_balance, storage={0x00: 0}
            ),
            target: Account(balance=1),
        }
    else:
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                factory: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=1
                                )
                            ],
                        )
                    ],
                ),
                target: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=bytes(Op.STOP)
                        )
                    ],
                ),
            }
        )
        post = {
            alice: Account(nonce=1),
            factory: Account(nonce=2, storage={0x00: 1}),
            target: Account(nonce=1, balance=1, code=Op.STOP),
        }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize(
    "storage_op",
    ["read", "write"],
    ids=["sload_then_selfdestruct", "sstore_then_selfdestruct"],
)
def test_bal_create_storage_op_then_selfdestruct_same_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    create_opcode: Op,
    storage_op: str,
) -> None:
    """
    Same-tx CREATE/CREATE2 + storage_op + SELFDESTRUCT.

    The deterministic address A is pre-funded. A single tx deploys a
    contract at A via the parametrized create opcode; init code performs
    SLOAD or SSTORE on slot B then SELFDESTRUCTs. Because the contract
    is destroyed in the same tx, slot B MUST appear in `storage_reads`
    and MUST NOT appear in `storage_changes` (writes demoted to reads
    per EIP-7928).
    """
    alice = pre.fund_eoa()
    beneficiary = pre.fund_eoa(amount=0)
    fund_amount = 100
    slot_b = 0x07

    if storage_op == "read":
        initcode = Op.POP(Op.SLOAD(slot_b)) + Op.SELFDESTRUCT(beneficiary)
    else:
        initcode = Op.SSTORE(slot_b, 0xCAFE) + Op.SELFDESTRUCT(beneficiary)
    initcode_bytes = bytes(initcode)

    salt = 0
    is_create2 = create_opcode == Op.CREATE2
    if is_create2:
        deploy_op = Op.CREATE2(
            value=0, offset=0, size=Op.CALLDATASIZE, salt=salt
        )
    else:
        deploy_op = Op.CREATE(value=0, offset=0, size=Op.CALLDATASIZE)

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, deploy_op)
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    target_a = compute_create_address(
        address=factory,
        nonce=1,
        salt=salt,
        initcode=initcode_bytes,
        opcode=create_opcode,
    )
    pre.fund_address(target_a, fund_amount)

    tx = Transaction(sender=alice, to=factory, data=initcode_bytes)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                target_a: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0),
                    ],
                    storage_reads=[slot_b],
                    storage_changes=[],
                    code_changes=[],
                    nonce_changes=[],
                ),
                beneficiary: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=fund_amount,
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            target_a: Account.NONEXISTENT,
            beneficiary: Account(balance=fund_amount),
            factory: Account(nonce=2, storage={0: target_a}),
        },
    )


@pytest.mark.parametrize(
    "pre_balance",
    [0, 100],
    ids=["no_balance", "with_balance"],
)
def test_bal_create2_selfdestruct_then_recreate_same_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    pre_balance: int,
) -> None:
    """
    Tx1 CREATE2+SSTORE+SELFDESTRUCT, Tx2 CREATE2 resurrection at same
    address.

    Two identical txs invoke the same factory with the same initcode
    (same hash => same CREATE2 address A). The factory branches on its
    own storage slot 1: on the first tx, the slot is 0 so the factory
    CREATE2's then CALLs A (runtime SSTOREs to a target slot then
    SELFDESTRUCTs) and records the CALL's return code in slot 1; on the
    second tx, slot 1 is non-zero so only CREATE2 runs and A persists
    with the runtime code (its runtime is never executed).

    Per EIP-7928 SELFDESTRUCT-in-tx semantics, Tx1's destructed A has no
    `nonce_changes` or `code_changes`; only `balance_changes` if it was
    pre-funded. The SSTORE is demoted to `storage_reads` because the
    contract is destroyed in the same tx. Tx2's fresh A has
    `nonce_changes` (post=1), `code_changes` (post=runtime), and empty
    storage.
    """
    alice = pre.fund_eoa()
    beneficiary = pre.fund_eoa(amount=0)
    salt = 0
    target_slot = 0x07

    runtime = Op.SSTORE(target_slot, 0xCAFE) + Op.SELFDESTRUCT(beneficiary)
    runtime_bytes = bytes(runtime)
    initcode_bytes = bytes(Initcode(deploy_code=runtime))

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            0,
            Op.CREATE2(value=0, offset=0, size=Op.CALLDATASIZE, salt=salt),
        )
        + Conditional(
            condition=Op.ISZERO(Op.SLOAD(1)),
            if_true=Op.SSTORE(1, Op.CALL(Op.GAS, Op.SLOAD(0), 0, 0, 0, 0, 0)),
            if_false=Op.STOP,
        )
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    target_a = compute_create_address(
        address=factory,
        salt=salt,
        initcode=initcode_bytes,
        opcode=Op.CREATE2,
    )

    if pre_balance > 0:
        pre.fund_address(target_a, pre_balance)

    tx1 = Transaction(sender=alice, to=factory, data=initcode_bytes)
    tx2 = Transaction(sender=alice, to=factory, data=initcode_bytes)

    target_a_balance_changes = []
    if pre_balance > 0:
        target_a_balance_changes = [
            BalBalanceChange(block_access_index=1, post_balance=0),
        ]
        beneficiary_expectation = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(
                    block_access_index=1, post_balance=pre_balance
                )
            ],
        )
    else:
        # SELFDESTRUCT touches the beneficiary even with 0 value; no
        # balance change is recorded.
        beneficiary_expectation = BalAccountExpectation.empty()

    block = Block(
        txs=[tx1, tx2],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                target_a: BalAccountExpectation(
                    # Tx1 destruction (EIP-7928 #165): no nonce/code changes;
                    # the SSTORE is demoted to a storage_read because A is
                    # destroyed same-tx. Tx2 resurrection: fresh contract
                    # with nonce=1, runtime, and untouched storage.
                    nonce_changes=[
                        BalNonceChange(block_access_index=2, post_nonce=1),
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=2, new_code=runtime_bytes
                        ),
                    ],
                    balance_changes=target_a_balance_changes,
                    storage_changes=[],
                    storage_reads=[target_slot],
                ),
                beneficiary: beneficiary_expectation,
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            target_a: Account(
                nonce=1, balance=0, code=runtime_bytes, storage={}
            ),
            beneficiary: Account(balance=pre_balance)
            if pre_balance > 0
            else Account.NONEXISTENT,
            factory: Account(nonce=3, storage={0: target_a, 1: 1}),
        },
    )


def test_bal_create2_selfdestruct_then_recreate_and_write(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure `storage_reads` unions the wiped `SSTORE`s of an address that two
    transactions each recreate, write and destroy at the same CREATE2
    destination.

    Reported in https://github.com/erigontech/erigon/issues/23407.
    """
    alice = pre.fund_eoa()
    beneficiary = pre.fund_eoa(amount=0)
    salt = 0
    target_balance = 100

    # The balance names the slot, so the second transaction cannot pick its
    # own until the first one has drained the account.
    initcode = bytes(
        Op.SSTORE(Op.SELFBALANCE, 0xCAFE) + Op.SELFDESTRUCT(beneficiary)
    )
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.POP(Op.CREATE2(offset=0, size=len(initcode), salt=salt))
    )
    target = compute_create_address(
        address=factory,
        salt=salt,
        initcode=initcode,
        opcode=Op.CREATE2,
    )
    pre.fund_address(target, target_balance)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=alice, to=factory) for _ in range(2)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        target: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=0
                                ),
                            ],
                            nonce_changes=[],
                            code_changes=[],
                            storage_changes=[],
                            storage_reads=[0, target_balance],
                        ),
                        beneficiary: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=target_balance,
                                ),
                            ],
                        ),
                    }
                ),
            )
        ],
        post={
            target: Account.NONEXISTENT,
            beneficiary: Account(balance=target_balance),
            factory: Account(nonce=3),
        },
    )


@pytest.mark.parametrize(
    "destruction_successful,oracle_suffix",
    [
        pytest.param(True, Op.STOP, id="destruction_succeeds"),
        pytest.param(False, Op.REVERT(0, 0), id="destruction_reverts"),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_bal_dirty_account_selfdestruct(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    create_opcode: Op,
    destruction_successful: bool,
    oracle_suffix: Bytecode,
) -> None:
    """
    BAL records dirty state changes on an ephemeral contract only when
    its same-tx SELFDESTRUCT is rolled back by a reverting parent
    frame.

    The factory deploys the ephemeral with non-zero endowment (balance
    dirty), initcode SSTOREs and SLOADs own slots (storage dirty),
    invokes an empty CREATE so the ephemeral's own nonce bumps 1→2
    (nonce dirty), and returns runtime (code dirty). The factory then
    CALLs an oracle which CALLs the ephemeral's runtime
    (SELFDESTRUCTs), and either STOPs or REVERTs.

    - destruction_succeeds: oracle STOPs; per EIP-6780 the same-tx
      selfdestruct fully removes the ephemeral; per EIP-7928 its BAL
      entry must contain no balance/nonce/code/storage changes — only
      `storage_reads` for the demoted slots.

    - destruction_reverts: oracle REVERTs; the SELFDESTRUCT (and the
      balance transfer to the beneficiary) are rolled back. The
      ephemeral persists with all four dirtied fields, which BAL must
      now record.
    """
    alice = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()
    factory_balance = 1000
    endowment = 100
    slot_write = 0x07
    slot_read = 0x09

    init_code = Initcode(
        deploy_code=Op.SELFDESTRUCT(beneficiary),
        initcode_prefix=(
            Op.SSTORE(slot_write, 0xCAFE)
            + Op.POP(Op.SLOAD(slot_read))
            + Op.POP(create_opcode(value=0, offset=0, size=0))
        ),
    )

    # Oracle CALLs whatever address it receives as calldata, then
    # either STOPs (destruction succeeds) or REVERTs (destruction
    # rolled back). Pre-deployed so its own creation doesn't appear
    # in the block's BAL.
    oracle = pre.deploy_contract(
        code=Op.POP(Op.CALL(Op.GAS, Op.CALLDATALOAD(0), 0, 0, 0, 0, 0))
        + oracle_suffix,
    )

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            0,
            create_opcode(value=endowment, offset=0, size=Op.CALLDATASIZE),
        )
        + Op.MSTORE(0, Op.SLOAD(0))
        + Op.POP(Op.CALL(Op.GAS, oracle, 0, 0, 32, 0, 0))
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code, balance=factory_balance)

    ephemeral = compute_create_address(
        address=factory,
        nonce=1,
        initcode=init_code,
        opcode=create_opcode,
    )
    zombie = compute_create_address(
        address=ephemeral,
        nonce=1,
        initcode=b"",
        opcode=create_opcode,
    )

    expected_ephemeral_post: Account | None
    expected_beneficiary_post: Account | None
    if destruction_successful:
        expected_ephemeral_bal = BalAccountExpectation(
            balance_changes=[],
            nonce_changes=[],
            code_changes=[],
            storage_changes=[],
            storage_reads=[slot_write, slot_read],
        )
        expected_beneficiary_bal = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=endowment)
            ],
        )
        expected_ephemeral_post = Account.NONEXISTENT
        expected_beneficiary_post = Account(balance=endowment)
    else:
        expected_ephemeral_bal = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=endowment)
            ],
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
            code_changes=[
                BalCodeChange(
                    block_access_index=1, new_code=init_code.deploy_code
                )
            ],
            storage_changes=[
                BalStorageSlot(
                    slot=slot_write,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1, post_value=0xCAFE
                        )
                    ],
                )
            ],
            storage_reads=[slot_read],
        )
        expected_beneficiary_bal = BalAccountExpectation.empty()
        expected_ephemeral_post = Account(
            nonce=2,
            balance=endowment,
            code=init_code.deploy_code,
            storage={slot_write: 0xCAFE},
        )
        expected_beneficiary_post = Account.NONEXISTENT

    tx = Transaction(
        sender=alice,
        to=factory,
        data=init_code,
        gas_limit=1_000_000,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                factory: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=factory_balance - endowment,
                        )
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1,
                                    post_value=ephemeral,
                                )
                            ],
                        )
                    ],
                ),
                ephemeral: expected_ephemeral_bal,
                # The zombie is ALWAYS crated
                # since it was deployed inside the factory's frame,
                # which never reverts.
                zombie: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation.empty(),
                beneficiary: expected_beneficiary_bal,
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            beneficiary: expected_beneficiary_post,
            factory: Account(
                nonce=2,
                balance=factory_balance - endowment,
                storage={0: ephemeral},
            ),
            ephemeral: expected_ephemeral_post,
            zombie: Account(nonce=1),
        },
    )
