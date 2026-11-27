"""
Registration tests for
[EIP-8483: Post-Quantum Material Registration](https://eips.ethereum.org/EIPS/eip-8483).
"""

from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    EIPChecklist,
    FeeSystemContractRequest,
    Header,
    Op,
    ParameterSet,
    PQBuilderRegistrationRequest,
    PQRegistrationRequest,
    Requests,
    Storage,
    SystemContractInteractionBase,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    relay_contract_code,
)
from execution_testing import Macros as Om

from ...amsterdam.eip7708_eth_transfer_logs.spec import transfer_log
from .helpers import (
    call_results_relay,
    queue_storage,
    record_storage,
    with_both_registrations,
)
from .spec import PROOFS_OF_POSSESSION, Spec, ref_spec_8483

REFERENCE_SPEC_GIT_PATH = ref_spec_8483.git_path
REFERENCE_SPEC_VERSION = ref_spec_8483.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    # The cases assume the predeploys at their genesis state: no balance,
    # an empty queue and the fee at its minimum.
    pytest.mark.execute(
        pytest.mark.skip(reason="Assumes the predeploys' genesis state")
    ),
]

# Records from a source that never registers in these tests, for a queue
# seeded in the pre-state.
SEEDED_SOURCE = Address(0x5EED)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "eoa",
            marks=EIPChecklist.SystemContract.Test.CallContexts.TxEntry(),
        ),
        pytest.param(
            "contract",
            marks=EIPChecklist.SystemContract.Test.CallContexts.Normal(),
        ),
    ],
)
@with_both_registrations
@EIPChecklist.SystemContract.Test.InputLengths.Static.Correct()
@EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Exact()
def test_registration_logs_and_stores_record(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
    source: str,
) -> None:
    """
    A registration records its caller as `source_address`. The receipt has
    the EIP-7708 log of the fee and the record the predeploy logs with
    `LOG0`, and the record is stored as the queue's first item.
    """
    predeploy = request_class.system_contract_address
    request = request_class.from_index(0).copy(fee=request_class.get_fee(0))
    sender = pre.fund_eoa()
    caller: Address
    if source == "eoa":
        caller = sender
        to, value = predeploy, request.value
    elif source == "contract":
        caller = pre.deploy_contract(
            relay_contract_code(
                [request], call_type=Op.CALL, extra_code=Bytecode()
            ),
            balance=request.value,
        )
        to, value = caller, 0
    else:
        raise ValueError(f"unhandled source {source}")
    record = request.with_source_address(caller)

    tx = Transaction(
        sender=sender,
        to=to,
        value=value,
        data=request.calldata,
        expected_receipt=TransactionReceipt(
            logs=[
                transfer_log(caller, predeploy, request.value),
                TransactionLog(
                    address=predeploy, topics=[], data=bytes(record)
                ),
            ]
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(requests_hash=Requests(record)),
            )
        ],
        # The system call emptied the queue, so its head, tail and count are
        # back to zero and only the record's slots hold values.
        post={
            predeploy: Account(
                balance=request.value, storage=record_storage(record, 0)
            )
        },
    )


def from_eoa(
    request_class: type[FeeSystemContractRequest], *indices: int
) -> SystemContractInteractionBase:
    """Return one transaction per request, all from one EOA."""
    return SystemContractInteractionTransaction(
        requests=[request_class.from_index(i) for i in indices]
    )


def from_contract(
    request_class: type[FeeSystemContractRequest], *indices: int
) -> SystemContractInteractionBase:
    """Return one transaction that makes every request from a relay."""
    return SystemContractInteractionContract(
        requests=[request_class.from_index(i) for i in indices]
    )


def registration_scenarios() -> List[ParameterSet]:
    """
    Return the queueing scenarios for both request classes, each a list of
    blocks of interactions.
    """
    scenarios: List[ParameterSet] = []
    for cls, name in (
        (PQRegistrationRequest, "validator"),
        (PQBuilderRegistrationRequest, "builder"),
    ):
        cases = {
            "multiple_from_same_eoa": [[from_eoa(cls, 0, 1, 2)]],
            "multiple_from_different_eoas": [
                [from_eoa(cls, 0), from_eoa(cls, 1)]
            ],
            "multiple_from_contract": [[from_contract(cls, 0, 1, 2)]],
            "from_nested_calls": [
                [
                    SystemContractInteractionContract(
                        requests=[cls.from_index(0), cls.from_index(1)],
                        call_depth=8,
                    )
                ]
            ],
            "eoas_and_contract_interleaved": [
                [from_eoa(cls, 0), from_contract(cls, 1, 2), from_eoa(cls, 3)]
            ],
            "multiple_blocks": [
                [from_eoa(cls, 0)],
                [],
                [from_contract(cls, 1, 2)],
            ],
        }
        if cls is PQBuilderRegistrationRequest:
            # A block's worth of validator registrations doesn't fit in a
            # transaction, so `test_backlog_drains_first` covers their cap.
            cases["one_more_than_max_per_block"] = [
                [from_contract(cls, *range(cls.max_per_block + 1))]
            ]
        scenarios += [
            pytest.param(cls, interactions, id=f"{name}-{case}")
            for case, interactions in cases.items()
        ]
    return scenarios


