"""
Filler object definitions.
"""
from copy import copy
from typing import List, Mapping, Optional

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool, map_fork

from ..common import Fixture, alloc_to_accounts
from ..spec import TestSpec
from ..vm.fork import get_reward


def fill_test(
    t8n: TransitionTool,
    b11r: BlockBuilder,
    test_spec: TestSpec,
    forks: List[str],
    engine: str,
    eips: Optional[List[int]] = None,
) -> Mapping[str, Fixture]:
    """
    Fills fixtures for certain forks.
    """
    fixtures: List[Fixture] = []
    for fork in forks:
        for index, test in enumerate(test_spec(fork)):
            mapped = map_fork(fork)
            if mapped is None:
                # Fork not supported by t8n, skip
                continue
            fork = str(mapped)
            if fork == "ArrowGlacier":
                # Fork not supported by hive, skip
                continue

            t8n.reset_traces()

            genesis_rlp, genesis = test.make_genesis(b11r, t8n, fork)

            try:
                (blocks, head, alloc) = test.make_blocks(
                    b11r,
                    t8n,
                    genesis,
                    fork,
                    reward=get_reward(fork),
                    eips=eips,
                )
            except Exception as e:
                print(f"Exception during test '{test.tag}'")
                raise e

            fixture = Fixture(
                blocks=blocks,
                genesis=genesis,
                genesis_rlp=genesis_rlp,
                head=head,
                fork="+".join([fork] + [str(eip) for eip in eips])
                if eips is not None
                else fork,
                pre_state=copy(test.pre),
                post_state=alloc_to_accounts(alloc),
                seal_engine=engine,
                name=test.tag,
                index=index,
            )
            fixture.fill_info(t8n, b11r)
            fixtures.append(fixture)

    out = {}
    for fixture in fixtures:
        name = str(fixture.index).zfill(3)
        if fixture.name:
            name += "_" + fixture.name.replace(" ", "_")
        name += "_" + fixture.fork.lower()
        out[name] = fixture

    return out
