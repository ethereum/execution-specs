"""
Tests [EIP-7251: Execution layer triggerable consolidation](https://eips.ethereum.org/EIPS/eip-7251).
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    ConsolidationRequest,
    Header,
    Op,
    Requests,
    SystemContractInteractionTransaction,
    Transaction,
    generate_system_contract_error_test,
)
from execution_testing import Macros as Om

from .spec import Spec as Spec_EIP7251
from .spec import ref_spec_7251

REFERENCE_SPEC_GIT_PATH: str = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_7251.version

pytestmark: List[pytest.MarkDecorator] = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.pre_alloc_mutable(),
]


def consolidation_list_with_custom_fee(n: int) -> List[ConsolidationRequest]:  # noqa: D103
    return [
        ConsolidationRequest(
            source_pubkey=0x01,
            target_pubkey=0x02,
            fee=ConsolidationRequest.get_fee(10),
        )
        for i in range(n)
    ]


@pytest.mark.parametrize(
    "requests_list",
    [
        pytest.param(
            [],
            id="empty_request_list",
        ),
        pytest.param(
            [
                *consolidation_list_with_custom_fee(1),
            ],
            id="1_consolidation_request",
        ),
        pytest.param(
            [
                *consolidation_list_with_custom_fee(2),
            ],
            id="2_consolidation_requests",
        ),
        pytest.param(
            [
                *consolidation_list_with_custom_fee(3),
            ],
            id="3_consolidation_requests",
        ),
        pytest.param(
            [
                *consolidation_list_with_custom_fee(4),
            ],
            id="4_consolidation_requests",
        ),
        pytest.param(
            [
                *consolidation_list_with_custom_fee(5),
            ],
            id="5_consolidation_requests",
        ),
    ],
)
def test_extra_consolidations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    requests_list: List[ConsolidationRequest],
) -> None:
    """
    Test how clients were to behave with more than 2 consolidations per block.
    """
    modified_code: Bytecode = Bytecode()
    memory_offset: int = 0

    for consolidation_request in requests_list:
        record = bytes(consolidation_request)
        assert len(record) == 116, (
            "Expected consolidation request to be of size 116 but got size "
            f"{len(record)}"
        )
        # Store records contiguously from offset 0 so the returned data is
        # exactly the concatenated records (no gap, no trailing padding).
        modified_code += Om.MSTORE(record, memory_offset)
        memory_offset += len(record)

    modified_code += Op.RETURN(0, memory_offset)

    pre[ConsolidationRequest.system_contract_address] = Account(
        code=modified_code,
        nonce=1,
        balance=0,
    )

    # given a list of consolidation requests construct a consolidation request
    # transaction
    consolidation_request_transaction = SystemContractInteractionTransaction(
        requests=requests_list
    )
    # prepare consolidation senders
    prepared = consolidation_request_transaction.update_pre(pre=pre)
    # get transaction list
    txs: List[Transaction] = prepared.transactions()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(requests_hash=Requests(*requests_list)),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "system_contract",
    [ConsolidationRequest.system_contract_address],
)
@generate_system_contract_error_test(  # type: ignore[arg-type]
    max_gas_limit=Spec_EIP7251.SYSTEM_CALL_GAS_LIMIT,
)
def test_system_contract_errors() -> None:
    """
    Test consolidation system contract raising different errors when called by
    the system account at the end of the block execution.

    To see the list of generated tests, please refer to the
    `generate_system_contract_error_test` decorator definition.
    """
    pass
