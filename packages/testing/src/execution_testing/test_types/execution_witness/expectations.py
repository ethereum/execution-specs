"""
Execution witness expectation classes for test validation.

This module contains classes for defining and validating expected
execution witness state, codes, and headers in tests.
"""

from __future__ import annotations

from typing import Callable, List

import ethereum_rlp as eth_rlp
from pydantic import Field, PrivateAttr

from execution_testing.base_types import Bytes, CamelModel, Hash
from execution_testing.forks import Fork, Prague

from .exceptions import ExecutionWitnessValidationError
from .types import ExecutionWitness


class ExecutionWitnessCodesExpectation(CamelModel):
    """
    Execution witness codes expectation model for test writing.

    Define which bytecodes should or should not appear in
    executionWitness.codes.

    Ambient block-level codes (system contracts called every block)
    are automatically added to codes_present by the framework before
    verification. Tests only need to declare scenario-specific codes.

    Example:
        expected_execution_witness_codes = ExecutionWitnessCodesExpectation(
            codes_present=[Bytes(runtime_code)],
            codes_absent=[Bytes(created_code)],
        )

    """

    codes_present: List[Bytes] = Field(
        default_factory=list,
        description="Bytecodes that must be present in witness codes",
    )
    codes_absent: List[Bytes] = Field(
        default_factory=list,
        description=("Bytecodes that must NOT be present in witness codes"),
    )

    _modifier: Callable[["ExecutionWitness"], "ExecutionWitness"] | None = (
        PrivateAttr(default=None)
    )

    def modify(
        self,
        *modifiers: Callable[["ExecutionWitness"], "ExecutionWitness"],
    ) -> "ExecutionWitnessCodesExpectation":
        """
        Create a new expectation with a modifier for invalid test cases.

        Args:
            modifiers: One or more functions that take and return
                       an ExecutionWitness

        Returns:
            A new ExecutionWitnessCodesExpectation with modifiers applied

        """
        new_instance = self.model_copy(deep=True)
        new_instance._modifier = _compose(*modifiers)
        return new_instance

    def modify_if_invalid_test(
        self, t8n_witness: "ExecutionWitness"
    ) -> "ExecutionWitness":
        """
        Apply the modifier to the given witness if this is an invalid test.

        Args:
            t8n_witness: The ExecutionWitness from the t8n tool

        Returns:
            The potentially transformed ExecutionWitness for the fixture

        """
        if self._modifier:
            return self._modifier(t8n_witness)
        return t8n_witness

    def verify_against(self, actual_witness: "ExecutionWitness") -> None:
        """
        Verify that the actual witness codes match this expectation.

        Validation steps:
        1. Structural invariants: no duplicates and lexicographic
           ascending order
        2. Presence checks: codes_present entries exist
        3. Absence checks: codes_absent entries do not exist
        4. Exhaustiveness: no extra codes are allowed

        Args:
            actual_witness: The ExecutionWitness from the t8n tool

        Raises:
            ExecutionWitnessValidationError: If verification fails

        """
        actual_codes = actual_witness.codes

        # 1. Structural invariants (always checked)
        if len(actual_codes) != len(set(actual_codes)):
            seen: set[Bytes] = set()
            dupes: list[Bytes] = []
            for code in actual_codes:
                if code in seen:
                    dupes.append(code)
                seen.add(code)
            raise ExecutionWitnessValidationError(
                f"Witness codes contain duplicates: {[c.hex() for c in dupes]}"
            )

        if actual_codes != sorted(actual_codes):
            raise ExecutionWitnessValidationError(
                "Witness codes are not sorted in lexicographic ascending order"
            )

        actual_set = set(actual_codes)

        # 2. Presence checks
        for code in self.codes_present:
            if code not in actual_set:
                raise ExecutionWitnessValidationError(
                    f"Expected bytecode {code.hex()} not found "
                    f"in witness codes"
                )

        # 3. Absence checks
        for code in self.codes_absent:
            if code in actual_set:
                raise ExecutionWitnessValidationError(
                    f"Bytecode {code.hex()} should not be in "
                    f"witness codes but was found"
                )

        # 4. Exhaustiveness check
        expected_set = set(self.codes_present)
        unexpected = actual_set - expected_set
        if unexpected:
            raise ExecutionWitnessValidationError(
                f"Unexpected bytecodes in witness codes: "
                f"{[c.hex() for c in unexpected]}"
            )


