"""Stateless helpers for blockchain test generation."""

from dataclasses import dataclass, replace
from typing import Any, Callable, List, Protocol

from execution_testing.base_types import (
    Bytes,
    Hash,
    ZeroPaddedHexNumber,
)
from execution_testing.client_clis import LazyAlloc, Result
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import Fork
from execution_testing.test_types import (
    Alloc,
    Environment,
    ExecutionWitness,
    Transaction,
    Withdrawal,
)
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


@dataclass(frozen=True)
class StatelessBlockOptions:
    """Stateless options derived before transition-tool execution."""

    skip_validation: bool
    witness_modifiers: tuple[
        Callable[[ExecutionWitness], ExecutionWitness], ...
    ]
    stateless_input_bytes_modifier: Callable[[Bytes], Bytes] | None
    expected_validation_success: bool | None

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
        expectation._modifier
        for expectation in (
            block.expected_execution_witness_state,
            block.expected_execution_witness_codes,
            block.expected_execution_witness_headers,
        )
        if expectation is not None and expectation._modifier is not None
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

    return StatelessBlockOptions(
        skip_validation=skip_stateless_validation or omit_stateless_artifacts,
        witness_modifiers=witness_modifiers,
        stateless_input_bytes_modifier=stateless_input_bytes_modifier,
        expected_validation_success=expected_success,
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


def finalize_stateless_artifacts(
    *,
    options: StatelessBlockOptions,
    original: StatelessValidationArtifacts,
    fork: Fork,
    block_number: int,
    timestamp: int,
    chain_id: int,
) -> StatelessValidationArtifacts:
    """Reuse original artifacts or execute modified input, then verify."""
    active_fork = fork.fork_at(block_number=block_number, timestamp=timestamp)
    if original.stateless_output_bytes is None:
        if options.expected_validation_success is not None:
            raise Exception(
                "Stateless guest verification requires stateless output bytes"
            )
        return original
    if active_fork.name() != "Amsterdam":
        if options.expected_validation_success is not None:
            raise Exception(
                "Stateless output decoding is only supported for Amsterdam"
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
    from ethereum.forks.amsterdam.stateless_guest import run_stateless_guest
    from ethereum_types.bytes import Bytes as AmsterdamBytes

    return StatelessValidationArtifacts(
        execution_witness=execution_witness,
        stateless_input_bytes=stateless_input_bytes,
        stateless_output_bytes=Bytes(
            run_stateless_guest(AmsterdamBytes(stateless_input_bytes))
        ),
    )


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


def _decode_amsterdam_header_bytes(header_rlp: Bytes) -> Any | None:
    """
    Decode an Amsterdam or immediate pre-Amsterdam RLP header.
    """
    from ethereum.forks.amsterdam.stateless import _decode_header
    from ethereum_types.bytes import Bytes as AmsterdamBytes

    try:
        return _decode_header(AmsterdamBytes(bytes(header_rlp)))
    except Exception:
        return None


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


def _convert_amsterdam_withdrawals(
    withdrawals: List[Withdrawal] | None,
) -> Any:
    """
    Convert fixture withdrawals to Amsterdam fork withdrawals.
    """
    from ethereum.forks.amsterdam.blocks import (
        Withdrawal as AmsterdamWithdrawal,
    )
    from ethereum.state import Address as AmsterdamAddress
    from ethereum_types.numeric import U64

    if withdrawals is None:
        return ()
    return tuple(
        AmsterdamWithdrawal(
            index=U64(int(withdrawal.index)),
            validator_index=U64(int(withdrawal.validator_index)),
            address=AmsterdamAddress(bytes(withdrawal.address)),
            amount=U64(int(withdrawal.amount)),
        )
        for withdrawal in withdrawals
    )


def _convert_amsterdam_block_access_list(
    block_access_list: BlockAccessList,
) -> Any:
    """
    Convert fixture BAL data to Amsterdam fork BAL data.
    """
    import importlib

    block_access_lists = importlib.import_module(
        "ethereum.forks.amsterdam.block_access_lists"
    )

    def bal_type(name: str) -> Any:
        return getattr(block_access_lists, name)

    account_changes = bal_type("AccountChanges")
    balance_change = bal_type("BalanceChange")
    code_change = bal_type("CodeChange")
    nonce_change = bal_type("NonceChange")
    slot_changes = bal_type("SlotChanges")
    storage_change = bal_type("StorageChange")

    from ethereum.state import Address as AmsterdamAddress
    from ethereum_types.bytes import Bytes as AmsterdamBytes
    from ethereum_types.numeric import U32, U64, U256

    return [
        account_changes(
            address=AmsterdamAddress(bytes(account.address)),
            storage_changes=tuple(
                slot_changes(
                    slot=U256(int(slot.slot)),
                    changes=tuple(
                        storage_change(
                            block_access_index=U32(
                                int(change.block_access_index)
                            ),
                            new_value=U256(int(change.post_value)),
                        )
                        for change in slot.slot_changes
                    ),
                )
                for slot in account.storage_changes
            ),
            storage_reads=tuple(
                U256(int(slot)) for slot in account.storage_reads
            ),
            balance_changes=tuple(
                balance_change(
                    block_access_index=U32(int(change.block_access_index)),
                    post_balance=U256(int(change.post_balance)),
                )
                for change in account.balance_changes
            ),
            nonce_changes=tuple(
                nonce_change(
                    block_access_index=U32(int(change.block_access_index)),
                    new_nonce=U64(int(change.post_nonce)),
                )
                for change in account.nonce_changes
            ),
            code_changes=tuple(
                code_change(
                    block_access_index=U32(int(change.block_access_index)),
                    new_code=AmsterdamBytes(bytes(change.new_code)),
                )
                for change in account.code_changes
            ),
        )
        for account in block_access_list.root
    ]


def build_amsterdam_stateless_artifacts_from_t8n(
    *,
    fork: Fork,
    block_number: int,
    timestamp: int,
    header: FixtureHeader,
    previous_env: Environment,
    txs: List[Transaction],
    result: Result,
    withdrawals: List[Withdrawal] | None,
    requests_list: List[Bytes] | None,
    execution_witness: ExecutionWitness,
    block_access_list: BlockAccessList,
    chain_id: int,
) -> tuple[Bytes, Bytes] | None:
    """
    Build Amsterdam stateless input/output bytes from t8n witness artifacts.

    Returns ``None`` when the finalized request list cannot be decoded into
    the Amsterdam request container, matching the existing EELS t8n behavior.
    """
    active_fork = fork.fork_at(block_number=block_number, timestamp=timestamp)
    if active_fork.name() != "Amsterdam" or block_number == 0:
        return None

    from ethereum.forks.amsterdam.blocks import (
        Block as AmsterdamBlock,
    )
    from ethereum.forks.amsterdam.blocks import (
        Header as AmsterdamHeader,
    )
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
        serialize_stateless_input,
    )
    from ethereum_types.bytes import Bytes as AmsterdamBytes
    from ethereum_types.numeric import U16, U64

    parent_number = ZeroPaddedHexNumber(block_number - 1)
    parent_header_rlp = previous_env.block_headers.get(parent_number)
    if parent_header_rlp is None:
        return None
    parent_header = _decode_amsterdam_header_bytes(parent_header_rlp)
    if parent_header is None:
        return None
    if Hash(parent_header_rlp.keccak256()) != header.parent_hash:
        return None

    current_header = _decode_amsterdam_header_bytes(header.rlp)
    if not isinstance(current_header, AmsterdamHeader):
        return None

    try:
        execution_requests = decode_execution_requests(
            tuple(
                AmsterdamBytes(bytes(request))
                for request in requests_list or []
            )
        )
    except Exception:
        return None

    rejected_indices = {
        int(rejected.index) for rejected in result.rejected_transactions
    }
    accepted_txs = tuple(
        AmsterdamBytes(bytes(tx.rlp()))
        for index, tx in enumerate(txs)
        if index not in rejected_indices
    )
    block = AmsterdamBlock(
        header=current_header,
        transactions=accepted_txs,
        ommers=(),
        withdrawals=_convert_amsterdam_withdrawals(withdrawals),
    )
    stateless_input = build_stateless_input(
        block,
        execution_witness=_convert_amsterdam_execution_witness(
            execution_witness
        ),
        execution_requests=execution_requests,
        block_access_list=_convert_amsterdam_block_access_list(
            block_access_list
        ),
        chain_id=U64(chain_id),
    )
    stateless_input_bytes = serialize_stateless_input(stateless_input)
    # Temporary trust path for external benchmark filling until Geth emits
    # both stateless byte fields.
    stateless_output = StatelessValidationResult(
        new_payload_request_root=compute_new_payload_request_root(
            stateless_input
        ),
        successful_validation=True,
        chain_id=U64(chain_id),
        schema_id=U16(STATELESS_INPUT_SCHEMA_ID),
    )
    stateless_output_bytes = serialize_stateless_output(stateless_output)
    return (
        Bytes(bytes(stateless_input_bytes)),
        Bytes(bytes(stateless_output_bytes)),
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
) -> None:
    """
    Verify the public values returned by the Amsterdam stateless guest.
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
        if input_bytes_modified and is_invalid_input_stateless_output(
            stateless_output
        ):
            return
        raise AssertionError(
            "Stateless input decoding failed for block "
            f"{block_number}, but its output is not the invalid-input sentinel"
        ) from exc

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
