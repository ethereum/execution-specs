"""
abstract: Tests [EIP-7251: Execution layer triggerable consolidation](https://eips.ethereum.org/EIPS/eip-7251)
    Test execution layer triggered exits [EIP-7251: Execution layer triggerable consolidation](https://eips.ethereum.org/EIPS/eip-7251).

"""  # noqa: E501

from typing import List

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Transaction,
)
from ethereum_test_tools import Macros as Om
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import Requests

from .helpers import (
    ConsolidationRequest,
    ConsolidationRequestTransaction,
)
from .spec import Spec as Spec_EIP7251
from .spec import ref_spec_7251

REFERENCE_SPEC_GIT_PATH: str = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_7251.version

pytestmark: pytest.MarkDecorator = pytest.mark.valid_from("Prague")


def consolidation_list_with_custom_fee(n: int) -> List[ConsolidationRequest]:  # noqa: D103
    return [
        ConsolidationRequest(
            source_pubkey=0x01,
            target_pubkey=0x02,
            fee=Spec_EIP7251.get_fee(10),
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
):
    """Test how clients were to behave with more than 2 consolidations per block."""
    modified_code: Bytecode = Bytecode()
    memory_offset: int = 0
    amount_of_requests: int = 0

    for consolidation_request in requests_list:
        # update memory_offset with the correct value
        consolidation_request_bytes_amount: int = len(bytes(consolidation_request))
        assert consolidation_request_bytes_amount == 116, (
            "Expected consolidation request to be of size 116 but got size "
            f"{consolidation_request_bytes_amount}"
        )
        memory_offset += consolidation_request_bytes_amount

        modified_code += Om.MSTORE(bytes(consolidation_request), memory_offset)
        amount_of_requests += 1

    modified_code += Op.RETURN(0, Op.MSIZE())

    pre[Spec_EIP7251.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS] = Account(
        code=modified_code,
        nonce=1,
        balance=0,
    )

    # given a list of consolidation requests construct a consolidation request transaction
    consolidation_request_transaction = ConsolidationRequestTransaction(requests=requests_list)
    # prepare consolidation senders
    consolidation_request_transaction.update_pre(pre=pre)
    # get transaction list
    txs: List[Transaction] = consolidation_request_transaction.transactions()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                requests_hash=Requests(*requests_list),
            ),
        ],
        post={},
    )
