"""Tests for the chain invariants checked on filled blocks."""

from typing import Any, Callable, Dict, List, Optional

import pytest

from execution_testing.base_types import Address
from execution_testing.client_clis import Result
from execution_testing.client_clis.cli_types import OpcodeCount
from execution_testing.evm_tools.t8n.evm_trace.bal_witness import BalWitness
from execution_testing.forks import Amsterdam, Cancun, Fork, Osaka, Shanghai
from execution_testing.test_types import (
    Account,
    Alloc,
    TransactionReceipt,
)
from execution_testing.test_types.block_access_list import (
    BalAccountChange,
    BalBalanceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessList,
)
from execution_testing.vm import Op

from ..invariants import (
    BlockTotals,
    InvariantViolation,
    check_bal_access_witness,
    check_bal_against_state_diff,
    check_ether_conservation,
    check_gas_accounting,
    check_nonce_monotonicity,
)

ACCOUNT = Address(0x1234)


def result(
    gas_used: int = 0,
    cumulative: List[int | None] | None = None,
    opcodes: Dict[Op, int] | None = None,
) -> Result:
    """Return a transition tool result with the fields the checks read."""
    return Result(
        state_root=0,
        transactions_trie=0,
        receipts_root=0,
        logs_hash=0,
        logs_bloom=0,
        receipts=[
            TransactionReceipt(cumulative_gas_used=gas)
            for gas in cumulative or []
        ],
        gas_used=gas_used,
        opcode_count=(
            None if opcodes is None else OpcodeCount.model_validate(opcodes)
        ),
    )


def totals(gas_used: int = 0, receipts_gas_used: int = 0) -> BlockTotals:
    """Return block totals with no fees and no issuance."""
    return BlockTotals(
        gas_limit=30_000_000,
        gas_used=gas_used,
        receipts_gas_used=receipts_gas_used,
        base_fee_per_gas=0,
        blob_gas_used=0,
        blob_gas_price=0,
        issued=0,
    )


def alloc(**account: Any) -> Alloc:
    """Return an allocation holding one account."""
    return Alloc({ACCOUNT: Account(**account)})


def violated(check: Callable[[], None]) -> Optional[InvariantViolation]:
    """Run a check and return the violation it raised, or `None`."""
    try:
        check()
    except InvariantViolation as violation:
        return violation
    return None


def name_of(violation: Optional[InvariantViolation]) -> Optional[str]:
    """Return the invariant a violation names, or `None`."""
    return violation.invariant if violation is not None else None


@pytest.mark.parametrize(
    "gas_used,expected",
    [
        pytest.param(700, None, id="equal"),
        pytest.param(699, "receipt_gas_totals", id="below"),
        pytest.param(701, "receipt_gas_totals", id="above"),
    ],
)
def test_receipts_equal_header_gas_before_eip7778(
    gas_used: int, expected: Optional[str]
) -> None:
    """Before EIP-7778 the last receipt equals the header's gas used."""
    violation = violated(
        lambda: check_gas_accounting(
            Osaka, result(gas_used, [200, 700]), totals(gas_used, 700)
        )
    )
    assert name_of(violation) == expected


RECEIPTS_GAS = 1000
REFUND_QUOTIENT = Amsterdam.max_refund_quotient()
LOWEST_HEADER_GAS = RECEIPTS_GAS // len(Amsterdam.block_gas_dimensions())
HIGHEST_HEADER_GAS = RECEIPTS_GAS * REFUND_QUOTIENT // (REFUND_QUOTIENT - 1)


@pytest.mark.parametrize(
    "gas_used,expected",
    [
        pytest.param(LOWEST_HEADER_GAS, None, id="lowest"),
        pytest.param(
            LOWEST_HEADER_GAS - 1, "receipt_gas_totals", id="below_lowest"
        ),
        pytest.param(HIGHEST_HEADER_GAS, None, id="highest"),
        pytest.param(
            HIGHEST_HEADER_GAS + 1, "receipt_gas_totals", id="above_highest"
        ),
    ],
)
def test_header_gas_bounds_with_two_dimensions(
    gas_used: int, expected: Optional[str]
) -> None:
    """
    With EIP-7778 and EIP-8037 the header lies between the receipts split
    over the gas dimensions and the receipts plus the largest refund.
    """
    violation = violated(
        lambda: check_gas_accounting(
            Amsterdam,
            result(gas_used, [400, RECEIPTS_GAS]),
            totals(gas_used, RECEIPTS_GAS),
        )
    )
    assert name_of(violation) == expected


