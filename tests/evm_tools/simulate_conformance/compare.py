"""
Walk a client's answer against the specification's, field by field.

The comparison is exact on everything except one exclusion, which is
taken from the existing RPC design rather than invented here:
`error.message` is not compared, because execution-apis states that the
messages are suggestions and only the codes are enforced — the same
position hive's `rpc-compat` reached when it started stripping the
messages before comparing.

Every other field counts, including the state root and the block hash,
which is what makes this a stronger assertion than any recorded corpus
makes: those two can only agree if both sides synthesized the very same
transactions and executed them to the very same state.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

IGNORED_PATHS = ("error.message",)
"""
Suffixes of paths that carry prose rather than data.

Matched as a suffix so the index a path picks up on the way down —
`[0].calls[1].error.message` — does not have to be enumerated.
"""


@dataclass
class Difference:
    """One place two answers disagree."""

    path: str
    ours: Any
    theirs: Any

    def __str__(self) -> str:
        """Render the disagreement on one line, elided if it is long."""

        def short(value: Any) -> str:
            text = repr(value)
            if len(text) <= 160:
                return text
            return f"{text[:157]}..."

        return (
            f"{self.path}: ours={short(self.ours)} client={short(self.theirs)}"
        )


@dataclass
class Comparison:
    """The verdict on one case."""

    name: str
    differences: List[Difference] = field(default_factory=list)
    ours_failed: Optional[str] = None
    """The exception the specification raised, if it raised one."""

    @property
    def matches(self) -> bool:
        """Whether the two answers agree everywhere that counts."""
        return not self.differences and self.ours_failed is None


def _ignored(path: str) -> bool:
    """Return whether a path names prose rather than data."""
    return any(path.endswith(suffix) for suffix in IGNORED_PATHS)


def _normalized(value: Any) -> Any:
    """
    Fold away the differences that are notation rather than answer.

    Hex is compared case-insensitively and quantities by value, so
    `0x01` and `0x1` are the same number. Anything the schema types as
    data is fixed-width, so a leading zero there is not notation and
    survives this.
    """
    if isinstance(value, str) and value.startswith("0x"):
        return value.lower()
    return value


def _quantity(value: Any) -> Optional[int]:
    """Return the integer a hex quantity denotes, if it is one."""
    if isinstance(value, str) and value.startswith("0x"):
        try:
            return int(value, 16)
        except ValueError:
            return None
    return None


def compare_values(
    ours: Any, theirs: Any, path: str, differences: List[Difference]
) -> None:
    """Recurse into two answers, recording wherever they part company."""
    if _ignored(path):
        return
    if isinstance(ours, dict) and isinstance(theirs, dict):
        for key in sorted(set(ours) | set(theirs)):
            child = f"{path}.{key}" if path else key
            if key not in ours:
                if not _ignored(child):
                    differences.append(
                        Difference(child, "<absent>", theirs[key])
                    )
                continue
            if key not in theirs:
                if not _ignored(child):
                    differences.append(
                        Difference(child, ours[key], "<absent>")
                    )
                continue
            compare_values(ours[key], theirs[key], child, differences)
        return
    if isinstance(ours, list) and isinstance(theirs, list):
        if len(ours) != len(theirs):
            differences.append(
                Difference(f"{path}.length", len(ours), len(theirs))
            )
        for index, (mine, yours) in enumerate(zip(ours, theirs, strict=False)):
            compare_values(mine, yours, f"{path}[{index}]", differences)
        return

    mine_quantity = _quantity(ours)
    yours_quantity = _quantity(theirs)
    if mine_quantity is not None and yours_quantity is not None:
        # Only compare as numbers when neither side is fixed-width
        # data; a hash and its value are never confused because the
        # lengths agree in that case anyway.
        if len(str(ours)) != len(str(theirs)):
            if mine_quantity != yours_quantity:
                differences.append(Difference(path, ours, theirs))
            return
    if _normalized(ours) != _normalized(theirs):
        differences.append(Difference(path, ours, theirs))


def compare_envelopes(
    name: str, ours: Dict[str, Any], theirs: Dict[str, Any]
) -> Comparison:
    """
    Compare two whole JSON-RPC envelopes for the same request.

    Whether a request succeeds or fails is itself part of the answer, so
    a case where one side returned a result and the other an error is a
    difference at the top rather than an error in the harness.
    """
    comparison = Comparison(name=name)
    ours_error = ours.get("error")
    theirs_error = theirs.get("error")
    if (ours_error is None) != (theirs_error is None):
        comparison.differences.append(
            Difference(
                "outcome",
                "error" if ours_error else "result",
                "error" if theirs_error else "result",
            )
        )
        comparison.differences.append(
            Difference(
                "detail",
                ours_error or ours.get("result"),
                theirs_error or theirs.get("result"),
            )
        )
        return comparison
    if ours_error is not None:
        compare_values(
            ours_error, theirs_error, "error", comparison.differences
        )
        return comparison
    compare_values(
        ours.get("result"),
        theirs.get("result"),
        "result",
        comparison.differences,
    )
    return comparison
