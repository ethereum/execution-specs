"""Types used to test `eth_config`."""

from binascii import crc32
from pathlib import Path
from typing import Dict, Self, Set

import yaml
from pydantic import BaseModel, Field

from ethereum_test_base_types import (
    Address,
    CamelModel,
    EthereumTestRootModel,
    ForkHash,
    Hash,
    HexNumber,
)
from ethereum_test_forks import Fork
from ethereum_test_rpc import (
    EthConfigResponse,
    ForkConfig,
    ForkConfigBlobSchedule,
)


class AddressOverrideDict(EthereumTestRootModel):
    """
    Dictionary with overrides to the default addresses specified for each fork.
    Required for testnets or devnets which have a different location of precompiles or system
    contracts.
    """

    root: Dict[Address, Address]


class ForkConfigBuilder(BaseModel):
    """Class to describe a current or next fork + bpo configuration."""

    fork: Fork
    activation_time: int
    chain_id: int
    address_overrides: AddressOverrideDict
    bpo_blob_schedule_override: ForkConfigBlobSchedule | None = None

    @property
    def blob_schedule(self) -> ForkConfigBlobSchedule | None:
        """Get the blob schedule."""
        if self.bpo_blob_schedule_override is not None:
            return self.bpo_blob_schedule_override
        return ForkConfigBlobSchedule.from_fork_blob_schedule(
            self.fork.blob_schedule()[self.fork.name()]
        )

    def add(
        self, fork_or_blob_schedule: Fork | ForkConfigBlobSchedule, activation_time: int
    ) -> Self:
        """Add or change the base fork or blob schedule."""
        if isinstance(fork_or_blob_schedule, ForkConfigBlobSchedule):
            return self.__class__(
                fork=self.fork,
                activation_time=activation_time,
                chain_id=self.chain_id,
                address_overrides=self.address_overrides,
                bpo_blob_schedule_override=fork_or_blob_schedule,
            )
        else:
            fork: Fork = fork_or_blob_schedule
            return self.__class__(
                fork=fork,
                activation_time=activation_time,
                chain_id=self.chain_id,
                address_overrides=self.address_overrides,
                bpo_blob_schedule_override=None
                if fork.blob_schedule() is not None
                else self.bpo_blob_schedule_override,
            )

    def with_fork_id(self, fork_id: ForkHash) -> Self:
        """Set the fork_id for this builder."""
        return self.__class__(
            fork=self.fork,
            activation_time=self.activation_time,
            chain_id=self.chain_id,
            address_overrides=self.address_overrides,
            bpo_blob_schedule_override=self.bpo_blob_schedule_override,
        )

    @property
    def precompiles(self) -> Dict[str, Address]:
        """Get the precompiles."""
        precompiles = {}
        for a in self.fork.precompiles():
            label = a.label
            if a in self.address_overrides.root:
                a = self.address_overrides.root[a]
            precompiles[f"{label}"] = a
        return precompiles

    @property
    def system_contracts(self) -> Dict[str, Address]:
        """Get the system contracts."""
        system_contracts = {}
        for a in self.fork.system_contracts():
            label = a.label
            if a in self.address_overrides.root:
                a = self.address_overrides.root[a]
            system_contracts[f"{label}"] = a
        return system_contracts

    def get_config(self, fork_id: ForkHash) -> ForkConfig:
        """
        Get the current and next fork configurations given the current time and the network
        configuration.
        """
        return ForkConfig(
            activation_time=self.activation_time,
            blob_schedule=self.blob_schedule,
            chain_id=self.chain_id,
            fork_id=fork_id,
            precompiles=self.precompiles,
            system_contracts=self.system_contracts,
        )


def calculate_fork_id(genesis_hash: Hash, activation_times: Set[int]) -> ForkHash:
    """Calculate the fork Id given the genesis hash and each fork activation times."""
    buffer = bytes(genesis_hash)
    for activation_time in sorted(activation_times):
        buffer += activation_time.to_bytes(length=8, byteorder="big")
    return ForkHash(crc32(buffer))


class NetworkConfig(CamelModel):
    """Ethereum network config."""

    chain_id: HexNumber
    genesis_hash: Hash
    fork_activation_times: Dict[int, Fork]
    bpo_fork_activation_times: Dict[int, ForkConfigBlobSchedule] = {}
    address_overrides: AddressOverrideDict = Field(default_factory=lambda: AddressOverrideDict({}))

    def get_eth_config(self, current_time: int) -> EthConfigResponse:
        """Get the current and next forks based on the given time."""
        all_activations: Dict[int, Fork | ForkConfigBlobSchedule] = {
            **self.fork_activation_times,
            **self.bpo_fork_activation_times,
        }
        network_kwargs = {
            "chain_id": self.chain_id,
            "address_overrides": self.address_overrides,
        }
        current_config_builder: ForkConfigBuilder = ForkConfigBuilder(
            fork=all_activations[0],
            activation_time=0,
            **network_kwargs,
        )
        current_activation_times: Set[int] = set()

        next_config_builder: ForkConfigBuilder | None = None
        next_activation_times: Set[int] = set()
        next_processed: bool = False

        last_config_builder: ForkConfigBuilder | None = None
        last_activation_times: Set[int] = set()

        for activation_time in all_activations.keys():
            if activation_time == 0:
                continue
            if activation_time <= current_time:
                current_config_builder = current_config_builder.add(
                    all_activations[activation_time], activation_time
                )
                current_activation_times.add(activation_time)
                next_activation_times.add(activation_time)
                last_activation_times.add(activation_time)
            else:
                if not next_processed:
                    next_config_builder = current_config_builder.add(
                        all_activations[activation_time], activation_time
                    )
                    next_activation_times.add(activation_time)
                    next_processed = True

                    last_config_builder = current_config_builder.add(
                        all_activations[activation_time], activation_time
                    )
                    last_activation_times.add(activation_time)
                else:
                    assert last_config_builder is not None, "Last config builder is None"
                    last_config_builder = last_config_builder.add(
                        all_activations[activation_time], activation_time
                    )
                    last_activation_times.add(activation_time)

        current_config = current_config_builder.get_config(
            calculate_fork_id(self.genesis_hash, current_activation_times)
        )
        kwargs = {
            "current": current_config,
        }
        if next_config_builder is not None:
            next_config = next_config_builder.get_config(
                calculate_fork_id(self.genesis_hash, next_activation_times)
            )
            kwargs["next"] = next_config
        if last_config_builder is not None:
            last_config = last_config_builder.get_config(
                calculate_fork_id(self.genesis_hash, last_activation_times)
            )
            kwargs["last"] = last_config

        return EthConfigResponse(**kwargs)


class NetworkConfigFile(EthereumTestRootModel):
    """Root model to describe a file that contains network configurations."""

    root: Dict[str, NetworkConfig]

    @classmethod
    def from_yaml(cls, path: Path) -> Self:
        """Read the network configuration from a yaml file."""
        with path.open("r") as file:
            config_data = yaml.safe_load(file)
            return cls.model_validate(config_data)