@pytest.mark.parametrize(
    "request_class,system_contract_interactions_per_block",
    registration_scenarios(),
)
@EIPChecklist.SystemContract.Test.Inputs.Valid()
def test_registrations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
    included_requests: List[List[FeeSystemContractRequest]],
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    The system call returns the queued registrations in queue order, up to
    the per-block maximum, with `source_address` set to each caller, and the
    predeploy keeps exactly their fees.
    """
    accepted_value = sum(
        request.value for block in included_requests for request in block
    )
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            request_class.system_contract_address: Account(
                balance=accepted_value
            )
        },
    )


@pytest.mark.pre_alloc_mutable
@with_both_registrations
@EIPChecklist.SystemContract.Test.Inputs.Boundary()
def test_backlog_drains_first(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    A queue holding one more record than the per-block maximum returns the
    maximum in the first block, then the last record and the registrations
    added meanwhile in the next. Once empty, the queue resets its head and
    tail.
    """
    predeploy = request_class.system_contract_address
    max_per_block = request_class.max_per_block
    backlog = [
        request_class.from_index(i).with_source_address(SEEDED_SOURCE)
        for i in range(max_per_block + 1)
    ]
    pre.update_account(predeploy, storage=queue_storage(backlog))

    new_requests = [
        request_class.from_index(i).copy(fee=request_class.get_fee(0))
        for i in range(2)
    ]
    interaction = SystemContractInteractionContract(
        requests=new_requests
    ).update_pre(pre)
    relay = interaction.request_source_address
    assert relay is not None
    new_records = [
        request.with_source_address(relay) for request in new_requests
    ]

    # The new records follow the backlog in the queue, and the slots of every
    # item keep their values once the queue resets.
    post_storage: Dict[int, int] = {}
    for index, record in enumerate(backlog + new_records):
        post_storage |= record_storage(record, index)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=interaction.transactions(),
                header_verify=Header(
                    requests_hash=Requests(*backlog[:max_per_block])
                ),
            ),
            Block(
                header_verify=Header(
                    requests_hash=Requests(
                        *backlog[max_per_block:], *new_records
                    )
                ),
            ),
            Block(header_verify=Header(requests_hash=Requests())),
        ],
        post={
            predeploy: Account(
                balance=sum(request.value for request in new_requests),
                storage=post_storage,
            )
        },
    )


