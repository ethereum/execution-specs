"""
Tests for the fast KZG setup hint in the consume client environment.

Consume clients compute no KZG proofs, so every consume simulator asks
client wrapper scripts for a fast KZG setup.
"""

from types import SimpleNamespace

from execution_testing.forks import Osaka

from ..simulators import multi_test_client, single_test_client
from .direct_calls import fixture_body

KZG_FAST_SETUP = ("HIVE_KZG_FAST_SETUP", "1")
"""The hint as it appears in the client environment."""


def test_single_test_clients_ask_for_a_fast_setup() -> None:
    """Engine, rlp, sync and build_block clients get the hint."""
    fixture = SimpleNamespace(fork=Osaka, config=SimpleNamespace(chain_id=1))
    environment = fixture_body(single_test_client.environment)(fixture, 8551)
    assert KZG_FAST_SETUP in environment.items()


def test_multi_test_clients_ask_for_a_fast_setup() -> None:
    """Enginex and wirex clients get the hint."""
    environment = fixture_body(multi_test_client.environment)(
        SimpleNamespace(fork=Osaka),
        SimpleNamespace(pre_hash="0x00"),
        8551,
        {},
    )
    assert KZG_FAST_SETUP in environment.items()
