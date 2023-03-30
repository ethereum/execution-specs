"""
Filler object definitions.
"""
from copy import copy
from typing import List, Mapping, Optional

from ethereum_test_forks import ArrowGlacier, Fork
from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import Fixture, alloc_to_accounts
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import TestSpec


def fill_test(
    name: str,
    t8n: TransitionTool,
    b11r: BlockBuilder,
    test_spec: TestSpec,
    forks: List[Fork],
    engine: str,
    spec: ReferenceSpec | None,
    eips: Optional[List[int]] = None,
) -> Mapping[str, Fixture]:
    """
    Fills fixtures for certain forks.
    """
    fixtures: List[Fixture] = []
    for fork in forks:
        for index, test in enumerate(test_spec(fork)):
            if not t8n.is_fork_supported(fork):
                # Fork not supported by t8n, skip
                continue
            if fork == ArrowGlacier:
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
                    eips=eips,
                )
            except Exception as e:
                name_tag = f"{name} {test.tag}" if test.tag else name
                print(f"Exception during test '{name_tag}'")
                raise e

            fixture = Fixture(
                blocks=blocks,
                genesis=genesis,
                genesis_rlp=genesis_rlp,
                head=head,
                fork="+".join([fork.__name__] + [str(eip) for eip in eips])
                if eips is not None
                else fork.__name__,
                pre_state=copy(test.pre),
                post_state=alloc_to_accounts(alloc),
                seal_engine=engine,
                name=test.tag,
                index=index,
            )
            fixture.fill_info(t8n, b11r, spec)
            fixtures.append(fixture)

    out = {}
    for fixture in fixtures:
        name = str(fixture.index).zfill(3)
        if fixture.name:
            name += "/" + fixture.name.replace(" ", "/")
        name += "/" + fixture.fork.lower()
        out[name] = fixture

    return out
