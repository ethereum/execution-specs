"""Stateless helpers for blockchain test generation."""

from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, List, Protocol

from execution_testing.base_types import Bytes, Hash
from execution_testing.client_clis import LazyAlloc
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayloadModifier,
)
from execution_testing.forks import Fork
from execution_testing.test_types import Alloc, ExecutionWitness, Removable
from execution_testing.test_types.block_access_list import BlockAccessList
from execution_testing.test_types.execution_witness import (
    ExecutionWitnessCodesExpectation,
    ExecutionWitnessHeadersExpectation,
    ExecutionWitnessStateExpectation,
)


class StatelessBlockProtocol(Protocol):
    """Block fields needed by stateless validation orchestration."""

    @property
    def rlp_modifier(self) -> object | None:
        """RLP modifier configured for the block."""
        ...

    @property
    def expected_execution_witness_codes(
        self,
    ) -> ExecutionWitnessCodesExpectation | None:
        """Expected execution witness codes."""
        ...

    @property
    def expected_execution_witness_state(
        self,
    ) -> ExecutionWitnessStateExpectation | None:
        """Expected execution witness state."""
        ...

    @property
    def expected_execution_witness_headers(
        self,
    ) -> ExecutionWitnessHeadersExpectation | None:
        """Expected execution witness headers."""
        ...

    @property
    def stateless_input_bytes_modifier(
        self,
    ) -> Callable[[Bytes], Bytes] | None:
        """Serialized stateless input modifier for raw-input reruns."""
        ...

    @property
    def expected_stateless_validation_success(self) -> bool | None:
        """Expected stateless guest validation result."""
        ...

    @property
    def expected_stateless_input_decode_failure(self) -> bool:
        """Whether the mutated stateless input bytes must fail to decode."""
        ...


@dataclass(frozen=True)
class StatelessBlockOptions:
    """Stateless options derived before transition-tool execution."""

    skip_validation: bool
    witness_modifiers: tuple[
        Callable[[ExecutionWitness], ExecutionWitness], ...
    ]
    stateless_input_bytes_modifier: Callable[[Bytes], Bytes] | None
    expected_validation_success: bool | None
    expected_input_decode_failure: bool

    @property
    def has_witness_modifier(self) -> bool:
        """Return whether the test requests witness mutation."""
        return bool(self.witness_modifiers)

    @property
    def has_stateless_input_bytes_modifier(self) -> bool:
        """Whether raw stateless input bytes should be mutated."""
        return self.stateless_input_bytes_modifier is not None


@dataclass(frozen=True)
class StatelessValidationArtifacts:
    """Keep a fixture witness with its serialized guest input and output."""

    execution_witness: ExecutionWitness | None
    stateless_input_bytes: Bytes | None = None
    stateless_output_bytes: Bytes | None = None


def stateless_options_for_block(
    *,
    block: StatelessBlockProtocol,
    skip_stateless_validation: bool,
) -> StatelessBlockOptions:
    """Derive stateless options and reject incompatible block settings."""
    has_witness_expectation = (
        block.expected_execution_witness_state is not None
        or block.expected_execution_witness_codes is not None
        or block.expected_execution_witness_headers is not None
    )
    stateless_input_bytes_modifier = block.stateless_input_bytes_modifier
    has_stateless_input_bytes_modifier = (
        stateless_input_bytes_modifier is not None
    )
    expected_success = block.expected_stateless_validation_success
    omit_stateless_artifacts = block.rlp_modifier is not None

    if omit_stateless_artifacts and (
        has_witness_expectation
        or has_stateless_input_bytes_modifier
        or expected_success is not None
    ):
        raise AssertionError(
            "Blocks with rlp_modifier omit stateless artifacts because "
            "they are generated before the RLP mutation. SSZ/stateless "
            "mutation tests require a separate explicit mechanism."
        )
    if skip_stateless_validation and (
        has_witness_expectation
        or has_stateless_input_bytes_modifier
        or expected_success is not None
    ):
        raise AssertionError(
            "skip_stateless_validation cannot be combined with "
            "execution witness expectations, stateless input byte "
            "modifiers, or "
            "expected_stateless_validation_success"
        )

    witness_modifiers = tuple(
        expectation.modifier
        for expectation in (
            block.expected_execution_witness_state,
            block.expected_execution_witness_codes,
            block.expected_execution_witness_headers,
        )
        if expectation is not None and expectation.modifier is not None
    )
    if witness_modifiers and expected_success is None:
        raise AssertionError(
            "Mutated execution witness tests must set "
            "expected_stateless_validation_success explicitly"
        )
    if has_stateless_input_bytes_modifier and expected_success is None:
        raise AssertionError(
            "Mutated stateless input byte tests must set "
            "expected_stateless_validation_success explicitly"
        )
    expected_decode_failure = block.expected_stateless_input_decode_failure
    if expected_decode_failure and not has_stateless_input_bytes_modifier:
        raise AssertionError(
            "expected_stateless_input_decode_failure requires "
            "stateless_input_bytes_modifier"
        )

    return StatelessBlockOptions(
        skip_validation=skip_stateless_validation or omit_stateless_artifacts,
        witness_modifiers=witness_modifiers,
        stateless_input_bytes_modifier=stateless_input_bytes_modifier,
        expected_validation_success=expected_success,
        expected_input_decode_failure=expected_decode_failure,
    )


