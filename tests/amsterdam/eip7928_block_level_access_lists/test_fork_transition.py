"""Fork-transition tests for EIP-7928 (Block-level Access Lists)."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    EIPChecklist,
    EngineAPIError,
    Environment,
    Hash,
    Header,
    Op,
    SystemContractInteractionTransaction,
    Transaction,
    TransactionReceipt,
    TransitionFork,
)
from execution_testing.forks.forks.eips.amsterdam.eip_8253 import (
    EIP_8253_TARGETED_ACCOUNTS,
)

from ..eip7708_eth_transfer_logs.spec import transfer_log
from ..eip8282_builder_execution_requests.helpers import (
    BuilderDepositRequest,
    BuilderExitRequest,
)
from ..eip8282_builder_execution_requests.spec import Spec as Spec8282
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

FORK_TIMESTAMP = 15_000


@EIPChecklist.BlockHeaderField.Test.ForkTransition.Initial()
@pytest.mark.valid_at_transition_to("Amsterdam")
def test_bal_fork_transition_happy_path(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify that a BAL is produced at the Amsterdam activation block.

    - Pre-fork block (timestamp < 15_000): no BAL hash, no BAL body.
    - Activation block (timestamp == 15_000): BAL hash and body are present
      and match the actual access activity in the block.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    pre_fork_tx = Transaction(sender=alice, to=bob, value=100, gas_price=10)
    post_fork_tx = Transaction(sender=alice, to=bob, value=100, gas_price=10)

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[pre_fork_tx],
            header_verify=Header(
                block_access_list_hash=Header.EMPTY_FIELD,
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[post_fork_tx],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    alice: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=2)
                        ],
                    ),
                    bob: BalAccountExpectation(
                        balance_changes=[
                            BalBalanceChange(
                                block_access_index=1, post_balance=200
                            ),
                        ],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={bob: Account(balance=200)},
    )


@EIPChecklist.BlockHeaderField.Test.ForkTransition.Before()
@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.exception_test
def test_invalid_pre_fork_block_with_bal_hash_field(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a pre-Amsterdam block whose header carries
    `block_access_list_hash`.

    The engine fixture sends a pre-Amsterdam `newPayload` carrying an
    empty `blockAccessList` param; the client's reconstructed header
    omits the hash, so the block hash check fails.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=receiver, value=100, gas_price=10)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP - 1,
                txs=[tx],
                rlp_modifier=Header(block_access_list_hash=Hash(0)),
                exception=BlockException.INVALID_BLOCK_HASH,
            ),
        ],
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.blockchain_test_engine_only
@pytest.mark.exception_test
def test_bal_invalid_engine_payload_field_before_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a pre-Amsterdam `newPayload` that carries a `blockAccessList`.

    The block and its header are otherwise valid, so the spurious payload
    field is the only defect: clients that silently drop unknown
    `newPayloadV4` fields would answer VALID and must fail this test.
    """
    sender = pre.fund_eoa()
    receiver = pre.nonexistent_account()

    tx = Transaction(sender=sender, to=receiver, value=100)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP - 1,
                txs=[tx],
                # A valid empty-BAL encoding: field presence alone, not
                # decodability, must trigger the rejection.
                engine_new_payload_block_access_list=Bytes(b"\xc0"),
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                engine_api_error_code=EngineAPIError.InvalidParams,
            ),
        ],
    )


@EIPChecklist.BlockHeaderField.Test.ForkTransition.After()
@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.exception_test
def test_invalid_post_fork_block_without_bal_hash_field(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject an Amsterdam activation block whose header is missing
    `block_access_list_hash`.

    The engine fixture sends `newPayloadV5` with the `blockAccessList`
    param omitted, which must return `-32602: Invalid params`.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=receiver, value=100, gas_price=10)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                rlp_modifier=Header(
                    block_access_list_hash=Header.REMOVE_FIELD,
                ),
                exception=BlockException.INVALID_BAL_HASH,
                engine_api_error_code=EngineAPIError.InvalidParams,
            ),
        ],
    )