def test_receipt_without_cumulative_gas() -> None:
    """A receipt missing its cumulative gas is reported, not skipped."""
    violation = violated(
        lambda: check_gas_accounting(
            Osaka, result(700, [200, None, 700]), totals(700, 700)
        )
    )
    assert name_of(violation) == "receipt_gas_monotonicity"


@pytest.mark.parametrize(
    "fork,opcodes,post_balance,expected",
    [
        pytest.param(
            Osaka, {Op.SELFDESTRUCT: 1}, 95, None, id="burn_before_eip8246"
        ),
        pytest.param(Osaka, None, 95, None, id="burn_without_opcode_counts"),
        pytest.param(
            Osaka,
            {},
            95,
            "ether_conservation",
            id="burn_without_selfdestruct",
        ),
        pytest.param(
            Osaka,
            {Op.SELFDESTRUCT: 1},
            105,
            "ether_conservation",
            id="mint_before_eip8246",
        ),
        pytest.param(
            Amsterdam,
            {Op.SELFDESTRUCT: 1},
            95,
            "ether_conservation",
            id="burn_with_eip8246",
        ),
    ],
)
def test_selfdestruct_may_only_burn_before_eip8246(
    fork: Fork,
    opcodes: Dict[Op, int] | None,
    post_balance: int,
    expected: Optional[str],
) -> None:
    """A block that ran SELFDESTRUCT may lose ether only before EIP-8246."""
    violation = violated(
        lambda: check_ether_conservation(
            fork,
            alloc(balance=100),
            alloc(balance=post_balance),
            result(opcodes=opcodes),
            totals(),
        )
    )
    assert name_of(violation) == expected


@pytest.mark.parametrize(
    "fork,opcodes,expected",
    [
        pytest.param(
            Shanghai,
            {},
            "nonce_never_decreases",
            id="without_selfdestruct_before_eip6780",
        ),
        pytest.param(
            Shanghai,
            {Op.SELFDESTRUCT: 1},
            None,
            id="with_selfdestruct_before_eip6780",
        ),
        pytest.param(
            Cancun,
            {Op.SELFDESTRUCT: 1},
            "nonce_never_decreases",
            id="with_selfdestruct_from_eip6780",
        ),
    ],
)
def test_nonce_decreases_only_with_selfdestruct_before_eip6780(
    fork: Fork, opcodes: Dict[Op, int], expected: Optional[str]
) -> None:
    """Only a SELFDESTRUCT before EIP-6780 can lower a nonce."""
    violation = violated(
        lambda: check_nonce_monotonicity(
            fork, alloc(nonce=2), alloc(nonce=0), [], result(opcodes=opcodes)
        )
    )
    assert name_of(violation) == expected


def bal(**changes: Any) -> BlockAccessList:
    """Return a BAL with one account entry."""
    return BlockAccessList([BalAccountChange(address=ACCOUNT, **changes)])


def balances(*values: int) -> List[BalBalanceChange]:
    """Return balance changes at consecutive indices."""
    return [
        BalBalanceChange(block_access_index=index + 1, post_balance=value)
        for index, value in enumerate(values)
    ]


@pytest.mark.parametrize(
    "recorded,expected",
    [
        pytest.param(balances(7), None, id="recorded"),
        pytest.param(balances(9, 7), None, id="recorded_twice"),
        pytest.param([], "bal_state_diff", id="missing"),
        pytest.param(balances(6), "bal_state_diff", id="last_value_differs"),
        pytest.param(balances(5, 7), "bal_state_diff", id="no_op_change"),
    ],
)
def test_bal_balance_against_state_diff(
    recorded: List[BalBalanceChange], expected: Optional[str]
) -> None:
    """A balance going from 5 to 7 must end at 7 with no repeated value."""
    violation = violated(
        lambda: check_bal_against_state_diff(
            alloc(balance=5), alloc(balance=7), bal(balance_changes=recorded)
        )
    )
    assert name_of(violation) == expected


