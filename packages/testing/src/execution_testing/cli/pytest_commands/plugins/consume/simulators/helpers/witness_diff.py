"""Set-based witness comparison helper for the engine-witness simulator."""

from typing import Iterable, List

from execution_testing.base_types import Bytes
from execution_testing.test_types.execution_witness import ExecutionWitness


def _diff_sets(
    field: str, expected: Iterable[Bytes], actual: Iterable[Bytes]
) -> List[str]:
    """Return human-readable diff messages for a single witness field."""
    exp = {bytes(x) for x in expected}
    act = {bytes(x) for x in actual}
    missing = exp - act
    extra = act - exp
    messages: List[str] = []
    if missing:
        preview = ", ".join(sorted("0x" + m.hex()[:16] for m in missing)[:5])
        messages.append(
            f"{field}: {len(missing)} missing (not emitted by client): {preview}"
        )
    if extra:
        preview = ", ".join(sorted("0x" + e.hex()[:16] for e in extra)[:5])
        messages.append(
            f"{field}: {len(extra)} extra (over-collected by client): {preview}"
        )
    return messages


class WitnessMismatchError(AssertionError):
    """Raised when a client-emitted witness does not match the fixture's."""


def assert_witness_matches(
    expected: ExecutionWitness, actual: ExecutionWitness
) -> None:
    """
    Assert the client-emitted `actual` witness matches the fixture `expected`
    witness under set-equality on each of `state`, `codes`, `headers`.

    Ordering is not mandated by execution-apis PR #773, so any permutation
    the client produces is acceptable. Duplicate items on either side are
    reduced to a single set element.
    """
    messages: List[str] = []
    messages += _diff_sets("state", expected.state, actual.state)
    messages += _diff_sets("codes", expected.codes, actual.codes)
    messages += _diff_sets("headers", expected.headers, actual.headers)

    if messages:
        raise WitnessMismatchError(
            "client witness does not match fixture witness:\n  "
            + "\n  ".join(messages)
        )
