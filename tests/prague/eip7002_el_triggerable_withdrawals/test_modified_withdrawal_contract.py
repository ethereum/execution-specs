"""
Tests [EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002).
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Header,
    Op,
    Requests,
    SystemContractInteractionTransaction,
    Transaction,
    WithdrawalRequest,
    generate_system_contract_error_test,
)
from execution_testing import Macros as Om

from .spec import Spec as Spec_EIP7002
from .spec import ref_spec_7002

REFERENCE_SPEC_GIT_PATH: str = ref_spec_7002.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_7002.version

pytestmark: List[pytest.MarkDecorator] = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.pre_alloc_mutable(),
]


def withdrawal_list_with_custom_fee(n: int) -> List[WithdrawalRequest]:  # noqa: D103
    return [
        WithdrawalRequest(
            validator_pubkey=i + 1,
            amount=0,
            fee=WithdrawalRequest.get_fee(0),
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
                *withdrawal_list_with_custom_fee(1),
            ],
            id="1_withdrawal_request",
        ),
        pytest.param(
            [
                *withdrawal_list_with_custom_fee(15),
            ],
            id="15_withdrawal_requests",
        ),
        pytest.param(
            [
                *withdrawal_list_with_custom_fee(16),
            ],
            id="16_withdrawal_requests",
        ),
        pytest.param(
            [
                *withdrawal_list_with_custom_fee(17),
            ],
            id="17_withdrawal_requests",
        ),
        pytest.param(
            [
                *withdrawal_list_with_custom_fee(18),
            ],
            id="18_withdrawal_requests",
        ),
    ],
)
def test_extra_withdrawals(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    requests_list: List[WithdrawalRequest],
) -> None:
    """
    Test how clients were to behave when more than 16 withdrawals would be
    allowed per block.
    """
    modified_code: Bytecode = Bytecode()
    memory_offset: int = 0

    for withdrawal_request in requests_list:
        record = bytes(withdrawal_request)
        assert len(record) == 76, (
            "Expected withdrawal request to be of size 76 but got size "
            f"{len(record)}"
        )
        # Store records contiguously from offset 0 so the returned data is
        # exactly the concatenated records (no gap, no trailing padding).
        modified_code += Om.MSTORE(record, memory_offset)
        memory_offset += len(record)

    modified_code += Op.RETURN(0, memory_offset)

    pre[WithdrawalRequest.system_contract_address] = Account(
        code=modified_code,
        nonce=1,
        balance=0,
    )

    # given a list of withdrawal requests construct a withdrawal request
    # transaction
    withdrawal_request_transaction = SystemContractInteractionTransaction(
        requests=requests_list
    )
    # prepare withdrawal senders
    prepared = withdrawal_request_transaction.update_pre(pre=pre)
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
    [WithdrawalRequest.system_contract_address],
)
@generate_system_contract_error_test(  # type: ignore[arg-type]
    max_gas_limit=Spec_EIP7002.SYSTEM_CALL_GAS_LIMIT,
)
@pytest.mark.eels_base_coverage
def test_system_contract_errors() -> None:
    """
    Test system contract raising different errors when called by the system
    account at the end of the block execution.

    To see the list of generated tests, please refer to the
    `generate_system_contract_error_test` decorator definition.
    """
    pass
