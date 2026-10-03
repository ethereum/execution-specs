"""Tests for engine-witness simulator behavior."""

from types import SimpleNamespace
from typing import Any, cast

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators.simulator_logic.test_via_engine_witness import (  # noqa: E501
    test_blockchain_via_engine_witness as run_engine_witness,
)


def test_mutated_execution_witness_fixture_is_skipped() -> None:
    """Fixtures with deliberately mutated witnesses are not consumable."""
    fixture = cast(
        Any,
        SimpleNamespace(
            payloads=[
                SimpleNamespace(
                    execution_witness=object(),
                    execution_witness_mutated=True,
                )
            ]
        ),
    )
    unused_dependency = cast(Any, None)

    with pytest.raises(
        pytest.skip.Exception,
        match="fixture contains a deliberately mutated executionWitness",
    ):
        run_engine_witness(
            timing_data=unused_dependency,
            eth_rpc=unused_dependency,
            engine_rpc=unused_dependency,
            engine_ssz_rpc=unused_dependency,
            fixture=fixture,
            genesis_header=unused_dependency,
            use_ssz_transport=False,
        )


@pytest.mark.parametrize(
    "use_ssz,expected_error,bal,skip",
    [
        (True, True, None, True),
        (False, True, None, False),
        (True, False, None, False),
        (True, True, b"", False),
    ],
)
def test_json_only_missing_bal_is_skipped_before_rest_discovery(
    use_ssz: bool, expected_error: bool, bal: bytes | None, skip: bool
) -> None:
    """Skip only intentional JSON-only BAL omissions in REST mode."""
    from unittest.mock import Mock

    from execution_testing.exceptions import EngineAPIError
    from execution_testing.forks import Amsterdam

    from ..timing import TimingData

    payload = SimpleNamespace(
        execution_witness=object(),
        execution_witness_mutated=False,
        error_code=EngineAPIError.InvalidParams if expected_error else None,
        params=[
            SimpleNamespace(number=1, timestamp=12, block_access_list=bal)
        ],
    )
    client = Mock()
    client.post_witness_request.return_value = SimpleNamespace(
        status_code=400,
        headers={"Content-Type": "application/problem+json"},
        json=lambda: {"type": "/engine-api/errors/ssz-decode-error"},
    )
    client.forkchoice_updated_with_retry.side_effect = RuntimeError(
        "reached execution"
    )
    fixture = SimpleNamespace(
        payloads=[payload],
        fork=Amsterdam,
        genesis=SimpleNamespace(block_hash=0),
    )
    payload.forkchoice_updated_version = 4

    def run() -> None:
        run_engine_witness(
            timing_data=TimingData("test"),
            eth_rpc=client,
            engine_rpc=client,
            engine_ssz_rpc=client,
            fixture=cast(Any, fixture),
            genesis_header=cast(Any, None),
            use_ssz_transport=use_ssz,
        )

    if skip:
        with pytest.raises(pytest.skip.Exception, match="JSON-only.*BAL"):
            run()
        assert not client.mock_calls
    else:
        with pytest.raises(RuntimeError, match="reached execution"):
            run()


@pytest.mark.parametrize("body", [b"", b"\x28", bytes(40)])
@pytest.mark.parametrize(
    "status,problem,content_type,accepted",
    [
        (400, "ssz-decode-error", "application/problem+json", True),
        (400, "parse-error", "application/problem+json", True),
        (200, "ssz-decode-error", "application/problem+json", False),
        (500, "ssz-decode-error", "application/problem+json", False),
        (400, "invalid-body", "application/problem+json", False),
        (400, "invalid-request", "application/problem+json", False),
        (400, "ssz-decode-error", "application/json", False),
    ],
)
def test_malformed_ssz_request_conformance(
    body: bytes,
    status: int,
    problem: str,
    content_type: str,
    accepted: bool,
) -> None:
    """Ensure the simulator detects incorrect malformed-request replies."""
    import json
    from unittest.mock import Mock

    import requests

    from execution_testing.cli.pytest_commands.plugins.consume.simulators.simulator_logic.test_via_engine_witness import (  # noqa: E501
        _assert_malformed_witness_request,
    )
    from execution_testing.forks import Amsterdam

    from ..exceptions import LoggedError

    response = requests.Response()
    response.status_code = status
    response.headers["Content-Type"] = content_type
    response._content = json.dumps(
        {"type": f"/engine-api/errors/{problem}"}
    ).encode()
    client = Mock()
    client.post_witness_request.return_value = response

    def run() -> None:
        _assert_malformed_witness_request(
            engine_ssz_rpc=client,
            body=body,
        )

    if accepted or (not body and problem == "invalid-request"):
        run()
    else:
        with pytest.raises(LoggedError, match="Malformed SSZ request"):
            run()
    client.post_witness_request.assert_called_once_with(body, fork=Amsterdam)


