"""
Filler object definitions.
"""
from typing import List, Mapping

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool, map_fork

from .fork import is_london
from .state_test import StateTest
from .types import Fixture


def fill_state_test(
    test: StateTest, forks: List[str], engine: str
) -> Mapping[str, Fixture]:
    """
    Fills fixtures for certain forks.
    """
    fixtures = []
    for fork in forks:
        b11r = BlockBuilder()
        t8n = TransitionTool()

        if is_london(fork) and test.env.base_fee is None:
            test.env.base_fee = 7

        mapped = map_fork(fork)
        if mapped is None:
            # Fork not supported by t8n, skip
            continue
        fork = str(mapped)
        if fork == "ArrowGlacier":
            # Fork not supported by hive, skip
            continue

        genesis = test.make_genesis(b11r, t8n, test.env, fork)
        (block, head) = test.make_block(
            b11r, t8n, fork, reward=2000000000000000000
        )

        fixtures.append(
            Fixture(
                blocks=[block],
                genesis=genesis,
                head=head,
                fork=fork,
                pre_state=test.pre,
                seal_engine=engine,
            )
        )

    out = {}
    for fixture in fixtures:
        out[fixture.fork.lower()] = fixture

    return out
