"""
Gas tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List, Type

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    FeeSystemContractRequest,
    Fork,
    Header,
    Op,
    Requests,
    SystemContractInteractionMeasuredOutOfGasContract,
    Transaction,
    TransactionException,
    While,
)
from execution_testing import Macros as Om
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.with_all_system_contract_request_types(
        selector=lambda cls: issubclass(cls, FeeSystemContractRequest)
    ),
    # The tests pin the predeploys' exact balances and queue state, which
    # earlier transactions on a live network have already moved.
    pytest.mark.execute(
        pytest.mark.skip(reason="Asserts the state of the shared predeploys")
    ),
]


@EIPChecklist.SystemContract.Test.GasUsage.Dynamic.Oog()
@EIPChecklist.SystemContract.Test.GasUsage.Dynamic.Exact()
def test_request_gas_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    The relay measures the gas a request consumes at runtime, then forwards
    one gas less than required to the third request and exactly the required
    gas to the fourth. A predeploy with a small per-block cap dequeues the
    accepted records over two blocks.
    """
    # The predeploy ends with a warm SSTORE, which EIP-2200 rejects unless
    # more than the call stipend remains, so the requirement exceeds the
    # consumption by that sentry.
    warm_sstore = Op.SSTORE(
        key_warm=True, original_value=0, current_value=1, new_value=2
    ).gas_cost(fork)
    sentry_margin = fork.call_value_stipend() - warm_sstore + 1

    # Keep the boundary requests third and fourth: with the exit contract's
    # target of two, a later request is priced on a higher in-block count and
    # takes a different path than the measured one.
    requests: List[FeeSystemContractRequest] = [
        request_class.from_index(i).copy(fee=request_class.get_fee(0))
        for i in range(4)
    ]
    # Starved of gas by the relay contract.
    requests[2].valid = False
    interaction = SystemContractInteractionMeasuredOutOfGasContract(
        requests=requests,
        exact_gas_indices=[3],
        exact_gas_margin=sentry_margin,
    ).update_pre(pre)
    relay = interaction.request_source_address
    assert relay is not None
    predeploy = request_class.system_contract_address
    # The relay is funded for all four requests and pays for the three that
    # succeed.
    value = requests[0].value
    accepted = [
        request.with_source_address(relay)
        for request in requests
        if request.valid
    ]
    enqueued = len(accepted)
    per_block = request_class.max_per_block
    assert enqueued <= 2 * per_block, "the second block must drain the queue"

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=interaction.transactions(),
                header_verify=Header(
                    requests_hash=Requests(*accepted[:per_block])
                ),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        relay: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=value
                                )
                            ],
                        ),
                        predeploy: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=enqueued * value,
                                )
                            ],
                            storage_changes=[
                                BalStorageSlot(
                                    slot=request_class.count_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=enqueued,
                                        ),
                                        BalStorageChange(
                                            block_access_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                )
                            ],
                        ),
                    }
                ),
            ),
            Block(
                header_verify=Header(
                    requests_hash=Requests(*accepted[per_block:])
                )
            ),
        ],
        post={
            relay: Account(balance=value),
            predeploy: Account(balance=enqueued * value),
        },
    )


