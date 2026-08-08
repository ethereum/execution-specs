"""
Validate JSON-RPC responses against the vendored OpenRPC schema.

execution-apis owns the response *shapes*; this repository owns the
*values*. Checking generated responses against the schema keeps the two
from drifting, and is the same check hive's `rpc-compat` simulator applies
to its own fixtures — the difference being that the responses validated
here are derived from the Python spec rather than recorded from a client.

The schema is fork-agnostic, so it cannot express "required at Cancun":
fields such as `blobGasUsed` are optional in every fork. Schema validation
is therefore a floor, not a ceiling. Exact comparison against a
fork-parameterized expectation is what actually pins those fields.
"""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any, Dict

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError, best_match

SCHEMA_PACKAGE = "execution_testing.rpc"
SCHEMA_FILE = "openrpc.json"


class SchemaViolationError(AssertionError):
    """Raised when a response does not conform to its result schema."""


@lru_cache(maxsize=1)
def openrpc_spec() -> Dict[str, Any]:
    """
    Return the vendored OpenRPC specification.

    Loaded lazily and cached; the document is a few megabytes, so importing
    this module must not pay for it.
    """
    resource = files(SCHEMA_PACKAGE) / "schemas" / SCHEMA_FILE
    return json.loads(resource.read_text())


@lru_cache(maxsize=None)
def result_validator(method: str) -> Draft7Validator:
    """Return a validator for the named method's result schema."""
    for entry in openrpc_spec()["methods"]:
        if entry["name"] == method:
            return Draft7Validator(entry["result"]["schema"])
    raise KeyError(f"method {method!r} is not present in the OpenRPC schema")


def _most_specific(error: ValidationError) -> ValidationError:
    """
    Return the sub-error that best explains a failure.

    Most `eth_` results are a `oneOf` of an object and null, so one bad
    field surfaces as "is not valid under any of the given schemas" against
    the entire response. That names nothing and dumps the whole object,
    which is useless to someone fixing a client.

    Descending needs care: the null branch also fails, with "is not of type
    'null'", and generic relevance heuristics prefer it because it is the
    shallower complaint. Root-level type mismatches are therefore dropped
    first, which leaves the branch that actually matched the response and
    the field that broke it.
    """
    while error.context:
        candidates = [
            candidate
            for candidate in error.context
            if candidate.validator != "type" or list(candidate.absolute_path)
        ]
        if not candidates:
            candidates = list(error.context)
        deepest = max(len(list(c.absolute_path)) for c in candidates)
        candidates = [
            c for c in candidates if len(list(c.absolute_path)) == deepest
        ]
        error = best_match(candidates) or candidates[0]
    return error


def validate_result(method: str, result: Any) -> None:
    """
    Check a result against its method's schema, raising on violation.

    Every violation is reported at once, because a response that is wrong
    in one field is usually wrong in several and fixing them one per run is
    needlessly slow.
    """
    errors = [
        _most_specific(error)
        for error in result_validator(method).iter_errors(result)
    ]
    if not errors:
        return

    errors.sort(key=lambda error: list(map(str, error.absolute_path)))
    details = "\n".join(
        f"  {'/'.join(str(part) for part in error.absolute_path) or '<root>'}"
        f": {error.message}"
        for error in errors
    )
    raise SchemaViolationError(
        f"{method} response does not conform to its result schema:\n{details}"
    )
