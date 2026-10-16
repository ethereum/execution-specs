"""Tests for scheduling the blob parameters of a BPO fork's fixtures."""

from contextlib import ExitStack
from typing import Any, Tuple, Type

import pytest
from execution_testing.forks.base_fork import BaseFork

from ethereum_spec_tools.loaders.fixture_loader import Load

from . import FORKS
from .helpers.load_blockchain_tests import (
    TESTING_FORKS,
    BlockchainTestFixture,
)

BPO_NETWORKS = sorted(
    network
    for network, fork in TESTING_FORKS.items()
    if fork.bpo_fork() and network in FORKS
)


def spec_blob_schedule(load: Load) -> Tuple[int, int, int]:
    """Return the blob schedule constants of the spec fork of `load`."""
    gas_costs = load.fork.hardfork.module("vm.gas").GasCosts
    return (
        int(gas_costs.BLOB_SCHEDULE_TARGET),
        int(gas_costs.BLOB_SCHEDULE_MAX),
        int(gas_costs.BLOB_BASE_FEE_UPDATE_FRACTION),
    )


def derived_blob_constants(load: Load) -> Tuple[int, int]:
    """Return the constants the spec fork derives from its blob schedule."""
    gas_costs = load.fork.hardfork.module("vm.gas").GasCosts
    fork_module = load.fork.hardfork.module("fork")
    return (
        int(gas_costs.BLOB_TARGET_GAS_PER_BLOCK),
        int(fork_module.MAX_BLOB_GAS_PER_BLOCK),
    )


def framework_blob_schedule(fork: Type[BaseFork]) -> Tuple[int, int, int]:
    """Return the blob schedule constants of the testing framework fork."""
    return (
        fork.target_blobs_per_block(),
        fork.max_blobs_per_block(),
        fork.blob_base_fee_update_fraction(),
    )


def test_every_bpo_fork_is_known_to_both_sides() -> None:
    """Pair every BPO fork of the testing framework with a spec fork."""
    assert BPO_NETWORKS
    for network, fork in TESTING_FORKS.items():
        if fork.bpo_fork():
            assert network in FORKS


@pytest.mark.parametrize("network", BPO_NETWORKS)
def test_bpo_fork_derives_its_constants_from_the_schedule(
    network: str,
) -> None:
    """
    Check the derivation the patch reproduces for the spec's own values.
    """
    load = Load(FORKS[network].short_name)
    per_blob = int(load.fork.hardfork.module("vm.gas").GasCosts.PER_BLOB)
    target, maximum, _ = spec_blob_schedule(load)
    assert derived_blob_constants(load) == (
        per_blob * target,
        per_blob * maximum,
    )


@pytest.mark.parametrize("network", BPO_NETWORKS)
def test_bpo_fork_validates_with_the_framework_blob_schedule(
    network: str,
) -> None:
    """Patch in the schedule the fixtures were filled with, then restore."""
    load = Load(FORKS[network].short_name)
    per_blob = int(load.fork.hardfork.module("vm.gas").GasCosts.PER_BLOB)
    spec_schedule = spec_blob_schedule(load)
    spec_derived = derived_blob_constants(load)
    framework_schedule = framework_blob_schedule(TESTING_FORKS[network])
    target, maximum, _ = framework_schedule

    with ExitStack() as stack:
        BlockchainTestFixture._schedule_blob_params(stack, load, network)
        assert spec_blob_schedule(load) == framework_schedule
        assert derived_blob_constants(load) == (
            per_blob * target,
            per_blob * maximum,
        )

    assert spec_blob_schedule(load) == spec_schedule
    assert derived_blob_constants(load) == spec_derived


@pytest.mark.parametrize("network", ["Cancun", "Osaka", "Amsterdam"])
def test_non_bpo_fork_is_left_alone(network: str) -> None:
    """Patch nothing for a fork that is not a BPO fork."""
    load = Load(FORKS[network].short_name)
    gas_costs = load.fork.hardfork.module("vm.gas").GasCosts
    before: dict[str, Any] = dict(vars(gas_costs))

    with ExitStack() as stack:
        BlockchainTestFixture._schedule_blob_params(stack, load, network)
        assert dict(vars(gas_costs)) == before
