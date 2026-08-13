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


_SUBSCHEMA = ("items", "additionalProperties", "not", "contains")
"""Keywords whose value is a single subschema, or a list of them."""

_SUBSCHEMA_LIST = ("allOf", "anyOf", "oneOf")
"""Keywords whose value is a list of subschemas."""

_SUBSCHEMA_MAP = ("properties", "patternProperties", "definitions")
"""Keywords whose value maps names onto subschemas."""


def _relaxed(node: Any) -> Any:
    """
    Return a schema that accepts any subset of what the original accepts.

    Two edits, applied at every depth. `required` is dropped, because an
    expectation that names five of six fields is incomplete on purpose.
    `oneOf` becomes an `anyOf` under `allOf`, because relaxing the branches
    of an exclusive choice tends to make more than one of them match, and
    "exactly one" would then reject a subset that is perfectly compatible
    with the schema. Everything else survives: types, patterns, enums and
    `additionalProperties: false` all still apply, so a partial expectation
    naming a field that does not exist, or giving one the wrong type, is
    still refused.
    """
    if isinstance(node, list):
        return [_relaxed(item) for item in node]
    if not isinstance(node, dict):
        return node

    relaxed = {
        key: value
        for key, value in node.items()
        if key not in ("required", "oneOf")
    }
    for key in _SUBSCHEMA:
        if key in relaxed:
            relaxed[key] = _relaxed(relaxed[key])
    for key in _SUBSCHEMA_LIST:
        if key in relaxed:
            relaxed[key] = [_relaxed(item) for item in relaxed[key]]
    for key in _SUBSCHEMA_MAP:
        if key in relaxed:
            relaxed[key] = {
                name: _relaxed(subschema)
                for name, subschema in relaxed[key].items()
            }
    if "oneOf" in node:
        relaxed.setdefault("allOf", [])
        relaxed["allOf"] = list(relaxed["allOf"]) + [
            {"anyOf": [_relaxed(branch) for branch in node["oneOf"]]}
        ]
    return relaxed


@lru_cache(maxsize=None)
def partial_result_validator(method: str) -> Draft7Validator:
    """Return a validator for a subset of the named method's result."""
    return Draft7Validator(_relaxed(result_validator(method).schema))


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


def _report(
    method: str, validator: Draft7Validator, result: Any, subject: str
) -> None:
    """
    Raise a single message naming every clause `result` breaches.

    Every violation is reported at once, because a response that is wrong
    in one field is usually wrong in several and fixing them one per run is
    needlessly slow.
    """
    errors = [_most_specific(error) for error in validator.iter_errors(result)]
    if not errors:
        return

    errors.sort(key=lambda error: list(map(str, error.absolute_path)))
    details = "\n".join(
        f"  {'/'.join(str(part) for part in error.absolute_path) or '<root>'}"
        f": {error.message}"
        for error in errors
    )
    raise SchemaViolationError(
        f"{method} {subject} does not conform to its result schema:\n{details}"
    )


def validate_result(method: str, result: Any) -> None:
    """Check a result against its method's schema, raising on violation."""
    _report(method, result_validator(method), result, "response")


def validate_partial_result(method: str, result: Any) -> None:
    """
    Check a subset of a result against a relaxed copy of the schema.

    Only completeness is waived; see `_relaxed`. A partial expectation is
    still refused if it names a field the schema does not define or gives
    one a value the schema forbids, which is what keeps the guard on
    derived expectations meaningful rather than decorative.
    """
    _report(
        method,
        partial_result_validator(method),
        result,
        "partial expectation",
    )
