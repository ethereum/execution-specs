"""
Filler object definitions.
"""
from typing import List, Optional

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..common import Fixture, alloc_to_accounts
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import BaseTest


def fill_test(
    t8n: TransitionTool,
    test_spec: BaseTest,
    fork: Fork,
    engine: str,
    spec: ReferenceSpec | None,
    eips: Optional[List[int]] = None,
) -> Fixture:
    """
    Fills fixtures for the specified fork.
    """
    t8n.reset_traces()

    pre, genesis_rlp, genesis = test_spec.make_genesis(t8n, fork)

    (blocks, head, alloc) = test_spec.make_blocks(
        t8n,
        genesis,
        pre,
        fork,
        eips=eips,
    )

    fcu_version: int | None = None
    if not test_spec.base_test_config.disable_hive:
        last_valid_block = next(
            (block.block_header for block in reversed(blocks) if block.expected_exception is None),
            None,
        )
        fcu_version = (
            fork.engine_forkchoice_updated_version(
                last_valid_block.number, last_valid_block.timestamp
            )
            if last_valid_block
            else None
        )

    fork_name = fork.name()
    fixture = Fixture(
        blocks=blocks,
        genesis=genesis,
        genesis_rlp=genesis_rlp,
        head=head,
        fork="+".join([fork_name] + [str(eip) for eip in eips]) if eips is not None else fork_name,
        pre_state=pre,
        post_state=alloc_to_accounts(alloc),
        seal_engine=engine,
        name=test_spec.tag,
        fcu_version=fcu_version,
    )
    fixture.fill_info(t8n, spec)

    return fixture
