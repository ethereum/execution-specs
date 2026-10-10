"""Tests for the reorg consumer's blob versioned-hash computation."""

import hashlib
from unittest.mock import MagicMock

from execution_testing.base_types import Bytes, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import (
    BlockchainEngineReorgFixture,
    GetPayloadStep,
)
from execution_testing.forks import Cancun
from execution_testing.rpc.rpc_types import BlobsBundle
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic.test_via_reorg import StepRunner


def test_get_payload_computes_blob_versioned_hashes(
    default_t8n: TransitionTool,
) -> None:
    """
    A built payload's blob commitments are converted to versioned hashes
    per EIP-4844 (PR3556-R0023), now via `BlobsBundle.blob_versioned_hashes`
    instead of a duplicated formula.
    """
    test = ReorgTest(
        fork=Cancun, pre=Alloc(), blocks=[ReorgBlock(label="a1")], steps=[]
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    engine = MagicMock()
    step_runner = StepRunner(
        fixture, MagicMock(), engine, TimingData("test"), 0.0
    )
    step_runner.last_payload_id = Bytes(b"\x01" * 8)
    commitment = Bytes(b"\xaa" * 48)
    expected_hash = Hash(
        bytes([1]) + hashlib.sha256(bytes(commitment)).digest()[1:]
    )
    response = MagicMock()
    response.execution_payload = fixture.blocks["a1"].payload.params[0]
    response.blobs_bundle = BlobsBundle(
        commitments=[commitment], proofs=[], blobs=[]
    )
    response.execution_requests = None
    engine.get_payload.return_value = response
    step_runner.get_payload(
        "gp", GetPayloadStep(bind="p1", parent="genesis", version=3)
    )
    assert step_runner.bound["p1"].versioned_hashes == [expected_hash]