class ExecutionWitnessStateExpectation(CamelModel):
    """
    Execution witness state expectation model for test writing.

    Define which encoded trie nodes should or should not appear in
    executionWitness.state.

    Example:
        expected_execution_witness_state = ExecutionWitnessStateExpectation(
            nodes_present=[Bytes(derived_node_rlp)],
        )

    """

    nodes_present: List[Bytes] = Field(
        default_factory=list,
        description="Encoded trie nodes that must be present in witness state",
    )
    nodes_absent: List[Bytes] = Field(
        default_factory=list,
        description=(
            "Encoded trie nodes that must NOT be present in witness state"
        ),
    )

    _modifier: Callable[["ExecutionWitness"], "ExecutionWitness"] | None = (
        PrivateAttr(default=None)
    )

    def modify(
        self,
        *modifiers: Callable[["ExecutionWitness"], "ExecutionWitness"],
    ) -> "ExecutionWitnessStateExpectation":
        """
        Create a new expectation with a modifier for invalid test cases.

        Args:
            modifiers: One or more functions that take and return
                       an ExecutionWitness

        Returns:
            A new ExecutionWitnessStateExpectation with modifiers applied

        """
        new_instance = self.model_copy(deep=True)
        new_instance._modifier = _compose(*modifiers)
        return new_instance

    def modify_if_invalid_test(
        self, t8n_witness: "ExecutionWitness"
    ) -> "ExecutionWitness":
        """
        Apply the modifier to the given witness if this is an invalid test.

        Args:
            t8n_witness: The ExecutionWitness from the t8n tool

        Returns:
            The potentially transformed ExecutionWitness for the fixture

        """
        if self._modifier:
            return self._modifier(t8n_witness)
        return t8n_witness

    def verify_against(self, actual_witness: "ExecutionWitness") -> None:
        """
        Verify that the actual witness state matches this expectation.

        Validation steps:
        1. Structural invariants: no duplicates and lexicographic
           ascending order
        2. Presence checks: nodes_present entries exist
        3. Absence checks: nodes_absent entries do not exist

        Args:
            actual_witness: The ExecutionWitness from the t8n tool

        Raises:
            ExecutionWitnessValidationError: If verification fails

        """
        actual_nodes = actual_witness.state

        if len(actual_nodes) != len(set(actual_nodes)):
            seen: set[Bytes] = set()
            dupes: list[Bytes] = []
            for node in actual_nodes:
                if node in seen:
                    dupes.append(node)
                seen.add(node)
            raise ExecutionWitnessValidationError(
                "Witness state contains duplicates: "
                f"{[n.hex() for n in dupes]}"
            )

        if actual_nodes != sorted(actual_nodes):
            raise ExecutionWitnessValidationError(
                "Witness state is not sorted in lexicographic ascending order"
            )

        actual_set = set(actual_nodes)

        for node in self.nodes_present:
            if node not in actual_set:
                raise ExecutionWitnessValidationError(
                    f"Expected trie node {node.hex()} not found "
                    f"in witness state"
                )

        for node in self.nodes_absent:
            if node in actual_set:
                raise ExecutionWitnessValidationError(
                    f"Trie node {node.hex()} should not be in "
                    f"witness state but was found"
                )