def verify_execution_witness_expectations(
    *,
    block: StatelessBlockProtocol,
    fork: Fork,
    previous_alloc: Alloc | LazyAlloc,
    block_number: int,
    timestamp: int,
    parent_hash: Hash,
    execution_witness: ExecutionWitness | None,
) -> None:
    """Check expectations against the original, unmodified witness."""
    if execution_witness is None:
        return

    state_expectation = block.expected_execution_witness_state
    if state_expectation is not None:
        state_expectation.verify_against(execution_witness)

    codes_expectation = block.expected_execution_witness_codes
    if codes_expectation is not None:
        effective_codes_expectation = with_execution_witness_implicit_codes(
            expectation=codes_expectation,
            fork=fork,
            alloc=previous_alloc,
            block_number=block_number,
            timestamp=timestamp,
        )
        effective_codes_expectation.verify_against(execution_witness)

    headers_expectation = block.expected_execution_witness_headers
    if headers_expectation is not None:
        headers_expectation.verify_against(
            execution_witness,
            parent_hash=parent_hash,
            fork=fork,
        )


def build_stateless_artifacts(
    *,
    options: StatelessBlockOptions,
    fork: Fork,
    execution_witness: ExecutionWitness | None,
    block_rlp: Bytes,
    block_access_list: BlockAccessList | None,
    requests_list: List[Bytes] | None,
    engine_payload_modifier: FixtureExecutionPayloadModifier | None,
    chain_id: int,
    block_valid: bool,
    run_guest: bool,
) -> StatelessValidationArtifacts:
    """
    Build the stateless guest input and output for the final fixture block.

    The input describes the engine payload that the block sends. The
    fixture block RLP, block access list and requests supply every field
    that ``engine_payload_modifier`` doesn't override, so the input
    includes any change the filler makes after the transition tool runs.
    Without ``run_guest`` the output trusts the transition tool instead of
    re-executing the block.

    Omit the input and output when the requests cannot be expressed as
    Amsterdam types, or when the engine payload leaves out a field, which
    the SSZ payload cannot express.
    """
    artifacts = StatelessValidationArtifacts(
        execution_witness=execution_witness
    )
    payload_modifier = (
        engine_payload_modifier or FixtureExecutionPayloadModifier()
    )
    if (
        options.skip_validation
        or execution_witness is None
        or fork.name() != "Amsterdam"
        or isinstance(payload_modifier.block_access_list, Removable)
        or isinstance(payload_modifier.slot_number, Removable)
    ):
        return artifacts
    assert block_access_list is not None

    from ethereum.forks.amsterdam.block_access_lists import (
        BlockAccessList as AmsterdamBlockAccessList,
    )
    from ethereum.forks.amsterdam.blocks import Block as AmsterdamBlock
    from ethereum.forks.amsterdam.execution_engine.requests import (
        decode_execution_requests,
    )
    from ethereum.forks.amsterdam.stateless import (
        STATELESS_INPUT_SCHEMA_ID,
        StatelessValidationResult,
        compute_new_payload_request_root,
    )
    from ethereum.forks.amsterdam.stateless_guest import (
        serialize_stateless_output,
    )
    from ethereum.forks.amsterdam.stateless_host import (
        build_stateless_input,
        deserialize_stateless_output,
        serialize_stateless_input,
    )
    from ethereum_rlp import rlp
    from ethereum_types.numeric import U16, U64

    try:
        execution_requests = decode_execution_requests(
            tuple(requests_list or ())
        )
    except Exception:
        # Mocked system contracts can produce requests that the typed
        # stateless input cannot hold.
        return artifacts
    try:
        amsterdam_block_access_list = rlp.decode_to(
            AmsterdamBlockAccessList, block_access_list.rlp
        )
    except Exception:
        # A re-encoded list need not decode. The payload bytes replace its
        # encoding below, so an empty list stands in for it.
        amsterdam_block_access_list = []

    stateless_input = build_stateless_input(
        rlp.decode_to(AmsterdamBlock, block_rlp),
        execution_witness=_convert_amsterdam_execution_witness(
            execution_witness
        ),
        execution_requests=execution_requests,
        block_access_list=amsterdam_block_access_list,
        chain_id=U64(chain_id),
    )
    execution_payload = replace(
        stateless_input.new_payload_request.execution_payload,
        block_access_list=(
            block_access_list.rlp
            if payload_modifier.block_access_list is None
            else payload_modifier.block_access_list
        ),
    )
    if payload_modifier.slot_number is not None:
        execution_payload = replace(
            execution_payload, slot_number=U64(payload_modifier.slot_number)
        )
    stateless_input = replace(
        stateless_input,
        new_payload_request=replace(
            stateless_input.new_payload_request,
            execution_payload=execution_payload,
        ),
    )
    input_bytes = Bytes(serialize_stateless_input(stateless_input))
    if run_guest:
        output_bytes = _run_stateless_guest(input_bytes)
    else:
        # Benchmark blocks are too slow to re-execute in the guest, so trust
        # the external transition tool and report the block as valid.
        output_bytes = Bytes(
            serialize_stateless_output(
                StatelessValidationResult(
                    new_payload_request_root=compute_new_payload_request_root(
                        stateless_input
                    ),
                    successful_validation=True,
                    chain_id=U64(chain_id),
                    schema_id=U16(STATELESS_INPUT_SCHEMA_ID),
                )
            )
        )

    output = deserialize_stateless_output(output_bytes)
    if output.successful_validation != block_valid:
        raise AssertionError(
            "Stateless validation of the unmodified block input returned "
            f"{output.successful_validation}, but the block is expected to "
            f"be {'valid' if block_valid else 'invalid'}"
        )
    return replace(
        artifacts,
        stateless_input_bytes=input_bytes,
        stateless_output_bytes=output_bytes,
    )


