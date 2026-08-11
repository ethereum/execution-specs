"""
The comparison itself, as a test.

Two tiers, so that most of what the harness pins costs nothing to check.
The offline tier validates every derived answer against the pinned
`eth_simulateV1` result schema and is always run. The client tier starts
go-ethereum and compares field by field, and is skipped unless
`--simulate-client` is passed and the hive image is present.
"""

from typing import Any, Dict, Iterator, List

import pytest
from execution_testing.rpc.serialization.schema import (
    SchemaViolationError,
    validate_result,
)

from .cases import CASES, Case
from .client import (
    ClientUnavailableError,
    SimulateClient,
    client_image_available,
    client_version,
    running_client,
)
from .genesis import genesis_hash
from .runner import compare_case, derive, summarize

METHOD = "eth_simulateV1"


def pytest_generate_tests(metafunc: Any) -> None:
    """Parametrize over the vectors by name."""
    if "case" in metafunc.fixturenames:
        metafunc.parametrize(
            "case", CASES, ids=[entry.name for entry in CASES]
        )


@pytest.fixture(scope="module")
def client(request: pytest.FixtureRequest) -> Iterator[SimulateClient]:
    """Start go-ethereum for the module, or skip the whole tier."""
    if not request.config.getoption("--simulate-client", default=False):
        pytest.skip("pass --simulate-client to compare against a client")
    if not client_image_available():
        pytest.skip("the hive go-ethereum image is not built locally")
    try:
        with running_client() as running:
            yield running
    except ClientUnavailableError as unavailable:
        pytest.skip(str(unavailable))


def test_every_case_conforms_to_the_schema(case: Case) -> None:
    """
    A derived answer either fails the request or satisfies the schema.

    Validated against the pinned OpenRPC result schema rather than
    against a client, so this holds whether or not Docker is around. A
    top-level error has no result to validate, which is itself the
    schema's position.
    """
    envelope = derive(case)
    if "error" in envelope:
        assert envelope["error"]["code"] != -32603, envelope["error"]
        return
    try:
        validate_result(METHOD, envelope["result"])
    except SchemaViolationError as violation:
        pytest.fail(f"{case.name}: {violation}")


@pytest.mark.slow
def test_case_matches_the_client(case: Case, client: SimulateClient) -> None:
    """
    The specification's answer is the client's, field for field.

    A case marked `contested` is expected to differ, and is reported the
    other way round: if it stops differing, the note explaining why it
    does has gone stale and should be revisited.
    """
    comparison = compare_case(case, client)
    if case.contested:
        assert not comparison.matches, (
            f"{case.name} now agrees with the client; the note saying why "
            f"it should not is out of date"
        )
        return
    assert comparison.matches, "\n".join(
        [f"{case.name} differs from the client:"]
        + [f"  {difference}" for difference in comparison.differences]
    )


@pytest.mark.slow
def test_the_genesis_agrees(client: SimulateClient) -> None:
    """
    Both sides start from the same block, and derived it separately.

    Nothing downstream means anything without this: a state root that
    matched from a genesis that did not would be a coincidence.
    """
    reported = client.request("eth_getBlockByNumber", ["0x0", False])
    assert reported["result"]["hash"] == "0x" + genesis_hash().hex()


@pytest.mark.slow
def test_the_measured_number(client: SimulateClient) -> None:
    """
    Report how many of the vectors match, and hold the line there.

    The count is the headline the assessment claims, so it is asserted
    rather than merely printed: a regression that moved one case from
    matching to differing would otherwise be invisible behind the
    per-case tests it also fails.
    """
    comparisons = [compare_case(entry, client) for entry in CASES]
    matched = sum(1 for entry in comparisons if entry.matches)
    expected = sum(1 for entry in CASES if not entry.contested)
    assert matched == expected, f"{client_version()}\n{summarize(comparisons)}"


def collect_report(client: SimulateClient) -> Dict[str, Any]:
    """Return the whole comparison as data, for reporting outside tests."""
    comparisons = [compare_case(entry, client) for entry in CASES]
    results: List[Dict[str, Any]] = []
    for entry, case in zip(comparisons, CASES, strict=False):
        results.append(
            {
                "name": entry.name,
                "contested": case.contested,
                "matches": entry.matches,
                "differences": [str(item) for item in entry.differences],
            }
        )
    return {"client": client_version(), "cases": results}
