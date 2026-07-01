"""
Tests [EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Requests,
    SystemContractInteractionTransaction,
    Transaction,
    generate_system_contract_error_test,
)
from execution_testing import Macros as Om

from .helpers import BuilderExitRequest
from .spec import Spec, ref_spec_8282

REFERENCE_SPEC_GIT_PATH: str = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_8282.version

pytestmark: List[pytest.MarkDecorator] = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.pre_alloc_mutable(),
]

# Serialized builder exit request record size (source_address ++ pubkey).
BUILDER_EXIT_REQUEST_BYTES = Spec.EXIT_REQUEST_INPUT_BYTES + 20


def builder_exit_list_with_custom_fee(n: int) -> List[BuilderExitRequest]:  # noqa: D103
    return [
        BuilderExitRequest(
            pubkey=i + 1,
            fee=BuilderExitRequest.get_fee(0),
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
                *builder_exit_list_with_custom_fee(1),
            ],
            id="1_builder_exit_request",
        ),
        pytest.param(
            [
                *builder_exit_list_with_custom_fee(15),
            ],
            id="15_builder_exit_requests",
        ),
        pytest.param(
            [
                *builder_exit_list_with_custom_fee(16),
            ],
            id="16_builder_exit_requests",
        ),
        pytest.param(
            [
                *builder_exit_list_with_custom_fee(17),
            ],
            id="17_builder_exit_requests",
        ),
        pytest.param(
            [
                *builder_exit_list_with_custom_fee(18),
            ],
            id="18_builder_exit_requests",
        ),
    ],
)
def test_extra_builder_exits(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    requests_list: List[BuilderExitRequest],
) -> None:
    """
    Test how clients were to behave when more than the per-block maximum of
    builder exit requests would be returned by the predeploy.
    """
    modified_code: Bytecode = Bytecode()
    memory_offset: int = 0
    amount_of_requests: int = 0

    for builder_exit_request in requests_list:
        # update memory_offset with the correct value
        builder_exit_request_bytes_amount: int = len(
            bytes(builder_exit_request)
        )
        if builder_exit_request_bytes_amount != BUILDER_EXIT_REQUEST_BYTES:
            raise Exception(
                "Expected builder exit request to be of size "
                f"{BUILDER_EXIT_REQUEST_BYTES} but got size "
                f"{builder_exit_request_bytes_amount}"
            )
        memory_offset += builder_exit_request_bytes_amount

        modified_code += Om.MSTORE(bytes(builder_exit_request), memory_offset)
        amount_of_requests += 1

    modified_code += Op.RETURN(0, Op.MSIZE())

    pre[Spec.BUILDER_EXIT_CONTRACT_ADDRESS] = Account(
        code=modified_code,
        nonce=1,
        balance=0,
    )

    # given a list of builder exit requests construct a builder exit request
    # transaction
    builder_exit_request_transaction = SystemContractInteractionTransaction(
        requests=requests_list
    )
    # prepare builder exit senders
    prepared = builder_exit_request_transaction.update_pre(pre=pre)
    # get transaction list
    txs: List[Transaction] = prepared.transactions()

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


@pytest.mark.parametrize(
    "system_contract",
    [
        pytest.param(
            Address(Spec.BUILDER_DEPOSIT_CONTRACT_ADDRESS),
            id="builder_deposit_contract",
        ),
        pytest.param(
            Address(Spec.BUILDER_EXIT_CONTRACT_ADDRESS),
            id="builder_exit_contract",
        ),
    ],
)
@generate_system_contract_error_test(  # type: ignore[arg-type]
    max_gas_limit=Spec.SYSTEM_CALL_GAS_LIMIT,
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