@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.parametrize(
    "exceeds_limit_at_fork",
    [
        pytest.param(False, id="at_fork_within_budget"),
        pytest.param(
            True,
            marks=pytest.mark.exception_test,
            id="at_fork_over_budget",
        ),
    ],
)
def test_fork_transition_bal_size_constraint(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    exceeds_limit_at_fork: bool,
) -> None:
    """
    Verify the BAL size constraint applies only on/after Amsterdam.

    - Pre-fork block at a `gas_limit` that *would* fail the post-fork
      constraint is accepted (the constraint is not yet enforced).
    - Activation block at the exact budget is accepted.
    - Activation block one item over the budget is rejected with
      `BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED`.
    """
    amsterdam = fork.transitions_to()
    fork_transition_items = len(EIP_8253_TARGETED_ACCOUNTS)
    min_gas_limit = max(
        amsterdam.minimum_block_gas_limit(),
        (amsterdam.empty_block_bal_item_count() + fork_transition_items)
        * amsterdam.gas_costs().BLOCK_ACCESS_LIST_ITEM,
    )
    over_budget_gas_limit = min_gas_limit - 1

    pre_fork_block = Block(
        timestamp=FORK_TIMESTAMP - 1,
        txs=[],
    )

    if exceeds_limit_at_fork:
        at_fork_block = Block(
            timestamp=FORK_TIMESTAMP,
            txs=[],
            exception=BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED,
        )
        block_gas_limit = over_budget_gas_limit
    else:
        at_fork_block = Block(
            timestamp=FORK_TIMESTAMP,
            txs=[],
        )
        block_gas_limit = min_gas_limit

    blockchain_test(
        pre=pre,
        post={},
        blocks=[pre_fork_block, at_fork_block],
        genesis_environment=Environment(gas_limit=block_gas_limit),
    )


