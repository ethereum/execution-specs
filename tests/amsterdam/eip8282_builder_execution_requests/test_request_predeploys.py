"""
Request predeploy tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

The builder deposit and exit contracts reuse the queue design of the
EIP-7002 withdrawal and EIP-7251 consolidation contracts, so every test
here runs against all four predeploys. Plain requests live in the deposit
and exit modules.
"""

from typing import Dict, List, Tuple, Type

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
    Bytecode,
    Environment,
    FeeSystemContractRequest,
    Fork,
    GasConsumer,
    Header,
    Op,
    Requests,
    Storage,
    SystemContractInteractionContract,
    SystemContractInteractionMeasuredOutOfGasContract,
    SystemContractInteractionTransaction,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
    create_op,
    relay_contract_code,
)
from execution_testing import Macros as Om
from execution_testing.checklists import EIPChecklist

from .spec import Spec, ref_spec_8282

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

CREATE2_SALT = 0x5A17


def queued_count_changes(
    request_class: Type[FeeSystemContractRequest],
    enqueued: int,
    system_call_index: int,
) -> BalStorageSlot:
    """
    Return the count slot's rise to `enqueued` and its reset by the
    end-of-block system call.
    """
    return BalStorageSlot(
        slot=request_class.count_slot,
        slot_changes=[
            BalStorageChange(block_access_index=1, post_value=enqueued),
            BalStorageChange(
                block_access_index=system_call_index, post_value=0
            ),
        ],
    )


@pytest.mark.parametrize(
    "beyond_target",
    [
        pytest.param(False, id="nothing_queued"),
        pytest.param(True, id="queued_beyond_target"),
    ],
)
@EIPChecklist.SystemContract.Test.InputLengths.Zero()
def test_fee_getter(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
    beyond_target: bool,
) -> None:
    """
    A relay queues requests and then calls the predeploy with empty calldata,
    which returns the current fee; calling it again with value attached
    reverts.
    """
    predeploy = request_class.system_contract_address
    per_block = request_class.max_per_block
    if beyond_target:
        excess = request_class.get_n_fee_increments(1)[0]
        queued = request_class.target_per_block + excess
        sweep_changes = [
            BalStorageSlot(
                slot=request_class.excess_slot,
                slot_changes=[
                    BalStorageChange(block_access_index=2, post_value=excess)
                ],
            ),
            queued_count_changes(request_class, queued, 2),
        ]
        if queued > per_block:
            # The sweep takes a block's worth and moves the head past them.
            sweep_changes.append(
                BalStorageSlot(
                    slot=request_class.queue_head_slot,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=2, post_value=per_block
                        )
                    ],
                )
            )
            predeploy_bal = BalAccountExpectation(
                storage_changes=sweep_changes
            )
        else:
            predeploy_bal = BalAccountExpectation(
                storage_reads=[request_class.queue_head_slot],
                storage_changes=sweep_changes,
            )
    else:
        excess = 0
        queued = 0
        predeploy_bal = BalAccountExpectation(
            storage_reads=[
                request_class.excess_slot,
                request_class.count_slot,
                request_class.queue_head_slot,
                request_class.queue_tail_slot,
            ],
            storage_changes=[],
        )
    requests = [
        request_class.from_index(i).copy(fee=fee)
        for i, fee in enumerate(request_class.get_enqueue_fees(queued))
    ]
    queued_value = sum(request.value for request in requests)
    # Per-call pricing already counts the requests queued this block;
    # per-block pricing returns the minimum until the system call runs.
    if request_class.excess_fee_processing == "call":
        quoted_fee = request_class.get_fee(excess)
    elif request_class.excess_fee_processing == "block":
        quoted_fee = request_class.get_fee(0)
    else:
        raise ValueError(
            f"unhandled fee processing {request_class.excess_fee_processing}"
        )

    storage = Storage()
    fee_getter = (
        Op.SSTORE(
            storage.store_next(1, "getter_success"),
            Op.CALL(Op.GAS, predeploy, 0, 0, 0, 0, 32),
        )
        + Op.SSTORE(
            storage.store_next(32, "getter_return_size"), Op.RETURNDATASIZE
        )
        + Op.SSTORE(storage.store_next(quoted_fee, "fee"), Op.MLOAD(0))
        + Op.SSTORE(
            storage.store_next(0, "getter_with_value_success"),
            Op.CALL(Op.GAS, predeploy, 1, 0, 0, 0, 0),
        )
    )
    relay = pre.deploy_contract(
        relay_contract_code(
            requests, call_type=Op.CALL, extra_code=fee_getter
        ),
        balance=queued_value + 1,
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=relay,
        data=b"".join(request.calldata for request in requests),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    requests_hash=Requests(
                        *(
                            r.with_source_address(relay)
                            for r in requests[:per_block]
                        )
                    )
                ),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        relay: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=value,
                                        )
                                    ],
                                )
                                for slot, value in storage.root.items()
                                if value != 0
                            ],
                        ),
                        predeploy: predeploy_bal,
                    }
                ),
            )
        ],
        post={
            relay: Account(storage=storage, balance=1),
            predeploy: Account(balance=queued_value),
        },
    )


