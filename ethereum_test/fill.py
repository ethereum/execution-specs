"""
Filler object definitions.
"""
from typing import List, Mapping

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool, map_fork

from .base_test import TestSpec
from .types import Fixture


def fill_test(
    test_spec: TestSpec, forks: List[str], engine: str
) -> Mapping[str, Fixture]:
    """
    Fills fixtures for certain forks.
    """
    fixtures: List[Fixture] = []
    for fork in forks:
        b11r = BlockBuilder()
        t8n = TransitionTool()

        for test in test_spec(fork):

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
                b11r, t8n, genesis, fork, reward=2000000000000000000
            )

            fixtures.append(
                Fixture(
                    blocks=blocks,
                    genesis=genesis,
                    head=head,
                    fork=fork,
                    pre_state=test.pre,
                    post_state=None,
                    seal_engine=engine,
                )
            )

    out = {}
    for fixture in fixtures:
        out[fixture.fork.lower()] = fixture

    return out
