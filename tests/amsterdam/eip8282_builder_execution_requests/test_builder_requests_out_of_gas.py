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
    BuilderDepositRequest,
    BuilderExitRequest,
    Environment,
    FeeSystemContractRequest,
    Fork,
    Header,
    Op,
    Requests,
    Storage,
    SystemContractInteractionMeasuredOutOfGasContract,
    Transaction,
    While,
)
from execution_testing import Macros as Om
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.parametrize(
        "request_class",
        [
            pytest.param(BuilderDepositRequest, id="deposit"),
            pytest.param(BuilderExitRequest, id="exit"),
        ],
    ),
]


@EIPChecklist.SystemContract.Test.GasUsage.Dynamic.Oog()
@EIPChecklist.SystemContract.Test.GasUsage.Dynamic.Exact()
def test_builder_request_gas_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    The relay measures the gas a request consumes at runtime, then forwards
    one gas less than required to the third request and exactly the required
    gas to the fourth.
    """
    # The predeploy ends with a warm SSTORE, which EIP-2200 rejects unless
    # more than the call stipend remains, so the requirement exceeds the
    # consumption by that sentry.
    warm_sstore = Op.SSTORE(
        key_warm=True, original_value=0, current_value=1, new_value=2
    ).gas_cost(fork)
    sentry_margin = fork.call_value_stipend() - warm_sstore + 1

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
    enqueued = 3

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=interaction.transactions(),
                header_verify=Header(
                    requests_hash=Requests(
                        *(
                            request.with_source_address(relay)
                            for request in requests
                            if request.valid
                        )
                    )
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
            Block(header_verify=Header(requests_hash=Requests())),
        ],
        post={
            relay: Account(balance=value),
            predeploy: Account(balance=enqueued * value),
        },
    )


@EIPChecklist.SystemContract.Test.ExcessiveGas.BlockGas()
@pytest.mark.execute(
    pytest.mark.skip(reason="Needs more ETH than a live network provides")
)
def test_builder_requests_exhaust_block_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    Transactions carrying the maximum gas fill a block with request enqueues
    until the block gas is spent; the system call dequeues the per-block
    maximum and leaves the rest queued.
    """
    template = request_class.from_index(0)
    predeploy = request_class.system_contract_address
    fee_word, cost_word, result_word, counter_word = 0x100, 0x120, 0x140, 0x160

    # Each iteration reads the current fee, then enqueues a request whose
    # pubkey's first word is the running counter kept in storage slot 0.
    enqueue = (
        Op.MSTORE(0, Op.MLOAD(counter_word))
        + Op.POP(Op.CALL(Op.GAS, predeploy, 0, 0, 0, fee_word, 32))
        + Op.MSTORE(
            result_word,
            Op.CALL(
                Op.GAS,
                predeploy,
                Op.ADD(Op.MLOAD(fee_word), template.value),
                0,
                len(template.calldata),
                0,
                0,
            ),
        )
        + Op.MSTORE(counter_word, Op.ADD(Op.MLOAD(counter_word), 1))
    )
    relay_code = (
        Om.MSTORE(template.calldata, 0)
        + Op.MSTORE(counter_word, Op.SLOAD(0))
        # Run one cold iteration, measure a warm one, then loop while the last
        # enqueue succeeded and two iterations of gas remain.
        + enqueue
        + Op.GAS
        + enqueue
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH2(cost_word)
        + Op.MSTORE
        + While(
            body=enqueue,
            condition=Op.AND(
                Op.MLOAD(result_word),
                Op.GT(Op.GAS, Op.MUL(Op.MLOAD(cost_word), 2)),
            ),
        )
        + Op.SSTORE(0, Op.MLOAD(counter_word))
        # Witness that the loop ended on gas, not on a failed enqueue, and
        # that every transaction ran to completion.
        + Op.SSTORE(1, Op.MLOAD(result_word))
        + Op.SSTORE(2, Op.ADD(Op.SLOAD(2), 1))
    )
    # The fee grows exponentially with the block's enqueue count; the balance
    # is oversized so that gas, not funds, ends the loop. The witness slots
    # are pre-seeded so their final writes are not slot creations.
    relay = pre.deploy_contract(
        relay_code, balance=2**160, storage={1: 2, 2: 1}
    )

    env = Environment()
    tx_gas_limit = fork.transaction_gas_limit_cap()
    assert tx_gas_limit is not None
    gas_limits = [tx_gas_limit] * (env.gas_limit // tx_gas_limit)
    if env.gas_limit % tx_gas_limit:
        gas_limits.append(env.gas_limit % tx_gas_limit)
    sender = pre.fund_eoa()
    txs = [
        Transaction(sender=sender, to=relay, gas_limit=gas_limit)
        for gas_limit in gas_limits
    ]
    dequeued = [
        template.copy(pubkey=i << 128).with_source_address(relay)
        for i in range(request_class.max_per_block)
    ]
    system_call_index = len(txs) + 1
    # The enqueue count in slot 0 depends on the gas schedule.
    relay_storage = Storage()
    relay_storage.set_expect_any(0)
    relay_storage[1] = 1
    relay_storage[2] = 1 + len(txs)

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(requests_hash=Requests(*dequeued)),
                # The sweep resets the count and advances the head past the
                # dequeued records; how many were queued is gas-dependent.
                expected_block_access_list=BlockAccessListExpectation(
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
        post={relay: Account(storage=relay_storage)},
    )
