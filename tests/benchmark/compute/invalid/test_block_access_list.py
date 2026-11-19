"""Benchmarks for blocks whose block access list is false."""

import itertools
import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, Iterator, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountChange,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BenchmarkTestFiller,
    Block,
    BlockAccessList,
    BlockAccessListExpectation,
    BlockException,
    Bytecode,
    Bytes,
    Environment,
    Fork,
    Header,
    Op,
    RecipientType,
    Storage,
    Transaction,
)
from execution_testing.test_types.block_access_list.expectations import (
    compose,
)
from execution_testing.test_types.block_access_list.modifiers import (
    BalScalarField,
    add_storage_reads,
    append_change,
    append_empty_slot,
    clear_all,
    duplicate_account,
    duplicate_balance_change,
    duplicate_code_change,
    duplicate_nonce_change,
    duplicate_slot_change,
    duplicate_storage_read,
    duplicate_storage_slot,
    encode_scalar_non_minimally,
    insert_accounts,
    insert_storage_read,
    keep_only,
    modify_balance,
    override_rlp,
    remove_account_strictly,
    remove_accounts,
    remove_balances,
    remove_nonces,
    reverse_accounts,
    reverse_balance_changes,
    reverse_code_changes,
    reverse_nonce_changes,
    reverse_slot_changes,
    reverse_storage_reads,
    reverse_storage_slots,
    swap_bal_indices,
    swap_last_two_accounts,
)

from tests.benchmark.helper.account_sender_receiver import (
    yield_distinct_nonexistent_receiver,
)
from tests.benchmark.helper.constants import (
    RECEIVER_BALANCE,
    TRANSFER_VALUE,
)

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.exception_test,
]

Modifier = Callable[[BlockAccessList], BlockAccessList]


class PaddedField(Enum):
    """Which field of each padded account holds the extra changes."""

    NONE = auto()
    BALANCE = auto()
    NONCE = auto()
    CODE = auto()
    STORAGE = auto()


@dataclass(frozen=True, kw_only=True)
class FalsifiableBlock:
    """A block to benchmark under a modified access list."""

    txs: List[Transaction]
    gas_used: int
    post: Dict[Address, Account] = field(default_factory=dict)
    fee_recipient: Address | None = None


@dataclass(frozen=True, kw_only=True)
class TransferBlock(FalsifiableBlock):
    """A block of ether transfers and the accounts a list can misstate."""

    sender: Address
    receivers: List[Address]


def ether_transfers(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> TransferBlock:
    """
    Build transfers to existing accounts that fill the gas target.

    Each receiver is distinct, so each balance change has its own block
    access index and a list can be made wrong at any point in the block.
    """
    # Every receiver already exists, so no transaction pays new-account
    # state gas and the block gas is the sum of the transfer costs.
    transfer_cost = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    ) + fork.transaction_top_frame_execution_gas(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    transfer_count = gas_benchmark_value // transfer_cost

    sender = pre.fund_eoa()
    # Tipped by every transfer, so it appears in every list.
    fee_recipient = pre.fund_eoa(amount=0)
    receivers = [pre.fund_eoa(RECEIVER_BALANCE) for _ in range(transfer_count)]
    return TransferBlock(
        # Explicit gas limits: the block must be exactly this full for
        # the `header_verify` in `benchmark_modified_list` to pin the
        # premise.
        txs=[
            Transaction(
                to=receiver,
                value=TRANSFER_VALUE,
                gas_limit=transfer_cost,
                sender=sender,
            )
            for receiver in receivers
        ],
        # The block is rejected, so no transfer lands.
        post={
            receiver: Account(balance=RECEIVER_BALANCE)
            for receiver in receivers
        },
        gas_used=transfer_count * transfer_cost,
        sender=sender,
        receivers=list(receivers),
        fee_recipient=fee_recipient,
    )


def nonexistent_addresses(count: int) -> List[Address]:
    """Return ``count`` addresses that hold no account."""
    return list(itertools.islice(yield_distinct_nonexistent_receiver(), count))


def item_budget(fork: Fork, block_gas_limit: int) -> int:
    """Return how many items EIP-7928 allows a list at this gas limit."""
    return block_gas_limit // fork.gas_costs().BLOCK_ACCESS_LIST_ITEM


def benchmark_modified_list(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    block: FalsifiableBlock,
    modifier: Modifier,
    exception: BlockException | List[BlockException],
    env: Environment | None = None,
) -> None:
    """Benchmark ``block`` with ``modifier`` applied to its list."""
    # Passed only when set: the filler fills an omitted `env` from its
    # fixture, whose gas limit differs from `Environment()`'s.
    kwargs = {"env": env} if env is not None else {}
    benchmark_test(
        pre=pre,
        post=block.post,
        blocks=[
            Block(
                txs=block.txs,
                fee_recipient=block.fee_recipient,
                # Pin the premise: the transactions used this much.
                header_verify=Header(gas_used=block.gas_used),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={},
                ).modify(modifier),
                exception=exception,
            )
        ],
        expected_benchmark_gas_used=block.gas_used,
        **kwargs,
    )


