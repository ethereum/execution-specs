"""
Tests for the EIP-7999 multidimensional transaction type: one `max_fee`
budget funds every resource, each settled at its own base fee.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    add_kzg_version,
    compute_create_address,
)

from ...cancun.eip4844_blobs.spec import Spec as Spec4844
from .conftest import SENDER_BALANCE, receipt_gas, transfer_gas
from .spec import Spec, ref_spec_7999

REFERENCE_SPEC_GIT_PATH = ref_spec_7999.git_path
REFERENCE_SPEC_VERSION = ref_spec_7999.version

pytestmark = pytest.mark.valid_from("EIP7999")


def blob_hashes(count: int) -> List[Hash]:
    """Return `count` versioned hashes for a blob-carrying transaction."""
    return add_kzg_version(
        [Hash(index + 1) for index in range(count)],
        Spec4844.BLOB_COMMITMENT_VERSION_KZG,
    )


def settlement_post(
    env: Environment,
    sender: Address,
    recipient: Address,
    total_paid: int,
    priority_fee_paid: int,
) -> Dict[Address, Account]:
    """Post state of a one-wei transfer that paid `total_paid` in fees."""
    post = {
        sender: Account(balance=SENDER_BALANCE - 1 - total_paid),
        recipient: Account(balance=2),
    }
    if priority_fee_paid > 0:
        post[env.fee_recipient] = Account(balance=priority_fee_paid)
    return post


@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(b"", id="no_calldata"),
        pytest.param(bytes(64) + b"\x01" * 8, id="calldata"),
    ],
)
@pytest.mark.parametrize("priority_fee_cap", [0, 2])
@pytest.mark.parametrize(
    "budget_multiplier",
    [pytest.param(1, id="exact_budget"), pytest.param(4, id="ample_budget")],
)
def test_transfer_settlement(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
    calldata: bytes,
    priority_fee_cap: int,
    budget_multiplier: int,
) -> None:
    """
    A transfer burns each resource's base fee on the gas it consumes, tips
    the rest up to its cap, and keeps the rest of its budget; the receipt
    counts EVM gas only.
    """
    gas_used = transfer_gas(fork, calldata)
    calldata_gas = fork.calldata_gas_calculator()(data=calldata)
    required_max_fee = Spec.resource_fees(
        base_fees, [gas_used, 0, calldata_gas]
    )
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        data=calldata,
        gas_limit=gas_used,
        max_fee=required_max_fee * budget_multiplier,
        max_priority_fees_per_gas=[priority_fee_cap],
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=receipt_gas(fork, gas_used, calldata)
        ),
    )
    settlement = Spec.settle(fork, tx, base_fees, evm_gas_used=gas_used)
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=settlement_post(
            env,
            sender,
            recipient,
            settlement.total_paid,
            settlement.priority_fee_paid,
        ),
    )


@pytest.mark.parametrize(
    "budget_headroom",
    [pytest.param(0, id="no_headroom"), pytest.param(10**6, id="headroom")],
)
def test_unused_gas_refund_and_tip(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
    budget_headroom: int,
) -> None:
    """
    Unused EVM gas is refunded at the base fee, and the budget left after
    the base fees of the gas consumed flows to the tip up to the cap.
    """
    gas_used = transfer_gas(fork)
    gas_limit = gas_used + 50_000
    required_max_fee = Spec.resource_fees(base_fees, [gas_limit, 0, 0])
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=gas_limit,
        max_fee=required_max_fee + budget_headroom,
        max_priority_fees_per_gas=[2],
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=receipt_gas(fork, gas_used)
        ),
    )
    settlement = Spec.settle(fork, tx, base_fees, evm_gas_used=gas_used)
    assert settlement.refund > 0, "test correctness: nothing to refund"
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=settlement_post(
            env,
            sender,
            recipient,
            settlement.total_paid,
            settlement.priority_fee_paid,
        ),
    )


@pytest.mark.exception_test
def test_budget_below_required(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
) -> None:
    """A budget one wei short of the reserved base fees is rejected."""
    calldata = bytes(32)
    gas_used = transfer_gas(fork, calldata)
    calldata_gas = fork.calldata_gas_calculator()(data=calldata)
    required_max_fee = Spec.resource_fees(
        base_fees, [gas_used, 0, calldata_gas]
    )
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        data=calldata,
        gas_limit=gas_used,
        max_fee=required_max_fee - 1,
        max_priority_fees_per_gas=[0],
        error=TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
    )
    state_test(env=env, pre=pre, tx=tx, post={})


@pytest.mark.parametrize(
    "priority_fee_caps",
    [
        pytest.param([1, 1], id="two_caps"),
        pytest.param([0, 0, 0, 0], id="four_caps"),
        pytest.param([2**64], id="cap_too_high"),
    ],
)
@pytest.mark.exception_test
def test_invalid_priority_fee_caps(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    sender: Address,
    recipient: Address,
    priority_fee_caps: List[int],
) -> None:
    """Priority fee caps must cover one or every resource, below the cap."""
    gas_used = transfer_gas(fork)
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=gas_used,
        max_fee=10**12,
        max_priority_fees_per_gas=priority_fee_caps,
        error=TransactionException.TYPE_5_TX_INVALID_PRIORITY_FEES,
    )
    state_test(env=env, pre=pre, tx=tx, post={})


@pytest.mark.parametrize(
    "max_fee,error",
    [
        pytest.param(Spec.MAX_FEE_LIMIT, None, id="at_limit"),
        pytest.param(
            Spec.MAX_FEE_LIMIT + 1,
            TransactionException.TYPE_5_TX_MAX_FEE_TOO_LARGE,
            id="above_limit",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_max_fee_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
    max_fee: int,
    error: TransactionException | None,
) -> None:
    """
    The budget is bounded at `MAX_FEE_LIMIT`; a budget at the bound needs
    no matching balance, since only the fee taken at inclusion is checked.
    """
    gas_used = transfer_gas(fork)
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=gas_used,
        max_fee=max_fee,
        max_priority_fees_per_gas=[0],
        error=error,
    )
    post: Dict[Address, Account] = {}
    if error is None:
        settlement = Spec.settle(fork, tx, base_fees, evm_gas_used=gas_used)
        post = settlement_post(
            env,
            sender,
            recipient,
            settlement.total_paid,
            settlement.priority_fee_paid,
        )
    state_test(env=env, pre=pre, tx=tx, post=post)


def test_per_resource_priority_fee_caps(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
) -> None:
    """
    A cap per resource tips every resource's gas, blob gas included, where
    a single cap leaves blob gas untipped.
    """
    calldata = bytes(32)
    gas_used = transfer_gas(fork, calldata)
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        data=calldata,
        blob_versioned_hashes=blob_hashes(1),
        gas_limit=gas_used,
        max_fee=10**12,
        max_priority_fees_per_gas=[1, 2, 3],
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=receipt_gas(fork, gas_used, calldata)
        ),
    )
    settlement = Spec.settle(fork, tx, base_fees, evm_gas_used=gas_used)
    gas_limits = Spec.resource_gas_limits(fork, tx)
    assert settlement.priority_fee_paid == (
        gas_limits[Spec.EVM_GAS]
        + 2 * gas_limits[Spec.BLOB_GAS]
        + 3 * gas_limits[Spec.CALLDATA_GAS]
    ), "test correctness: the budget must not bind"
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=settlement_post(
            env,
            sender,
            recipient,
            settlement.total_paid,
            settlement.priority_fee_paid,
        ),
    )


@pytest.mark.parametrize(
    "with_blobs",
    [
        pytest.param(False, id="without_blobs"),
        pytest.param(True, id="with_blobs", marks=pytest.mark.exception_test),
    ],
)
def test_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    sender: Address,
    with_blobs: bool,
) -> None:
    """
    A multidimensional transaction can create a contract unless it carries
    blobs, as a blob transaction cannot.
    """
    # Deploy a single STOP byte.
    initcode = Op.MSTORE8(0, 0) + Op.RETURN(0, 1)
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=None,
        data=initcode,
        blob_versioned_hashes=blob_hashes(1) if with_blobs else None,
        error=(
            TransactionException.TYPE_5_TX_CONTRACT_CREATION
            if with_blobs
            else None
        ),
    )
    post: Dict[Address, Account] = {}
    if not with_blobs:
        created = compute_create_address(address=sender, nonce=0)
        post[created] = Account(nonce=1, code=b"\x00")
    state_test(env=env, pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "balance_shortfall",
    [
        pytest.param(0, id="exact_balance"),
        pytest.param(1, id="short_by_one", marks=pytest.mark.exception_test),
    ],
)
def test_balance_covers_fee_to_deduct(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    recipient: Address,
    balance_shortfall: int,
) -> None:
    """
    The sender needs the fee taken at inclusion plus the value, not the
    whole budget.
    """
    gas_used = transfer_gas(fork)
    required_max_fee = Spec.resource_fees(base_fees, [gas_used, 0, 0])
    # With a zero cap the fee taken at inclusion is the base fees alone.
    fee_to_deduct = required_max_fee
    sender = pre.fund_eoa(amount=fee_to_deduct + 1 - balance_shortfall)
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=gas_used,
        max_fee=required_max_fee * 3,
        max_priority_fees_per_gas=[0],
        error=(
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            if balance_shortfall
            else None
        ),
    )
    post: Dict[Address, Account] = {}
    if not balance_shortfall:
        post = {sender: Account(balance=0), recipient: Account(balance=2)}
    state_test(env=env, pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("priority_fee_cap", [0, 3])
def test_block_fee_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    priority_fee_cap: int,
) -> None:
    """
    CALLDATABASEFEE, BASEFEE and BLOBBASEFEE report the block's base fees
    and GASLIMIT its EVM gas limit; GASPRICE spreads the admitted tip over
    the tipped gas.
    """
    calldata = bytes(16)
    # Five cold storage writes, each charged state gas under EIP-8037.
    gas_limit = 1_000_000
    calldata_gas = fork.calldata_gas_calculator()(data=calldata)
    required_max_fee = Spec.resource_fees(
        base_fees, [gas_limit, 0, calldata_gas]
    )
    tx = Transaction(
        ty=Spec.MULTIDIM_TX_TYPE,
        sender=sender,
        data=calldata,
        gas_limit=gas_limit,
        max_fee=required_max_fee * 2,
        max_priority_fees_per_gas=[priority_fee_cap],
    )
    storage = Storage()
    code = (
        Op.SSTORE(
            storage.store_next(base_fees[Spec.CALLDATA_GAS]),
            Op.CALLDATABASEFEE,
        )
        + Op.SSTORE(storage.store_next(base_fees[Spec.EVM_GAS]), Op.BASEFEE)
        + Op.SSTORE(
            storage.store_next(base_fees[Spec.BLOB_GAS]), Op.BLOBBASEFEE
        )
        + Op.SSTORE(storage.store_next(int(env.gas_limit)), Op.GASLIMIT)
        + Op.SSTORE(
            storage.store_next(Spec.effective_gas_price(fork, tx, base_fees)),
            Op.GASPRICE,
        )
        + Op.STOP
    )
    contract = pre.deploy_contract(code)
    tx.to = contract
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={contract: Account(storage=storage)},
    )