@with_both_registrations
def test_queue_reuses_slots_after_reset(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    Once the system call empties the queue, the next registration is stored
    as its first item again, over the slots of the first record dequeued.
    """
    predeploy = request_class.system_contract_address
    fee = request_class.get_fee(0)
    first = [request_class.from_index(i).copy(fee=fee) for i in range(2)]
    second = [request_class.from_index(2).copy(fee=fee)]
    first_interaction = SystemContractInteractionContract(
        requests=first
    ).update_pre(pre)
    second_interaction = SystemContractInteractionContract(
        requests=second
    ).update_pre(pre)
    first_relay = first_interaction.request_source_address
    second_relay = second_interaction.request_source_address
    assert first_relay is not None and second_relay is not None
    first_records = [r.with_source_address(first_relay) for r in first]
    second_records = [r.with_source_address(second_relay) for r in second]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=first_interaction.transactions(),
                header_verify=Header(requests_hash=Requests(*first_records)),
            ),
            Block(
                txs=second_interaction.transactions(),
                header_verify=Header(requests_hash=Requests(*second_records)),
            ),
        ],
        post={
            predeploy: Account(
                balance=3 * fee,
                storage=record_storage(first_records[1], 1)
                | record_storage(second_records[0], 0),
            )
        },
    )


@pytest.mark.parametrize(
    "caller_failure",
    [
        pytest.param(Op.REVERT(0, 0), id="caller_reverts"),
        pytest.param(Om.OOG, id="caller_runs_out_of_gas"),
    ],
)
@with_both_registrations
def test_registration_undone_by_caller(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
    caller_failure: Bytecode,
) -> None:
    """
    A relay whose registration succeeded and that then fails leaves nothing
    queued: the record, the count and the fee go back with its frame.
    """
    predeploy = request_class.system_contract_address
    request = request_class.from_index(0).copy(fee=request_class.get_fee(0))
    relay = pre.deploy_contract(
        relay_contract_code(
            [request], call_type=Op.CALL, extra_code=caller_failure
        ),
        balance=request.value,
    )
    entry_storage = Storage()
    entry = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            entry_storage.store_next(0, "relay_success"),
            Op.CALL(Op.GAS, relay, 0, 0, Op.CALLDATASIZE, 0, 0),
        ),
        storage=entry_storage.canary(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=pre.fund_eoa(), to=entry, data=request.calldata
                    )
                ],
                header_verify=Header(requests_hash=Requests()),
            )
        ],
        post={
            entry: Account(storage=entry_storage),
            relay: Account(balance=request.value),
            predeploy: Account(balance=0, storage={}),
        },
    )


@pytest.mark.parametrize(
    "calldata_case",
    [
        pytest.param(
            "one_byte_short",
            marks=EIPChecklist.SystemContract.Test.InputLengths.Static.TooShort(),
        ),
        pytest.param(
            "one_byte_long",
            marks=EIPChecklist.SystemContract.Test.InputLengths.Static.TooLong(),
        ),
        pytest.param(
            "without_signature",
            marks=EIPChecklist.SystemContract.Test.InputLengths.Static.TooShort(),
        ),
        pytest.param(
            "other_contract_request",
            marks=EIPChecklist.SystemContract.Test.Inputs.Invalid.Checks(),
        ),
    ],
)
@with_both_registrations
def test_invalid_calldata_length(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
    calldata_case: str,
) -> None:
    """
    A call whose calldata isn't a whole request for this predeploy reverts,
    including a valid request for the other predeploy. The same relay's valid
    request is then stored as the queue's first item.
    """
    predeploy = request_class.system_contract_address
    fee = request_class.get_fee(0)
    valid = request_class.from_index(0).copy(fee=fee)
    if calldata_case == "one_byte_short":
        calldata = valid.calldata[:-1]
    elif calldata_case == "one_byte_long":
        calldata = valid.calldata + b"\x00"
    elif calldata_case == "without_signature":
        calldata = valid.calldata[: -Spec.PROOF_SIZE]
    elif calldata_case == "other_contract_request":
        other_class = (
            PQBuilderRegistrationRequest
            if request_class is PQRegistrationRequest
            else PQRegistrationRequest
        )
        calldata = other_class.from_index(0).calldata
    else:
        raise ValueError(f"unhandled calldata case {calldata_case}")
    assert len(calldata) != len(valid.calldata)

    relay, data, relay_storage = call_results_relay(
        pre,
        [
            (predeploy, calldata, fee, False),
            (predeploy, valid.calldata, fee, True),
        ],
    )
    record = valid.with_source_address(relay)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=relay, data=data)],
                header_verify=Header(requests_hash=Requests(record)),
            )
        ],
        post={
            relay: Account(storage=relay_storage, balance=fee),
            predeploy: Account(balance=fee, storage=record_storage(record, 0)),
        },
    )


@pytest.mark.parametrize(
    "unsigned",
    [
        pytest.param(
            0,
            id="zero",
            marks=EIPChecklist.SystemContract.Test.Inputs.AllZeros(),
        ),
        pytest.param(1, id="one"),
        pytest.param(1 << 128, id="low_bit_of_first_half"),
        pytest.param(
            2**256 - 1,
            id="all_ones",
            marks=EIPChecklist.SystemContract.Test.Inputs.MaxValues(),
        ),
    ],
)
def test_validator_unsigned_pq_data(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    unsigned: int,
) -> None:
    """
    The proof of possession signs only the first half of a validator's
    `pq_data`, so any second half is accepted, stored and dequeued as sent.
    """
    predeploy = PQRegistrationRequest.system_contract_address
    request = PQRegistrationRequest.from_proof(
        PROOFS_OF_POSSESSION.proofs[0], unsigned=unsigned
    ).copy(fee=PQRegistrationRequest.get_fee(0))
    sender = pre.fund_eoa()
    record = request.with_source_address(sender)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=predeploy,
                        value=request.value,
                        data=request.calldata,
                    )
                ],
                header_verify=Header(requests_hash=Requests(record)),
            )
        ],
        post={
            predeploy: Account(
                balance=request.value, storage=record_storage(record, 0)
            )
        },
    )
