"""
Tests [EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List, Sequence, Type

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderDepositRequest,
    BuilderExitRequest,
    Bytecode,
    Bytes,
    FeeSystemContractRequest,
    Header,
    Op,
    Requests,
    SystemContractRequest,
    Transaction,
    TransactionReceipt,
    generate_system_contract_error_test,
)
from execution_testing import Macros as Om
from execution_testing.base_types import Bloom
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH: str = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_8282.version

pytestmark: List[pytest.MarkDecorator] = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.pre_alloc_mutable(),
]

MIN_DEPOSIT_GWEI = BuilderDepositRequest.min_deposit_wei // 10**9


def builder_deposit_list_with_custom_fee(  # noqa: D103
    n: int,
) -> List[BuilderDepositRequest]:
    return [
        BuilderDepositRequest(
            pubkey=i + 1,
            withdrawal_credentials=0x02,
            amount=MIN_DEPOSIT_GWEI,
            signature=0x03,
            fee=BuilderDepositRequest.get_fee(0),
        )
        for i in range(n)
    ]


def builder_exit_list_with_custom_fee(n: int) -> List[BuilderExitRequest]:  # noqa: D103
    return [
        BuilderExitRequest(
            pubkey=i + 1,
            fee=BuilderExitRequest.get_fee(0),
        )
        for i in range(n)
    ]


def run_modified_requests_test(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    *,
    predeploy_address: Address,
    requests_list: Sequence[SystemContractRequest],
) -> None:
    """
    Replace a request predeploy with code that returns the given request
    records verbatim, then verify the transition tool dequeues exactly those
    records into the block, even when there are more than the per-block cap.
    """
    modified_code: Bytecode = Bytecode()
    memory_offset: int = 0

    for request in requests_list:
        record = bytes(request)
        # Store records contiguously from offset 0 so the returned data is
        # exactly the concatenated records (no gap, no trailing padding).
        modified_code += Om.MSTORE(record, memory_offset)
        memory_offset += len(record)

    modified_code += Op.RETURN(0, memory_offset)

    pre[predeploy_address] = Account(code=modified_code, nonce=1)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                # No transaction runs and the system call has no receipt, so
                # nothing the predeploy logs reaches the bloom.
                header_verify=Header(
                    requests_hash=Requests(*requests_list),
                    logs_bloom=Bloom(0),
                ),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "requests_list",
    [
        pytest.param([], id="empty_request_list"),
        pytest.param(
            builder_deposit_list_with_custom_fee(1),
            id="1_builder_deposit_request",
        ),
        pytest.param(
            builder_deposit_list_with_custom_fee(
                BuilderDepositRequest.max_per_block - 1
            ),
            id="max_minus_1_builder_deposit_requests",
        ),
        pytest.param(
            builder_deposit_list_with_custom_fee(
                BuilderDepositRequest.max_per_block
            ),
            id="max_builder_deposit_requests",
        ),
        pytest.param(
            builder_deposit_list_with_custom_fee(
                BuilderDepositRequest.max_per_block + 1
            ),
            id="max_plus_1_builder_deposit_requests",
        ),
        pytest.param(
            builder_deposit_list_with_custom_fee(
                BuilderDepositRequest.max_per_block + 2
            ),
            id="max_plus_2_builder_deposit_requests",
        ),
    ],
)
@EIPChecklist.SystemContract.Test.ContractSubstitution.ReturnLengths()
def test_extra_builder_deposits(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    requests_list: List[BuilderDepositRequest],
) -> None:
    """
    Test how clients were to behave when more than the per-block maximum of
    builder deposit requests would be returned by the predeploy.
    """
    run_modified_requests_test(
        blockchain_test,
        pre,
        predeploy_address=BuilderDepositRequest.system_contract_address,
        requests_list=requests_list,
    )


@pytest.mark.parametrize(
    "requests_list",
    [
        pytest.param([], id="empty_request_list"),
        pytest.param(
            builder_exit_list_with_custom_fee(1),
            id="1_builder_exit_request",
        ),
        pytest.param(
            builder_exit_list_with_custom_fee(
                BuilderExitRequest.max_per_block - 1
            ),
            id="max_minus_1_builder_exit_requests",
        ),
        pytest.param(
            builder_exit_list_with_custom_fee(
                BuilderExitRequest.max_per_block
            ),
            id="max_builder_exit_requests",
        ),
        pytest.param(
            builder_exit_list_with_custom_fee(
                BuilderExitRequest.max_per_block + 1
            ),
            id="max_plus_1_builder_exit_requests",
        ),
        pytest.param(
            builder_exit_list_with_custom_fee(
                BuilderExitRequest.max_per_block + 2
            ),
            id="max_plus_2_builder_exit_requests",
        ),
    ],
)
@EIPChecklist.SystemContract.Test.ContractSubstitution.ReturnLengths()
def test_extra_builder_exits(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    requests_list: List[BuilderExitRequest],
) -> None:
    """
    Test how clients were to behave when more than the per-block maximum of
    builder exit requests would be returned by the predeploy.
    """
    run_modified_requests_test(
        blockchain_test,
        pre,
        predeploy_address=BuilderExitRequest.system_contract_address,
        requests_list=requests_list,
    )


@pytest.mark.parametrize(
    "system_contract",
    [
        pytest.param(
            BuilderDepositRequest.system_contract_address,
            id="builder_deposit_contract",
        ),
        pytest.param(
            BuilderExitRequest.system_contract_address,
            id="builder_exit_contract",
        ),
    ],
)
@EIPChecklist.SystemContract.Test.ContractSubstitution.RaisesException()
@EIPChecklist.SystemContract.Test.ContractSubstitution.GasLimitSuccess()
@EIPChecklist.SystemContract.Test.ContractSubstitution.GasLimitFailure()
@EIPChecklist.SystemContract.Test.ExcessiveGas.SystemCall()
@generate_system_contract_error_test()  # type: ignore[arg-type]
@pytest.mark.eels_base_coverage
def test_system_contract_errors() -> None:
    """
    Test system contract raising different errors when called by the system
    account at the end of the block execution.

    To see the list of generated tests, please refer to the
    `generate_system_contract_error_test` decorator definition.
    """
    pass


@pytest.mark.with_all_system_contract_request_types(
    selector=lambda cls: issubclass(cls, FeeSystemContractRequest)
)
@EIPChecklist.SystemContract.Test.ContractSubstitution.Logs()
def test_system_contract_logs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    Replace a request predeploy with code that logs before returning a
    record: the block stays valid, the record is dequeued, and the log
    reaches neither a receipt nor the block's logs bloom.
    """
    queued_request = request_class.from_index(0).copy(
        fee=request_class.get_fee(0)
    )
    record = bytes(queued_request)
    pre[queued_request.system_contract_address] = Account(
        code=Om.MSTORE(record, 0)
        + Op.LOG0(0, len(record))
        + Op.RETURN(0, len(record)),
        nonce=1,
    )
    # A transaction that logs nothing, so the last receipt is where a leaked
    # system-call log would show up.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.deploy_contract(Op.STOP),
        expected_receipt=TransactionReceipt(logs=[]),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    requests_hash=Requests(queued_request),
                    logs_bloom=Bloom(0),
                ),
            ),
        ],
        post={},
    )


@pytest.mark.with_all_system_contract_request_types(
    selector=lambda cls: issubclass(cls, FeeSystemContractRequest)
)
@pytest.mark.parametrize(
    "length_delta",
    [None, -1, 1],
    ids=["one_byte", "record_minus_one", "record_plus_one"],
)
@EIPChecklist.SystemContract.Test.ContractSubstitution.ReturnLengths()
def test_partial_request_records(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: Type[FeeSystemContractRequest],
    length_delta: int | None,
) -> None:
    """Commit raw system-call output without parsing or truncating records."""
    if length_delta is None:
        size = 1
    else:
        size = len(bytes(request_class.from_index(0))) + length_delta
    returned = bytes((i % 255) + 1 for i in range(size))
    pre[request_class.system_contract_address] = Account(
        code=Om.MSTORE(returned, 0) + Op.RETURN(0, size),
        nonce=1,
    )
    expected = Requests(
        requests_lists=[Bytes(bytes([request_class.type]) + returned)]
    )
    blockchain_test(
        pre=pre,
        blocks=[Block(header_verify=Header(requests_hash=expected))],
        post={},
    )
