"""
abstract: Tests [EIP-7685: General purpose execution layer requests](https://eips.ethereum.org/EIPS/eip-7685)
    Cross testing for withdrawal and deposit request for [EIP-7685: General purpose execution layer requests](https://eips.ethereum.org/EIPS/eip-7685).

"""  # noqa: E501

from itertools import permutations
from typing import Any, Generator, List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestEngineFiller,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Environment,
    Header,
    Requests,
    Storage,
    TestAddress,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from ..eip6110_deposits.helpers import DepositContract, DepositRequest, DepositTransaction
from ..eip6110_deposits.spec import Spec as Spec_EIP6110
from ..eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
    WithdrawalRequestContract,
    WithdrawalRequestTransaction,
)
from ..eip7002_el_triggerable_withdrawals.spec import Spec as Spec_EIP7002
from ..eip7251_consolidations.helpers import (
    ConsolidationRequest,
    ConsolidationRequestContract,
    ConsolidationRequestTransaction,
)
from ..eip7251_consolidations.spec import Spec as Spec_EIP7251
from .spec import ref_spec_7685

REFERENCE_SPEC_GIT_PATH = ref_spec_7685.git_path
REFERENCE_SPEC_VERSION = ref_spec_7685.version

pytestmark = pytest.mark.valid_from("Prague")


def single_deposit(i: int) -> DepositRequest:  # noqa: D103
    return DepositRequest(
        pubkey=(i * 3),
        withdrawal_credentials=(i * 3) + 1,
        amount=32_000_000_000,
        signature=(i * 3) + 2,
        index=i,
    )


def single_deposit_from_eoa(i: int) -> DepositTransaction:  # noqa: D103
    return DepositTransaction(requests=[single_deposit(i)])


def single_deposit_from_contract(i: int) -> DepositContract:  # noqa: D103
    return DepositContract(requests=[single_deposit(i)])


def single_withdrawal(i: int) -> WithdrawalRequest:  # noqa: D103
    return WithdrawalRequest(
        validator_pubkey=i + 1,
        amount=0,
        fee=1,
    )


def single_withdrawal_from_eoa(i: int) -> WithdrawalRequestTransaction:  # noqa: D103
    return WithdrawalRequestTransaction(requests=[single_withdrawal(i)])


def single_withdrawal_from_contract(i: int) -> WithdrawalRequestContract:  # noqa: D103
    return WithdrawalRequestContract(requests=[single_withdrawal(i)])


def single_consolidation(i: int) -> ConsolidationRequest:  # noqa: D103
    return ConsolidationRequest(
        source_pubkey=(i * 2),
        target_pubkey=(i * 2) + 1,
        fee=1,
    )


def single_consolidation_from_eoa(i: int) -> ConsolidationRequestTransaction:  # noqa: D103
    return ConsolidationRequestTransaction(requests=[single_consolidation(i)])


def single_consolidation_from_contract(i: int) -> ConsolidationRequestContract:  # noqa: D103
    return ConsolidationRequestContract(requests=[single_consolidation(i)])


def get_permutations(n: int = 3) -> Generator[Any, None, None]:
    """Return possible permutations of the requests from an EOA."""
    requests = [
        (
            "deposit",
            single_deposit(0),
        ),
        (
            "withdrawal",
            single_withdrawal(0),
        ),
        (
            "consolidation",
            single_consolidation(0),
        ),
    ]
    for perm in permutations(requests, n):
        yield pytest.param([p[1] for p in perm], id="+".join([p[0] for p in perm]))


def get_eoa_permutations(n: int = 3) -> Generator[Any, None, None]:
    """Return possible permutations of the requests from an EOA."""
    requests = [
        (
            "deposit_from_eoa",
            single_deposit_from_eoa(0),
        ),
        (
            "withdrawal_from_eoa",
            single_withdrawal_from_eoa(0),
        ),
        (
            "consolidation_from_eoa",
            single_consolidation_from_eoa(0),
        ),
    ]
    for perm in permutations(requests, n):
        yield pytest.param([p[1] for p in perm], id="+".join([p[0] for p in perm]))


def get_contract_permutations(n: int = 3) -> Generator[Any, None, None]:
    """Return possible permutations of the requests from a contract."""
    requests = [
        (
            "deposit_from_contract",
            single_deposit_from_contract(0),
        ),
        (
            "withdrawal_from_contract",
            single_withdrawal_from_contract(0),
        ),
        (
            "consolidation_from_contract",
            single_consolidation_from_contract(0),
        ),
    ]
    for perm in permutations(requests, n):
        yield pytest.param([p[1] for p in perm], id="+".join([p[0] for p in perm]))