class ExecutionWitnessHeadersExpectation(CamelModel):
    """
    Execution witness headers expectation model for test writing.

    Define expected properties of executionWitness.headers.

    Example:
        expected_execution_witness_headers = (
            ExecutionWitnessHeadersExpectation(
                expected_count=5,
            )
        )

    """

    expected_count: int = Field(
        description="Exact number of RLP-encoded headers expected",
    )

    _modifier: Callable[["ExecutionWitness"], "ExecutionWitness"] | None = (
        PrivateAttr(default=None)
    )

    def modify(
        self,
        *modifiers: Callable[["ExecutionWitness"], "ExecutionWitness"],
    ) -> "ExecutionWitnessHeadersExpectation":
        """
        Create a new expectation with a modifier for invalid test cases.

        Args:
            modifiers: One or more functions that take and return
                       an ExecutionWitness

        Returns:
            A new ExecutionWitnessHeadersExpectation with modifiers
            applied

        """
        new_instance = self.model_copy(deep=True)
        new_instance._modifier = _compose(*modifiers)
        return new_instance

    def modify_if_invalid_test(
        self, t8n_witness: "ExecutionWitness"
    ) -> "ExecutionWitness":
        """
        Apply the modifier to the given witness if this is an invalid test.

        Args:
            t8n_witness: The ExecutionWitness from the t8n tool

        Returns:
            The potentially transformed ExecutionWitness for the fixture

        """
        if self._modifier:
            return self._modifier(t8n_witness)
        return t8n_witness

    def verify_against(
        self,
        actual_witness: ExecutionWitness,
        parent_hash: Hash,
        fork: Fork,
    ) -> None:
        """
        Verify header count and structural invariants.

        Validation steps:
        1. Count matches expected_count
        2. No more than 256 headers
        3. Sorted ascending by block number (Prague+)
        4. Contiguous: keccak256(headers[i]) == parent_hash of
           headers[i+1] (Prague+)
        5. Last header is the current block's parent:
           keccak256(headers[-1]) == parent_hash (Prague+)

        Steps 3-5 require RLP decoding and are only performed for
        Prague and newer forks where EIP-2935 guarantees at least
        one ancestor header (the parent) is always tracked.

        Args:
            actual_witness: The ExecutionWitness from the t8n tool
            parent_hash: The parent hash of the current block
            fork: The fork under test

        Raises:
            ExecutionWitnessValidationError: If verification fails

        """
        actual_headers = actual_witness.headers

        # 1. Count check
        if len(actual_headers) != self.expected_count:
            raise ExecutionWitnessValidationError(
                f"Expected {self.expected_count} witness headers, "
                f"got {len(actual_headers)}"
            )

        # 2. Max 256 headers
        if len(actual_headers) > 256:
            raise ExecutionWitnessValidationError(
                f"Witness headers exceed maximum of 256: "
                f"got {len(actual_headers)}"
            )

        # Since Prague we have EIP-2935 which requires the parent
        # block's header to be included.
        if len(actual_headers) == 0 or fork < Prague:
            return

        # Decode all headers to extract block numbers and parent
        # hashes for structural checks.
        decoded = []
        for rlp_header in actual_headers:
            fields: list[bytes] = eth_rlp.decode(rlp_header)  # type: ignore[assignment]
            header_parent_hash = Hash(fields[0])
            block_number = int.from_bytes(fields[8], "big")
            header_hash = rlp_header.keccak256()
            decoded.append((block_number, header_parent_hash, header_hash))

        # 3. Sorted ascending by block number
        block_numbers = [d[0] for d in decoded]
        if block_numbers != sorted(block_numbers):
            raise ExecutionWitnessValidationError(
                "Witness headers are not sorted in ascending "
                f"block number order: {block_numbers}"
            )

        # 4. Contiguous: keccak256(headers[i]) == parent_hash of
        #    headers[i+1]
        for i in range(len(decoded) - 1):
            _, _, current_hash = decoded[i]
            _, next_parent_hash, _ = decoded[i + 1]
            if current_hash != next_parent_hash:
                raise ExecutionWitnessValidationError(
                    f"Witness headers not contiguous at index "
                    f"{i}: hash {current_hash.hex()} != "
                    f"parent_hash {next_parent_hash.hex()} of "
                    f"header {i + 1}"
                )

        # 5. Last header is the current block's parent
        _, _, last_hash = decoded[-1]
        if last_hash != parent_hash:
            raise ExecutionWitnessValidationError(
                f"Last witness header hash "
                f"{last_hash.hex()} != current block "
                f"parent_hash {parent_hash.hex()}"
            )


def _compose(
    *modifiers: Callable[["ExecutionWitness"], "ExecutionWitness"],
) -> Callable[["ExecutionWitness"], "ExecutionWitness"]:
    """Compose multiple modifiers into a single modifier."""

    def composed(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        result = witness
        for modifier in modifiers:
            result = modifier(result)
        return result

    return composed


__all__ = [
    "ExecutionWitnessCodesExpectation",
    "ExecutionWitnessHeadersExpectation",
    "ExecutionWitnessStateExpectation",
]
