"""Test fork-block activation derived from the transition schedule."""

import argparse
import json
from io import StringIO
from typing import Literal

import pytest

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


def transition_tool_data(
    fork: Fork | TransitionFork, parent_timestamp: int, timestamp: int
) -> TransitionTool.TransitionToolData:
    """Return the data the filler hands to the t8n for one empty block."""
    return TransitionTool.TransitionToolData(
        alloc=Alloc(),
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
@pytest.mark.parametrize(
    "fork,parent_timestamp,timestamp,active_fork,expect_bump",
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
    fork: Fork | TransitionFork,
    parent_timestamp: int,
    timestamp: int,
    active_fork: Fork,
    expect_bump: bool,
    path: Literal["in-process", "cli"],
) -> None:
    """
    Apply the EIP-8253 bump only on the block that crosses the boundary.

    External tools keep receiving the resolved per-block fork name and no
    activation flag; the EELS t8n derives activation from the schedule,
    both in-process and through the CLI given the transition name.
    """
    data = transition_tool_data(fork, parent_timestamp, timestamp)
    request = data.get_request_data().model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    assert request["state"]["fork"] == active_fork.transition_tool_name()
    assert "forkActivation" not in request["state"]

    with ForkCache() as cache:
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
        assert t8n.is_fork_block == expect_bump
        output = t8n.run().alloc.materialize()

    for address in Amsterdam.zero_nonce_storage_accounts():
        if expect_bump:
            account = output[address]
            assert account is not None
            assert account.nonce == 1
        else:
            assert address not in output
