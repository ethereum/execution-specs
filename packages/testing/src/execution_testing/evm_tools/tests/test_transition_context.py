"""Exercise fork-boundary execution through the t8n CLI input path."""

import argparse
import json
from io import StringIO

import pytest

from execution_testing import (
    Account,
    Alloc,
    BlockAccessList,
    Environment,
    Hash,
)
from execution_testing.client_clis.transition_tool import TransitionTool
from execution_testing.evm_tools.t8n import ForkCache
from execution_testing.evm_tools.t8n.cli import (
    build_t8n_from_cli_options,
    t8n_arguments,
)
from execution_testing.forks import (
    Amsterdam,
    BPO2ToAmsterdamAtTime15k,
    Fork,
    TransitionFork,
)


@pytest.mark.parametrize(
    "seed_accounts", [False, True], ids=["absent", "stored"]
)
@pytest.mark.parametrize(
    "fork,parent_timestamp,timestamp,expect_bump",
    [
        pytest.param(
            BPO2ToAmsterdamAtTime15k, 14998, 14999, False, id="before"
        ),
        pytest.param(BPO2ToAmsterdamAtTime15k, 14999, 15000, True, id="at"),
        pytest.param(
            BPO2ToAmsterdamAtTime15k, 14999, 15007, True, id="skipped-slot"
        ),
        pytest.param(
            BPO2ToAmsterdamAtTime15k, 15000, 15001, False, id="after"
        ),
        pytest.param(Amsterdam, 14999, 15000, False, id="ordinary-fork"),
    ],
)
def test_transition_context_cli(
    fork: Fork | TransitionFork,
    parent_timestamp: int,
    timestamp: int,
    expect_bump: bool,
    seed_accounts: bool,
) -> None:
    """Apply the nonce bump only when the configured boundary is crossed."""
    targeted = Amsterdam.zero_nonce_storage_accounts()
    pre = Alloc(
        {
            address: Account(
                nonce=0 if expect_bump else 2,
                balance=index + 1,
                storage={0: 7, 1: 11},
            )
            for index, address in enumerate(targeted)
        }
        if seed_accounts
        else {}
    )
    pre = Alloc.merge(
        Alloc.model_validate(
            fork.transitions_to().pre_allocation_blockchain()
        ),
        pre,
    )
    data = TransitionTool.TransitionToolData(
        alloc=pre,
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
    request = data.get_request_data().model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    assert request["state"]["fork"] == fork.name()
    assert "forkActivation" not in request["state"]

    parser = argparse.ArgumentParser()
    t8n_arguments(parser.add_subparsers())
    options = parser.parse_args(
        [
            "t8n",
            f"--state.fork={request['state']['fork']}",
            "--input.alloc=stdin",
            "--input.env=stdin",
            "--input.txs=stdin",
        ]
    )
    with ForkCache() as cache:
        t8n = build_t8n_from_cli_options(
            options, StringIO(json.dumps(request["input"])), cache=cache
        )
        result = t8n.run()
        assert result.result.block_exception is None
        output = result.alloc.materialize()

    for address in targeted:
        if expect_bump or seed_accounts:
            account = output[address]
            assert account is not None
            assert account.nonce == (1 if expect_bump else 2)
            if seed_accounts:
                initial = pre[address]
                assert initial is not None
                assert account.balance == initial.balance
                assert account.storage == initial.storage
        else:
            assert address not in output

    if result.result.block_access_list is not None:
        # Reconstruct from the emitted BAL, independently of the execution
        # output, including changes made by the predeployed system contracts.
        reconstructed = pre.model_copy(deep=True)
        reconstructed.migrate_state_commitment(
            data.active_fork.state_commitment()
        )
        bal = BlockAccessList.from_rlp(result.result.block_access_list)
        for entry in bal.root:
            if not (
                entry.nonce_changes
                or entry.balance_changes
                or entry.code_changes
                or entry.storage_changes
            ):
                continue
            account = reconstructed.get(entry.address) or Account()
            if entry.nonce_changes:
                if entry.address in targeted:
                    assert len(entry.nonce_changes) == 1
                    assert entry.nonce_changes[0].block_access_index == 0
            reconstructed[entry.address] = Account(
                nonce=entry.nonce_changes[-1].post_nonce
                if entry.nonce_changes
                else account.nonce,
                balance=entry.balance_changes[-1].post_balance
                if entry.balance_changes
                else account.balance,
                code=entry.code_changes[-1].new_code
                if entry.code_changes
                else account.code,
                storage=account.storage.root
                | {
                    slot.slot: slot.slot_changes[-1].post_value
                    for slot in entry.storage_changes
                },
            )
        assert reconstructed.state_root() == result.result.state_root