def _single_request_bus_expectation(
    enqueue_index: int, system_call_index: int, post_balance: int
) -> BalAccountExpectation:
    """
    Build the BAL expectation for a builder predeploy dequeuing a single
    request in a clean sweep: count and queue tail rise to one and reset,
    while the excess and head slots stay read-only.
    """

    def bus_slot_changes() -> list:
        return [
            BalStorageChange(block_access_index=enqueue_index, post_value=1),
            BalStorageChange(
                block_access_index=system_call_index, post_value=0
            ),
        ]

    return BalAccountExpectation(
        balance_changes=[
            BalBalanceChange(
                block_access_index=enqueue_index, post_balance=post_balance
            )
        ],
        storage_changes=[
            BalStorageSlot(
                slot=Spec8282.COUNT_STORAGE_SLOT,
                slot_changes=bus_slot_changes(),
            ),
            BalStorageSlot(
                slot=Spec8282.QUEUE_TAIL_STORAGE_SLOT,
                slot_changes=bus_slot_changes(),
            ),
        ],
        storage_reads=[
            Spec8282.EXCESS_STORAGE_SLOT,
            Spec8282.QUEUE_HEAD_STORAGE_SLOT,
        ],
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
def test_bal_fork_transition_builder_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the BAL of an activation block that dequeues EIP-8282 builder
    requests.

    The first Amsterdam block carries the chain's first builder deposit
    and exit requests: the BAL must record both predeploys' request-bus
    slots, the enqueuing transaction indices, and the clean-sweep dequeue
    by the post-execution system calls.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    deposit = BuilderDepositRequest(
        pubkey=1,
        withdrawal_credentials=2,
        amount=Spec8282.BUILDER_MIN_DEPOSIT // 10**9,
        signature=3,
        fee=BuilderDepositRequest.get_fee(0),
    )
    builder_exit = BuilderExitRequest(
        pubkey=1, fee=BuilderExitRequest.get_fee(0)
    )

    deposit_interaction = SystemContractInteractionTransaction(
        requests=[deposit]
    ).update_pre(pre)
    exit_interaction = SystemContractInteractionTransaction(
        requests=[builder_exit]
    ).update_pre(pre)
    txs = deposit_interaction.transactions() + exit_interaction.transactions()
    system_call_index = len(txs) + 1

    deposit_sender = deposit_interaction.sender_account
    exit_sender = exit_interaction.sender_account
    assert deposit_sender is not None and exit_sender is not None

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[Transaction(sender=alice, to=bob, value=100, gas_price=10)],
            header_verify=Header(
                block_access_list_hash=Header.EMPTY_FIELD,
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=txs,
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    deposit_sender: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=1)
                        ],
                    ),
                    exit_sender: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=2, post_nonce=1)
                        ],
                    ),
                    Address(
                        Spec8282.BUILDER_DEPOSIT_CONTRACT_ADDRESS
                    ): _single_request_bus_expectation(
                        1, system_call_index, deposit.value
                    ),
                    Address(
                        Spec8282.BUILDER_EXIT_CONTRACT_ADDRESS
                    ): _single_request_bus_expectation(
                        2, system_call_index, builder_exit.value
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            Address(Spec8282.BUILDER_DEPOSIT_CONTRACT_ADDRESS): Account(
                balance=deposit.value
            ),
            Address(Spec8282.BUILDER_EXIT_CONTRACT_ADDRESS): Account(
                balance=builder_exit.value
            ),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
def test_bal_fork_transition_transfers_and_storage(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the BAL of an activation block with ordinary transfers,
    storage writes and Transfer logs.

    The first Amsterdam block mixes a plain EOA transfer with a contract
    call that writes storage and forwards value: the BAL must carry the
    balance and storage changes while the receipts carry the EIP-7708
    Transfer logs.
    """
    transfer_value = 100
    forward_value = 500

    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    carol = pre.fund_eoa()
    dave = pre.fund_eoa(amount=0)
    relay = pre.deploy_contract(
        code=Op.SSTORE(0, 1)
        + Op.POP(Op.CALL(Op.GAS, dave, forward_value, 0, 0, 0, 0)),
        balance=forward_value,
    )

    pre_fork_tx = Transaction(
        sender=alice, to=bob, value=transfer_value, gas_price=10
    )
    tx_transfer = Transaction(
        sender=alice,
        to=bob,
        value=transfer_value,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(alice, bob, transfer_value)]
        ),
    )
    tx_relay = Transaction(
        sender=carol,
        to=relay,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(relay, dave, forward_value)]
        ),
    )

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[pre_fork_tx],
            header_verify=Header(
                block_access_list_hash=Header.EMPTY_FIELD,
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[tx_transfer, tx_relay],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    alice: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=2)
                        ],
                    ),
                    bob: BalAccountExpectation(
                        balance_changes=[
                            BalBalanceChange(
                                block_access_index=1,
                                post_balance=transfer_value * 2,
                            )
                        ],
                    ),
                    carol: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=2, post_nonce=1)
                        ],
                    ),
                    relay: BalAccountExpectation(
                        balance_changes=[
                            BalBalanceChange(
                                block_access_index=2, post_balance=0
                            )
                        ],
                        storage_changes=[
                            BalStorageSlot(
                                slot=0,
                                slot_changes=[
                                    BalStorageChange(
                                        block_access_index=2, post_value=1
                                    )
                                ],
                            )
                        ],
                    ),
                    dave: BalAccountExpectation(
                        balance_changes=[
                            BalBalanceChange(
                                block_access_index=2,
                                post_balance=forward_value,
                            )
                        ],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            bob: Account(balance=transfer_value * 2),
            dave: Account(balance=forward_value),
            relay: Account(balance=0, storage={0: 1}),
        },
    )
