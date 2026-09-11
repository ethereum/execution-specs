"""
Call-context tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

Behavior shared by every fee-charging request predeploy that the per-type
request matrices cannot express: the fee getter, the fee decaying once demand
stops, requests made while the inhibitor is set, from an account whose code
is delegated, from initcode, with more value than the request costs, and
through call types other than CALL. The tests run against all such
predeploys of the fork, so they cover the withdrawal and consolidation
contracts as well as the builder ones.
"""

from typing import Dict, Tuple, Type

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
    FeeSystemContractRequest,
    Fork,
    Header,
    Op,
    Requests,
    Storage,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    Transaction,
    compute_create_address,
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
    reverts. A predeploy that prices the fee per call already counts the
    requests queued in the block, one that prices it per block returns the
    minimum until the system call runs.
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
    if request_class.excess_fee_processing == "call":
        quoted_fee = request_class.get_fee(excess)
    elif request_class.excess_fee_processing == "block":
        quoted_fee = request_class.get_fee(0)

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
    Queue enough requests in one block to raise the fee, then send nothing
    for the following blocks.

    Each system call after that lowers the stored excess by the per-block
    target, whatever it dequeues, until it reaches zero, so a request paying
    the minimum fee is accepted again.
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


@pytest.mark.pre_alloc_mutable()
@EIPChecklist.SystemContract.Test.InputLengths.Zero()
def test_fee_getter_inhibited(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    While the inhibitor is set, a fee query reverts like any other call from
    an address other than the system address.

    The inhibitor is checked before the predeploy looks at the calldata size,
    so the empty-calldata path is rejected too. The end-of-block system call
    clears the inhibitor, and the same query in the next block returns the
    minimum fee.
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
    elif create_opcode == Op.CREATE:
        factory = pre.deploy_contract(
            Om.MSTORE(bytes(initcode), 0)
            + Op.SSTORE(0, Op.CREATE(Op.CALLVALUE, 0, len(initcode)))
        )
        tx = Transaction(sender=sender, to=factory, value=request.value)
        created = compute_create_address(address=factory, nonce=1)
    elif create_opcode == Op.CREATE2:
        factory = pre.deploy_contract(
            Om.MSTORE(bytes(initcode), 0)
            + Op.SSTORE(
                0,
                Op.CREATE2(Op.CALLVALUE, 0, len(initcode), CREATE2_SALT),
            )
        )
        tx = Transaction(sender=sender, to=factory, value=request.value)
        created = compute_create_address(
            address=factory,
            salt=CREATE2_SALT,
            initcode=initcode,
            opcode=Op.CREATE2,
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
    None of these call types queues a request in the predeploy.

    DELEGATECALL and STATICCALL do not pass a value, so the predeploy's code
    sees a call value of zero and reverts on the fee check before it can
    write anything. CALLCODE does pass the value, so the code runs to
    completion, but it runs on the relay's own account: the queued record and
    the bookkeeping slots land in the relay's storage, and the predeploy is
    left untouched.
    """
    request = request_class.from_index(0).copy(fee=request_class.get_fee(0))
    predeploy = request_class.system_contract_address
    # The relay stores the sub-call's result offset by one, so a relay that
    # never made the call is distinguishable from one whose call reverted.
    result_slot = 0x100
    value_arg = [request.value] if call_type == Op.CALLCODE else []
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
