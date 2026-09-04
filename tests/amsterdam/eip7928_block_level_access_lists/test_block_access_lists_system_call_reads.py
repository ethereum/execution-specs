"""
Tests for EIP-7928 block access lists when the post-execution system calls
still owe storage reads that no transaction paid for.
"""

from typing import Type

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Environment,
    FeeSystemContractRequest,
    Fork,
    Header,
    Macros,
    SystemCallPhase,
    SystemContractInteractionTransaction,
    Transaction,
)
from execution_testing.test_types.block_access_list.modifiers import (
    insert_storage_read,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

# Room for two blocks' worth of every request type in one enqueue block.
BLOCK_GAS_LIMIT = 100_000_000


def _queued_request_types(fork: Fork) -> list[Type[FeeSystemContractRequest]]:
    """Return the fork's queued request classes in request type order."""
    queued_request_types = [
        request_type
        for request_type in fork.system_contract_request_types()
        if issubclass(request_type, FeeSystemContractRequest)
    ]
    return sorted(queued_request_types, key=lambda cls: cls.type)


def _enqueue_requests(
    request_class: Type[FeeSystemContractRequest], count: int
) -> list[FeeSystemContractRequest]:
    """Return `count` requests, each paying the fee it owes."""
    return [
        request_class.from_index(i).copy(fee=fee)
        for i, fee in enumerate(request_class.get_enqueue_fees(count))
    ]


def _dequeue_reads(
    request_class: Type[FeeSystemContractRequest], start_index: int, count: int
) -> list[int]:
    """Return the slots a dequeue of `count` requests reads, ascending."""
    return [request_class.count_slot] + request_class.record_slots(
        start_index, count
    )


def _drained_queue_changes(
    request_class: Type[FeeSystemContractRequest], block_access_index: int
) -> list[BalStorageSlot]:
    """Return the head and tail resets of a sweep that drains the queue."""
    return [
        BalStorageSlot(
            slot=slot,
            slot_changes=[
                BalStorageChange(
                    block_access_index=block_access_index, post_value=0
                )
            ],
        )
        for slot in (
            request_class.queue_head_slot,
            request_class.queue_tail_slot,
        )
    ]


def _split_gas(total: int, cap: int) -> list[int]:
    """Split `total` gas into chunks of at most `cap`."""
    assert total >= 0, "the gas to burn must not be negative"
    full, rest = divmod(total, cap)
    return [cap] * full + ([rest] if rest else [])


@pytest.mark.parametrize(
    "leftover_gas_case",
    [
        "one_short_of_pending_reads",
        "block_full",
        "block_packed_with_cheapest_txs",
    ],
)
def test_bal_pending_system_call_reads_vs_leftover_gas(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    leftover_gas_case: str,
) -> None:
    """
    A block stays valid however little gas it leaves for the storage reads
    its post-execution system calls still owe. The dequeues spend no block
    gas, so a gas-feasibility check on those reads (`BLOCK_ACCESS_LIST_ITEM`
    each) would wrongly reject these blocks; see ethereum/EIPs#12277.
    """
    request_types = _queued_request_types(fork)
    post_execution_contracts = {
        address
        for address, phase in fork.system_contract_call_phases().items()
        if phase is SystemCallPhase.AFTER_TRANSACTIONS
    }
    assert post_execution_contracts == {
        cls.system_contract_address for cls in request_types
    }, (
        f"{fork} calls a system contract after its transactions that this "
        "test does not model as a request queue"
    )

    enqueue_txs: list[Transaction] = []
    pending_reads: dict[Address, list[int]] = {}
    post: dict[Address, Account] = {}
    for request_class in request_types:
        # Block 1 dequeues the first block's worth, block 2 the second.
        requests = _enqueue_requests(
            request_class, 2 * request_class.max_per_block
        )
        interaction = SystemContractInteractionTransaction(requests=requests)
        enqueue_txs += interaction.update_pre(pre).transactions()
        address = request_class.system_contract_address
        pending_reads[address] = _dequeue_reads(
            request_class,
            start_index=request_class.max_per_block,
            count=request_class.max_per_block,
        )
        post[address] = Account(balance=sum(r.value for r in requests))

    pending_read_count = sum(len(reads) for reads in pending_reads.values())
    read_budget = pending_read_count * fork.gas_costs().BLOCK_ACCESS_LIST_ITEM
    cheapest_tx = fork.transaction_intrinsic_cost_calculator()(calldata=b"")
    tx_gas_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_cap is not None, f"{fork} has no transaction gas limit cap"

    tail_length = 0
    if leftover_gas_case == "one_short_of_pending_reads":
        leftover_gas = read_budget - 1
    elif leftover_gas_case == "block_full":
        leftover_gas = 0
    elif leftover_gas_case == "block_packed_with_cheapest_txs":
        # Filling the gas below the budget with the cheapest transactions
        # puts every late transaction boundary short of the pending reads.
        tail_length, leftover_gas = divmod(read_budget - 1, cheapest_tx)
        assert tail_length > 0, "the window must fit a cheapest transaction"
    else:
        raise ValueError(f"unhandled leftover_gas_case {leftover_gas_case}")

    burn_gas = BLOCK_GAS_LIMIT - leftover_gas - tail_length * cheapest_tx
    gas_limits = _split_gas(burn_gas, tx_gas_cap) + [cheapest_tx] * tail_length
    assert min(gas_limits) >= cheapest_tx, (
        "every burn must cover its intrinsic cost"
    )

    # Each burn runs out of gas, so it spends exactly its gas limit.
    burner = pre.deploy_contract(code=Macros.OOG)
    sender = pre.fund_eoa()
    burn_txs = [
        Transaction(sender=sender, to=burner, gas_limit=gas_limit)
        for gas_limit in gas_limits
    ]
    system_call_index = len(burn_txs) + 1

    account_expectations = {}
    for request_class in request_types:
        address = request_class.system_contract_address
        account_expectations[address] = BalAccountExpectation(
            storage_reads=pending_reads[address],
            storage_changes=_drained_queue_changes(
                request_class, system_call_index
            ),
        )

    blockchain_test(
        pre=pre,
        blocks=[
            # Nothing checks the hundreds of enqueue receipts.
            Block(txs=enqueue_txs, include_receipts_in_output=False),
            Block(
                txs=burn_txs,
                header_verify=Header(
                    gas_limit=BLOCK_GAS_LIMIT,
                    gas_used=BLOCK_GAS_LIMIT - leftover_gas,
                ),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            ),
        ],
        post=post,
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
    )


@pytest.mark.exception_test
@pytest.mark.parametrize_by_fork(
    "request_class",
    lambda fork: [
        pytest.param(cls, id=cls.__name__)
        for cls in _queued_request_types(fork)
    ],
)
def test_bal_invalid_phantom_read_on_request_predeploy(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    A phantom storage read declared on a request predeploy is rejected. The
    predeploys' reads escape gas accounting, which a client may special-case,
    but not validation.
    """
    predeploy = request_class.system_contract_address
    # An empty queue's sweep never reaches the first record slot.
    phantom_slot = request_class.queue_offset

    blockchain_test(
        pre=pre,
        # The block is rejected, and the queue it declares a read on is empty.
        post={predeploy: Account(storage={})},
        blocks=[
            Block(
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        predeploy: BalAccountExpectation(
                            storage_reads=[request_class.count_slot]
                        ),
                    }
                ).modify(insert_storage_read(predeploy, phantom_slot)),
            )
        ],
    )
