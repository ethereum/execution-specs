"""Types used to test `eth_config`."""

import re
from binascii import crc32
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, ClassVar, Dict, List, Self, Set

import yaml
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    PrivateAttr,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from execution_testing.base_types import (
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
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import (
    Fork,
    FromForkValidatable,
    Frontier,
    London,
    SpuriousDragon,
    TangerineWhistle,
    TransitionFork,
)
from execution_testing.rpc import (
    EthConfigResponse,
    ForkConfig,
    ForkConfigBlobSchedule,
)
from execution_testing.test_types import Alloc, Environment


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


def _fork_ancestry(fork: Fork) -> List[Fork]:
    """Return `fork` and every one of its ancestors, closest first."""
    chain = [fork]
    parent = fork.parent()
    while parent is not None:
        chain.append(parent)
        parent = parent.parent()
    return chain


def _label_to_camel_case(label: str) -> str:
    """Camel-case a SCREAMING_SNAKE_CASE system contract label."""
    words = label.split("_")
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def _fork_key(fork: Fork) -> str:
    """CamelCase `fork.ruleset_name()`."""
    return _label_to_camel_case(fork.ruleset_name() or fork.name())


def _has_own_config_entry(fork: Fork) -> bool:
    """Whether `fork` has a parent and a non-`None` `ruleset_name()`."""
    return fork.parent() is not None and fork.ruleset_name() is not None


class ForkActivationTimes(EthereumTestRootModel, FromForkValidatable):
    """Fork activation times."""

    root: Dict[Fork, int]

    # Fork config key overrides.
    _CONFIG_KEY_OVERRIDES: ClassVar[Dict[Fork, str | List[str]]] = {
        TangerineWhistle: "eip150Block",
        SpuriousDragon: ["eip155Block", "eip158Block"],
    }

    @model_serializer(mode="plain")
    def _serialize(self) -> Dict[str, int]:
        """
        Convert fork names and override the ones in the `_CONFIG_KEY_OVERRIDES`
        dict.
        """
        serialized = {}
        for fork, activation_time in self.root.items():
            if not _has_own_config_entry(fork):
                continue
            suffix = "Time" if fork._fork_by_timestamp else "Block"
            keys = self._CONFIG_KEY_OVERRIDES.get(
                fork, f"{_fork_key(fork)}{suffix}"
            )
            for key in [keys] if isinstance(keys, str) else keys:
                serialized[key] = activation_time

        return serialized

    @classmethod
    def from_fork(cls, fork: Fork) -> Self:
        """
        Build the fork-activation map for `fork`: every ancestor active from
        genesis.
        """
        return cls(dict.fromkeys(_fork_ancestry(fork), 0))

    @classmethod
    def from_transition_fork(cls, transition_fork: TransitionFork) -> Self:
        """
        Build the fork-activation map for `fork`: every ancestor active from
        genesis, plus the transition target at its configured block/time.
        """
        times = dict.fromkeys(
            _fork_ancestry(transition_fork.transitions_from()), 0
        )
        transition = transition_fork.at_timestamp or transition_fork.at_block
        times[transition_fork.transitions_to()] = transition
        return cls(times)

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


class GenesisConfigBlobSchedule(EthereumTestRootModel, FromForkValidatable):
    """Blob schedule appearing in the genesis config."""

    root: Dict[
        Annotated[Fork, PlainSerializer(_fork_key)], ForkConfigBlobSchedule
    ]

    exclude_identical_schedules: ClassVar[bool] = False

    @classmethod
    def from_fork_or_transition(cls, fork: Fork | TransitionFork) -> Self:
        """Get the blob schedule in the genesis config for a given fork."""
        fork_activation_times = ForkActivationTimes.model_validate(fork)
        blob_schedules = {}
        last_blob_schedule: ForkConfigBlobSchedule | None = None
        for f in sorted(fork_activation_times.root):
            if f.supports_blobs():
                current_blob_schedule = ForkConfigBlobSchedule(
                    target_blobs_per_block=f.target_blobs_per_block(),
                    max_blobs_per_block=f.max_blobs_per_block(),
                    base_fee_update_fraction=f.blob_base_fee_update_fraction(),
                )
                if (
                    last_blob_schedule is None
                    or not cls.exclude_identical_schedules
                    or last_blob_schedule != current_blob_schedule
                ):
                    blob_schedules[f] = current_blob_schedule
                last_blob_schedule = current_blob_schedule
        return cls(root=blob_schedules)

    def get(self, key: Fork) -> ForkConfigBlobSchedule | None:
        """Get a given fork's blob schedule if it exists, otherwise None."""
        return self.root.get(key)


class NetworkConfig(CamelModel):
    """Ethereum network config."""

    chain_id: HexNumber
    genesis_hash: Hash
    fork_activation_times: ForkActivationTimes
    blob_schedule: GenesisConfigBlobSchedule = Field(
        default_factory=lambda: GenesisConfigBlobSchedule(root={})
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

    ethash: Dict[str, str] = Field(default_factory=dict)
    chain_id: int
    terminal_total_difficulty: int | None = None
    terminal_total_difficulty_passed: bool = Field(True, exclude=True)
    # Per-label address overrides for the fork's system contracts.
    system_contract_overrides: Dict[str, Address] = Field(
        default_factory=dict, exclude=True
    )
    fork_activation_times: ForkActivationTimes = Field(...)
    blob_schedule: GenesisConfigBlobSchedule = Field(
        ..., exclude_if=lambda v: not v
    )
    _fork: Fork | None = PrivateAttr(default=None)

    fork_synonyms: ClassVar[Dict[str, str | None]] = {
        # TODO: Ideally add fork synonyms, but not important for now.
        "eip150": None,
        "eip155": None,
        "eip158": None,
        "petersburg": None,
        "mergeNetsplit": "paris",
    }

    @classmethod
    def from_fork_or_transition(
        cls, fork: Fork | TransitionFork, chain_id: int, **kwargs: Any
    ) -> Self:
        """Get the genesis config for a given fork."""
        instance = cls(
            chain_id=chain_id,
            terminal_total_difficulty=0 if fork > London else None,
            terminal_total_difficulty_passed=fork > London,
            fork_activation_times=fork,
            blob_schedule=fork,
            **kwargs,
        )
        instance._fork = fork.transitions_from()
        return instance

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        serialized = handler(self)
        fork_activation_times = serialized.pop("forkActivationTimes")
        for key, value in fork_activation_times.items():
            serialized[key] = value
        return serialized

    @property
    def address_overrides(self) -> AddressOverrideDict:
        """Get the address overrides."""
        overrides: Dict[Address, Address] = {}
        for contract in self.fork().system_contracts():
            if contract.label is None:
                continue
            override = self.system_contract_overrides.get(contract.label)
            if override is not None and override != contract:
                overrides[contract] = override
        return AddressOverrideDict(overrides)

    def fork(self) -> Fork:
        """Return the latest fork active at genesis."""
        if self._fork is None:
            current_fork: Fork = Frontier
            for (
                fork,
                activation_block_time,
            ) in self.fork_activation_times.root.items():
                if activation_block_time == 0 and fork > current_fork:
                    current_fork = fork
            self._fork = current_fork
        return self._fork

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
                            # Remove deprecated fork keys that have no synonym
                            data.pop(key)
                            continue
                    fork_activation_times[stripped_key] = data.pop(key)
            if fork_activation_times:
                data["forkActivationTimes"] = fork_activation_times
        return data

    @model_validator(mode="before")
    @classmethod
    def preprocess_system_contract_addresses(cls, data: Any) -> Any:
        """
        Move `<label>Address`-style root keys into
        `systemContractOverrides`, keyed by the SCREAMING_SNAKE_CASE
        label.
        """
        if isinstance(data, dict):
            overrides = dict(data.get("systemContractOverrides", {}))
            for key in list(data.keys()):
                if key == "systemContractOverrides" or not key.endswith(
                    "Address"
                ):
                    continue
                label = re.sub(r"(?<!^)(?=[A-Z])", "_", key).upper()
                overrides[label] = data.pop(key)
            if overrides:
                data["systemContractOverrides"] = overrides
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

    def model_post_init(self, __context: Any) -> None:
        """
        Seed the alloc's commitment scheme from the genesis fork.
        """
        super().model_post_init(__context)
        self.alloc.migrate_state_commitment(
            self.config.fork().state_commitment()
        )

    @cached_property
    def hash(self) -> Hash:
        """Calculate the genesis hash."""
        dumped_genesis = self.model_dump(
            mode="json",
            exclude={"config", "alloc", "nonce", "mixhash", "parent_hash"},
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
