"""
Tests EIP-7685 General purpose execution layer requests.

Cross testing for withdrawal and deposit request for
[EIP-7685: General purpose execution layer requests](https://eips.ethereum.org/EIPS/eip-7685).
"""

from itertools import permutations
from pathlib import Path
from typing import Callable, Dict, Generator, List, Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    BuilderDepositRequest,
    BuilderExitRequest,
    Bytes,
    ConsolidationRequest,
    DepositRequest,
    EIPChecklist,
    Environment,
    FeeSystemContractRequest,
    Fork,
    Header,
    ParameterSet,
    Requests,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
    SystemContractRequest,
    TestAddress,
    Transaction,
    WithdrawalRequest,
)

from .spec import ref_spec_7685

REFERENCE_SPEC_GIT_PATH: str = ref_spec_7685.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_7685.version

pytestmark: pytest.MarkDecorator = pytest.mark.valid_from("Prague")

SAME_BLOCK_DEPLOYMENT_CASES = [
    pytest.param(
        WithdrawalRequest,
        Path(__file__).parents[1]
        / "eip7002_el_triggerable_withdrawals"
        / "contract_deploy_tx.json",
        id="withdrawal",
    ),
    pytest.param(
        ConsolidationRequest,
        Path(__file__).parents[1]
        / "eip7251_consolidations"
        / "contract_deploy_tx.json",
        id="consolidation",
    ),
]


# All request types under test, in ascending request-type order. Adding a new
# request type here makes the permutations and parametrizations pick it up.
# Required for future forks to add new request types to this dictionary.
REQUEST_TYPES: List[type[SystemContractRequest]] = [
    DepositRequest,
    WithdrawalRequest,
    ConsolidationRequest,
    BuilderDepositRequest,
    BuilderExitRequest,
]
REQUEST_TYPE_BY_ADDRESS = {
    rt.system_contract_address: rt for rt in REQUEST_TYPES
}
# Number of requests used for request types that have no per-block cap (e.g.
# deposits), to exercise "many in a single block".
UNCAPPED_REQUEST_SAMPLE = 18


def request_type_to_id_str(ty: type[SystemContractRequest]) -> str:
    """Return an id-friendly string from the system contract request."""
    return ty.__name__.removesuffix("Request").lower()


def request_types_from_fork(fork: Fork) -> List[type[SystemContractRequest]]:
    """Return the types of system contract requests for a given fork."""
    assert len(REQUEST_TYPES) > fork.max_request_type(), (
        f"Request type {fork.max_request_type()} not in REQUEST_TYPES. "
        "Test needs update"
    )
    return REQUEST_TYPES[: fork.max_request_type() + 1]


def eoa_interaction(
    request_type: type[SystemContractRequest], i: int = 0
) -> SystemContractInteractionTransaction:
    """Build an EOA-originated interaction for a single request."""
    return SystemContractInteractionTransaction(
        requests=[request_type.from_index(i)]
    )


def contract_interaction(
    request_type: type[SystemContractRequest], i: int = 0
) -> SystemContractInteractionContract:
    """Build a relay-contract-originated interaction for a single request."""
    return SystemContractInteractionContract(
        requests=[request_type.from_index(i)]
    )


