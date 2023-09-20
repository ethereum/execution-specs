"""
Filler object definitions.
"""
from typing import List, Optional, Union

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..common import Fixture, HiveFixture, alloc_to_accounts
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import BaseTest


def fill_test(
    t8n: TransitionTool,
    test_spec: BaseTest,
    fork: Fork,
    engine: str,
    spec: ReferenceSpec | None,
    eips: Optional[List[int]] = None,
) -> Optional[Union[Fixture, HiveFixture]]:
    """
    Fills fixtures for the specified fork.
    """
    t8n.reset_traces()

    pre, genesis_rlp, genesis = test_spec.make_genesis(t8n, fork)

    (blocks, payloads, head, alloc, fcu_version) = test_spec.make_blocks(
        t8n,
        genesis,
        pre,
        fork,
        eips=eips,
    )

    network_info = (
        "+".join([fork.name()] + [str(eip) for eip in eips]) if eips is not None else fork.name()
    )

    fixture: Union[Fixture, HiveFixture]
    if test_spec.base_test_config.enable_hive:
        if fork.engine_new_payload_version() is not None:
            fixture = HiveFixture(
                payloads=payloads,
                fcu_version=fcu_version,
                genesis=genesis,
                fork=network_info,
                pre_state=pre,
                post_state=alloc_to_accounts(alloc),
                name=test_spec.tag,
            )
        else:  # pre Merge tests are not supported in Hive
            # TODO: remove this logic. if hive enabled set --from to Merge
            return None
    else:
        fixture = Fixture(
            blocks=blocks,
            genesis=genesis,
            genesis_rlp=genesis_rlp,
            head=head,
            fork=network_info,
            pre_state=pre,
            post_state=alloc_to_accounts(alloc),
            seal_engine=engine,
            name=test_spec.tag,
        )
    fixture.fill_info(t8n, spec)

    return fixture