def finalize_stateless_artifacts(
    *,
    options: StatelessBlockOptions,
    original: StatelessValidationArtifacts,
    block_number: int,
    chain_id: int,
) -> StatelessValidationArtifacts:
    """Reuse original artifacts or execute modified input, then verify."""
    if original.stateless_output_bytes is None:
        if options.expected_validation_success is not None:
            raise Exception(
                "Stateless guest verification requires stateless output bytes"
            )
        return original

    final_artifacts = original
    if (
        options.has_witness_modifier
        or options.has_stateless_input_bytes_modifier
    ):
        witness, input_bytes = prepare_modified_stateless_input(
            original=original, options=options
        )
        final_artifacts = execute_stateless_guest(
            execution_witness=witness, stateless_input_bytes=input_bytes
        )

    verify_stateless_result(
        artifacts=final_artifacts,
        options=options,
        block_number=block_number,
        chain_id=chain_id,
    )
    return final_artifacts


def prepare_modified_stateless_input(
    *,
    original: StatelessValidationArtifacts,
    options: StatelessBlockOptions,
) -> tuple[ExecutionWitness | None, Bytes]:
    """Apply witness modifiers to a copy, then apply the raw-byte modifier."""
    from ethereum.forks.amsterdam.stateless_guest import (
        deserialize_stateless_input,
    )
    from ethereum.forks.amsterdam.stateless_host import (
        serialize_stateless_input,
    )
    from ethereum_types.bytes import Bytes as AmsterdamBytes

    input_bytes = original.stateless_input_bytes
    if input_bytes is None:
        raise Exception("Stateless guest rerun requires stateless input bytes")

    witness = original.execution_witness
    if options.has_witness_modifier:
        if witness is None:
            raise Exception(
                "Stateless guest witness mutation rerun requires "
                "execution witness"
            )
        witness = witness.model_copy(deep=True)
        for modifier in options.witness_modifiers:
            witness = modifier(witness)
        stateless_input = deserialize_stateless_input(
            AmsterdamBytes(input_bytes)
        )
        stateless_input = replace(
            stateless_input,
            witness=_convert_amsterdam_execution_witness(witness),
        )
        input_bytes = Bytes(serialize_stateless_input(stateless_input))

    if options.stateless_input_bytes_modifier is not None:
        input_bytes = options.stateless_input_bytes_modifier(input_bytes)
    return witness, input_bytes