def test_fee_decays_to_minimum(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    Raise the fee with one block of requests, then send nothing: each
    system call lowers the stored excess by the per-block target until it
    reaches zero, and a final request paying the minimum fee is accepted.
    """
    predeploy = request_class.system_contract_address
    target = request_class.target_per_block
    raised_excess = request_class.get_n_fee_increments(1)[0]
    assert request_class.get_fee(raised_excess) > request_class.get_fee(0)

    queued = [
        request_class.from_index(i).copy(fee=fee)
        for i, fee in enumerate(
            request_class.get_enqueue_fees(target + raised_excess)
        )
    ]
    interaction = SystemContractInteractionContract(
        requests=queued
    ).update_pre(pre)
    relay = interaction.request_source_address
    assert relay is not None

    def stored_excess(
        value: int, system_call_index: int
    ) -> BlockAccessListExpectation:
        return BlockAccessListExpectation(
            account_expectations={
                predeploy: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=request_class.excess_slot,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=system_call_index,
                                    post_value=value,
                                )
                            ],
                        )
                    ],
                )
            }
        )

    txs = interaction.transactions()
    per_block = request_class.max_per_block
    remaining = [request.with_source_address(relay) for request in queued]
    blocks = [
        Block(
            txs=txs,
            header_verify=Header(
                requests_hash=Requests(*remaining[:per_block])
            ),
            expected_block_access_list=stored_excess(
                raised_excess, len(txs) + 1
            ),
        )
    ]
    remaining = remaining[per_block:]
    excess = raised_excess
    # Records beyond the per-block cap drain over the following blocks while
    # the excess decays, so keep going until both are gone.
    while excess or remaining:
        decayed = max(0, excess - target)
        blocks.append(
            Block(
                header_verify=Header(
                    requests_hash=Requests(*remaining[:per_block])
                ),
                expected_block_access_list=(
                    stored_excess(decayed, 1) if decayed != excess else None
                ),
            )
        )
        excess = decayed
        remaining = remaining[per_block:]

    sender = pre.fund_eoa()
    final = request_class.from_index(len(queued)).copy(
        fee=request_class.get_fee(0)
    )
    blocks.append(
        Block(
            txs=SystemContractInteractionTransaction(
                sender_account=sender, requests=[final]
            ).transactions(),
            header_verify=Header(
                requests_hash=Requests(final.with_source_address(sender))
            ),
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            predeploy: Account(
                balance=sum(request.value for request in queued) + final.value
            )
        },
    )


@pytest.mark.pre_alloc_mutable
@EIPChecklist.SystemContract.Test.InputLengths.Zero()
def test_fee_getter_inhibited(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    While the inhibitor is set, a fee query reverts like any other call from
    an address other than the system address, because the inhibitor is
    checked before the calldata size; once the end-of-block system call
    clears it, the same query in the next block returns the minimum fee.
    """
    predeploy = request_class.system_contract_address
    genesis_account = Alloc.model_validate(fork.pre_allocation_blockchain())[
        predeploy
    ]
    assert genesis_account is not None
    pre[predeploy] = Account(
        nonce=genesis_account.nonce,
        code=genesis_account.code,
        storage={request_class.excess_slot: Spec.EXCESS_INHIBITOR},
    )

    # The result is stored offset by one, so a relay that never made the call
    # is distinguishable from one whose call reverted.
    query = Op.SSTORE(
        0, Op.ADD(Op.CALL(Op.GAS, predeploy, 0, 0, 0, 0, 32), 1)
    ) + Op.SSTORE(1, Op.MLOAD(0))
    inhibited_relay = pre.deploy_contract(query)
    cleared_relay = pre.deploy_contract(query)
    sender = pre.fund_eoa()

    def relay_bal(*changes: Tuple[int, int]) -> BalAccountExpectation:
        return BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=slot,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1, post_value=value
                        )
                    ],
                )
                for slot, value in changes
            ],
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=inhibited_relay)],
                header_verify=Header(requests_hash=Requests()),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        inhibited_relay: relay_bal((0, 1)),
                        predeploy: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=request_class.excess_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=2, post_value=0
                                        )
                                    ],
                                )
                            ],
                        ),
                    }
                ),
            ),
            Block(
                txs=[Transaction(sender=sender, to=cleared_relay)],
                header_verify=Header(requests_hash=Requests()),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        cleared_relay: relay_bal(
                            (0, 2), (1, request_class.get_fee(0))
                        ),
                        predeploy: BalAccountExpectation(storage_changes=[]),
                    }
                ),
            ),
        ],
        post={
            inhibited_relay: Account(storage={0: 1, 1: 0}),
            cleared_relay: Account(
                storage={0: 2, 1: request_class.get_fee(0)}
            ),
            predeploy: Account(storage={request_class.excess_slot: 0}),
        },
    )


