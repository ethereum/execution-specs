"""Dial a mock devp2p peer that serves a fixture's chain to the client."""

import logging
import os
import time

from hive.client import Client

from execution_testing.devp2p.chain import Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.devp2p.protocol import EthVersion, ForkSchedule
from execution_testing.forks import Fork, TransitionFork
from execution_testing.forks.transition_base_fork import TransitionBaseClass

from .timing import TimingData

logger = logging.getLogger(__name__)

DEFAULT_NETWORK_ID = 1
"""Network identifier the client is started with, and the peer claims."""


def fork_schedule_of(fork: Fork | TransitionFork) -> ForkSchedule:
    """
    Return when the network a client runs for `fork` forks after genesis.

    The client is configured from the Hive ruleset of the fixture's fork,
    which activates every fork of a post-merge network at genesis except
    the second fork of a transition fork: Shanghai at timestamp 15000 for
    `ParisToShanghaiAtTime15k`, say.
    """
    if not issubclass(fork, TransitionBaseClass):
        return ForkSchedule()
    return ForkSchedule(
        block_numbers=(fork.at_block,), timestamps=(fork.at_timestamp,)
    )


def dial_mock_peer(
    client: Client,
    chain: Chain,
    eth_versions: tuple[EthVersion, ...],
    serve_bals: bool,
    fork_schedule: ForkSchedule,
    total_timing_data: TimingData,
) -> MockPeer:
    """Dial a fresh peer connection to `client`, serving `chain`."""
    enode = client.enode()
    logger.info(f"Connecting mock peer to {enode}")
    peer = MockPeer(
        host=str(client.ip),
        port=enode.port,
        remote_public_key=bytes.fromhex(enode.id),
        private_key=os.urandom(32),
        network_id=DEFAULT_NETWORK_ID,
        eth_versions=eth_versions,
        serve_bals=serve_bals,
        fork_schedule=fork_schedule,
    )
    with total_timing_data.time("Connect mock peer"):
        # The client readiness gate waits on the Engine API port only;
        # a freshly started client may open its devp2p listener a
        # moment later, so the first dial gets a deadline rather than
        # a single attempt.
        deadline = time.monotonic() + 10.0
        while True:
            try:
                peer.connect(chain)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.25)
        peer.start()
    logger.info(f"Mock peer connected to {peer.remote_name}")
    return peer
