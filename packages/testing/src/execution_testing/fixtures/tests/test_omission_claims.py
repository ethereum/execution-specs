"""Pin separate ILs and committed claim ordering in Engine fixtures."""

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.forks import Bogota
from execution_testing.rpc.rpc_types import PayloadAttributes
from execution_testing.specs.blockchain import GENESIS_ENVIRONMENT_DEFAULTS
from execution_testing.test_types import (
    BlockAccessList,
    Environment,
    OmissionClaim,
    Transaction,
)
from execution_testing.test_types.inclusion_list import (
    validate_inclusion_list_metadata,
)


def test_claims_and_lists_reach_engine_fixture() -> None:
    """Preserve exact lists and duplicate claims across serialization."""
    env = Environment(**GENESIS_ENVIRONMENT_DEFAULTS).set_fork_requirements(
        Bogota
    )
    header = FixtureHeader.genesis(Bogota, env, Hash(0))
    tx = Transaction(gas_limit=21_000).with_signature_and_sender()
    claim = OmissionClaim(transaction_hash=tx.hash, evaluation_index=7)
    claims = [
        claim,
        claim,
        OmissionClaim(transaction_hash=tx.hash, evaluation_index=0),
    ]
    lists = [[tx] if i in (0, 9) else [] for i in range(16)]
    payload = FixtureEngineNewPayload.from_fixture_header(
        fork=Bogota,
        header=header,
        transactions=[],
        withdrawals=[],
        requests=[],
        block_access_list=BlockAccessList().rlp,
        inclusion_lists=lists,
        omission_claims=claims,
        inclusion_list_satisfied=False,
    )

    encoded = payload.model_dump(mode="json", by_alias=True)
    assert payload.new_payload_version == 6
    assert payload.forkchoice_updated_version == 5
    assert len(encoded["params"]) == 6
    assert encoded["params"][4] == [
        [tx.rlp().hex()] if il else [] for il in lists
    ]
    assert encoded["params"][5] == [
        {"transactionHash": tx.hash.hex(), "evaluationIndex": "0x7"},
        {"transactionHash": tx.hash.hex(), "evaluationIndex": "0x7"},
        {"transactionHash": tx.hash.hex(), "evaluationIndex": "0x0"},
    ]
    assert FixtureEngineNewPayload.model_validate(encoded) == payload
    attributes = payload.get_payload_attributes()
    assert attributes.inclusion_lists == [
        [tx.rlp()] if il else [] for il in lists
    ]
    assert "omissionClaims" not in attributes.model_dump(by_alias=True)


def test_payload_attributes_require_all_committee_positions() -> None:
    """Reject a shortened outer list rather than guessing positions."""
    with pytest.raises(ValueError, match="committee position"):
        PayloadAttributes.for_fork(
            Bogota,
            timestamp=1,
            target_gas_limit=30_000_000,
            slot_number=1,
            inclusion_lists=[[Bytes("0xc0")]],
        )


@pytest.mark.parametrize("index", [-1, 2**64])
def test_claim_index_is_uint64(index: int) -> None:
    """Reject negative and overflowing insertion indices."""
    with pytest.raises(ValueError):
        OmissionClaim(transaction_hash=Hash(1), evaluation_index=index)


def test_claim_index_uint64_boundary() -> None:
    """Preserve an in-range index for EIP-7805's end-of-payload clamp."""
    claim = OmissionClaim(transaction_hash=Hash(1), evaluation_index=2**64 - 1)
    assert claim.model_dump(mode="json")["evaluation_index"] == (
        "0xffffffffffffffff"
    )


@pytest.mark.parametrize(
    "lists",
    [
        [],
        [[]] * 15,
        [[]] * 17,
        [[Bytes()]] + [[]] * 15,
        [[Bytes(b"a" * 8192), Bytes("0xc0")]] + [[]] * 15,
        [[Bytes(b"a" * 4097)] * 2] + [[]] * 15,
    ],
)
def test_malformed_inclusion_metadata(lists: list[list[Bytes]]) -> None:
    """Reject malformed containers before a fixture can request execution."""
    with pytest.raises(ValueError):
        validate_inclusion_list_metadata(lists)


def test_inclusion_metadata_bounds_per_committee_member() -> None:
    """Keep repeated transactions and independent per-list byte bounds."""
    validate_inclusion_list_metadata(
        [
            [Bytes(b"a" * 8191), Bytes("0xc0")],
            [Bytes("0xc0"), Bytes(b"b" * 8191)],
        ]
        + [[]] * 14,
    )
    validate_inclusion_list_metadata([[Bytes("0xc0")] * 2] + [[]] * 15)
    claims = [OmissionClaim(transaction_hash=Hash(0), evaluation_index=0)]
    validate_inclusion_list_metadata([[]] * 16, claims * 4096)
    with pytest.raises(ValueError, match="Too many"):
        validate_inclusion_list_metadata([[]] * 16, claims * 4097)
