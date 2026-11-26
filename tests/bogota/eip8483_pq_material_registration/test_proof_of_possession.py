"""
Proof of possession tests for
[EIP-8483: Post-Quantum Material Registration](https://eips.ethereum.org/EIPS/eip-8483).

A registration carries a leanXMSS signature by the registered key over that
key and the BLS key, and the predeploys only queue it if the verifier
contract accepts that proof.
"""

from dataclasses import replace
from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    FeeSystemContractRequest,
    Header,
    Op,
    ParameterSet,
    PQBuilderRegistrationRequest,
    PQRegistrationRequest,
    Requests,
    SystemContractInteractionContract,
    Transaction,
    keccak256,
)

from .helpers import (
    PQRequestClass,
    call_results_relay,
    flip_byte,
    record_storage,
    with_both_registrations,
)
from .spec import (
    OTHER_CHAIN_PROOFS_OF_POSSESSION,
    PROOFS_OF_POSSESSION,
    ProofOfPossession,
    Spec,
    ref_spec_8483,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_8483.git_path
REFERENCE_SPEC_VERSION = ref_spec_8483.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.execute(
        pytest.mark.skip(reason="Assumes the predeploys' genesis state")
    ),
]

VALID_PROOF = PROOFS_OF_POSSESSION.proofs[0]
# The signature is the leaf index (4 bytes, little-endian), then the bottom
# and the top layer of the hypertree (1200 bytes each).
LEAF_INDEX_SIZE = 4
LAYER_SIZE = 1200


def every_proof_scenarios() -> List[ParameterSet]:
    """Register every valid proof with each predeploy from one relay."""
    return [
        pytest.param(
            request_class,
            [
                [
                    SystemContractInteractionContract(
                        requests=[
                            request_class.from_proof(proof)
                            for proof in PROOFS_OF_POSSESSION.proofs
                        ]
                    )
                ]
            ],
            id=name,
        )
        for request_class, name in (
            (PQRegistrationRequest, "validator"),
            (PQBuilderRegistrationRequest, "builder"),
        )
    ]


