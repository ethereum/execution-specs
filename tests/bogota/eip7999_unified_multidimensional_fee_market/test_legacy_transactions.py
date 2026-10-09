"""
Tests for transactions of the older types under EIP-7999: their calldata
gas moves to the calldata resource and their fee caps become one budget
that is fungible across resources.
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
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as Spec4844
from .conftest import SENDER_BALANCE, receipt_gas, transfer_gas
from .spec import Spec, ref_spec_7999

REFERENCE_SPEC_GIT_PATH = ref_spec_7999.git_path
REFERENCE_SPEC_VERSION = ref_spec_7999.version

pytestmark = pytest.mark.valid_from("EIP7999")


def transfer_intrinsic_gas(fork: Fork, calldata: bytes) -> int:
    """Return the gas limit a transfer with `calldata` needs."""
    return fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        sends_value=True,
        recipient_type=RecipientType.EOA,
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
    "tx_type", [0, 1, 2], ids=["legacy", "access_list", "fee_market"]
)
@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(bytes(1000), id="zero_bytes"),
        pytest.param(bytes(500) + b"\xff" * 50, id="mixed_bytes"),
    ],
)
def test_calldata_priced_by_its_resource(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
    tx_type: int,
    calldata: bytes,
) -> None:
    """
    An older transaction's calldata gas leaves its gas limit for the
    calldata resource, priced at the calldata base fee and no longer
    subject to the EIP-7623 floor; the receipt counts EVM gas only.
    """
    gas_limit = transfer_intrinsic_gas(fork, calldata)
    gas_used = transfer_gas(fork, calldata)
    fee_fields = (
        {"gas_price": 10}
        if tx_type <= 1
        else {"max_fee_per_gas": 10, "max_priority_fee_per_gas": 2}
    )
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=recipient,
        value=1,
        data=calldata,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=receipt_gas(fork, gas_used, calldata)
        ),
        **fee_fields,
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
    "shortfall_from,error",
    [
        pytest.param(
            "calldata_gas",
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="below_calldata_gas",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "intrinsic_gas",
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="below_intrinsic_gas",
            marks=pytest.mark.exception_test,
        ),
        pytest.param("none", None, id="exact_intrinsic_gas"),
    ],
)
def test_gas_limit_covers_calldata_and_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
    shortfall_from: str,
    error: TransactionException | None,
) -> None:
    """
    An older transaction's gas limit must cover its calldata gas and then
    the EVM intrinsic cost of what remains.
    """
    calldata = bytes(100)
    calldata_gas = fork.calldata_gas_calculator()(data=calldata)
    intrinsic_gas = transfer_intrinsic_gas(fork, calldata)
    gas_limit = {
        "calldata_gas": calldata_gas - 1,
        "intrinsic_gas": intrinsic_gas - 1,
        "none": intrinsic_gas,
    }[shortfall_from]
    tx = Transaction(
        ty=2,
        sender=sender,
        to=recipient,
        value=1,
        data=calldata,
        gas_limit=gas_limit,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=0,
        error=error,
    )
    post: Dict[Address, Account] = {}
    if error is None:
        gas_used = transfer_gas(fork, calldata)
        settlement = Spec.settle(fork, tx, base_fees, evm_gas_used=gas_used)
        post = settlement_post(
            env,
            sender,
            recipient,
            settlement.total_paid,
            settlement.priority_fee_paid,
        )
    state_test(env=env, pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "calldata_bytes,valid",
    [
        pytest.param(4000, True, id="cheap_calldata_funds_evm_gas"),
        pytest.param(
            0, False, id="no_calldata", marks=pytest.mark.exception_test
        ),
    ],
)
def test_fee_cap_below_evm_base_fee(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
    calldata_bytes: int,
    valid: bool,
) -> None:
    """
    A fee cap per gas below the EVM base fee no longer rejects on its own:
    the budget it implies over the whole gas limit is fungible, so enough
    calldata gas priced below the cap funds EVM gas priced above it.
    """
    calldata = bytes(calldata_bytes)
    gas_limit = transfer_intrinsic_gas(fork, calldata)
    tx = Transaction(
        ty=2,
        sender=sender,
        to=recipient,
        value=1,
        data=calldata,
        gas_limit=gas_limit,
        max_fee_per_gas=base_fees[Spec.EVM_GAS] - 1,
        max_priority_fee_per_gas=0,
        error=(
            None
            if valid
            else TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS
        ),
    )
    gas_limits = Spec.resource_gas_limits(fork, tx)
    assert (
        Spec.resource_fees(base_fees, gas_limits) <= Spec.max_fee(fork, tx)
    ) == valid, "test correctness: budget on the wrong side of required"
    post: Dict[Address, Account] = {}
    if valid:
        gas_used = transfer_gas(fork, calldata)
        settlement = Spec.settle(fork, tx, base_fees, evm_gas_used=gas_used)
        post = settlement_post(
            env,
            sender,
            recipient,
            settlement.total_paid,
            settlement.priority_fee_paid,
        )
    state_test(env=env, pre=pre, tx=tx, post=post)


def test_blob_fee_cap_not_binding(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    base_fees: List[int],
    sender: Address,
    recipient: Address,
) -> None:
    """
    A blob fee cap below the blob base fee no longer rejects a blob
    transaction: its budget over EVM gas and blob gas together funds the
    blobs.
    """
    gas_used = transfer_gas(fork)
    tx = Transaction(
        ty=3,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=gas_used,
        max_fee_per_gas=20,
        max_priority_fee_per_gas=0,
        max_fee_per_blob_gas=0,
        blob_versioned_hashes=add_kzg_version(
            [Hash(1)], Spec4844.BLOB_COMMITMENT_VERSION_KZG
        ),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=receipt_gas(fork, gas_used)
        ),
    )
    assert int(tx.max_fee_per_blob_gas or 0) < base_fees[Spec.BLOB_GAS], (
        "test correctness: the blob fee cap must be below the blob base fee"
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