@EIPChecklist.SystemContract.Test.CallContexts.SetCode()
def test_request_from_set_code_delegated_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    An account delegated to a relay submits a request; the predeploy records
    the delegated account as the caller and its balance pays the value.
    """
    request = request_class.from_index(0).copy(fee=request_class.get_fee(0))
    predeploy = request_class.system_contract_address
    relay = pre.deploy_contract(
        relay_contract_code(
            [request], call_type=Op.CALL, extra_code=Bytecode()
        )
    )
    delegated = pre.fund_eoa(amount=request.value, delegation=relay)
    tx = Transaction(
        sender=pre.fund_eoa(), to=delegated, data=request.calldata
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    requests_hash=Requests(
                        request.with_source_address(delegated)
                    )
                ),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        delegated: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=0
                                )
                            ],
                        ),
                        predeploy: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=request.value,
                                )
                            ],
                            storage_changes=[
                                queued_count_changes(request_class, 1, 2)
                            ],
                        ),
                    }
                ),
            )
        ],
        post={
            delegated: Account(balance=0),
            predeploy: Account(balance=request.value),
        },
    )


@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(None, id="creation_transaction"),
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@EIPChecklist.SystemContract.Test.CallContexts.Initcode.Tx()
@EIPChecklist.SystemContract.Test.CallContexts.Initcode.CREATE()
def test_request_from_initcode(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
    create_opcode: Op | None,
) -> None:
    """
    Initcode submits a request; the predeploy records the address under
    construction as the caller.
    """
    request = request_class.from_index(0).copy(fee=request_class.get_fee(0))
    predeploy = request_class.system_contract_address
    initcode = (
        Om.MSTORE(request.calldata, 0)
        + Op.POP(
            Op.CALL(
                Op.GAS,
                predeploy,
                request.value,
                0,
                len(request.calldata),
                0,
                0,
            )
        )
        + Op.STOP
    )
    sender = pre.fund_eoa()
    post: Dict[Address, Account] = {}
    bal: Dict[Address, BalAccountExpectation] = {}

    if create_opcode is None:
        tx = Transaction(
            sender=sender, to=None, data=initcode, value=request.value
        )
        created = compute_create_address(address=sender, nonce=0)
    elif create_opcode in (Op.CREATE, Op.CREATE2):
        factory = pre.deploy_contract(
            Om.MSTORE(bytes(initcode), 0)
            + Op.SSTORE(
                0,
                create_op(
                    create_opcode,
                    value=Op.CALLVALUE,
                    size=len(initcode),
                    salt=CREATE2_SALT,
                ),
            )
        )
        tx = Transaction(sender=sender, to=factory, value=request.value)
        created = compute_create_address(
            address=factory,
            nonce=1,
            salt=CREATE2_SALT,
            initcode=initcode,
            opcode=create_opcode,
        )
    else:
        raise ValueError(f"unhandled create opcode {create_opcode}")

    if create_opcode is not None:
        post[factory] = Account(storage={0: created})
        bal[factory] = BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1, post_value=created
                        )
                    ],
                )
            ],
        )
    post[created] = Account(nonce=1, code=b"", balance=0)
    post[predeploy] = Account(balance=request.value)
    bal[created] = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )
    bal[predeploy] = BalAccountExpectation(
        balance_changes=[
            BalBalanceChange(block_access_index=1, post_balance=request.value)
        ],
        storage_changes=[queued_count_changes(request_class, 1, 2)],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    requests_hash=Requests(
                        request.with_source_address(created)
                    )
                ),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=bal
                ),
            )
        ],
        post=post,
    )


@EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Over()
def test_request_overpayment(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    A request paying one wei more than required is queued and the surplus
    stays in the predeploy.
    """
    request = request_class.from_index(0).copy(
        fee=request_class.get_fee(0) + 1
    )
    predeploy = request_class.system_contract_address
    sender = pre.fund_eoa()
    txs = SystemContractInteractionTransaction(
        sender_account=sender, requests=[request]
    ).transactions()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(
                    requests_hash=Requests(request.with_source_address(sender))
                ),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        predeploy: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=request.value,
                                )
                            ],
                            storage_changes=[
                                queued_count_changes(request_class, 1, 2)
                            ],
                        ),
                    }
                ),
            )
        ],
        post={predeploy: Account(balance=request.value)},
    )


