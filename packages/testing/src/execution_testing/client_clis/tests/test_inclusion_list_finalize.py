"""Pin complete newPayloadV6 inputs on both live block-building paths."""

from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.cli.pytest_commands.plugins.execute.rpc.chain_builder_eth_rpc import (  # noqa: E501
    ChainBuilderEthRPC,
)
from execution_testing.client_clis import ClientBackend
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.forks import Bogota
from execution_testing.rpc.rpc_types import (
    BlobsBundle,
    GetPayloadResponse,
    PayloadStatus,
    PayloadStatusEnum,
)
from execution_testing.specs.blockchain import GENESIS_ENVIRONMENT_DEFAULTS
from execution_testing.test_types import Environment, InclusionListClaim


def built_payload() -> GetPayloadResponse:
    """Return a minimal payload with a duplicate committed claim list."""
    environment = Environment(
        **GENESIS_ENVIRONMENT_DEFAULTS
    ).set_fork_requirements(Bogota)
    header = FixtureHeader.genesis(Bogota, environment, Hash(0))
    claim = InclusionListClaim(transaction_hash=Hash(1), evaluation_index=7)
    return GetPayloadResponse(
        execution_payload=FixtureExecutionPayload.from_fixture_header(
            header=header, transactions=[], withdrawals=[]
        ),
        blobs_bundle=BlobsBundle(commitments=[], proofs=[], blobs=[]),
        execution_requests=[],
        inclusion_list_claims=[claim, claim],
    )


@pytest.mark.parametrize("client_backend", [True, False])
def test_live_finalize_preserves_context(client_backend: bool) -> None:
    """Keep exact inputs available while waiting for a deferred verdict."""
    payload = built_payload()
    rpc = MagicMock()
    status = PayloadStatus(
        status=PayloadStatusEnum.VALID,
        latest_valid_hash=payload.execution_payload.block_hash,
        validation_error=None,
        inclusion_list_satisfied=None,
        inclusion_list_context_id=Hash(7),
    )
    completed = status.model_copy(
        update={"inclusion_list_satisfied": not client_backend}
    )
    rpc.wait_for_inclusion_list.return_value = completed
    rpc.new_payload.return_value = status
    rpc.new_payload_with_retry.return_value = status
    rpc.forkchoice_updated.return_value.payload_status = status
    rpc.forkchoice_updated_with_retry.return_value.payload_status = status
    if client_backend:
        backend = ClientBackend.__new__(ClientBackend)
        backend.engine_rpc = rpc
        assert (
            backend._finalize(
                payload,
                parent_beacon_block_root=Hash(0),
                block_fork=Bogota,
                inclusion_list_transactions=[Bytes("0xc0")],
                inclusion_list_membership=[Bytes("0x0002")],
            )
            is False
        )
        call = rpc.new_payload_with_retry.call_args
        assert call.args[4:6] == ([Bytes("0xc0")], [Bytes("0x0002")])
    else:
        builder = ChainBuilderEthRPC.__new__(ChainBuilderEthRPC)
        builder.engine_rpc = rpc
        builder.fork = Bogota
        builder._finalize_payload(payload, Hash(0))
        call = rpc.new_payload.call_args
        assert call.args[4:6] == ([], [])
    assert call.kwargs["version"] == 6
    assert len(call.args) == 7
    assert call.args[6] == payload.inclusion_list_claims
    rpc.wait_for_inclusion_list.assert_called_once_with(
        status, *call.args, version=6
    )


def test_live_finalize_requires_get_payload_claims() -> None:
    """A missing required V7 field cannot be mistaken for no omissions."""
    payload = built_payload()
    payload.inclusion_list_claims = None
    backend = ClientBackend.__new__(ClientBackend)
    rpc = MagicMock()
    backend.engine_rpc = rpc
    with pytest.raises(ValueError, match="getPayloadV7"):
        backend._finalize(
            payload,
            parent_beacon_block_root=Hash(0),
            block_fork=Bogota,
            inclusion_list_membership=[],
            inclusion_list_claims=[],
        )
    rpc.new_payload_with_retry.assert_not_called()
