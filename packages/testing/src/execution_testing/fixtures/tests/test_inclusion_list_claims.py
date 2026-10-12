"""Pin membership and committed claim ordering in Engine fixtures."""

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
    InclusionListClaim,
    Transaction,
)
from execution_testing.test_types.inclusion_list import (
    validate_inclusion_list_metadata,
)


def test_claims_and_membership_reach_engine_fixture() -> None:
    """Preserve exact membership and duplicate claims across serialization."""
    env = Environment(**GENESIS_ENVIRONMENT_DEFAULTS).set_fork_requirements(
        Bogota
    )
    header = FixtureHeader.genesis(Bogota, env, Hash(0))
    tx = Transaction(gas_limit=21_000).with_signature_and_sender()
    claim = InclusionListClaim(transaction_hash=tx.hash, transaction_index=7)
    claims = [
        claim,
        claim,
        InclusionListClaim(transaction_hash=tx.hash, transaction_index=0),
    ]
    membership = [Bytes("0x0102")]
    payload = FixtureEngineNewPayload.from_fixture_header(
        fork=Bogota,
        header=header,
        transactions=[],
        withdrawals=[],
        requests=[],
        block_access_list=BlockAccessList().rlp,
        inclusion_list_transactions=[tx],
        inclusion_list_membership=membership,
        inclusion_list_claims=claims,
        inclusion_list_satisfied=False,
    )

    encoded = payload.model_dump(mode="json", by_alias=True)
    assert payload.new_payload_version == 6
    assert payload.forkchoice_updated_version == 5
    assert len(encoded["params"]) == 7
    assert encoded["params"][4] == [tx.rlp().hex()]
    assert encoded["params"][5] == ["0x0102"]
    assert encoded["params"][6] == [
        {"transactionHash": tx.hash.hex(), "transactionIndex": "0x7"},
        {"transactionHash": tx.hash.hex(), "transactionIndex": "0x7"},
        {"transactionHash": tx.hash.hex(), "transactionIndex": "0x0"},
    ]
    assert FixtureEngineNewPayload.model_validate(encoded) == payload
    attributes = payload.get_payload_attributes()
    assert attributes.inclusion_list_transactions == [tx.rlp()]
    assert attributes.inclusion_list_membership == membership
    assert "inclusionListClaims" not in attributes.model_dump(by_alias=True)


def test_payload_attributes_require_explicit_membership() -> None:
    """Do not infer committee provenance for a supplied nonempty list."""
    with pytest.raises(ValueError, match="need membership"):
        PayloadAttributes.for_fork(
            Bogota,
            timestamp=1,
            target_gas_limit=30_000_000,
            slot_number=1,
            inclusion_list_transactions=[Bytes("0xc0")],
        )


@pytest.mark.parametrize("index", [-1, 2**64])
def test_claim_index_is_uint64(index: int) -> None:
    """Reject negative and overflowing insertion indices."""
    with pytest.raises(ValueError):
        InclusionListClaim(transaction_hash=Hash(1), transaction_index=index)


def test_claim_index_uint64_boundary() -> None:
    """Preserve an in-range index for EIP-7805's end-of-payload clamp."""
    claim = InclusionListClaim(
        transaction_hash=Hash(1), transaction_index=2**64 - 1
    )
    assert claim.model_dump(mode="json")["transaction_index"] == (
        "0xffffffffffffffff"
    )


@pytest.mark.parametrize(
    "transactions,membership",
    [
        ([Bytes("0xc0")], []),
        ([Bytes("0xc0")], [Bytes("0x00")]),
        ([Bytes("0xc0")], [Bytes("0x0000")]),
        ([Bytes("0xc0")], [Bytes("0x010000")]),
        ([Bytes()], [Bytes("0x0100")]),
        ([Bytes("0xc0"), Bytes("0xc0")], [Bytes("0x0100")] * 2),
        ([Bytes(b"a" * 8192), Bytes("0xc0")], [Bytes("0x0100")] * 2),
    ],
)
def test_malformed_inclusion_metadata(
    transactions: list[Bytes], membership: list[Bytes]
) -> None:
    """Reject malformed containers before a fixture can request execution."""
    with pytest.raises(ValueError):
        validate_inclusion_list_metadata(transactions, membership)


def test_inclusion_metadata_bounds_per_committee_member() -> None:
    """Charge shared envelopes to each member, keeping members independent."""
    validate_inclusion_list_metadata(
        [Bytes(b"a" * 8191), Bytes("0xc0"), Bytes(b"b" * 8191)],
        [Bytes("0x0100"), Bytes("0x0102"), Bytes("0x0002")],
    )
    claims = [
        InclusionListClaim(transaction_hash=Hash(0), transaction_index=0)
    ]
    validate_inclusion_list_metadata([], [], claims * 4096)
    with pytest.raises(ValueError, match="Too many"):
        validate_inclusion_list_metadata([], [], claims * 4097)