@pytest.mark.parametrize("repeat_has_witness", [True, False])
@pytest.mark.parametrize("transition", [True, False])
def test_rest_checks_already_known_payload(
    repeat_has_witness: bool, transition: bool
) -> None:
    """Require a complete witness again when a valid payload is repeated."""
    from unittest.mock import Mock

    from execution_testing.base_types import Bytes, Hash
    from execution_testing.forks import Amsterdam, BPO2ToAmsterdamAtTime15k
    from execution_testing.rpc.rpc_types import (
        NewPayloadWithWitnessResponse,
        PayloadStatusEnum,
    )
    from execution_testing.test_types.execution_witness import ExecutionWitness

    from ..exceptions import LoggedError
    from ..timing import TimingData

    witness = ExecutionWitness(state=[], codes=[], headers=[Bytes(b"header")])
    valid = NewPayloadWithWitnessResponse(
        PayloadStatusEnum.VALID, Hash(1), None, witness
    )
    missing = NewPayloadWithWitnessResponse(
        PayloadStatusEnum.VALID, Hash(1), None, None
    )
    payload = SimpleNamespace(
        execution_witness=witness,
        execution_witness_mutated=False,
        error_code=None,
        valid=lambda: True,
        forkchoice_updated_version=4,
        params=[
            SimpleNamespace(number=2, timestamp=15000, block_hash=Hash(1))
        ],
    )
    setup_payload = SimpleNamespace(
        execution_witness=None,
        execution_witness_mutated=False,
        error_code=None,
        valid=lambda: True,
        new_payload_version=4,
        forkchoice_updated_version=3,
        params=[
            SimpleNamespace(number=1, timestamp=14999, block_hash=Hash(2))
        ],
    )
    genesis = SimpleNamespace(block_hash=Hash(0))
    fixture = SimpleNamespace(
        payloads=[setup_payload, payload] if transition else [payload],
        genesis=genesis,
        fork=BPO2ToAmsterdamAtTime15k if transition else Amsterdam,
    )
    engine = Mock()
    forkchoice = SimpleNamespace(
        payload_status=SimpleNamespace(status=PayloadStatusEnum.VALID)
    )
    engine.forkchoice_updated_with_retry.return_value = forkchoice
    engine.forkchoice_updated.return_value = forkchoice
    engine.new_payload.return_value = SimpleNamespace(
        status=PayloadStatusEnum.VALID,
        latest_valid_hash=Hash(2),
        validation_error=None,
    )
    rest = Mock()
    rest.post_witness_request.return_value = SimpleNamespace(
        status_code=400,
        headers={"Content-Type": "application/problem+json"},
        json=lambda: {"type": "/engine-api/errors/ssz-decode-error"},
    )
    calls = Mock()
    calls.attach_mock(engine.new_payload, "setup")
    calls.attach_mock(engine.forkchoice_updated, "forkchoice")
    calls.attach_mock(rest.new_payload_with_witness, "witness")
    rest.new_payload_with_witness.side_effect = [
        valid,
        valid if repeat_has_witness else missing,
    ]
    eth = Mock()
    eth.get_block_by_number.return_value = {"hash": str(genesis.block_hash)}

    def run() -> None:
        run_engine_witness(
            timing_data=TimingData("test"),
            eth_rpc=eth,
            engine_rpc=engine,
            engine_ssz_rpc=rest,
            fixture=cast(Any, fixture),
            genesis_header=cast(Any, genesis),
            use_ssz_transport=True,
        )

    if repeat_has_witness:
        run()
        assert engine.forkchoice_updated.call_count == 1 + int(transition)
    else:
        with pytest.raises(LoggedError, match="no witness"):
            run()
        assert engine.forkchoice_updated.call_count == int(transition)
    if transition:
        engine.new_payload.assert_called_once_with(
            *setup_payload.params, version=4
        )
    else:
        engine.new_payload.assert_not_called()
    engine.new_payload_with_witness.assert_not_called()
    assert [call[0] for call in calls.mock_calls] == (
        (["setup", "forkchoice"] if transition else [])
        + ["witness", "witness"]
        + (["forkchoice"] if repeat_has_witness else [])
    )
    rest.check_witness_capability.assert_called_once_with(Amsterdam)
    assert [
        call.args[0] for call in rest.post_witness_request.call_args_list
    ] == [b"", b"\x28", bytes(40)]
    assert rest.new_payload_with_witness.call_count == 2


