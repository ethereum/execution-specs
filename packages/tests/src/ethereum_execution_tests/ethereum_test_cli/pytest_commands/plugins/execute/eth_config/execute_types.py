"""Types used to test `eth_config`."""

from binascii import crc32
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, ClassVar, Dict, List, Self, Set

import yaml
from pydantic import BaseModel, BeforeValidator, Field, model_validator

from ethereum_test_base_types import (
    Address,
    Bytes,
    CamelModel,
    EthereumTestRootModel,
    ForkHash,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
)
from ethereum_test_fixtures.blockchain import FixtureHeader
from ethereum_test_forks import Fork, Frontier
from ethereum_test_rpc import (
    EthConfigResponse,
    ForkConfig,
    ForkConfigBlobSchedule,
)
from ethereum_test_types import Alloc, Environment


class AddressOverrideDict(EthereumTestRootModel):
    """
    Dictionary with overrides to the default addresses specified for each fork.
    Required for testnets or devnets which have a different location of
    precompiles or system contracts.
    """

    root: Dict[Address, Address]


class ForkConfigBuilder(BaseModel):
    """Class to describe a current or next fork + bpo configuration."""

    fork: Fork
    activation_time: int
    chain_id: int
    address_overrides: AddressOverrideDict
    blob_schedule: ForkConfigBlobSchedule | None = None

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
        Get the current and next fork configurations given the current time and
        the network configuration.
        """
        return ForkConfig(
            activation_time=self.activation_time,
            blob_schedule=self.blob_schedule,
            chain_id=self.chain_id,
            fork_id=fork_id,
            precompiles=self.precompiles,
            system_contracts=self.system_contracts,
        )


def calculate_fork_id(
    genesis_hash: Hash, activation_times: Set[int]
) -> ForkHash:
    """
    Calculate the fork Id given the genesis hash and each fork activation
    times.
    """
    buffer = bytes(genesis_hash)
    for activation_time in sorted(activation_times):
        if activation_time == 0:
            continue
        buffer += activation_time.to_bytes(length=8, byteorder="big")
    return ForkHash(crc32(buffer))


class ForkActivationTimes(EthereumTestRootModel[Dict[Fork, int]]):
    """Fork activation times."""

    root: Dict[Fork, int]

    def forks_by_activation_time(self) -> Dict[int, Set[Fork]]:
        """Get the forks by activation time."""
        forks_by_activation_time = defaultdict(set)
        for fork, activation_time in self.root.items():
            forks_by_activation_time[activation_time].add(fork)
        return forks_by_activation_time

    def active_forks(self, current_time: int) -> List[Fork]:
        """Get the active forks."""
        forks_by_activation_time = self.forks_by_activation_time()
        active_forks = []
        for activation_time in sorted(forks_by_activation_time.keys()):
            if activation_time <= current_time:
                active_forks.extend(
                    sorted(forks_by_activation_time[activation_time])
                )
        return active_forks

    def next_forks(self, current_time: int) -> List[Fork]:
        """Get the next forks."""
        forks_by_activation_time = self.forks_by_activation_time()
        next_forks = []
        for activation_time in sorted(forks_by_activation_time.keys()):
            if activation_time > current_time:
                next_forks.extend(
                    sorted(forks_by_activation_time[activation_time])
                )
        return next_forks

    def active_fork(self, current_time: int) -> Fork:
        """Get the active fork."""
        return self.active_forks(current_time)[-1]

    def next_fork(self, current_time: int) -> Fork | None:
        """Get the next fork."""
        next_forks = self.next_forks(current_time)
        if next_forks:
            return next_forks[0]
        return None

    def last_fork(self, current_time: int) -> Fork | None:
        """Get the last fork."""
        next_forks = self.next_forks(current_time)
        if next_forks:
            return next_forks[-1]
        return None

    def __getitem__(self, key: Fork) -> int:
        """Get the activation time for a given fork."""
        return self.root[key]


class NetworkConfig(CamelModel):
    """Ethereum network config."""

    chain_id: HexNumber
    genesis_hash: Hash
    fork_activation_times: ForkActivationTimes
    blob_schedule: Dict[Fork, ForkConfigBlobSchedule] = Field(
        default_factory=dict
    )
    address_overrides: AddressOverrideDict = Field(
        default_factory=lambda: AddressOverrideDict({})
    )

    def get_eth_config(self, current_time: int) -> EthConfigResponse:
        """Get the current and next forks based on the given time."""
        network_kwargs = {
            "chain_id": self.chain_id,
            "address_overrides": self.address_overrides,
        }

        activation_times = set(
            self.fork_activation_times.forks_by_activation_time().keys()
        )

        current_activation_times = {
            activation_time
            for activation_time in activation_times
            if activation_time <= current_time
        }
        next_activation_times = {
            activation_time
            for activation_time in activation_times
            if activation_time > current_time
        }
        active_fork = self.fork_activation_times.active_fork(current_time)
        current_config_builder: ForkConfigBuilder = ForkConfigBuilder(
            fork=active_fork,
            activation_time=self.fork_activation_times[active_fork],
            blob_schedule=self.blob_schedule.get(active_fork),
            **network_kwargs,
        )
        current_config = current_config_builder.get_config(
            calculate_fork_id(self.genesis_hash, current_activation_times)
        )
        kwargs = {"current": current_config}

        next_fork = self.fork_activation_times.next_fork(current_time)
        if next_fork:
            next_config_builder: ForkConfigBuilder = ForkConfigBuilder(
                fork=next_fork,
                activation_time=self.fork_activation_times[next_fork],
                blob_schedule=self.blob_schedule.get(next_fork),
                **network_kwargs,
            )
            kwargs["next"] = next_config_builder.get_config(
                calculate_fork_id(
                    self.genesis_hash,
                    current_activation_times
                    | {sorted(next_activation_times)[0]},
                )
            )

        last_fork = self.fork_activation_times.last_fork(current_time)
        if last_fork:
            last_config_builder: ForkConfigBuilder = ForkConfigBuilder(
                fork=last_fork,
                activation_time=self.fork_activation_times[last_fork],
                blob_schedule=self.blob_schedule.get(last_fork),
                **network_kwargs,
            )
            kwargs["last"] = last_config_builder.get_config(
                calculate_fork_id(
                    self.genesis_hash,
                    current_activation_times | next_activation_times,
                )
            )

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


class GenesisConfig(CamelModel):
    """Config model contained in a Geth-type genesis file."""

    chain_id: int
    terminal_total_difficulty: int
    terminal_total_difficulty_passed: bool
    deposit_contract_address: Address = Address(
        0x00000000219AB540356CBB839CBE05303D7705FA
    )
    fork_activation_times: ForkActivationTimes
    blob_schedule: Dict[Fork, ForkConfigBlobSchedule]

    fork_synonyms: ClassVar[Dict[str, str | None]] = {
        # TODO: Ideally add fork synonyms, but not important for now.
        "eip150": None,
        "eip155": None,
        "eip158": None,
        "petersburg": None,
        "mergeNetsplit": "paris",
    }

    @property
    def address_overrides(self) -> AddressOverrideDict:
        """Get the address overrides."""
        if self.deposit_contract_address == Address(
            0x00000000219AB540356CBB839CBE05303D7705FA
        ):
            return AddressOverrideDict({})
        return AddressOverrideDict(
            {
                Address(
                    0x00000000219AB540356CBB839CBE05303D7705FA
                ): self.deposit_contract_address
            }
        )

    def fork(self) -> Fork:
        """Return the latest fork active at genesis."""
        current_fork: Fork = Frontier
        for (
            fork,
            activation_block_time,
        ) in self.fork_activation_times.root.items():
            if activation_block_time == 0 and fork > current_fork:
                current_fork = fork
        return current_fork

    @model_validator(mode="before")
    @classmethod
    def preprocess_fork_times_blocks(cls, data: Any) -> Any:
        """
        Pre-process the dictionary to put fork block numbers and times in the
        correct format.

        Fork times and block numbers have the following format in the root of
        the object:

        ```
        "berlinBlock": 0,
        "londonBlock": 0,
        ...
        "pragueTime": 0,
        "osakaTime": 1753379304,
        ```

        This function strips the "*Block" and "*Time" part and moves the
        values.
        """
        if isinstance(data, dict):
            fork_activation_times: Dict[str, int] = {}
            for key in list(data.keys()):
                assert isinstance(key, str)
                if key.endswith("Block") or key.endswith("Time"):
                    if key.endswith("Block"):
                        stripped_key = key.removesuffix("Block")
                    else:
                        stripped_key = key.removesuffix("Time")
                    if stripped_key in cls.fork_synonyms:
                        synonym = cls.fork_synonyms[stripped_key]
                        if synonym:
                            stripped_key = synonym
                        else:
                            continue
                    fork_activation_times[stripped_key] = data.pop(key)
            if fork_activation_times:
                data["forkActivationTimes"] = fork_activation_times
        return data


class Genesis(CamelModel):
    """Geth-type genesis file."""

    config: GenesisConfig
    alloc: Alloc
    fee_recipient: Address = Field(validation_alias="coinbase")
    difficulty: HexNumber
    extra_data: Bytes
    gas_limit: HexNumber
    nonce: Annotated[HeaderNonce, BeforeValidator(lambda x: HexNumber(x))]
    mixhash: Hash
    timestamp: Number
    parent_hash: Hash
    base_fee_per_gas: HexNumber = HexNumber(10**9)
    number: HexNumber = HexNumber(0)

    @cached_property
    def hash(self) -> Hash:
        """Calculate the genesis hash."""
        dumped_genesis = self.model_dump(
            mode="json", exclude={"config", "alloc"}
        )
        genesis_fork = self.config.fork()
        env = Environment(**dumped_genesis).set_fork_requirements(genesis_fork)
        genesis_header = FixtureHeader.genesis(
            genesis_fork, env, self.alloc.state_root()
        )
        genesis_header.extra_data = self.extra_data
        genesis_header.nonce = self.nonce
        return genesis_header.block_hash

    def network_config(self) -> NetworkConfig:
        """Get the network config."""
        return NetworkConfig(
            chain_id=self.config.chain_id,
            genesis_hash=self.hash,
            fork_activation_times=self.config.fork_activation_times,
            blob_schedule=self.config.blob_schedule,
            address_overrides=self.config.address_overrides,
        )