def execute_stateless_guest(
    *,
    execution_witness: ExecutionWitness | None,
    stateless_input_bytes: Bytes,
) -> StatelessValidationArtifacts:
    """Execute the final input bytes and pair them with the guest output."""
    return StatelessValidationArtifacts(
        execution_witness=execution_witness,
        stateless_input_bytes=stateless_input_bytes,
        stateless_output_bytes=_run_stateless_guest(stateless_input_bytes),
    )


_stateless_guest_outputs: Dict[Hash, Bytes] = {}
"""Stateless guest output bytes, keyed by the hash of their input bytes."""


def _run_stateless_guest(stateless_input_bytes: Bytes) -> Bytes:
    """
    Run the stateless guest on serialized input bytes.

    Every fixture format of a test builds the same blocks, so reuse the
    output for an input that already ran.
    """
    from ethereum.forks.amsterdam.stateless_guest import run_stateless_guest
    from ethereum.trace import discard_evm_trace, set_evm_trace

    key = Hash(stateless_input_bytes.keccak256())
    if key not in _stateless_guest_outputs:
        # The transition tool leaves its tracers installed. The replay must
        # not add to their opcode counts or overwrite their traces.
        previous_tracer = set_evm_trace(discard_evm_trace)
        try:
            _stateless_guest_outputs[key] = Bytes(
                run_stateless_guest(stateless_input_bytes)
            )
        finally:
            set_evm_trace(previous_tracer)
    return _stateless_guest_outputs[key]


def verify_stateless_result(
    *,
    artifacts: StatelessValidationArtifacts,
    options: StatelessBlockOptions,
    block_number: int,
    chain_id: int,
) -> None:
    """Check the guest's validation result and its public output values."""
    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum_types.bytes import Bytes as AmsterdamBytes

    assert artifacts.stateless_output_bytes is not None
    output = deserialize_stateless_output(
        AmsterdamBytes(artifacts.stateless_output_bytes)
    )
    if (
        options.expected_validation_success is not None
        and output.successful_validation != options.expected_validation_success
    ):
        raise AssertionError(
            "Stateless guest validation result mismatch: "
            f"got {output.successful_validation}, "
            f"want {options.expected_validation_success}"
        )
    if artifacts.stateless_input_bytes is None:
        raise Exception(
            "Stateless output verification requires stateless input bytes"
        )
    verify_amsterdam_stateless_output(
        block_number=block_number,
        chain_id=chain_id,
        stateless_input_bytes=artifacts.stateless_input_bytes,
        stateless_output=output,
        input_bytes_modified=options.has_stateless_input_bytes_modifier,
        expected_decode_failure=options.expected_input_decode_failure,
    )


def execution_witness_implicit_codes_for_block(
    *,
    fork: Fork,
    alloc: Alloc | LazyAlloc,
    block_number: int,
    timestamp: int,
) -> List[Bytes]:
    """
    Return ambient witness bytecodes implied by block-level execution.

    These codes are resolved from the effective pre-state for the block, not
    from raw fork defaults, so test `pre` overrides are respected.
    """
    active_fork = fork.fork_at(block_number=block_number, timestamp=timestamp)
    addresses = active_fork.execution_witness_implicit_code_addresses(
        block_number=block_number,
        timestamp=timestamp,
    )
    if not addresses:
        return []

    effective_alloc = (
        alloc.materialize() if isinstance(alloc, LazyAlloc) else alloc
    )

    codes: List[Bytes] = []
    seen: set[Bytes] = set()
    for address in addresses:
        if address not in effective_alloc:
            continue
        account = effective_alloc[address]
        if account is None or len(account.code) == 0:
            continue
        code = Bytes(account.code)
        if code in seen:
            continue
        codes.append(code)
        seen.add(code)
    return codes