@pytest.mark.parametrize("use_ssz", [True, False])
@pytest.mark.parametrize(
    "latest_hash,error,message",
    [
        (None, None, "latest valid hash"),
        (2, None, "latest valid hash"),
        (1, "", "validation error"),
        (1, "bad block", "validation error"),
    ],
)
def test_valid_payload_status_fields(
    use_ssz: bool,
    latest_hash: int | None,
    error: str | None,
    message: str,
) -> None:
    """Check VALID status fields even without a fixture witness to compare."""
    from execution_testing.base_types import Hash
    from execution_testing.cli.pytest_commands.plugins.consume.simulators.simulator_logic.test_via_engine_witness import (  # noqa: E501
        _assert_witness_response,
    )
    from execution_testing.rpc.rpc_types import (
        NewPayloadWithWitnessResponse,
        PayloadStatusEnum,
    )

    from ..exceptions import LoggedError
    from ..timing import TimingData

    payload = SimpleNamespace(
        error_code=None,
        valid=lambda: True,
        execution_witness=None,
        params=[SimpleNamespace(block_hash=Hash(1))],
    )
    result = NewPayloadWithWitnessResponse(
        PayloadStatusEnum.VALID,
        Hash(latest_hash) if latest_hash is not None else None,
        error,
    )
    with pytest.raises(LoggedError, match=message):
        _assert_witness_response(
            payload=cast(Any, payload),
            payload_number=1,
            result=result,
            payload_timing=TimingData("test"),
            use_ssz_transport=use_ssz,
        )


@pytest.mark.parametrize("use_ssz", [True, False])
def test_missing_advertised_rest_method_fails(use_ssz: bool) -> None:
    """Do not skip a broken REST endpoint after capability discovery."""
    from unittest.mock import Mock

    from execution_testing.cli.pytest_commands.plugins.consume.simulators.simulator_logic.test_via_engine_witness import (  # noqa: E501
        _send_payload_with_witness,
    )
    from execution_testing.rpc.rpc_types import JSONRPCError

    error = JSONRPCError(-32601, "missing")
    client = Mock()
    client.new_payload_with_witness.side_effect = error
    payload = cast(
        Any, SimpleNamespace(params=[], error_code=None, new_payload_version=5)
    )
    if use_ssz:
        assert (
            _send_payload_with_witness(
                use_ssz_transport=True,
                engine_rpc=client,
                engine_ssz_rpc=client,
                payload=payload,
            )
            is error
        )
    else:
        with pytest.raises(pytest.skip.Exception, match="does not support"):
            _send_payload_with_witness(
                use_ssz_transport=False,
                engine_rpc=client,
                engine_ssz_rpc=client,
                payload=payload,
            )