@pytest.mark.parametrize(
    "call_type",
    [
        pytest.param(
            Op.DELEGATECALL,
            id="delegatecall",
            marks=EIPChecklist.SystemContract.Test.CallContexts.Delegate(),
        ),
        pytest.param(
            Op.STATICCALL,
            id="staticcall",
            marks=EIPChecklist.SystemContract.Test.CallContexts.Static(),
        ),
        pytest.param(
            Op.CALLCODE,
            id="callcode",
            marks=EIPChecklist.SystemContract.Test.CallContexts.Callcode(),
        ),
    ],
)
def test_request_via_delegatecall_staticcall_callcode(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
    call_type: Op,
) -> None:
    """
    None of these call types queues a request in the predeploy: DELEGATECALL
    and STATICCALL pass no value, so the fee check reverts before any write,
    and CALLCODE runs the predeploy's code on the relay's own account, so the
    record lands in the relay's storage and the predeploy stays untouched.
    """
    request = request_class.from_index(0).copy(fee=request_class.get_fee(0))
    predeploy = request_class.system_contract_address
    # The relay stores the sub-call's result offset by one, so a relay that
    # never made the call is distinguishable from one whose call reverted.
    result_slot = 0x100
    if call_type in (Op.DELEGATECALL, Op.STATICCALL):
        value_arg = []
    elif call_type == Op.CALLCODE:
        value_arg = [request.value]
    else:
        raise ValueError(f"unhandled call type {call_type}")
    relay = pre.deploy_contract(
        Om.MSTORE(request.calldata, 0)
        + Op.SSTORE(
            result_slot,
            Op.ADD(
                call_type(
                    Op.GAS,
                    predeploy,
                    *value_arg,
                    0,
                    len(request.calldata),
                    0,
                    0,
                ),
                1,
            ),
        ),
        balance=request.value,
    )

    relay_storage = Storage()
    if call_type in (Op.DELEGATECALL, Op.STATICCALL):
        relay_storage[result_slot] = 1
        relay_changes = []
    elif call_type == Op.CALLCODE:
        relay_storage[result_slot] = 2
        relay_storage[request_class.count_slot] = 1
        relay_storage[request_class.queue_tail_slot] = 1
        for slot in request_class.record_slots(0, 1):
            relay_storage.set_expect_any(slot)
        relay_changes = [
            BalStorageSlot(
                slot=request_class.count_slot,
                slot_changes=[
                    BalStorageChange(block_access_index=1, post_value=1)
                ],
            )
        ]
    else:
        raise ValueError(f"unhandled call type {call_type}")
    relay_changes.append(
        BalStorageSlot(
            slot=result_slot,
            slot_changes=[
                BalStorageChange(
                    block_access_index=1,
                    post_value=relay_storage[result_slot],
                )
            ],
        )
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=relay)],
                header_verify=Header(requests_hash=Requests()),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        relay: BalAccountExpectation(
                            storage_changes=relay_changes
                        ),
                        predeploy: BalAccountExpectation(storage_changes=[]),
                    }
                ),
            )
        ],
        post={
            relay: Account(balance=request.value, storage=relay_storage),
            predeploy: Account(balance=0, storage={}),
        },
    )