def with_execution_witness_implicit_codes(
    *,
    expectation: ExecutionWitnessCodesExpectation,
    fork: Fork,
    alloc: Alloc | LazyAlloc,
    block_number: int,
    timestamp: int,
) -> ExecutionWitnessCodesExpectation:
    """Return expectation copy with ambient block-level codes added."""
    codes_present = list(expectation.codes_present)
    seen = set(codes_present)

    for code in execution_witness_implicit_codes_for_block(
        fork=fork,
        alloc=alloc,
        block_number=block_number,
        timestamp=timestamp,
    ):
        if code in seen:
            continue
        codes_present.append(code)
        seen.add(code)

    return expectation.model_copy(update={"codes_present": codes_present})


def _convert_amsterdam_execution_witness(
    execution_witness: ExecutionWitness,
) -> Any:
    """
    Convert fixture execution witness data to Amsterdam fork types.
    """
    from ethereum.forks.amsterdam.stateless import (
        ExecutionWitness as AmsterdamExecutionWitness,
    )
    from ethereum_types.bytes import Bytes as AmsterdamBytes

    return AmsterdamExecutionWitness(
        state=tuple(
            AmsterdamBytes(bytes(node)) for node in execution_witness.state
        ),
        codes=tuple(
            AmsterdamBytes(bytes(code)) for code in execution_witness.codes
        ),
        headers=tuple(
            AmsterdamBytes(bytes(header))
            for header in execution_witness.headers
        ),
    )


def is_invalid_input_stateless_output(stateless_output: Any) -> bool:
    """
    Return whether output is the invalid stateless input sentinel.
    """
    from ethereum_types.numeric import U16, U64

    return (
        not stateless_output.successful_validation
        and bytes(stateless_output.new_payload_request_root) == b"\0" * 32
        and stateless_output.chain_id == U64(0)
        and stateless_output.schema_id == U16(0)
    )


def verify_amsterdam_stateless_output(
    *,
    block_number: int,
    chain_id: int,
    stateless_input_bytes: Bytes,
    stateless_output: Any,
    input_bytes_modified: bool,
    expected_decode_failure: bool,
) -> None:
    """
    Verify the public values returned by the Amsterdam stateless guest.

    The input must fail to decode exactly when ``expected_decode_failure`` is
    set, so a mutation cannot silently move to a different validation stage.
    """
    from ethereum.forks.amsterdam.stateless import (
        STATELESS_INPUT_SCHEMA_ID,
        compute_new_payload_request_root,
    )
    from ethereum.forks.amsterdam.stateless_guest import (
        deserialize_stateless_input,
    )
    from ethereum_types.bytes import Bytes as AmsterdamBytes

    try:
        stateless_input = deserialize_stateless_input(
            AmsterdamBytes(bytes(stateless_input_bytes))
        )
    except Exception as exc:
        if not expected_decode_failure:
            raise AssertionError(
                f"Stateless input decoding failed for block {block_number}, "
                "but expected_stateless_input_decode_failure is not set"
            ) from exc
        if not is_invalid_input_stateless_output(stateless_output):
            raise AssertionError(
                "Stateless input decoding failed for block "
                f"{block_number}, but its output is not the invalid-input "
                "sentinel"
            ) from exc
        return
    if expected_decode_failure:
        raise AssertionError(
            f"Stateless input for block {block_number} decodes, but "
            "expected_stateless_input_decode_failure is set"
        )

    expected_root = compute_new_payload_request_root(stateless_input)
    actual_root = stateless_output.new_payload_request_root
    if actual_root != expected_root:
        raise AssertionError(
            "Stateless output new_payload_request_root mismatch for block "
            f"{block_number}: got 0x{bytes(actual_root).hex()}, "
            f"want 0x{bytes(expected_root).hex()}"
        )

    if stateless_output.schema_id != STATELESS_INPUT_SCHEMA_ID:
        raise AssertionError(
            "Stateless output schema_id mismatch for block "
            f"{block_number}: got {stateless_output.schema_id}, "
            f"want {STATELESS_INPUT_SCHEMA_ID}"
        )

    expected_chain_id = (
        stateless_input.chain_id if input_bytes_modified else chain_id
    )
    if stateless_output.chain_id != expected_chain_id:
        raise AssertionError(
            "Stateless output chain_id mismatch for block "
            f"{block_number}: got {stateless_output.chain_id}, "
            f"want {expected_chain_id}"
        )