@pytest.mark.parametrize(
    "extra_transaction",
    [
        pytest.param(False, id="full_block"),
        pytest.param(
            True, id="one_more_transaction", marks=pytest.mark.exception_test
        ),
    ],
)
@EIPChecklist.SystemContract.Test.ExcessiveGas.BlockGas()
def test_requests_exhaust_block_gas(
    extra_transaction: bool,
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    Transactions carrying the maximum execution gas fill a block with request
    enqueues, then burn what they have left, so the block's execution gas is
    spent down to less than a transaction's intrinsic cost; the system call
    dequeues the per-block maximum and leaves the rest queued.

    The block meters execution gas and state gas separately, and gas above
    the transaction cap funds a state gas reservoir. Each relay transaction
    queues a fixed number of records and carries a reservoir sized for the
    slots they create, so no state charge spills into the execution gas the
    block counts, and the reservoirs of all the transactions fit the block's
    state gas.
    """
    template = request_class.from_index(0)
    predeploy = request_class.system_contract_address
    env = Environment()
    tx_gas_limit = fork.transaction_gas_limit_cap()
    assert tx_gas_limit is not None
    assert fork.state_gas_reservoir_enabled(), (
        "gas above the transaction cap must fund a state gas reservoir"
    )
    full_transactions = env.gas_limit // tx_gas_limit
    remainder_gas = env.gas_limit % tx_gas_limit

    # Every word of a record is a slot first set from zero, as are the
    # queue's count and tail slots and the relay's enqueue counter on the
    # block's first enqueue.
    slot_state_gas = Op.SSTORE(
        original_value=0, current_value=0, new_value=1
    ).state_cost(fork)
    record_state_gas = request_class.slots_per_request * slot_state_gas
    first_enqueue_state_gas = 3 * slot_state_gas
    # The block admits a transaction only while its whole gas limit fits the
    # state gas left by the transactions before it, so each full
    # transaction's reservoir takes an equal share of what the block's gas
    # leaves beyond one execution cap.
    reservoir_budget = (env.gas_limit - tx_gas_limit) // full_transactions
    enqueues_per_transaction = (
        reservoir_budget - first_enqueue_state_gas
    ) // record_state_gas
    assert enqueues_per_transaction > 0, "the reservoir must fit a record"
    reservoir = (
        enqueues_per_transaction * record_state_gas + first_enqueue_state_gas
    )
    total_enqueued = full_transactions * enqueues_per_transaction
    assert total_enqueued > request_class.max_per_block, (
        "the block must queue more than the system call dequeues"
    )

    fee_word, result_word, counter_word, remaining_word = (
        0x100,
        0x120,
        0x140,
        0x160,
    )
    # Each iteration reads the current fee, enqueues a request whose first
    # calldata word is the running counter, and folds the call's result into
    # the success witness.
    enqueue = (
        Op.MSTORE(0, Op.MLOAD(counter_word))
        + Op.POP(Op.CALL(Op.GAS, predeploy, 0, 0, 0, fee_word, 32))
        + Op.MSTORE(
            result_word,
            Op.AND(
                Op.MLOAD(result_word),
                Op.CALL(
                    Op.GAS,
                    predeploy,
                    Op.ADD(Op.MLOAD(fee_word), template.value),
                    0,
                    len(template.calldata),
                    0,
                    0,
                ),
            ),
        )
        + Op.MSTORE(counter_word, Op.ADD(Op.MLOAD(counter_word), 1))
        + Op.MSTORE(remaining_word, Op.SUB(Op.MLOAD(remaining_word), 1))
    )
    # A call into code that runs out of gas at once burns all but a 64th of
    # the caller's gas; three in a row leave next to nothing.
    burner = pre.deploy_contract(Om.OOG())
    burn = Bytecode()
    for _ in range(3):
        burn += Op.POP(Op.CALL(Op.GAS, burner, 0, 0, 0, 0, 0))
    relay_code = (
        Om.MSTORE(template.calldata, 0)
        + Op.MSTORE(counter_word, Op.SLOAD(0))
        + Op.MSTORE(result_word, 1)
        + Op.MSTORE(remaining_word, Op.CALLDATALOAD(0))
        + While(body=enqueue, condition=Op.GT(Op.MLOAD(remaining_word), 0))
        # Witness the enqueue count, that every enqueue succeeded and that
        # every transaction ran to completion, then burn the rest.
        + Op.SSTORE(0, Op.MLOAD(counter_word))
        + Op.SSTORE(1, Op.MLOAD(result_word))
        + Op.SSTORE(2, Op.ADD(Op.SLOAD(2), 1))
        + burn
    )
    # The witness slots are pre-seeded so their final writes are not slot
    # creations.
    relay_balance = 2**160
    relay = pre.deploy_contract(
        relay_code, balance=relay_balance, storage={1: 2, 2: 1}
    )
    exhaust = pre.deploy_contract(burn)

    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            to=relay,
            gas_limit=tx_gas_limit + reservoir,
            data=enqueues_per_transaction.to_bytes(32, "big"),
        )
        for _ in range(full_transactions)
    ]
    if remainder_gas:
        # The remainder must fit the execution gas the block has left, so it
        # carries no reservoir and only burns.
        txs.append(
            Transaction(sender=sender, to=exhaust, gas_limit=remainder_gas)
        )
    # The counter lands in the first word of the calldata, and every fee
    # request type's calldata starts with a pubkey field.
    first_field = next(
        name for name in request_class.model_fields if name.endswith("pubkey")
    )
    dequeued = [
        template.copy(**{first_field: i << 128}).with_source_address(relay)
        for i in range(request_class.max_per_block)
    ]
    paid = (
        sum(request_class.get_enqueue_fees(total_enqueued))
        + total_enqueued * template.value
    )
    system_call_index = len(txs) + 1
    error = None
    if extra_transaction:
        # Even a minimum-cost transaction cannot fit after the burners.
        error = TransactionException.GAS_ALLOWANCE_EXCEEDED
        txs.append(
            Transaction(
                sender=sender,
                to=pre.fund_eoa(),
                gas_limit=fork.transaction_intrinsic_cost_calculator()(),
                error=error,
            )
        )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                # Each enqueue logs, and nothing here asserts a receipt; the
                # receipts root in the header still commits to them.
                include_receipts_in_output=False,
                header_verify=None
                if error
                else Header(requests_hash=Requests(*dequeued)),
                exception=error,
                # The sweep resets the count and advances the head past the
                # dequeued records.
                expected_block_access_list=None
                if error
                else BlockAccessListExpectation(
                    account_expectations={
                        predeploy: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=request_class.count_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=system_call_index,
                                            post_value=0,
                                        )
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=request_class.queue_head_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=system_call_index,
                                            post_value=request_class.max_per_block,
                                        )
                                    ],
                                ),
                            ],
                        ),
                    }
                ),
            )
        ],
        post={}
        if error
        else {
            relay: Account(
                balance=relay_balance - paid,
                storage={
                    0: total_enqueued,
                    1: 1,
                    2: 1 + full_transactions,
                },
            ),
            predeploy: Account(balance=paid),
        },
    )