@EIPChecklist.SystemContract.Test.CallContexts.TxEntry()
@EIPChecklist.SystemContract.Test.InputLengths.Zero()
@EIPChecklist.SystemContract.Test.ValueTransfer.NoFee()
def test_value_without_calldata_from_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    A transaction that sends value to the predeploy with empty calldata
    reverts, because the fee getter takes no value, so nothing is queued,
    logged or kept.
    """
    predeploy = request_class.system_contract_address
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=predeploy,
        value=1,
        expected_receipt=TransactionReceipt(status=0, logs=[]),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(requests_hash=Requests()),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        predeploy: BalAccountExpectation(
                            balance_changes=[], storage_changes=[]
                        ),
                    }
                ),
            )
        ],
        post={predeploy: Account(balance=0)},
    )


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

    # Keep the boundary requests third and fourth: once the in-block count
    # passes `target_per_block` (two for exits), a request is priced on a
    # higher count and takes a different path than the measured one.
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
    Fill a block with request enqueues from transactions carrying the
    maximum execution gas, then burn what they have left, so less than one
    intrinsic cost remains; the system call dequeues the per-block maximum
    and leaves the rest queued.
    """
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
    # queue's count and tail slots on the block's first enqueue.
    slot_state_gas = Op.SSTORE(
        original_value=0, current_value=0, new_value=1
    ).state_cost(fork)
    record_state_gas = request_class.slots_per_request * slot_state_gas
    first_enqueue_state_gas = 2 * slot_state_gas
    # Under EIP-8037 a block has an execution-gas budget and an equal
    # state-gas budget, and a transaction is admitted only while its
    # reservoir fits in the state gas still free. Split the gas beyond one
    # execution cap evenly so every full transaction gets a reservoir the
    # block will admit.
    reservoir_budget = (env.gas_limit - tx_gas_limit) // full_transactions
    per_transaction = (
        reservoir_budget - first_enqueue_state_gas
    ) // record_state_gas
    assert per_transaction > 0, "the reservoir must fit a record"
    reservoir = per_transaction * record_state_gas + first_enqueue_state_gas
    total_enqueued = full_transactions * per_transaction
    assert total_enqueued > request_class.max_per_block, (
        "the block must queue more than the system call dequeues"
    )

    # Every request pays the highest fee any of them will meet, so one relay
    # serves every transaction; the predeploy keeps the overpayment.
    fee = max(request_class.get_enqueue_fees(total_enqueued))
    requests = [
        request_class.from_index(i).copy(fee=fee)
        for i in range(total_enqueued)
    ]
    paid = sum(request.value for request in requests)
    # A call into code that runs out of gas at once burns all but a 64th of
    # the caller's gas; three in a row leave next to nothing.
    burner = pre.deploy_contract(GasConsumer.out_of_gas(fork))
    burn = Op.POP(Op.CALL(Op.GAS, burner, 0, 0, 0, 0, 0)) * 3
    relay = pre.deploy_contract(
        relay_contract_code(
            requests[:per_transaction], call_type=Op.CALL, extra_code=burn
        ),
        balance=paid,
    )

    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=sender,
            to=relay,
            gas_limit=tx_gas_limit + reservoir,
            data=b"".join(
                request.calldata
                for request in requests[start : start + per_transaction]
            ),
        )
        for start in range(0, total_enqueued, per_transaction)
    ]
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    if remainder_gas >= intrinsic_gas:
        # A last transaction spends exactly the execution gas the full ones
        # leave, and carries no reservoir.
        exhaust = pre.deploy_contract(
            GasConsumer(gas=remainder_gas - intrinsic_gas, fork=fork)
        )
        txs.append(
            Transaction(sender=sender, to=exhaust, gas_limit=remainder_gas)
        )
    dequeued = [
        request.with_source_address(relay)
        for request in requests[: request_class.max_per_block]
    ]
    system_call_index = len(txs) + 1
    header_verify: Header | None
    expected_block_access_list: BlockAccessListExpectation | None
    post: Dict[Address, Account]
    error: TransactionException | None
    if extra_transaction:
        # Even a minimum-cost transaction cannot fit after the burners, and
        # the state budget still admits it, so only execution gas rejects it.
        assert full_transactions * reservoir + intrinsic_gas <= env.gas_limit
        error = TransactionException.GAS_ALLOWANCE_EXCEEDED
        txs.append(
            Transaction(
                sender=sender,
                to=pre.fund_eoa(),
                gas_limit=intrinsic_gas,
                error=error,
            )
        )
        header_verify = None
        expected_block_access_list = None
        post = {}
    else:
        error = None
        header_verify = Header(requests_hash=Requests(*dequeued))
        # The sweep resets the count and advances the head past the
        # dequeued records.
        expected_block_access_list = BlockAccessListExpectation(
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
        )
        post = {
            relay: Account(balance=0),
            predeploy: Account(balance=paid),
        }

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                # Each enqueue logs, and nothing here asserts a receipt; the
                # receipts root in the header still commits to them.
                include_receipts_in_output=False,
                header_verify=header_verify,
                exception=error,
                expected_block_access_list=expected_block_access_list,
            )
        ],
        post=post,
    )