@pytest.mark.parametrize(
    "post_storage,expected",
    [
        pytest.param({1: 0}, "bal_state_diff", id="netted_to_zero"),
        pytest.param({}, "bal_state_diff", id="absent_means_zero"),
        pytest.param({1: 1}, None, id="kept"),
    ],
)
def test_bal_storage_no_op_change(
    post_storage: Dict[int, int], expected: Optional[str]
) -> None:
    """A slot recorded as written back to its pre-state value is a no-op."""
    recorded = [
        BalStorageSlot(
            slot=1,
            slot_changes=[
                BalStorageChange(
                    block_access_index=1, post_value=post_storage.get(1, 0)
                )
            ],
        )
    ]
    violation = violated(
        lambda: check_bal_against_state_diff(
            alloc(storage={}),
            alloc(storage=post_storage),
            bal(storage_changes=recorded),
        )
    )
    assert name_of(violation) == expected


@pytest.mark.parametrize(
    "pre_nonce,post_storage,expected",
    [
        pytest.param(0, {}, None, id="storage_only_account_wiped"),
        pytest.param(1, {}, "bal_state_diff", id="account_with_nonce_cleared"),
        pytest.param(
            0,
            {1: 1, 2: 3},
            "bal_state_diff",
            id="storage_only_account_written",
        ),
    ],
)
def test_bal_storage_wipe_of_storage_only_account(
    pre_nonce: int, post_storage: Dict[int, int], expected: Optional[str]
) -> None:
    """
    Deleting a storage-only account wipes its storage, which the BAL
    cannot record, so only that account's storage is exempt, and only
    when it ends empty.
    """
    violation = violated(
        lambda: check_bal_against_state_diff(
            alloc(nonce=pre_nonce, storage={1: 1, 2: 2}),
            alloc(nonce=pre_nonce, storage=post_storage),
            bal(),
        )
    )
    assert name_of(violation) == expected


def test_bal_entry_for_an_account_absent_from_the_state() -> None:
    """A change recorded for an account in neither state is reported."""
    violation = violated(
        lambda: check_bal_against_state_diff(
            Alloc({}), Alloc({}), bal(balance_changes=balances(7))
        )
    )
    assert name_of(violation) == "bal_state_diff"


DROPPED = "accessed but absent from the BAL"
INVENTED = "in the BAL but never accessed"


@pytest.mark.parametrize(
    "listed,expected",
    [
        pytest.param(bal(storage_reads=[1, 2]), None, id="every_started_slot"),
        pytest.param(
            bal(storage_changes=[BalStorageSlot(slot=1, slot_changes=[])]),
            None,
            id="changed_slot",
        ),
        pytest.param(bal(storage_reads=[2]), DROPPED, id="dropped"),
        pytest.param(bal(storage_reads=[1, 9]), INVENTED, id="invented"),
        pytest.param(bal(storage_reads=[9]), DROPPED, id="both_sides"),
    ],
)
def test_bal_slots_between_witness_bounds(
    listed: BlockAccessList, expected: Optional[str]
) -> None:
    """
    Slots 1 and 2 were accessed and only slot 1's access completed, so the
    BAL must list slot 1 and may list slot 2. The dropped slot is reported
    before an invented one.
    """
    account = int.from_bytes(ACCOUNT, "big")
    witness = BalWitness(
        started=frozenset({(account, 1), (account, 2)}),
        ended=frozenset({(account, 1)}),
    )
    violation = violated(lambda: check_bal_access_witness(witness, listed))
    if expected is None:
        assert violation is None
    else:
        assert violation is not None
        assert violation.invariant == "bal_access_witness"
        assert violation.message.partition(" (")[0] == expected
