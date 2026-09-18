"""
Tests for access list cost calculations in [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    EIPChecklist,
    Fork,
    Hash,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import calculate_access_list_data_cost
from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,expected_floor_tokens",
    [
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[])],
            # 20 bytes total: 20 * 4 = 80 floor tokens
            80,
            id="single_zero_address_no_keys",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    ),
                    storage_keys=[],
                )
            ],
            # 20 bytes total: 20 * 4 = 80 floor tokens
            80,
            id="single_nonzero_address_no_keys",
        ),
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[Hash(0)])],
            # Total bytes: 20 + 32 = 52, floor tokens: 52 * 4 = 208
            208,
            id="zero_address_zero_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    ),
                    storage_keys=[
                        Hash(
                            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                        )
                    ],
                )
            ],
            # Total bytes: 20 + 32 = 52, floor tokens: 52 * 4 = 208
            208,
            id="nonzero_address_nonzero_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(0), Hash(1), Hash(2)],
                )
            ],
            # Total bytes: 20 + (3 * 32) = 116, floor tokens: 116 * 4 = 464
            464,
            id="one_address_three_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
                AccessList(address=Address(2), storage_keys=[Hash(1)]),
            ],
            # Total bytes: 2 * (20 + 32) = 104, floor tokens: 104 * 4 = 416
            416,
            id="two_addresses_with_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_access_list_token_calculation(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    tx: Transaction,
    access_list: list,
    expected_floor_tokens: int,
) -> None:
    """
    Test that access list floor tokens are calculated correctly.

    Every access list byte contributes four floor tokens regardless of
    whether it is zero or non-zero. Verify the reference helper's data
    surcharge and the fork's floor cost against explicit token counts.
    """
    gas_costs = fork.gas_costs()
    expected_data_cost = expected_floor_tokens * gas_costs.TX_DATA_TOKEN_FLOOR
    assert (
        calculate_access_list_data_cost(access_list, fork)
        == expected_data_cost
    )

    expected_floor_cost = (
        expected_data_cost
        + gas_costs.TX_BASE
        # EIP-2780 anchors the floor on the decomposed intrinsic base; the
        # tx targets a non-self account, adding the recipient-access charge.
        + gas_costs.COLD_ACCOUNT_ACCESS
    )
    actual_floor_cost = fork.transaction_data_floor_cost_calculator()(
        data=b"", access_list=access_list
    )
    assert actual_floor_cost == expected_floor_cost

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
# A type 4 authorization's top-frame state gas outgrows any moderate
# floor, and the floor does not depend on the transaction type.
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2, 3))
@pytest.mark.parametrize(
    "access_list,tx_data",
    [
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            Bytes(b"\x01" * 400),
            id="access_list_and_calldata",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(i) for i in range(10)],
                )
            ],
            Bytes(b"\x00" * 500 + b"\x01" * 500),
            id="large_access_list_mixed_calldata",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_access_list_floor_cost_with_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx: Transaction,
    access_list: list,
    tx_data: Bytes,
    tx_intrinsic_gas_cost_before_execution: int,
) -> None:
    """Bill the calldata floor with the access list surcharge inside it."""
    floor = fork.transaction_data_floor_cost_calculator()(
        data=tx_data, access_list=access_list
    )
    assert floor > tx_intrinsic_gas_cost_before_execution
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            [
                AccessList(
                    address=Address(i),
                    storage_keys=[Hash(j) for j in range(5)],
                )
                for i in range(1, 6)
            ],
            id="five_addresses_five_keys_each",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_large_access_list_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test gas costs for large access lists.

    With EIP-7981, large access lists should incur:
    1. Storage access costs (per-address and per-key charges, priced
       at the fork's cold access costs since EIP-8038)
    2. Data footprint costs (16 per floor token)
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            [
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
            ],
            id="duplicate_access_list_entries",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0), Hash(0)])],
            id="duplicate_storage_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_duplicate_access_list_entries(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test that duplicate access list entries are charged multiple times.

    According to EIP-2930, non-unique addresses and storage keys are allowed
    and charged multiple times. EIP-7981 should maintain this behavior.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"\x00" * 400, id="zero_calldata"),
        pytest.param(b"\xff" * 400, id="nonzero_calldata"),
    ],
)
@pytest.mark.parametrize(
    "execution_gas_delta",
    [
        pytest.param(-10_000, id="floor_dominates"),
        pytest.param(-1, id="below_crossover"),
        pytest.param(0, id="at_crossover"),
        pytest.param(1, id="above_crossover"),
        pytest.param(10_000, id="execution_dominates"),
    ],
)
def test_access_list_data_cost_with_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    data: bytes,
    execution_gas_delta: int,
) -> None:
    """
    Charge the full surcharge on either side of the billing crossover.

    The execution gas is placed relative to the gas at which the
    intrinsic-plus-execution side meets the calldata floor.
    """
    access_list = [
        AccessList(address=Address(1), storage_keys=[Hash(0), Hash(1)])
    ]
    gas_costs = fork.gas_costs()
    surcharge = calculate_access_list_data_cost(access_list, fork)
    intrinsic_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_without_access_list = intrinsic_calculator(
        calldata=data,
        return_cost_deducted_prior_execution=True,
    )
    # The subject is the access-list schedule: derive the surcharge
    # separately from the calculator's handling of access lists.
    entry_charges = (
        gas_costs.TX_ACCESS_LIST_ADDRESS
        + 2 * gas_costs.TX_ACCESS_LIST_STORAGE_KEY
    )
    calldata_floor = fork.transaction_data_floor_cost_calculator()(data=data)
    execution_budget = (
        calldata_floor - intrinsic_without_access_list - entry_charges
    )
    # JUMPDEST is a one-gas operation; size the program from its modeled
    # cost so each case lands exactly where the delta places it.
    jumpdest_gas = Op.JUMPDEST.gas_cost(fork)
    assert execution_budget % jumpdest_gas == 0
    jumpdests = execution_budget // jumpdest_gas + execution_gas_delta
    assert jumpdests >= 0
    code = Op.JUMPDEST * jumpdests
    contract = pre.deploy_contract(code + Op.STOP)
    execution_cost = (
        intrinsic_without_access_list + entry_charges + code.gas_cost(fork)
    )
    assert (
        execution_cost - calldata_floor == execution_gas_delta * jumpdest_gas
    )
    expected_gas_used = max(execution_cost, calldata_floor) + surcharge

    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        access_list=access_list,
        # Surplus gas distinguishes actual billing from simply burning
        # a gas limit that happens to equal the expected receipt value.
        gas_limit=expected_gas_used + 1000,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    state_test(pre=pre, post={}, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize("self_transfer", [False, True])
@pytest.mark.parametrize("value", [0, 1])
@pytest.mark.parametrize("floor_dominates", [False, True])
def test_access_list_surcharge_with_recipient_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    self_transfer: bool,
    value: int,
    floor_dominates: bool,
) -> None:
    """Preserve the surcharge with self-transfer and value-transfer bases."""
    sender = pre.fund_eoa()
    target = sender if self_transfer else pre.fund_eoa(amount=1)
    access_list = [AccessList(address=target, storage_keys=[])]
    recipient_type = RecipientType.SELF if self_transfer else RecipientType.EOA
    data = b"\x00" * (400 if floor_dominates else 0)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=data,
        sends_value=value > 0,
        recipient_type=recipient_type,
        return_cost_deducted_prior_execution=True,
    )
    floor = fork.transaction_data_floor_cost_calculator()(
        data=data, sends_value=value > 0, recipient_type=recipient_type
    )
    costs = fork.gas_costs()
    execution_cost = intrinsic + costs.TX_ACCESS_LIST_ADDRESS
    surcharge = calculate_access_list_data_cost(access_list, fork)
    assert (floor > execution_cost) == floor_dominates
    expected_gas = max(execution_cost, floor) + surcharge
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=target,
        value=value,
        data=data,
        access_list=access_list,
        gas_limit=expected_gas + 1000,
        expected_receipt=TransactionReceipt(status=1, gas_used=expected_gas),
    )
    state_test(pre=pre, post={}, tx=tx)
