"""
Output of client test runners (`blocktest`, `enginetest`).

The interface is described in `docs/running_tests/consume/client_runners.md`;
the docs build renders their JSON Schemas into that page.
"""

from typing import List, Literal

from pydantic import ConfigDict, Field

from execution_testing.base_types import (
    CamelModel,
    EthereumTestRootModel,
    Hash,
)


class RunnerModel(CamelModel):
    """Base for runner output: clients may add keys, which are kept."""

    model_config = ConfigDict(extra="allow")


class Rejection(RunnerModel):
    """A block or payload the client rejected."""

    index: int = Field(
        ge=0,
        description=(
            "Position in the fixture's `blocks` or `engineNewPayloads`, "
            "from 0."
        ),
    )
    hash: Hash | None = Field(
        default=None,
        description="The rejected block's hash, when the client computed one.",
    )
    error: str = Field(
        description=(
            "The client's own message, untranslated. A JSON-RPC error reads "
            '"<code>: <message>", plus ": <data>" when it carries data.'
        ),
    )


class FixtureResult(RunnerModel):
    """The outcome of one fixture."""

    name: str = Field(
        description="The fixture's key in the fixture file, verbatim.",
    )
    passed: bool = Field(
        alias="pass",
        description=(
            "Whether the fixture's expected outcome (valid, or rejected) "
            "was met, whatever the reason given."
        ),
    )
    rejections: List[Rejection] = Field(
        description=(
            "Every block or payload the client rejected, in fixture order."
        ),
    )


class RunnerResults(EthereumTestRootModel[List[FixtureResult]]):
    """The JSON array a runner prints on stdout: one object per fixture."""

    root: List[FixtureResult]


class BalExecution(RunnerModel):
    """The executor that ran one block, printed with `--bal-report`."""

    event: Literal["balExecution"]
    block: int = Field(ge=0, description="The block number.")
    hash: Hash = Field(description="The block hash.")
    path: Literal["parallel", "sequential"] = Field(
        description="The executor that ran the block.",
    )
    reason: str = Field(
        description=(
            "Why the block took its path: `withheld`, `bad-access-list`, "
            "`disabled`, `no-access-list`, `pre-amsterdam`, a lowercase "
            "client-specific name, or empty for `parallel`."
        ),
    )


class BalFallback(RunnerModel):
    """A sequential rerun after the parallel executor failed on a block."""

    event: Literal["balFallback"]
    block: int = Field(ge=0, description="The block number.")
    hash: Hash = Field(description="The block hash.")
    parallel_error: str = Field(
        description="The parallel executor's error.",
    )
    sequential_result: Literal["valid", "invalid"] = Field(
        description="The sequential rerun's verdict, which the block keeps.",
    )
    sequential_error: str = Field(
        description="The sequential rerun's error, empty when valid.",
    )
