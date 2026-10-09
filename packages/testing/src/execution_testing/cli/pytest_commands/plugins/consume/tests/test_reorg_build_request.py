"""Tests for which ``forkchoiceUpdated`` replaces the consumer's build."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.blockchain import PayloadAttributes
from execution_testing.fixtures.reorg import (
    BlockchainEngineReorgFixture,
    ForkchoiceUpdatedStep,
    Outcome,
)
from execution_testing.forks import Cancun
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic.test_via_reorg import StepRunner

FIRST = Bytes(b"\x01" * 8)
SECOND = Bytes(b"\x02" * 8)
ATTRIBUTES = PayloadAttributes(
    timestamp=12, prev_randao=Hash(0), suggested_fee_recipient=Address(0)
)


def response(status: str, payload_id: Bytes | None) -> MagicMock:
    """A ``forkchoiceUpdated`` response."""
    reply = MagicMock()
    reply.payload_status.status.value = status
    reply.payload_status.latest_valid_hash = None
    reply.payload_status.validation_error = None
    reply.payload_id = payload_id
    return reply


@pytest.mark.parametrize(
    "attributes,reply,outcome,kept",
    [
        pytest.param(
            None,
            response("VALID", None),
            Outcome(id="o", status="VALID"),
            FIRST,
            id="update_without_attributes",
        ),
        pytest.param(
            ATTRIBUTES,
            response("SYNCING", None),
            Outcome(id="o", status="SYNCING"),
            FIRST,
            id="build_answered_without_payload_id",
        ),
        pytest.param(
            ATTRIBUTES,
            JSONRPCError(-38003, "Invalid payload attributes"),
            Outcome(
                id="o", error_code=EngineAPIError.InvalidPayloadAttributes
            ),
            FIRST,
            id="build_answered_with_an_error",
        ),
        pytest.param(
            ATTRIBUTES,
            response("VALID", SECOND),
            Outcome(id="o", status="VALID"),
            SECOND,
            id="build_answered_with_a_payload_id",
        ),
    ],
)
def test_only_a_returned_payload_id_replaces_the_build(
    default_t8n: TransitionTool,
    attributes: PayloadAttributes | None,
    reply: Any,
    outcome: Outcome,
    kept: Bytes,
) -> None:
    """
    ``getPayload`` retrieves the last ``payloadId`` a ``forkchoiceUpdated``
    returned; a response without one starts no build and ends none.
    """
    test = ReorgTest(
        fork=Cancun, pre=Alloc(), blocks=[ReorgBlock(label="a1")], steps=[]
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    engine = MagicMock()
    engine.forkchoice_updated.side_effect = [
        response("VALID", FIRST),
        reply,
    ]
    step_runner = StepRunner(
        fixture, MagicMock(), engine, TimingData("test"), 0.0
    )
    step_runner.forkchoice_updated(
        "build",
        ForkchoiceUpdatedStep(
            head="a1",
            version=3,
            payload_attributes=ATTRIBUTES,
            expect=[Outcome(id="o", status="VALID")],
        ),
        0,
    )
    step_runner.forkchoice_updated(
        "next",
        ForkchoiceUpdatedStep(
            head="a1",
            version=3,
            payload_attributes=attributes,
            expect=[outcome],
        ),
        0,
    )
    assert step_runner.last_payload_id == kept