@pytest.mark.parametrize(
    "request_class,system_contract_interactions_per_block",
    every_proof_scenarios(),
)
def test_every_proof_accepted(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
    included_requests: List[List[FeeSystemContractRequest]],
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    Every proof in the vectors registers its key with either predeploy,
    since a proof doesn't depend on the role.
    """
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            request_class.system_contract_address: Account(
                balance=sum(
                    request.value
                    for block in included_requests
                    for request in block
                )
            )
        },
    )


def invalid_proofs() -> List[ParameterSet]:
    """Return proofs the verifier must reject, each with an id."""
    signature = VALID_PROOF.signature
    other_proof = PROOFS_OF_POSSESSION.proofs[1]
    cases = {
        "at_leaf_one": PROOFS_OF_POSSESSION.wrong_leaf,
        "without_domain": PROOFS_OF_POSSESSION.no_domain,
        "for_other_chain": OTHER_CHAIN_PROOFS_OF_POSSESSION.proofs[0],
        "other_bls_pubkey": replace(
            VALID_PROOF, bls_pubkey=other_proof.bls_pubkey
        ),
        "bls_pubkey_last_byte_changed": replace(
            VALID_PROOF,
            bls_pubkey=flip_byte(VALID_PROOF.bls_pubkey, 47),
        ),
        "xmss_pubkey_first_byte_changed": replace(
            VALID_PROOF,
            xmss_pubkey=flip_byte(VALID_PROOF.xmss_pubkey, 0),
        ),
        "xmss_pubkey_last_byte_changed": replace(
            VALID_PROOF,
            xmss_pubkey=flip_byte(VALID_PROOF.xmss_pubkey, 31),
        ),
        "signature_of_other_proof": replace(
            VALID_PROOF, signature=other_proof.signature
        ),
        "signature_leaf_index_changed": replace(
            VALID_PROOF, signature=flip_byte(signature, 0)
        ),
        "signature_bottom_layer_changed": replace(
            VALID_PROOF, signature=flip_byte(signature, LEAF_INDEX_SIZE)
        ),
        "signature_top_layer_changed": replace(
            VALID_PROOF,
            signature=flip_byte(signature, LEAF_INDEX_SIZE + LAYER_SIZE),
        ),
        "signature_last_byte_changed": replace(
            VALID_PROOF, signature=flip_byte(signature, len(signature) - 1)
        ),
    }
    return [pytest.param(proof, id=name) for name, proof in cases.items()]


@pytest.mark.parametrize("invalid_proof", invalid_proofs())
@with_both_registrations
def test_invalid_proof_rejected(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: PQRequestClass,
    invalid_proof: ProofOfPossession,
) -> None:
    """
    A registration whose proof doesn't verify reverts and writes nothing:
    the same relay's registration with the valid proof is then stored as the
    queue's first item.
    """
    predeploy = request_class.system_contract_address
    fee = request_class.get_fee(0)
    rejected = request_class.from_proof(invalid_proof).copy(fee=fee)
    accepted = request_class.from_proof(VALID_PROOF).copy(fee=fee)
    relay, data, relay_storage = call_results_relay(
        pre,
        [
            (predeploy, rejected.calldata, fee, False),
            (predeploy, accepted.calldata, fee, True),
        ],
    )
    record = accepted.with_source_address(relay)

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
    "verifier_code,accepted",
    [
        pytest.param(None, False, id="no_code"),
        pytest.param(Op.REVERT(0, 0), False, id="reverts"),
        pytest.param(
            Op.MSTORE(0, 1) + Op.REVERT(0, 32), False, id="reverts_one"
        ),
        pytest.param(Op.STOP, False, id="returns_nothing"),
        pytest.param(Op.RETURN(0, 32), False, id="returns_zero"),
        pytest.param(
            Op.MSTORE(0, 2) + Op.RETURN(0, 32), False, id="returns_two"
        ),
        pytest.param(
            Op.MSTORE(0, 1) + Op.RETURN(1, 31), False, id="returns_31_bytes"
        ),
        pytest.param(
            Op.MSTORE(0, 1) + Op.RETURN(0, 64), False, id="returns_64_bytes"
        ),
        # The predeploy calls the verifier with STATICCALL, so a verifier
        # that writes storage fails before it returns.
        pytest.param(
            Op.SSTORE(0, 1) + Op.MSTORE(0, 1) + Op.RETURN(0, 32),
            False,
            id="writes_storage",
        ),
        pytest.param(
            Op.MSTORE(0, 1) + Op.RETURN(0, 32), True, id="returns_one"
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
@with_both_registrations
def test_verifier_response(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: PQRequestClass,
    verifier_code: Bytecode | None,
    accepted: bool,
) -> None:
    """
    With the verifier replaced, a registration is queued only when the
    verifier returns the 32-byte word 1. The registration carries a proof the
    real verifier rejects, so the replacement alone decides.
    """
    if verifier_code is None:
        del pre[Spec.VERIFIER]
    else:
        pre.update_account(Spec.VERIFIER, code=verifier_code)
    predeploy = request_class.system_contract_address
    fee = request_class.get_fee(0)
    request = request_class.from_proof(PROOFS_OF_POSSESSION.wrong_leaf).copy(
        fee=fee
    )
    relay, data, relay_storage = call_results_relay(
        pre, [(predeploy, request.calldata, fee, accepted)]
    )
    record = request.with_source_address(relay)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=relay, data=data)],
                header_verify=Header(
                    requests_hash=Requests(record) if accepted else Requests()
                ),
            )
        ],
        post={
            relay: Account(storage=relay_storage),
            predeploy: Account(
                balance=fee if accepted else 0,
                storage=record_storage(record, 0) if accepted else {},
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@with_both_registrations
def test_verifier_input(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    The predeploy passes the verifier the BLS key, the leanXMSS key and the
    signature, without the unsigned half of a validator's `pq_data`. A
    replaced verifier accepts the registration only if its input is exactly
    that.
    """
    proof = VALID_PROOF
    expected_input = (
        bytes(proof.bls_pubkey)
        + bytes(proof.xmss_pubkey)
        + bytes(proof.signature)
    )
    pre.update_account(
        Spec.VERIFIER,
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.MSTORE(
            0,
            Op.AND(
                Op.EQ(Op.CALLDATASIZE, len(expected_input)),
                Op.EQ(Op.SHA3(0, Op.CALLDATASIZE), keccak256(expected_input)),
            ),
        )
        + Op.RETURN(0, 32),
    )
    predeploy = request_class.system_contract_address
    fee = request_class.get_fee(0)
    request: FeeSystemContractRequest
    if request_class is PQRegistrationRequest:
        request = PQRegistrationRequest.from_proof(proof, unsigned=2**256 - 1)
    elif request_class is PQBuilderRegistrationRequest:
        request = PQBuilderRegistrationRequest.from_proof(proof)
    else:
        raise ValueError(f"unhandled request class {request_class}")
    request = request.copy(fee=fee)
    relay, data, relay_storage = call_results_relay(
        pre, [(predeploy, request.calldata, fee, True)]
    )
    record = request.with_source_address(relay)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=relay, data=data)],
                header_verify=Header(requests_hash=Requests(record)),
            )
        ],
        post={
            relay: Account(storage=relay_storage),
            predeploy: Account(balance=fee, storage=record_storage(record, 0)),
        },
    )
