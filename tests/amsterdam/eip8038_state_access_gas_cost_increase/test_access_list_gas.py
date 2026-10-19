"""
Tests for [EIP-8038: State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 access-list repricing:

* The intrinsic surcharge per access-list entry is
  ``TX_ACCESS_LIST_ADDRESS`` per address and
  ``TX_ACCESS_LIST_STORAGE_KEY`` per storage key, isolated from
  the EIP-7981 calldata-floor tokens that the Amsterdam intrinsic
  calculator also charges on access-list bytes.
* A storage slot named in the access list is *warm* on its first runtime
  access (``SLOAD``/``SSTORE`` pays ``WARM_SLOAD`` rather than the cold
  cost).
* Warmth is scoped to ``(address, slot)``: listing slot ``s`` of account
  ``A`` does not warm slot ``s`` of account ``B``.
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _make_access_list(
    n_addr: int, n_keys_each: int, *, duplicate: bool = False
) -> List[AccessList]:
    """Build an access list of ``n_addr`` entries, each with keys."""
    entries: List[AccessList] = []
    for i in range(n_addr):
        address = Address(0x1000) if duplicate else Address(0x1000 + i)
        keys = [bytes([j]) * 32 for j in range(n_keys_each)]
        entries.append(AccessList(address=address, storage_keys=keys))
    return entries


# (n_addr, n_keys_each, duplicate, id)
ACCESS_LIST_SHAPES = [
    pytest.param(0, 0, False, id="empty"),
    pytest.param(1, 0, False, id="single_addr"),
    pytest.param(1, 3, False, id="one_addr_three_keys"),
    pytest.param(2, 0, False, id="two_addr"),
    pytest.param(2, 1, True, id="duplicate_addr"),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("n_addr,n_keys_each,duplicate", ACCESS_LIST_SHAPES)
def test_access_list_intrinsic_surcharge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    n_addr: int,
    n_keys_each: int,
    duplicate: bool,
) -> None:
    """
    Pin the exact intrinsic cost of each access-list shape.

    The transaction is handed a ``gas_limit`` equal to its intrinsic and
    sent to a codeless recipient, so it runs nothing and the receipt
    accounts for the intrinsic alone — including the per-entry surcharge
    and the EIP-7981 floor tokens the Amsterdam calculator charges on
    access-list bytes. Pinning every shape pins the per-entry increments
    as the differences between them, duplicate entries included: the
    ``duplicate_addr`` shape lists one address twice and is billed twice.
    """
    access_list = _make_access_list(n_addr, n_keys_each, duplicate=duplicate)
    entries = access_list if access_list else None

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=entries
    )

    # A codeless recipient executes nothing, so the whole limit is the
    # intrinsic and the receipt pins it exactly.
    recipient = pre.fund_eoa(amount=0)

    tx = Transaction(
        to=recipient,
        sender=pre.fund_eoa(),
        access_list=entries,
        gas_limit=intrinsic,
        expected_receipt=TransactionReceipt(cumulative_gas_used=intrinsic),
    )

    state_test(pre=pre, post={}, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_access_list_duplicate_address_key_intrinsic_and_warmth(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A duplicated ``(address, storage_key)`` access-list entry warms the
    slot only once.

    The same ``(contract, slot)`` pair is listed twice, yet the slot is
    warm on its first ``SLOAD`` and pays ``WARM_SLOAD``, since warmth is
    set-membership rather than a counter. That the duplicate is
    nonetheless *billed* twice in the intrinsic is pinned by
    ``test_access_list_intrinsic_surcharge``'s ``duplicate_addr`` shape;
    this test asserts only the warmth, which is all its measurement can
    see.
    """
    slot = 0x42

    # First runtime SLOAD of the listed slot stores the warm access cost.
    measured_read = Op.SLOAD(slot)
    overhead = measured_read.gas_cost(fork) - Op.SLOAD(
        key_warm=False
    ).gas_cost(fork)
    contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=measured_read,
            overhead_cost=overhead,
            extra_stack_items=1,
            sstore_key=1,
        ),
        storage={slot: 1},
    )

    # Build the access list after deploying so the address is real, then
    # list the identical (contract, slot) pair twice.
    access_list = [
        AccessList(address=contract, storage_keys=[slot]),
        AccessList(address=contract, storage_keys=[slot]),
    ]

    expected_gas = Op.SLOAD(key_warm=True).gas_cost(fork)
    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    # Slot 1 holds the measured warm cost; the read slot keeps its value.
    post = {contract: Account(storage={1: expected_gas, slot: 1})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("op", ["SLOAD", "SSTORE"], ids=["sload", "sstore"])
def test_access_list_warms_storage_slot(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    op: str,
) -> None:
    """
    A storage slot named in the access list is warm on first access.

    The first runtime ``SLOAD``/``SSTORE`` of an access-list slot pays
    the warm cost: ``WARM_SLOAD`` for ``SLOAD``; for ``SSTORE`` an
    overwrite of a non-zero original to a new non-zero value pays
    ``WARM_SLOAD + STORAGE_WRITE``.
    """
    very_low = Op.PUSH1(0).execution_cost(fork)
    slot = 0x42

    if op == "SLOAD":
        measured_code: Bytecode = Op.SLOAD(slot)
        # Overhead is just the single PUSH (key); the stored value is the
        # bare warm SLOAD access cost.
        overhead_cost = 1 * very_low
        extra_stack_items = 1
        expected_gas = Op.SLOAD(key_warm=True).gas_cost(fork)
    else:
        measured_code = Op.SSTORE(slot, 2)
        # Overhead is the two PUSHes (key, value); the stored value is
        # the bare warm SSTORE execution cost (overwrite of a non-zero
        # original, no state gas).
        overhead_cost = 2 * very_low
        extra_stack_items = 0
        expected_gas = (
            Op.SSTORE.with_metadata(
                key_warm=True,
                original_value=1,
                current_value=1,
                new_value=2,
            )(slot, 2).execution_cost(fork)
            - 2 * very_low
        )

    code = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=extra_stack_items,
        sstore_key=1,
    )
    contract = pre.deploy_contract(code=code, storage={slot: 1})

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=contract, storage_keys=[slot])],
    )

    # Slot 1 holds the measured warm cost. The data slot ends at its
    # original (SLOAD) or the written value (SSTORE).
    final_slot_value = 1 if op == "SLOAD" else 2
    post = {
        contract: Account(storage={1: expected_gas, slot: final_slot_value})
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_access_list_slot_warmth_is_address_scoped(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Access-list slot warmth is scoped to ``(address, slot)``.

    Slot ``s`` of account ``A`` is listed in the access list. Reading
    slot ``s`` of ``A`` is warm (``WARM_SLOAD``); reading the same slot
    number of a different account ``B`` is cold (``COLD_STORAGE_ACCESS``).
    """
    slot = 0x42
    warm_gas = Op.SLOAD(key_warm=True).gas_cost(fork)
    cold_gas = Op.SLOAD(key_warm=False).gas_cost(fork)

    # Both accounts read their own slot ``s`` with the same wrapper, so the
    # overhead that strips the operand PUSH is identical for each.
    measured_read = Op.SLOAD(slot)
    overhead = measured_read.gas_cost(fork) - cold_gas

    # B reads its own slot ``s`` (cold), storing the result in B's slot 1.
    account_b = pre.deploy_contract(
        code=CodeGasMeasure(
            code=measured_read,
            overhead_cost=overhead,
            extra_stack_items=1,
            sstore_key=1,
        ),
        storage={slot: 1},
    )

    # A reads its own slot ``s`` (warm via the access list), then calls B.
    account_a = pre.deploy_contract(
        code=CodeGasMeasure(
            code=measured_read,
            overhead_cost=overhead,
            extra_stack_items=1,
            sstore_key=1,
        )
        + Op.POP(Op.CALL(gas=200_000, address=account_b)),
        storage={slot: 1},
    )

    tx = Transaction(
        to=account_a,
        sender=pre.fund_eoa(),
        # Only A's slot is listed; B's identical slot stays cold.
        access_list=[AccessList(address=account_a, storage_keys=[slot])],
    )

    post = {
        account_a: Account(storage={1: warm_gas, slot: 1}),
        account_b: Account(storage={1: cold_gas, slot: 1}),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