def get_fork_permutations(fork: Fork) -> Generator[ParameterSet, None, None]:
    """Get request permutations for a given fork."""
    request_types = request_types_from_fork(fork)

    # EOA permutations
    for perm in permutations(request_types):
        perm_id = "+".join(
            [f"{request_type_to_id_str(rt)}_from_eoa" for rt in perm]
        )
        yield pytest.param([eoa_interaction(rt) for rt in perm], id=perm_id)

    # Contract permutations
    for perm in permutations(request_types):
        perm_id = "+".join(
            [f"{request_type_to_id_str(rt)}_from_contract" for rt in perm]
        )
        yield pytest.param(
            [contract_interaction(rt) for rt in perm], id=perm_id
        )

    # Multiple request types from same transaction
    for perm in permutations(request_types):
        yield pytest.param(
            [
                SystemContractInteractionContract(
                    requests=[rt.from_index(0) for rt in perm]
                )
            ],
            id="+".join(request_type_to_id_str(rt) for rt in perm)
            + "_from_same_tx",
        )
    # Empty requests
    yield pytest.param([], id="empty_requests")

    # One more than the per-block cap of each request type, so the surplus of
    # capped types carries over to a following block. Uncapped types (e.g.
    # deposits) have no cap, so an arbitrary sample count is used and all are
    # included in the same block.
    over_cap_interactions: List[SystemContractInteractionContract] = []
    ids: List[str] = []
    for rt in request_types:
        if issubclass(rt, FeeSystemContractRequest):
            cap = rt.max_per_block
        else:
            cap = UNCAPPED_REQUEST_SAMPLE
        over_cap_interactions.append(
            SystemContractInteractionContract(
                requests=[rt.from_index(i) for i in range(cap + 1)]
            )
        )
        ids.append(f"{request_type_to_id_str(rt)}_over_cap")
    yield pytest.param(over_cap_interactions, id="+".join(ids))


@pytest.mark.parametrize_by_fork("requests", get_fork_permutations)
@pytest.mark.eels_base_coverage
@EIPChecklist.ExecutionLayerRequest.Test.CrossRequestType.Update(eip=[8282])
def test_valid_multi_type_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """
    Test valid combinations of every request type in the same block, from
    EOAs and from relay contracts, including per-type maximums.
    """
    blockchain_test(
        genesis_environment=Environment(
            # Per-type maximums exceed the default block gas limit.
            gas_limit=500_000_000
        ),
        pre=pre,
        post={},
        blocks=blocks,
    )