@pytest.mark.blockchain_test_engine_only
def test_list_the_header_does_not_name(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark an empty list sent under a header naming the real one.

    A client only hashes the list and compares it with the header, with
    no state or execution, so this is the baseline for the other
    benchmarks here.
    """
    block = ether_transfers(pre, fork, gas_benchmark_value)

    benchmark_test(
        pre=pre,
        post=block.post,
        blocks=[
            Block(
                txs=block.txs,
                fee_recipient=block.fee_recipient,
                header_verify=Header(gas_used=block.gas_used),
                # The payload does not carry the header's hash field, so
                # the only way to make the two disagree is the list.
                engine_new_payload_block_access_list=Bytes(b"\xc0"),
                exception=[
                    BlockException.INVALID_BLOCK_ACCESS_LIST,
                    BlockException.INVALID_BAL_HASH,
                    BlockException.INVALID_BLOCK_HASH,
                ],
            )
        ],
        expected_benchmark_gas_used=block.gas_used,
    )


def nonce_past_the_end(block: TransferBlock) -> Modifier:
    """Append a sender nonce change at an index past the block's end."""
    # Appended, not inserted: the index is above every index already
    # there, so the only thing wrong is the bound.
    last_index = len(block.txs)
    return append_change(
        block.sender,
        BalNonceChange(
            block_access_index=last_index + 2,
            post_nonce=last_index + 1,
        ),
    )


@pytest.mark.parametrize(
    "defect",
    # The sender pays for every transaction, so it is the one account whose
    # field lists are long enough to put out of order.
    [
        pytest.param(lambda _: reverse_accounts(), id="accounts_reversed"),
        pytest.param(
            lambda _: swap_last_two_accounts(),
            id="accounts_unsorted_at_end",
        ),
        pytest.param(
            lambda block: duplicate_account(block.sender),
            id="account_duplicated",
        ),
        pytest.param(
            lambda block: reverse_nonce_changes(block.sender),
            id="nonce_changes_reversed",
        ),
        pytest.param(
            lambda block: duplicate_nonce_change(block.sender, 1),
            id="nonce_change_duplicated",
        ),
        pytest.param(
            lambda block: reverse_balance_changes(block.sender),
            id="balance_changes_reversed",
        ),
        pytest.param(
            lambda block: duplicate_balance_change(block.sender, 1),
            id="balance_change_duplicated",
        ),
        # Every change is right; which transaction each is attributed to is
        # not, which also puts the indices out of order.
        pytest.param(
            lambda block: swap_bal_indices(1, len(block.txs)),
            id="indices_swapped",
        ),
        pytest.param(nonce_past_the_end, id="index_past_the_end"),
        pytest.param(
            lambda block: append_empty_slot(block.sender, 0),
            id="empty_slot_changes",
        ),
    ],
)
def test_malformed_list(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    defect: Callable[[TransferBlock], Modifier],
) -> None:
    """
    Benchmark a list that breaks an encoding rule.

    Each defect is visible without executing the block, so the time taken
    shows whether a client checks the list before executing.
    """
    block = ether_transfers(pre, fork, gas_benchmark_value)
    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        defect(block),
        [
            BlockException.INVALID_BLOCK_ACCESS_LIST,
            BlockException.INCORRECT_BLOCK_FORMAT,
        ],
    )


