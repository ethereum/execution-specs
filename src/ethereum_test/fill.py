"""
Filler object definitions.
"""
from typing import List, Mapping

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool, map_fork

from .base_test import TestSpec
from .fork import get_reward
from .types import Fixture


def fill_test(
    t8n: TransitionTool,
    b11r: BlockBuilder,
    test_spec: TestSpec,
    forks: List[str],
    engine: str,
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

            genesis = test.make_genesis(b11r, t8n, fork)
            (blocks, head) = test.make_blocks(
                b11r, t8n, genesis, fork, reward=get_reward(fork)
            )

            fixture = Fixture(
                blocks=blocks,
                genesis=genesis,
                head=head,
                fork=fork,
                pre_state=test.pre,
                post_state=None,
                seal_engine=engine,
                name=test.name,
                index=index + 1,
            )
            fixture.fill_info(t8n, b11r)
            fixtures.append(fixture)

    out = {}
    for fixture in fixtures:
        outname = str(fixture.index).zfill(3)
        if fixture.name:
            outname += "_" + fixture.name.replace(" ", "_")
        outname += "_" + fixture.fork.lower()
        out[outname] = fixture

    return out