def invalid_requests_block_combinations(
    *,
    correct_requests_hash_in_header: bool,
) -> Callable[[Fork], List[ParameterSet]]:
    """
    Return a list of invalid request combinations for the given fork.

    Combinations are derived from `REQUEST_TYPES` for the fork, so a new
    request type is picked up by adding it there. The hand-crafted
    "incorrect order" cases remain valid for more types but are not
    exhaustive, so revisit them when adding a type.

    Returned parameters are: requests, block_body_override_requests, exception
    """

    def func(fork: Fork) -> List[ParameterSet]:
        request_types = request_types_from_fork(fork)

        # Per type: the EOA interaction that triggers it, and the bare request
        # (source-addressed) used to build the block body. Source addressing is
        # a no-op for fee-less requests (e.g. deposits) whose bytes omit it.
        all_request_types: Dict[
            str,
            Tuple[SystemContractInteractionTransaction, SystemContractRequest],
        ] = {
            request_type_to_id_str(request_type): (
                eoa_interaction(request_type, 0),
                request_type.from_index(0).with_source_address(TestAddress),
            )
            for request_type in request_types
        }

        expected_exceptions: List[BlockException] = [
            BlockException.INVALID_REQUESTS
        ]
        if correct_requests_hash_in_header:
            # The client also might reject the block with an invalid-block-hash
            # error because it might convert the requests in the new payload
            # parameters to the requests hash in the header and compare it with
            # the block hash.
            expected_exceptions.append(BlockException.INVALID_BLOCK_HASH)

        # - Empty requests list with invalid hash
        combinations: List[ParameterSet] = [
            pytest.param(
                [],
                [
                    bytes([i]) for i in range(fork.max_request_type() + 1)
                ],  # Using empty requests, calculate the hash using an invalid
                # calculation method:
                # sha256(sha256(b"\0") ++ sha256(b"\1") ++ sha256(b"\2") ++
                # ...)
                expected_exceptions,
                id="no_requests_and_invalid_hash_calculation_method",
            ),
            pytest.param(
                [],
                [
                    bytes([]) for _ in range(fork.max_request_type() + 1)
                ],  # Using empty requests, calculate the hash using an invalid
                # calculation method:
                # sha256(sha256(b"") ++ sha256(b"") ++ sha256(b"") ++ ...)
                expected_exceptions,
                id="no_requests_and_invalid_hash_calculation_method_2",
            ),
        ]

        # - Missing request or request type byte tests
        for request_type, (
            eoa_request,
            block_request,
        ) in all_request_types.items():
            combinations.extend(
                [
                    pytest.param(
                        [eoa_request],
                        [
                            block_request
                        ],  # The request type byte missing because we need to
                        # use `Requests`
                        expected_exceptions,
                        id=f"single_{request_type}_missing_type_byte",
                    ),
                    pytest.param(
                        [eoa_request],
                        [],
                        expected_exceptions,
                        id=f"single_{request_type}_empty_requests_list",
                    ),
                ]
            )

        # - Incorrect order tests
        correct_order: List[Bytes] = Requests(
            *[r[1] for r in all_request_types.values()]
        ).requests_list  # Requests automatically adds the type byte
        correct_order_transactions: List[
            SystemContractInteractionTransaction
        ] = [r[0] for r in all_request_types.values()]

        # Send first element to the end
        combinations.append(
            pytest.param(
                correct_order_transactions[1:]
                + [correct_order_transactions[0]],
                correct_order[1:] + [correct_order[0]],
                expected_exceptions,
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
                expected_exceptions,
                id="incorrect_order_second_request_at_end",
            ),
        )

        # Bring last element to the beginning
        combinations.append(
            pytest.param(
                [correct_order_transactions[-1]]
                + correct_order_transactions[:-1],
                [correct_order[-1]] + correct_order[:-1],
                expected_exceptions,
                id="incorrect_order_last_request_at_beginning",
            ),
        )

        # - Duplicate request tests
        for request_type, (
            eoa_request,
            block_request,
        ) in all_request_types.items():
            combinations.append(
                pytest.param(
                    [eoa_request],
                    Requests(block_request).requests_list * 2,
                    expected_exceptions,
                    id=f"duplicate_{request_type}_request",
                ),
            )

        # - Extra invalid request tests
        combinations.append(
            pytest.param(
                correct_order_transactions,
                correct_order + [b""],
                expected_exceptions,
                id="extra_empty_request",
            ),
        )
        combinations.append(
            pytest.param(
                correct_order_transactions,
                correct_order + [bytes([fork.max_request_type() + 1])],
                expected_exceptions,
                id="extra_invalid_type_request_with_no_data",
            ),
        )
        combinations.append(
            pytest.param(
                correct_order_transactions,
                correct_order + [bytes([fork.max_request_type() + 1, 0x00])],
                expected_exceptions,
                id="extra_invalid_type_request_with_data_0x00",
            ),
        )
        combinations.append(
            pytest.param(
                correct_order_transactions,
                correct_order + [bytes([fork.max_request_type() + 1, 0x01])],
                expected_exceptions,
                id="extra_invalid_type_request_with_data_0x01",
            ),
        )
        combinations.append(
            pytest.param(
                correct_order_transactions,
                correct_order + [bytes([fork.max_request_type() + 1, 0xFF])],
                expected_exceptions,
                id="extra_invalid_type_request_with_data_0xff",
            ),
        )

        return combinations

    return func