def surplus_code_change(block: TransferBlock, fork: Fork) -> Modifier:
    """Append a contract-sized code change to the sender."""
    # Nothing bounds the bytes a code change carries, so the largest a
    # true list could hold is a whole contract.
    return append_change(
        block.sender,
        BalCodeChange(
            block_access_index=len(block.txs),
            new_code=b"\x00" * fork.max_code_size(),
        ),
    )


@pytest.mark.parametrize(
    "defect",
    [
        # No items, no changes: the cheapest false list that exists.
        pytest.param(lambda *_: clear_all(), id="empty_list"),
        pytest.param(
            lambda block, _: keep_only(block.sender),
            id="only_the_sender",
        ),
        pytest.param(
            lambda block, _: remove_accounts(block.sender),
            id="sender_missing",
        ),
        pytest.param(
            lambda block, _: remove_nonces(block.sender),
            id="sender_nonces_missing",
        ),
        pytest.param(
            lambda block, _: remove_balances(block.sender),
            id="sender_balances_missing",
        ),
        # Strictly: the fee recipient is in the list only if the transactions
        # tipped it.
        pytest.param(
            lambda block, _: remove_account_strictly(block.fee_recipient),
            id="fee_recipient_missing",
        ),
        pytest.param(
            lambda block, _: remove_accounts(block.receivers[0]),
            id="first_receiver_missing",
        ),
        pytest.param(
            lambda block, _: remove_accounts(
                block.receivers[len(block.receivers) // 2]
            ),
            id="middle_receiver_missing",
        ),
        pytest.param(
            lambda block, _: remove_accounts(block.receivers[-1]),
            id="last_receiver_missing",
        ),
        pytest.param(
            lambda block, _: modify_balance(
                block.receivers[0],
                block_access_index=1,
                balance=RECEIVER_BALANCE + TRANSFER_VALUE + 1,
            ),
            id="first_balance_wrong",
        ),
        pytest.param(
            lambda block, _: modify_balance(
                block.receivers[-1],
                block_access_index=len(block.txs),
                balance=RECEIVER_BALANCE + TRANSFER_VALUE + 1,
            ),
            id="last_balance_wrong",
        ),
        # An account with no change at any index: no per-index comparison can
        # see it, only a comparison of the account sets.
        pytest.param(
            lambda *_: insert_accounts(
                [BalAccountChange(address=nonexistent_addresses(1)[0])]
            ),
            id="surplus_account",
        ),
        pytest.param(surplus_code_change, id="surplus_code_change"),
    ],
)
def test_untrue_list(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    defect: Callable[[TransferBlock, Fork], Modifier],
) -> None:
    """
    Benchmark a well-formed list that disagrees with execution.

    No encoding rule is broken, so a client can only catch the list by
    executing the block. The arms differ in where the disagreement first
    shows.
    """
    block = ether_transfers(pre, fork, gas_benchmark_value)
    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        defect(block, fork),
        BlockException.INVALID_BLOCK_ACCESS_LIST,
    )


# Slots on each account when storage is padded. Other fields put their
# changes on the account, so they pad no slots.
SLOTS_PER_ACCOUNT = 7

# What besu, nethermind and reth accept as one engine API request. A
# list past it is refused by the transport before a client has read a
# byte of it, which measures the transport and not the list.
ENGINE_API_REQUEST_LIMIT = 128 * 1024 * 1024

# Bytes one unbudgeted change adds to the list: a block access index, a
# small value, and an RLP header for each. The encoded figure is 6.61
# for all four fields alike, so no arm is favoured by the estimate
# being short; `PAYLOAD_SHARE` covers the difference.
BYTES_PER_CHANGE = 6

# What of one request the list may fill. The payload carries the block
# as well, and `BYTES_PER_CHANGE` rounds down, so leave a fifth of the
# request free for both.
PAYLOAD_SHARE = 4 / 5


def padded_items(
    fork: Fork, block_gas_limit: int, padded_field: PaddedField
) -> tuple[int, int, int]:
    """Return the accounts, slots per account and items carrying changes."""
    slots = SLOTS_PER_ACCOUNT if padded_field is PaddedField.STORAGE else 0
    accounts = item_budget(fork, block_gas_limit) // (slots + 1)
    if padded_field is PaddedField.STORAGE:
        return accounts, slots, accounts * slots
    return accounts, slots, accounts


