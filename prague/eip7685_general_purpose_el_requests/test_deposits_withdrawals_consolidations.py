"""
abstract: Tests [EIP-7685: General purpose execution layer requests](https://eips.ethereum.org/EIPS/eip-7685)
    Cross testing for withdrawal and deposit request for [EIP-7685: General purpose execution layer requests](https://eips.ethereum.org/EIPS/eip-7685).

"""  # noqa: E501

from itertools import permutations
from typing import Any, Dict, Generator, List, Tuple

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
    Bytes,
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
        pytest.param(
            [],
            id="empty_requests",
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


def invalid_requests_block_combinations(fork: Fork) -> List[Any]:
    """
    Return a list of invalid request combinations for the given fork.

    In the event of a new request type, the `all_request_types` dictionary should be updated
    with the new request type and its corresponding request-generating transaction.

    Returned parameters are: requests, block_body_override_requests, exception
    """
    assert fork.max_request_type() == 2, "Test update is needed for new request types"

    all_request_types: Dict[
        str,
        Tuple[
            DepositTransaction | WithdrawalRequestTransaction | ConsolidationRequestTransaction,
            DepositRequest | WithdrawalRequest | ConsolidationRequest,
        ],
    ] = {
        "deposit": (
            single_deposit_from_eoa(0),
            single_deposit(0),
        ),
        "withdrawal": (
            single_withdrawal_from_eoa(0),
            single_withdrawal(0).with_source_address(TestAddress),
        ),
        "consolidation": (
            single_consolidation_from_eoa(0),
            single_consolidation(0).with_source_address(TestAddress),
        ),
    }

    # - Empty requests list with invalid hash
    combinations = [
        pytest.param(
            [],
            [
                bytes([i]) for i in range(fork.max_request_type() + 1)
            ],  # Using empty requests, calculate the hash using an invalid calculation method:
            # sha256(sha256(b"\0") ++ sha256(b"\1") ++ sha256(b"\2") ++ ...)
            BlockException.INVALID_REQUESTS,
            id="no_requests_invalid_hash_calculation_method",
        ),
        pytest.param(
            [],
            [
                bytes([]) for _ in range(fork.max_request_type() + 1)
            ],  # Using empty requests, calculate the hash using an invalid calculation method:
            # sha256(sha256(b"") ++ sha256(b"") ++ sha256(b"") ++ ...)
            BlockException.INVALID_REQUESTS,
            id="no_requests_invalid_hash_calculation_method_2",
        ),
    ]

    # - Missing request or request type byte tests
    for request_type, (eoa_request, block_request) in all_request_types.items():
        combinations.extend(
            [
                pytest.param(
                    [eoa_request],
                    [
                        block_request
                    ],  # The request type byte missing because we need to use the `Requests` class
                    BlockException.INVALID_REQUESTS,
                    id=f"single_{request_type}_missing_type_byte",
                ),
                pytest.param(
                    [eoa_request],
                    [],
                    BlockException.INVALID_REQUESTS,
                    id=f"single_{request_type}_empty_requests_list",
                ),
            ]
        )

    # - Incorrect order tests
    correct_order: List[Bytes] = Requests(
        *[r[1] for r in all_request_types.values()]
    ).requests_list  # Requests automatically adds the type byte
    correct_order_transactions: List[
        DepositTransaction | WithdrawalRequestTransaction | ConsolidationRequestTransaction
    ] = [r[0] for r in all_request_types.values()]

    # Send first element to the end
    combinations.append(
        pytest.param(
            correct_order_transactions[1:] + [correct_order_transactions[0]],
            correct_order[1:] + [correct_order[0]],
            BlockException.INVALID_REQUESTS,
            id="incorrect_order_first_request_at_end",
        ),
    )

    # Send second element to the end
    combinations.append(
        pytest.param(
            [correct_order_transactions[0]]
            + correct_order_transactions[2:]
            + [correct_order_transactions[1]],
            [correct_order[0]] + correct_order[2:] + [correct_order[1]],
            BlockException.INVALID_REQUESTS,
            id="incorrect_order_second_request_at_end",
        ),
    )

    # Bring last element to the beginning
    combinations.append(
        pytest.param(
            [correct_order_transactions[-1]] + correct_order_transactions[:-1],
            [correct_order[-1]] + correct_order[:-1],
            BlockException.INVALID_REQUESTS,
            id="incorrect_order_last_request_at_beginning",
        ),
    )

    # - Duplicate request tests
    for request_type, (eoa_request, block_request) in all_request_types.items():
        combinations.append(
            pytest.param(
                [eoa_request],
                Requests(block_request).requests_list * 2,
                BlockException.INVALID_REQUESTS,
                id=f"duplicate_{request_type}_request",
            ),
        )

    # - Extra invalid request tests
    combinations.append(
        pytest.param(
            correct_order_transactions,
            correct_order + [b""],
            BlockException.INVALID_REQUESTS,
            id="extra_empty_request",
        ),
    )
    combinations.append(
        pytest.param(
            correct_order_transactions,
            correct_order + [bytes([fork.max_request_type() + 1])],
            BlockException.INVALID_REQUESTS,
            id="extra_invalid_type_request_with_no_data",
        ),
    )
    combinations.append(
        pytest.param(
            correct_order_transactions,
            correct_order + [bytes([fork.max_request_type() + 1, 0x00])],
            BlockException.INVALID_REQUESTS,
            id="extra_invalid_type_request_with_data_0x00",
        ),
    )
    combinations.append(
        pytest.param(
            correct_order_transactions,
            correct_order + [bytes([fork.max_request_type() + 1, 0x01])],
            BlockException.INVALID_REQUESTS,
            id="extra_invalid_type_request_with_data_0x01",
        ),
    )
    combinations.append(
        pytest.param(
            correct_order_transactions,
            correct_order + [bytes([fork.max_request_type() + 1, 0xFF])],
            BlockException.INVALID_REQUESTS,
            id="extra_invalid_type_request_with_data_0xff",
        ),
    )

    return combinations


@pytest.mark.parametrize_by_fork(
    "requests,block_body_override_requests,exception",
    invalid_requests_block_combinations,
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


@pytest.mark.parametrize_by_fork(
    "requests,block_body_override_requests,exception",
    invalid_requests_block_combinations,
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

    Note that the only difference between the engine version produced by this test and
    the ones produced by `test_invalid_deposit_withdrawal_consolidation_requests` is the
    `blockHash` value in the new payloads, which is calculated using different request hashes
    for each test, but since the request hash is not a value that is included in the payload,
    it might not be immediately apparent.

    Also these tests would not fail if the block is imported via RLP (syncing from a peer),
    so we only generate the BlockchainTestEngine for them.
    """
    blockchain_test_engine(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=blocks,
    )
