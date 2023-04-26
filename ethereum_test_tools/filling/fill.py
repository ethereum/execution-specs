"""
Filler object definitions.
"""
from copy import copy
from typing import List, Mapping, Optional

from ethereum_test_forks import Fork
from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import Fixture, alloc_to_accounts
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import BaseTest


def fill_test(
    name: str,
    t8n: TransitionTool,
    b11r: BlockBuilder,
    test_spec: BaseTest,
    fork: Fork,
    engine: str,
    spec: ReferenceSpec | None,
    eips: Optional[List[int]] = None,
) -> Mapping[str, Fixture]:
    """
    Fills fixtures for the specified fork.
    """
    t8n.reset_traces()

    genesis_rlp, genesis = test_spec.make_genesis(b11r, t8n, fork)

    try:
        (blocks, head, alloc) = test_spec.make_blocks(
            b11r,
            t8n,
            genesis,
            fork,
            eips=eips,
        )
    except Exception as e:
        name_tag = f"{name} {test_spec.tag}" if test_spec.tag else name
        print(f"Exception during test '{name_tag}'")
        raise e
    fork_name = fork.name()
    fixture = Fixture(
        blocks=blocks,
        genesis=genesis,
        genesis_rlp=genesis_rlp,
        head=head,
        fork="+".join([fork_name] + [str(eip) for eip in eips])
        if eips is not None
        else fork_name,
        pre_state=copy(test_spec.pre),
        post_state=alloc_to_accounts(alloc),
        seal_engine=engine,
        name=test_spec.tag,
        index=0,  # TODO: Pytest refactor: index is always 0
    )
    fixture.fill_info(t8n, b11r, spec)

    out = {}
    name = str(fixture.index).zfill(3)
    if fixture.name:
        name += "/" + fixture.name.replace(" ", "/")
    name += "/" + fixture.fork.lower()
    out[name] = fixture

    return out
