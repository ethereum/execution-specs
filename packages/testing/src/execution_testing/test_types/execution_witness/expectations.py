"""
Execution witness codes expectation classes for test validation.

This module contains classes for defining and validating expected
execution witness codes in tests.
"""

from typing import Callable, List

from pydantic import Field, PrivateAttr

from execution_testing.base_types import Bytes, CamelModel

from .exceptions import ExecutionWitnessValidationError
from .types import ExecutionWitness


class ExecutionWitnessCodesExpectation(CamelModel):
    """
    Execution witness codes expectation model for test writing.

    Define which bytecodes should or should not appear in
    executionWitness.codes.

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
    allow_unexpected: bool = Field(
        default=True,
        description=(
            "If False, fail when witness codes contains bytecodes "
            "not listed in codes_present"
        ),
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
        1. Structural invariants: no duplicates and sorted order
        2. Presence checks: codes_present entries exist
        3. Absence checks: codes_absent entries do not exist
        4. Exhaustiveness: if allow_unexpected=False, no extra codes

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
                "Witness codes are not sorted in lexicographic order"
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
        if not self.allow_unexpected:
            expected_set = set(self.codes_present)
            unexpected = actual_set - expected_set
            if unexpected:
                raise ExecutionWitnessValidationError(
                    f"Unexpected bytecodes in witness codes: "
                    f"{[c.hex() for c in unexpected]}"
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
]
