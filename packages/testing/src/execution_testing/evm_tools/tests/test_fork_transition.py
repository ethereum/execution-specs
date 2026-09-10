"""Test fork-block activation derived from the transition schedule."""

import argparse
import json
from io import StringIO
from typing import Generator, Literal

import pytest
from ethereum.fork_criteria import ByTimestamp, Unscheduled
from ethereum_spec_tools.loaders.fork_loader import ForkLoad

from execution_testing import Alloc, Environment, Hash
from execution_testing.client_clis.transition_tool import TransitionTool
from execution_testing.evm_tools.t8n import T8N, ForkCache
from execution_testing.evm_tools.t8n.cli import (
    build_t8n_from_cli_options,
    t8n_arguments,
)
from execution_testing.forks import (
    BPO2,
    Amsterdam,
    BPO2ToAmsterdamAtTime15k,
    Fork,
    TransitionFork,
)

pytestmark = pytest.mark.evm_tools


@pytest.fixture(scope="module")
def cache() -> Generator[ForkCache, None, None]:
    """Share one fork cache so each criteria clone is built once."""
    with ForkCache() as fork_cache:
        yield fork_cache


def transition_tool_data(
    fork: Fork | TransitionFork, parent_timestamp: int, timestamp: int
) -> TransitionTool.TransitionToolData:
    """
    Return the data the filler hands to the t8n for one empty block.

    The pre-state holds the system contracts of the target fork, as a
    filled fixture's genesis would.
    """
    return TransitionTool.TransitionToolData(
        alloc=Alloc.model_validate(
            fork.transitions_to().pre_allocation_blockchain()
        ),
        txs=[],
        env=Environment(
            number=2,
            timestamp=timestamp,
            parent_timestamp=parent_timestamp,
            block_hashes={1: Hash(1)},
            base_fee_per_gas=7,
            parent_beacon_block_root=Hash(0),
            excess_blob_gas=0,
            prev_randao=Hash(0),
            slot_number=2,
        ),
        fork=fork,
        chain_id=1,
        reward=0,
        blob_schedule=None,
    )


@pytest.mark.parametrize("path", ["in-process", "cli"])
@pytest.mark.parametrize("fork_block_logic", [False, True])
@pytest.mark.parametrize(
    "fork,parent_timestamp,timestamp,active_fork,crosses",
    [
        pytest.param(
            BPO2ToAmsterdamAtTime15k, 14998, 14999, BPO2, False, id="before"
        ),
        pytest.param(
            BPO2ToAmsterdamAtTime15k, 14999, 15000, Amsterdam, True, id="at"
        ),
        pytest.param(
            BPO2ToAmsterdamAtTime15k,
            14999,
            15007,
            Amsterdam,
            True,
            id="skipped-slot",
        ),
        pytest.param(
            BPO2ToAmsterdamAtTime15k,
            15000,
            15001,
            Amsterdam,
            False,
            id="after",
        ),
        pytest.param(
            Amsterdam, 14999, 15000, Amsterdam, False, id="no-schedule"
        ),
    ],
)
def test_fork_block_from_schedule(
    cache: ForkCache,
    monkeypatch: pytest.MonkeyPatch,
    fork: Fork | TransitionFork,
    parent_timestamp: int,
    timestamp: int,
    active_fork: Fork,
    crosses: bool,
    fork_block_logic: bool,
    path: Literal["in-process", "cli"],
) -> None:
    """
    Run the target fork with the transition's criteria only when it has
    fork-block logic, and report the fork block only on the crossing.

    External tools keep receiving the resolved per-block fork name and no
    activation information. The EELS t8n derives activation from the
    schedule, both in-process and through the CLI given the transition
    name. Amsterdam is unscheduled in the spec, so without an override its
    criteria never match.
    """
    monkeypatch.setattr(
        ForkLoad, "has_fork_block_logic", property(lambda _: fork_block_logic)
    )
    data = transition_tool_data(fork, parent_timestamp, timestamp)
    request = data.get_request_data().model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    assert request["state"] == {
        "fork": active_fork.transition_tool_name(),
        "chainid": 1,
        "reward": 0,
    }

    if path == "in-process":
        t8n = T8N(data, cache=cache)
    else:
        parser = argparse.ArgumentParser()
        t8n_arguments(parser.add_subparsers())
        options = parser.parse_args(
            [
                "t8n",
                f"--state.fork={fork.name()}",
                "--input.alloc=stdin",
                "--input.env=stdin",
                "--input.txs=stdin",
            ]
        )
        t8n = build_t8n_from_cli_options(
            options, StringIO(json.dumps(request["input"])), cache=cache
        )

    overridden = (
        fork_block_logic
        and fork.is_transition_fork
        and active_fork == Amsterdam
    )
    if overridden:
        assert t8n.fork.fork_criteria == ByTimestamp(15_000)
    elif active_fork == Amsterdam:
        assert isinstance(t8n.fork.fork_criteria, Unscheduled)
    assert t8n.is_fork_block == (overridden and crosses)
    assert t8n.run().result.block_exception is None