@pytest.mark.parametrize_by_fork(
    "requests,block_body_override_requests,exception",
    invalid_requests_block_combinations(correct_requests_hash_in_header=False),
)
@pytest.mark.exception_test
def test_invalid_multi_type_requests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    override_blocks: List[Block],
) -> None:
    """
    Negative testing for all request types in the same block.

    In these tests, the requests hash in the header reflects what's received in
    the parameters portion of the `engine_newPayloadVX` call, so the block hash
    calculation might pass if a client copies the info received verbatim, but
    block validation must fail after the block is executed (via RLP or Engine
    API).
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=override_blocks,
    )


@pytest.mark.parametrize_by_fork(
    "requests,block_body_override_requests,exception",
    invalid_requests_block_combinations(correct_requests_hash_in_header=True),
)
@pytest.mark.parametrize("correct_requests_hash_in_header", [True])
@pytest.mark.blockchain_test_engine_only
@pytest.mark.exception_test
def test_invalid_multi_type_requests_engine(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    override_blocks: List[Block],
) -> None:
    """
    Negative testing for all request types in the same block with incorrect
    parameters in the Engine API new payload parameters, but with the correct
    requests hash in the header so the block hash is correct.

    In these tests, the requests hash in the header reflects what's actually in
    the executed block, so the block might execute properly if the client
    ignores the requests in the new payload parameters.

    Note that the only difference between the engine version produced by this
    test and the ones produced by `test_invalid_multi_type_requests` is the
    `blockHash` value in the new payloads, which is calculated using different
    request hashes for each test, but since the request hash is not a value
    that is included in the payload, it might not be immediately apparent.

    Also these tests would not fail if the block is imported via RLP (syncing
    from a peer), so we only generate the BlockchainTestEngine for them.

    The client also might reject the block with an invalid-block-hash error
    because it might convert the requests in the new payload parameters to the
    requests hash in the header and compare it with the block hash.
    """
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=override_blocks,
    )


@pytest.mark.parametrize(
    "request_type,deployment_path", SAME_BLOCK_DEPLOYMENT_CASES
)
@pytest.mark.pre_alloc_mutable
# The pre-signed deployment transactions carry a fixed gas limit that no
# longer covers contract creation under Amsterdam's state gas pricing.
@pytest.mark.valid_until("Osaka")
def test_system_contract_deployed_and_called_in_same_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_type: type[FeeSystemContractRequest],
    deployment_path: Path,
) -> None:
    """
    Deploy a request system contract and call it in the same block.

    The post-execution system call must run against the block's accumulated
    state: it finds the code deployed earlier in the block (empty code would
    invalidate the block) and clears the inhibitor the deployment stores, so
    a request sent in the deployment block is rejected and one sent in the
    next block is accepted.
    """
    deployment_tx = Transaction.model_validate_json(
        deployment_path.read_text()
    ).with_signature_and_sender()
    deployer = deployment_tx.sender
    assert deployer is not None
    gas_price = deployment_tx.gas_price
    assert gas_price is not None
    pre.fund_address(deployer, deployment_tx.gas_limit * gas_price)

    # Drop the pre-allocated contract so the deployment transaction creates
    # it.
    pre[request_type.system_contract_address] = Account(
        balance=0,
        code=b"",
        nonce=0,
        storage={},
    )

    request_sender = pre.fund_eoa()
    # The fee once the inhibitor is cleared; the same-block request pays it
    # too, so only the inhibitor rejects it.
    fee = request_type.get_fee(0)
    rejected_request = request_type.from_index(0).copy(fee=fee)
    accepted_request = (
        request_type.from_index(1)
        .copy(fee=fee)
        .with_source_address(request_sender)
    )

    def request_tx(request: FeeSystemContractRequest) -> Transaction:
        return Transaction(
            to=request_type.system_contract_address,
            data=request.calldata,
            value=request.value,
            sender=request_sender,
        )

    expected_code = fork.pre_allocation_blockchain()[
        int.from_bytes(request_type.system_contract_address, "big")
    ]["code"]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[deployment_tx, request_tx(rejected_request)],
                header_verify=Header(requests_hash=Requests()),
            ),
            Block(
                txs=[request_tx(accepted_request)],
                header_verify=Header(requests_hash=Requests(accepted_request)),
            ),
        ],
        post={
            request_type.system_contract_address: Account(
                code=expected_code,
                nonce=1,
                # The rejected request's fee was refunded.
                balance=fee,
            ),
            deployer: Account(nonce=1),
            request_sender: Account(nonce=2),
        },
    )
