"""
Tests for EIP-7928 block access lists when the post-execution system calls
still owe storage reads that no transaction paid for.
"""

from dataclasses import dataclass

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
    SystemContractInteractionTransaction,
    Transaction,
)
from execution_testing.test_types.block_access_list.modifiers import (
    insert_storage_read,
)

from ...cancun.eip4788_beacon_root.spec import Spec as Spec4788
from ...prague.eip2935_historical_block_hashes_from_state.spec import (
    Spec as Spec2935,
)
from ...prague.eip6110_deposits.spec import Spec as Spec6110
from ...prague.eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
)
from ...prague.eip7002_el_triggerable_withdrawals.spec import Spec as Spec7002
from ...prague.eip7251_consolidations.helpers import ConsolidationRequest
from ...prague.eip7251_consolidations.spec import Spec as Spec7251
from ..eip8282_builder_execution_requests.helpers import (
    BuilderDepositRequest,
    BuilderExitRequest,
)
from ..eip8282_builder_execution_requests.spec import Spec as Spec8282
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

# Room for two blocks' worth of every request type in one enqueue block.
BLOCK_GAS_LIMIT = 100_000_000


@dataclass(frozen=True, kw_only=True)
class RequestBus:
    """A request predeploy whose system call dequeues queued records."""

    request_class: type[FeeSystemContractRequest]
    count_slot: int
    head_slot: int
    tail_slot: int
    queue_offset: int
    slots_per_request: int

    @property
    def address(self) -> Address:
        """Return the predeploy address."""
        return self.request_class.interaction_contract_address

    @property
    def max_per_block(self) -> int:
        """Return how many requests one system call dequeues at most."""
        return self.request_class.max_per_block

    def requests(self, count: int) -> list[FeeSystemContractRequest]:
        """Return requests to enqueue in one block, each paying its fee."""
        return [
            self.request_class.from_index(i).copy(fee=self._fee(i))
            for i in range(count)
        ]

    def _fee(self, index: int) -> int:
        request_class = self.request_class
        if request_class.excess_fee_processing == "call":
            excess = max(index - request_class.target_per_block, 0)
        elif request_class.excess_fee_processing == "block":
            excess = 0
        else:
            raise ValueError(
                "unhandled fee processing "
                f"{request_class.excess_fee_processing}"
            )
        return request_class.get_fee(excess)

    def dequeue_reads(self, start_index: int, count: int) -> list[int]:
        """Return the slots a dequeue of `count` requests reads, ascending."""
        slots = [self.count_slot]
        for i in range(start_index, start_index + count):
            base = self.queue_offset + i * self.slots_per_request
            slots.extend(range(base, base + self.slots_per_request))
        return slots

    def drained_queue_changes(
        self, block_access_index: int
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
            for slot in (self.head_slot, self.tail_slot)
        ]


REQUEST_BUSES = [
    RequestBus(
        request_class=WithdrawalRequest,
        count_slot=Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT,
        head_slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
        tail_slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
        queue_offset=Spec7002.WITHDRAWAL_REQUEST_QUEUE_STORAGE_OFFSET,
        slots_per_request=Spec7002.WITHDRAWAL_REQUEST_QUEUE_SLOTS_PER_REQUEST,
    ),
    RequestBus(
        request_class=ConsolidationRequest,
        count_slot=Spec7251.CONSOLIDATION_REQUEST_COUNT_STORAGE_SLOT,
        head_slot=Spec7251.CONSOLIDATION_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
        tail_slot=Spec7251.CONSOLIDATION_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
        queue_offset=Spec7251.CONSOLIDATION_REQUEST_QUEUE_STORAGE_OFFSET,
        slots_per_request=(
            Spec7251.CONSOLIDATION_REQUEST_QUEUE_SLOTS_PER_REQUEST
        ),
    ),
    RequestBus(
        request_class=BuilderDepositRequest,
        count_slot=Spec8282.COUNT_STORAGE_SLOT,
        head_slot=Spec8282.QUEUE_HEAD_STORAGE_SLOT,
        tail_slot=Spec8282.QUEUE_TAIL_STORAGE_SLOT,
        queue_offset=Spec8282.QUEUE_STORAGE_OFFSET,
        slots_per_request=Spec8282.DEPOSIT_REQUEST_QUEUE_SLOTS_PER_REQUEST,
    ),
    RequestBus(
        request_class=BuilderExitRequest,
        count_slot=Spec8282.COUNT_STORAGE_SLOT,
        head_slot=Spec8282.QUEUE_HEAD_STORAGE_SLOT,
        tail_slot=Spec8282.QUEUE_TAIL_STORAGE_SLOT,
        queue_offset=Spec8282.QUEUE_STORAGE_OFFSET,
        slots_per_request=Spec8282.EXIT_REQUEST_QUEUE_SLOTS_PER_REQUEST,
    ),
]

# Beacon roots, history, and the deposit contract have no request queue.
SYSTEM_CONTRACTS_WITHOUT_QUEUE = {
    Address(Spec4788.BEACON_ROOTS_ADDRESS),
    Address(Spec2935.HISTORY_STORAGE_ADDRESS),
    Address(Spec6110.DEPOSIT_CONTRACT_ADDRESS),
}


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
    assert set(fork.system_contracts()) == (
        {bus.address for bus in REQUEST_BUSES} | SYSTEM_CONTRACTS_WITHOUT_QUEUE
    ), f"{fork} has a system contract this test does not classify"

    enqueue_txs: list[Transaction] = []
    pending_reads: dict[Address, list[int]] = {}
    post: dict[Address, Account] = {}
    for bus in REQUEST_BUSES:
        # Block 1 dequeues the first block's worth, block 2 the second.
        requests = bus.requests(2 * bus.max_per_block)
        interaction = SystemContractInteractionTransaction(requests=requests)
        enqueue_txs += interaction.update_pre(pre).transactions()
        pending_reads[bus.address] = bus.dequeue_reads(
            start_index=bus.max_per_block, count=bus.max_per_block
        )
        post[bus.address] = Account(balance=sum(r.value for r in requests))

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
                    account_expectations={
                        bus.address: BalAccountExpectation(
                            storage_reads=pending_reads[bus.address],
                            storage_changes=bus.drained_queue_changes(
                                system_call_index
                            ),
                        )
                        for bus in REQUEST_BUSES
                    }
                ),
            ),
        ],
        post=post,
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "bus", REQUEST_BUSES, ids=lambda bus: bus.request_class.__name__
)
def test_bal_invalid_phantom_read_on_request_predeploy(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    bus: RequestBus,
) -> None:
    """
    A phantom storage read declared on a request predeploy is rejected. The
    predeploys' reads escape gas accounting, which a client may special-case,
    but not validation.
    """
    # An empty queue's sweep never reaches the first record slot.
    phantom_slot = bus.queue_offset

    blockchain_test(
        pre=pre,
        # The block is rejected, and the queue it declares a read on is empty.
        post={bus.address: Account(storage={})},
        blocks=[
            Block(
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        bus.address: BalAccountExpectation(
                            storage_reads=[bus.count_slot]
                        ),
                    }
                ).modify(insert_storage_read(bus.address, phantom_slot)),
            )
        ],
    )