@pytest.mark.parametrize(
    "requests",
    [
        *get_eoa_permutations(),
        *get_contract_permutations(),
        pytest.param(
            [
                single_deposit_from_eoa(0),
                single_withdrawal_from_eoa(0),
                single_deposit_from_contract(1),
            ],
            id="deposit_from_eoa+withdrawal_from_eoa+deposit_from_contract",
        ),
        pytest.param(
            [
                single_withdrawal_from_eoa(0),
                single_deposit_from_eoa(0),
                single_withdrawal_from_contract(1),
            ],
            id="withdrawal_from_eoa+deposit_from_eoa+withdrawal_from_contract",
        ),
        pytest.param(
            [
                single_deposit_from_eoa(0),
                single_consolidation_from_eoa(0),
                single_deposit_from_contract(1),
            ],
            id="deposit_from_eoa+consolidation_from_eoa+deposit_from_contract",
        ),
        pytest.param(
            [
                single_consolidation_from_eoa(0),
                single_deposit_from_eoa(0),
                single_consolidation_from_contract(1),
            ],
            marks=pytest.mark.skip("Only one consolidation request is allowed per block"),
            id="consolidation_from_eoa+deposit_from_eoa+consolidation_from_contract",
        ),
        pytest.param(
            [
                single_consolidation_from_eoa(0),
                single_withdrawal_from_eoa(0),
                single_consolidation_from_contract(1),
            ],
            marks=pytest.mark.skip("Only one consolidation request is allowed per block"),
            id="consolidation_from_eoa+withdrawal_from_eoa+consolidation_from_contract",
        ),
        pytest.param(
            [
                single_withdrawal_from_eoa(0),
                single_consolidation_from_eoa(0),
                single_withdrawal_from_contract(1),
            ],
            id="withdrawal_from_eoa+consolidation_from_eoa+withdrawal_from_contract",
        ),
    ],
)
def test_valid_deposit_withdrawal_consolidation_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
):
    """
    Test making a deposit to the beacon chain deposit contract and a withdrawal
    in the same block.
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.parametrize("requests", [*get_permutations()])
def test_valid_deposit_withdrawal_consolidation_request_from_same_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    requests: List[DepositRequest | WithdrawalRequest | ConsolidationRequest],
    fork: Fork,
):
    """
    Test making a deposit to the beacon chain deposit contract and a withdrawal in
    the same tx.
    """
    withdrawal_request_fee = 1
    consolidation_request_fee = 1

    calldata = b""
    contract_code = Bytecode()
    total_value = 0
    storage = Storage()

    for request in requests:
        calldata_start = len(calldata)
        current_calldata = request.calldata
        calldata += current_calldata

        contract_code += Op.CALLDATACOPY(0, calldata_start, len(current_calldata))

        call_contract_address = 0
        value = 0
        if isinstance(request, DepositRequest):
            call_contract_address = Spec_EIP6110.DEPOSIT_CONTRACT_ADDRESS
            value = request.value
        elif isinstance(request, WithdrawalRequest):
            call_contract_address = Spec_EIP7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS
            value = withdrawal_request_fee
        elif isinstance(request, ConsolidationRequest):
            call_contract_address = Spec_EIP7251.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS
            value = consolidation_request_fee

        total_value += value

        contract_code += Op.SSTORE(
            storage.store_next(1),
            Op.CALL(
                address=call_contract_address,
                value=value,
                args_offset=0,
                args_size=len(current_calldata),
            ),
        )

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=contract_code,
    )

    tx = Transaction(
        gas_limit=10_000_000,
        to=contract_address,
        value=total_value,
        data=calldata,
        sender=sender,
    )

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={
            contract_address: Account(
                storage=storage,
            )
        },
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    requests_hash=Requests(
                        *[
                            request.with_source_address(contract_address)
                            for request in sorted(requests, key=lambda r: r.type)
                        ],
                    )
                ),
            )
        ],
    )


invalid_requests_block_combinations = [
    pytest.param(
        [],
        [],  # Even with no requests, the requests hash is not sha256(b""),
        # but sha256(sha256(b"\0") ++ sha256(b"\1") ++ sha256(b"\2") ++ ...)
        BlockException.INVALID_REQUESTS,
        id="no_requests_empty_list",
    ),
    pytest.param(
        [
            single_deposit_from_eoa(0),
        ],
        [
            single_deposit(0),
        ],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_incomplete_requests_list",
    ),
    pytest.param(
        [
            single_deposit_from_eoa(0),
        ],
        [],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_empty_requests_list",
    ),
    # Incorrect order tests
    pytest.param(
        [
            single_deposit_from_eoa(0),
        ],
        [
            b"",
            single_deposit(0),
            b"",
        ],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_incorrect_order_1",
    ),
    pytest.param(
        [
            single_deposit_from_eoa(0),
        ],
        [
            b"",
            b"",
            single_deposit(0),
        ],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_incorrect_order_2",
    ),
    pytest.param(
        [
            single_withdrawal_from_eoa(0),
        ],
        [
            single_withdrawal(0).with_source_address(TestAddress),
            b"",
            b"",
        ],
        BlockException.INVALID_REQUESTS,
        id="single_withdrawal_incorrect_order_1",
    ),
    pytest.param(
        [
            single_withdrawal_from_eoa(0),
        ],
        [
            b"",
            b"",
            single_withdrawal(0).with_source_address(TestAddress),
        ],
        BlockException.INVALID_REQUESTS,
        id="single_withdrawal_incorrect_order_2",
    ),
    pytest.param(
        [
            single_consolidation_from_eoa(0),
        ],
        [
            single_consolidation(0).with_source_address(TestAddress),
            b"",
            b"",
        ],
        BlockException.INVALID_REQUESTS,
        id="single_consolidation_incorrect_order_1",
    ),
    pytest.param(
        [
            single_consolidation_from_eoa(0),
        ],
        [
            b"",
            single_consolidation(0).with_source_address(TestAddress),
            b"",
        ],
        BlockException.INVALID_REQUESTS,
        id="single_consolidation_incorrect_order_2",
    ),
    pytest.param(
        [
            single_deposit_from_eoa(0),
            single_withdrawal_from_eoa(0),
        ],
        [
            single_deposit(0),
            single_withdrawal(0).with_source_address(TestAddress),
        ],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_single_withdrawal_incomplete_requests_list",
    ),
    pytest.param(
        [
            single_deposit_from_eoa(0),
            single_withdrawal_from_eoa(0),
        ],
        [
            single_deposit(0),
        ],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_single_withdrawal_incomplete_requests_list_2",
    ),
    pytest.param(
        [
            single_deposit_from_eoa(0),
            single_withdrawal_from_eoa(0),
            single_consolidation_from_eoa(0),
        ],
        [
            single_deposit(0),
            single_withdrawal(0).with_source_address(TestAddress),
        ],
        BlockException.INVALID_REQUESTS,
        id="single_deposit_single_withdrawal_single_consolidation_incomplete_requests_list",
    ),
]


@pytest.mark.parametrize(
    "requests,block_body_override_requests,exception",
    invalid_requests_block_combinations,
    indirect=["block_body_override_requests"],
)
def test_invalid_deposit_withdrawal_consolidation_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
):
    """
    Negative testing for all request types in the same block.

    In these tests, the requests hash in the header reflects what's received in the parameters
    portion of the `engine_newPayloadVX` call, so the block hash calculation might pass if
    a client copies the info received verbatim, but block validation must fail after
    the block is executed (via RLP or Engine API).
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.parametrize(
    "requests,block_body_override_requests,exception",
    invalid_requests_block_combinations,
    indirect=["block_body_override_requests"],
)
@pytest.mark.parametrize("correct_requests_hash_in_header", [True])
def test_invalid_deposit_withdrawal_consolidation_requests_engine(
    blockchain_test_engine: BlockchainTestEngineFiller,
    pre: Alloc,
    blocks: List[Block],
):
    """
    Negative testing for all request types in the same block with incorrect parameters
    in the Engine API new payload parameters, but with the correct requests hash in the header
    so the block hash is correct.

    In these tests, the requests hash in the header reflects what's actually in the executed block,
    so the block might execute properly if the client ignores the requests in the new payload
    parameters.

    Also these tests would not fail if the block is imported via RLP (syncing from a peer),
    so we only generate the BlockchainTestEngine for them.
    """
    blockchain_test_engine(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
