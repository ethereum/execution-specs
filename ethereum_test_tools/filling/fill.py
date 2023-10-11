"""
Test filler definitions.
"""
from typing import List, Optional, Union

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..common import Fixture, HiveFixture
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import BaseTest


def fill_test(
    t8n: TransitionTool,
    test_spec: BaseTest,
    fork: Fork,
    spec: ReferenceSpec | None,
    eips: Optional[List[int]] = None,
) -> Optional[Union[Fixture, HiveFixture]]:
    """
    Fills default/hive fixture for the specified fork and test spec.
    """
    fixture: Union[Fixture, HiveFixture]
    t8n.reset_traces()
    if test_spec.base_test_config.enable_hive:
        if fork.engine_new_payload_version() is None:
            return None  # pre Merge tests are not supported in Hive
        fixture = test_spec.make_hive_fixture(t8n, fork, eips)
    else:
        fixture = test_spec.make_fixture(t8n, fork, eips)
    fixture.fill_info(t8n, spec)
    return fixture