def padded_change_cap(carrying: int) -> int:
    """Return the changes per item one engine API request will hold."""
    return int(
        ENGINE_API_REQUEST_LIMIT
        * PAYLOAD_SHARE
        // 2
        // (carrying * BYTES_PER_CHANGE)
    )


def zero_value_transfers(
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    max_transfers: int | None = None,
) -> FalsifiableBlock:
    """
    Build zero-value transfers that give the list its indices.

    ``max_transfers`` defaults to what a list padded on every slot can
    afford.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)
    transfer_cost = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    ) + fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    if max_transfers is None:
        _, _, slots = padded_items(
            fork, gas_benchmark_value, PaddedField.STORAGE
        )
        max_transfers = (
            ENGINE_API_REQUEST_LIMIT // 2 // (slots * BYTES_PER_CHANGE)
        )
    transfers = max(
        1, min(max_transfers, gas_benchmark_value // transfer_cost)
    )
    return FalsifiableBlock(
        txs=[
            Transaction(
                sender=sender,
                to=receiver,
                gas_limit=transfer_cost,
                value=0,
            )
            for _ in range(transfers)
        ],
        gas_used=transfers * transfer_cost,
    )


def padded_account(
    padded_field: PaddedField,
    address: Address,
    slots_per_account: int,
    changes_per_field: int,
    values: Iterator[int],
) -> BalAccountChange:
    """
    Return a fake account padded with changes in ``padded_field``.

    Each change takes the next number from ``values``, so no two are equal.
    """
    # A slot needs at least one change; padding storage fills it instead.
    changes_per_slot = 1
    if padded_field is PaddedField.STORAGE:
        changes_per_slot = changes_per_field

    slots = []
    for slot in range(slots_per_account):
        slot_changes = [
            BalStorageChange(block_access_index=i, post_value=next(values))
            for i in range(changes_per_slot)
        ]
        slots.append(BalStorageSlot(slot=slot, slot_changes=slot_changes))
    account = BalAccountChange(address=address, storage_changes=slots)

    match padded_field:
        case PaddedField.NONE:
            pass
        case PaddedField.STORAGE:
            # Carried by the slots above.
            pass
        case PaddedField.BALANCE:
            account.balance_changes = [
                BalBalanceChange(
                    block_access_index=i, post_balance=next(values)
                )
                for i in range(changes_per_field)
            ]
        case PaddedField.NONCE:
            account.nonce_changes = [
                BalNonceChange(block_access_index=i, post_nonce=next(values))
                for i in range(changes_per_field)
            ]
        case PaddedField.CODE:
            account.code_changes = [
                # Distinct code, so a client indexing by code hash holds
                # one entry per change rather than one in total.
                BalCodeChange(
                    block_access_index=i,
                    new_code=next(values).to_bytes(3, "big"),
                )
                for i in range(changes_per_field)
            ]
        case _:
            raise ValueError(f"unknown padded field: {padded_field}")
    return account


@pytest.mark.parametrize(
    "padded_field",
    [pytest.param(f, id=f.name.lower()) for f in PaddedField],
)
def test_padded_accounts(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    padded_field: PaddedField,
) -> None:
    """
    Benchmark fake accounts padded with changes the item limit ignores.

    The budget counts only addresses and unique storage slots. Each arm
    fills the list to the budget, then puts one uncounted change per block
    access index on every item, in the field ``padded_field`` names.
    """
    accounts, slots, carrying = padded_items(
        fork, gas_benchmark_value, padded_field
    )
    block = zero_value_transfers(
        pre, fork, gas_benchmark_value, padded_change_cap(carrying)
    )

    changes_per_field = 0
    if padded_field is not PaddedField.NONE:
        changes_per_field = len(block.txs)

    values = itertools.count(1)
    padded_accounts = [
        padded_account(
            padded_field=padded_field,
            address=address,
            slots_per_account=slots,
            changes_per_field=changes_per_field,
            values=values,
        )
        for address in nonexistent_addresses(accounts)
    ]

    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        insert_accounts(padded_accounts),
        BlockException.INVALID_BLOCK_ACCESS_LIST,
    )


@pytest.mark.parametrize(
    "padded_field",
    [
        pytest.param(PaddedField.CODE, id="code"),
        pytest.param(PaddedField.STORAGE, id="storage"),
    ],
)
def test_padded_accounts_on_a_full_block(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    padded_field: PaddedField,
) -> None:
    """Benchmark a padded list on a block that uses all its gas."""
    accounts, slots, carrying = padded_items(
        fork, gas_benchmark_value, padded_field
    )
    # Every index the gas target buys, not only the ones the list uses.
    block = zero_value_transfers(
        pre, fork, gas_benchmark_value, gas_benchmark_value
    )
    changes_per_field = min(padded_change_cap(carrying), len(block.txs))

    values = itertools.count(1)
    padded_accounts = [
        padded_account(
            padded_field=padded_field,
            address=address,
            slots_per_account=slots,
            changes_per_field=changes_per_field,
            values=values,
        )
        for address in nonexistent_addresses(accounts)
    ]

    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        insert_accounts(padded_accounts),
        BlockException.INVALID_BLOCK_ACCESS_LIST,
    )


# Mebibytes of false code in each rejected block.
REJECTED_LIST_MIB = 8


@pytest.mark.parametrize(
    "rejections",
    [pytest.param(n, id=f"{n}_blocks") for n in (1, 5, 10)],
)
def test_repeated_rejection(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    rejections: int,
) -> None:
    """Benchmark rejecting several false-list blocks at one height."""
    block = zero_value_transfers(pre, fork, gas_benchmark_value, 1)
    code_size = fork.max_code_size()
    changes = REJECTED_LIST_MIB * 1024 * 1024 // code_size

    blocks = []
    for attempt in range(rejections):
        # Distinct bytes per attempt, so no two rejected blocks hash
        # alike and none of them can be recognised and skipped.
        rng = random.Random(attempt)
        false_account = BalAccountChange(
            address=nonexistent_addresses(1)[0],
            code_changes=[
                BalCodeChange(
                    block_access_index=change,
                    new_code=rng.randbytes(code_size),
                )
                for change in range(changes)
            ],
        )
        blocks.append(
            Block(
                txs=block.txs,
                header_verify=Header(gas_used=block.gas_used),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={},
                ).modify(insert_accounts([false_account])),
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
            )
        )

    benchmark_test(
        pre=pre,
        post={},
        blocks=blocks,
        expected_benchmark_gas_used=block.gas_used,
    )


@pytest.mark.parametrize(
    "code_mib",
    # Code bytes each arm hangs off the list, in mebibytes. A client is
    # sent them as hex, so the payload carries twice this and the last
    # arm is as much code as `ENGINE_API_REQUEST_LIMIT` will hold. The
    # arms do not scale with the gas limit because nothing about them
    # is budgeted: the item budget counts no byte of a code change.
    [pytest.param(size, id=f"{size}MiB") for size in [4, 8, 16, 32, 56]],
)
def test_large_code_changes(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    code_mib: int,
) -> None:
    """
    Benchmark megabytes of code a block never deployed.

    EIP-7928 does not bound the bytes in a code change, and the item
    budget does not count them, so the arms use a few items and differ
    only in how many bytes they carry.
    """
    block = zero_value_transfers(pre, fork, gas_benchmark_value)

    # Each change is as large as a real contract can be.
    code_size = fork.max_code_size()
    change_count = code_mib * 1024 * 1024 // code_size

    # An account holds at most one change per transaction, so use as few
    # accounts as that allows and split the changes evenly between them.
    max_changes_per_account = len(block.txs)
    account_count = math.ceil(change_count / max_changes_per_account)
    changes_per_account = math.ceil(change_count / account_count)

    # Random so the bytes cannot be compressed; seeded so every fill
    # produces the same bytes.
    rng = random.Random(code_mib)

    padded_accounts = []
    for address in nonexistent_addresses(account_count):
        code_changes = [
            BalCodeChange(
                block_access_index=i, new_code=rng.randbytes(code_size)
            )
            for i in range(changes_per_account)
        ]
        padded_accounts.append(
            BalAccountChange(address=address, code_changes=code_changes)
        )

    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        insert_accounts(padded_accounts),
        BlockException.INVALID_BLOCK_ACCESS_LIST,
    )


@pytest.mark.parametrize(
    "far_over",
    [
        pytest.param(False, id="one_item_over"),
        pytest.param(True, id="far_over"),
    ],
)
def test_oversized_list(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    far_over: bool,
) -> None:
    """
    Benchmark a list with surplus accounts past the item budget.

    The arms differ in how far past the budget they go, and so in how much
    of the list a client reads before rejecting it.

    The gas limit is pinned so the budget is reachable. A stateful fixture
    ignores ``env`` and keeps its chain's gas limit, so there both arms
    are just large false lists.
    """
    block = ether_transfers(pre, fork, gas_benchmark_value)
    # Twice the gas target: room for the block, and a budget small enough
    # to exceed in a list the engine API will carry.
    gas_limit = gas_benchmark_value * 2
    item_limit = item_budget(fork, gas_limit)
    # The real list is the system contracts' items and one item per
    # account: the sender, the receivers and the fee recipient.
    real_items = fork.empty_block_bal_item_count() + len(block.receivers) + 2

    if far_over:
        target_items = 3 * item_limit
        # A storage read is the fewest bytes that still counts as an item.
        reads_per_account = 4
    else:
        target_items = item_limit + 1
        reads_per_account = 0

    items_per_account = 1 + reads_per_account
    account_count = (target_items - real_items) // items_per_account
    padded_accounts = [
        BalAccountChange(
            address=address,
            storage_reads=list(range(reads_per_account)),
        )
        for address in nonexistent_addresses(account_count)
    ]

    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        insert_accounts(padded_accounts),
        [
            BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED,
            BlockException.INVALID_BLOCK_ACCESS_LIST,
        ],
        env=Environment(gas_limit=gas_limit),
    )


@pytest.mark.parametrize(
    "one_account",
    [
        pytest.param(False, id="across_accounts"),
        pytest.param(True, id="one_account"),
    ],
)
def test_false_read_set(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    one_account: bool,
) -> None:
    """
    Benchmark a budget's worth of storage reads that never happened.

    The list stays within the item budget, so a client warms every
    declared slot before executing a block it then rejects. The arms carry
    the same reads, spread over every account of the block or put on one.
    """
    block = ether_transfers(pre, fork, gas_benchmark_value)
    item_limit = item_budget(fork, gas_benchmark_value)
    # The real list is one item per account: the sender, the receivers
    # and the fee recipient, none of which touches storage.
    account_count = len(block.receivers) + 2

    if one_account:
        # A new account: its address takes one item, its reads the rest.
        read_count = item_limit - account_count - 1
        modifier = insert_accounts(
            [
                BalAccountChange(
                    address=nonexistent_addresses(1)[0],
                    storage_reads=list(range(read_count)),
                )
            ]
        )
    else:
        # Each account already takes one item; its reads fill its share.
        reads_per_account = item_limit // account_count - 1
        modifier = add_storage_reads(reads_per_account)

    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        modifier,
        BlockException.INVALID_BLOCK_ACCESS_LIST,
    )


@dataclass(frozen=True, kw_only=True)
class StorageBlock(FalsifiableBlock):
    """A block of calls to one contract that writes and reads storage."""

    contract: Address
    sender: Address
    written_slots: List[int]
    read_slots: List[int]


def storage_writes(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> StorageBlock:
    """
    Build calls to a contract that writes two slots and reads two others.

    The contract's list entry then has several slots, several changes per
    slot and several reads: every storage list a defect can break.
    """
    # Every slot starts at 1, so each write goes from non-zero to
    # non-zero and every call costs the same.
    storage = Storage()
    code = Bytecode()

    written_slots: List[int] = []
    for _ in range(2):
        slot = storage.store_next(1)
        # Increment, so every call changes the slot and adds a change.
        code += Op.SSTORE(
            slot,
            Op.ADD(Op.SLOAD(slot), 1),
            key_warm=True,
            original_value=1,
            new_value=2,
        )
        written_slots.append(slot)

    read_slots: List[int] = []
    for _ in range(2):
        slot = storage.store_next(1)
        code += Op.POP(Op.SLOAD(slot))
        read_slots.append(slot)

    contract = pre.deploy_contract(code=code, storage=storage)
    sender = pre.fund_eoa()

    call_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_execution_gas()
        + code.gas_cost(fork)
    )
    call_count = gas_benchmark_value // call_gas
    txs = [
        Transaction(to=contract, gas_limit=call_gas, sender=sender)
        for _ in range(call_count)
    ]
    return StorageBlock(
        txs=txs,
        gas_used=call_count * call_gas,
        contract=contract,
        sender=sender,
        written_slots=written_slots,
        read_slots=read_slots,
    )


def two_code_changes(account: Address) -> Modifier:
    """Append two code changes to ``account``."""
    # No block gives one account two code changes, so the ordering and
    # uniqueness of that list can only be broken by writing the pair the
    # rule is about.
    return compose(
        append_change(
            account,
            BalCodeChange(block_access_index=1, new_code=b"\x01"),
        ),
        append_change(
            account,
            BalCodeChange(block_access_index=2, new_code=b"\x02"),
        ),
    )


@pytest.mark.parametrize(
    "defect",
    [
        pytest.param(
            lambda block: reverse_storage_slots(block.contract),
            id="slots_reversed",
        ),
        pytest.param(
            lambda block: reverse_slot_changes(
                block.contract, block.written_slots[0]
            ),
            id="slot_changes_reversed",
        ),
        pytest.param(
            lambda block: reverse_storage_reads(block.contract),
            id="reads_reversed",
        ),
        pytest.param(
            lambda block: duplicate_storage_slot(
                block.contract, block.written_slots[0]
            ),
            id="slot_duplicated",
        ),
        pytest.param(
            lambda block: duplicate_slot_change(
                block.contract, block.written_slots[0], 1
            ),
            id="slot_change_duplicated",
        ),
        pytest.param(
            lambda block: duplicate_storage_read(
                block.contract, block.read_slots[0]
            ),
            id="read_duplicated",
        ),
        # A slot may be read or changed, never both, and this one is already
        # in the account's changes.
        pytest.param(
            lambda block: insert_storage_read(
                block.contract, block.written_slots[0]
            ),
            id="read_of_written_slot",
        ),
        pytest.param(
            lambda block: compose(
                two_code_changes(block.contract),
                reverse_code_changes(block.contract),
            ),
            id="code_changes_reversed",
        ),
        pytest.param(
            lambda block: compose(
                two_code_changes(block.contract),
                duplicate_code_change(block.contract, 1),
            ),
            id="code_change_duplicated",
        ),
    ],
)
def test_malformed_storage_list(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    defect: Callable[[StorageBlock], Modifier],
) -> None:
    """
    Benchmark a list that breaks a storage or code encoding rule.

    EIP-7928 requires an account's slots, each slot's changes, its reads
    and its code changes to be ordered and unique, and forbids a slot
    being both read and changed. None of these checks needs the block, so
    the time taken shows whether a client runs them before executing.
    """
    block = storage_writes(pre, fork, gas_benchmark_value)
    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        defect(block),
        [
            BlockException.INVALID_BLOCK_ACCESS_LIST,
            BlockException.INCORRECT_BLOCK_FORMAT,
        ],
    )


@pytest.mark.parametrize(
    "field",
    # Scalars EIP-7928 requires in minimal big-endian form. The storage
    # fields sit on the contract; the balance and the index, read off a
    # balance change, sit on the sender, who pays for every call.
    [
        "storage_slot",
        "storage_value",
        "storage_read",
        "balance",
        "block_access_index",
    ],
)
# Re-encoded bytes reach a client only in an engine payload.
@pytest.mark.blockchain_test_engine_only
def test_non_minimal_scalar(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    field: BalScalarField,
) -> None:
    """
    Benchmark a list whose scalar carries a leading zero byte.

    The header commits to these bytes, so another encoding of the same
    value is a different list. A client that skips the minimality check
    accepts a second encoding of a block it already has.
    """
    block = storage_writes(pre, fork, gas_benchmark_value)
    on_sender = field in ("balance", "block_access_index")
    account = block.sender if on_sender else block.contract
    benchmark_modified_list(
        benchmark_test,
        pre,
        block,
        override_rlp(encode_scalar_non_minimally(account, field)),
        [
            BlockException.INVALID_BLOCK_ACCESS_LIST,
            BlockException.INCORRECT_BLOCK_FORMAT,
            BlockException.INVALID_BLOCK_HASH,
        ],
    )
