"""
Chains delivered to a client by syncing from a peer rather than by
``engine_newPayload``.

Post-merge clients do not gossip blocks, so a client that is told a head it
has never been sent can only reach it by syncing the chain from a peer over
devp2p. That is the delivery path hive's ``ReOrgViaSync`` variants exercise
and the one no single-client fixture can express.

WIP: the multi-client fixture interface (an additional peer client, per-step
client targeting, and a poll-for-head step) is withheld pending the design of
a general, reusable sync step shared across the framework's test cases
(PR3556-R0019). The scenario below is the intended shape for that follow-up:

    - Load a whole linear chain (labels a1..a5) onto a second, peered client
      via ``newPayload``/``forkchoiceUpdated``.
    - Assert the peer's head is a5 and the main client's head is still
      genesis (it never received a payload).
    - Send the main client ``forkchoiceUpdated(head=a5)``: legal outcomes are
      SYNCING (unknown payload, most likely) or an immediate VALID apply;
      branch the SYNCING outcome into a step that polls
      ``eth_getBlockByNumber("latest")`` on main until it equals a5.
    - Assert the main client's head is a5.
"""

import pytest
from execution_testing import Alloc
from execution_testing.specs import ReorgTestFiller


@pytest.mark.skip(
    reason="Multi-client reorg fixture design pending (PR3556-R0019)"
)
@pytest.mark.valid_from("Cancun")
def test_head_synced_from_peer(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    A head that was never delivered to the client must be reached by
    syncing. Withheld until the multi-client fixture interface is designed;
    see the module docstring for the intended scenario.
    """
