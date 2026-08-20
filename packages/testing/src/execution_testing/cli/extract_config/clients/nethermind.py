"""Models used to generate Nethermind style genesis files."""

from typing import ClassVar, Dict, List, Self, Set

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    computed_field,
    model_serializer,
)
from pydantic.alias_generators import to_pascal

from execution_testing import Address
from execution_testing.base_types import (
    Alloc,
    CamelModel,
    EthereumTestRootModel,
    HexNumber,
    Number,
)
from execution_testing.cli.pytest_commands.plugins.execute.eth_config.execute_types import (  # noqa: E501
    ForkActivationTimes,
    GenesisConfig,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import (
    Berlin,
    Byzantium,
    Constantinople,
    ConstantinopleFix,
    Fork,
    FromForkValidatable,
    Istanbul,
    London,
    Osaka,
    Shanghai,
    SpuriousDragon,
    TangerineWhistle,
    TransitionFork,
)

from ..exportable_genesis import ExportableGenesis


class NethermindForkConfigBlobSchedule(CamelModel):
    """Nethrmind representation of the blob schedule items."""

    target_blobs_per_block: HexNumber = Field(..., alias="target")
    max_blobs_per_block: HexNumber = Field(..., alias="max")
    base_fee_update_fraction: HexNumber
    timestamp: HexNumber


class NethermindGenesisConfigBlobSchedule(
    EthereumTestRootModel, FromForkValidatable
):
    """Blob schedule appearing in the genesis config."""

    root: List[NethermindForkConfigBlobSchedule]

    def append_fork(self, fork: Fork, timestamp: int) -> None:
        """Append a given fork at the given timestamp."""
        blob_schedule = fork.blob_schedule()
        if blob_schedule is None:
            return
        last = blob_schedule.last()
        if last is None:
            return
        schedule = NethermindForkConfigBlobSchedule.model_validate(
            {
                "max": last.max_blobs_per_block,
                "target": last.target_blobs_per_block,
                "base_fee_update_fraction": last.base_fee_update_fraction,
                "timestamp": timestamp,
            }
        )
        self.root.append(schedule)

    @classmethod
    def from_fork(cls, fork: Fork) -> Self:
        """Instantiate from a `Fork`."""
        blob_schedules: Self = cls(root=[])
        blob_schedules.append_fork(fork, timestamp=0)
        return blob_schedules

    @classmethod
    def from_transition_fork(cls, transition_fork: TransitionFork) -> Self:
        """Instantiate from a `TransitionFork`."""
        blob_schedules: Self = cls(root=[])
        blob_schedules.append_fork(
            transition_fork.transitions_from(), timestamp=0
        )
        blob_schedules.append_fork(
            transition_fork.transitions_to(),
            timestamp=transition_fork.at_timestamp,
        )
        return blob_schedules


def _fork_and_ancestors(fork: Fork) -> List[Fork]:
    """
    Return `fork` and every one of its ancestors: some forks (e.g.
    Tangerine Whistle, Petersburg) contribute no EIP of their own to
    `_enabled_eips`, so they never show up as another EIP's
    `_enabling_forks` directly and must be found via ancestry instead.
    """
    forks = [fork]
    parent = fork.parent()
    while parent is not None:
        forks.append(parent)
        parent = parent.parent()
    return forks


EXTRAS_BY_FORK: Dict[Fork, Dict[str, str]] = {
    TangerineWhistle: {
        "eip150Transition": "0x0",
    },
    SpuriousDragon: {
        "eip160Transition": "0x0",
        "eip161abcTransition": "0x0",
        "eip161dTransition": "0x0",
    },
    Byzantium: {
        "eip658Transition": "0x0",
    },
    Constantinople: {
        "eip1283Transition": "0x0",
    },
    ConstantinopleFix: {
        "eip1283DisableTransition": "0x0",
    },
    Istanbul: {
        "eip2200Transition": "0x0",
    },
    Berlin: {
        "eip2565Transition": "0x0",
        "eip2718Transition": "0x0",
        "eip2929Transition": "0x0",
    },
    London: {
        "eip3238Transition": "0x0",
        "eip3541Transition": "0x0",
    },
    Shanghai: {
        "eip3651TransitionTimestamp": "0x0",
    },
    Osaka: {
        "eip7823TransitionTimestamp": "0x0",
    },
}

# Unconditional: present regardless of the target fork, not tied to any
# EIP's activation.
_ALWAYS_EXTRAS: Dict[str, str] = {
    "eip7934MaxRlpBlockSize": "0x800000",
}


class NethermindEIPActivationTimes(ForkActivationTimes):
    """EIP activation times."""

    root: Dict[Fork, HexNumber]  # type: ignore[assignment]

    _SKIPPED_EIPS: ClassVar[List[int]] = [
        2,
        7,
        161,
        170,
        196,
        197,
        198,
        649,
        1234,
        3675,
        7516,
        7691,
        8070,
    ]

    @model_serializer(mode="plain")
    def _serialize(self) -> Dict[str, str]:  # type: ignore[override]
        """
        Convert fork names and override the ones in the `_CONFIG_KEY_OVERRIDES`
        dict.
        """
        serialized = {}
        active_forks: set = set()
        for fork, activation_time in self.root.items():
            for enabling_fork in fork._enabling_forks:
                active_forks.update(_fork_and_ancestors(enabling_fork))
            if fork.eip() in self._SKIPPED_EIPS:
                continue
            suffix = (
                "TransitionTimestamp"
                if list(fork._enabling_forks)[0]._fork_by_timestamp
                else "Transition"
            )
            keys = self._CONFIG_KEY_OVERRIDES.get(
                fork, f"{fork.name().lower()}{suffix}"
            )
            for key in [keys] if isinstance(keys, str) else keys:
                serialized[key] = str(HexNumber(activation_time))

        extras: Dict[str, str] = dict(_ALWAYS_EXTRAS)
        for active_fork in active_forks:
            extras.update(EXTRAS_BY_FORK.get(active_fork, {}))

        return serialized | extras

    @classmethod
    def from_fork(cls, fork: Fork) -> Self:
        """
        Build the fork-activation map for `fork`: every ancestor active from
        genesis.
        """
        return cls(dict.fromkeys(fork._enabled_eips, HexNumber(0)))

    @classmethod
    def from_transition_fork(cls, transition_fork: TransitionFork) -> Self:
        """
        Build the fork-activation map for `fork`: every ancestor active from
        genesis, plus the transition target at its configured block/time.
        """
        from_eips = transition_fork.transitions_from()._enabled_eips
        to_eips = transition_fork.transitions_to()._enabled_eips
        activation_time = HexNumber(
            transition_fork.at_timestamp or transition_fork.at_block
        )
        times = dict.fromkeys(to_eips, HexNumber(0))
        times.update(dict.fromkeys(to_eips - from_eips, activation_time))
        return cls(times)


class Pricing(BaseModel):
    """Base pricing."""

    name: ClassVar[str]


class PricingLinear(Pricing):
    """Linear pricing."""

    base: int
    word: int

    name: ClassVar[str] = "linear"


class PricingBN128Pairing(Pricing):
    """Linear pricing."""

    base: int
    pair: int

    name: ClassVar[str] = "alt_bn128_pairing"


class PricingBlake2(Pricing):
    """Linear pricing."""

    gas_per_round: int

    name: ClassVar[str] = "blake2_f"


class PricingModexp(Pricing):
    """Linear pricing."""

    divisor: int

    name: ClassVar[str] = "modexp"


class NethermindPrecompile(BaseModel):
    """Nethermind precompile definition."""

    name: str
    pricing: (
        PricingLinear | PricingBN128Pairing | PricingBlake2 | PricingModexp
    )

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        precompile_dict = handler(self)
        precompile_dict["pricing"] = {
            self.pricing.name: precompile_dict["pricing"]
        }
        return {"builtin": precompile_dict}


PRECOMPILES = {
    Address(1): NethermindPrecompile(
        name="ecrecover", pricing=PricingLinear(base=3000, word=0)
    ),
    Address(2): NethermindPrecompile(
        name="sha256", pricing=PricingLinear(base=60, word=12)
    ),
    Address(3): NethermindPrecompile(
        name="ripemd160", pricing=PricingLinear(base=600, word=120)
    ),
    Address(4): NethermindPrecompile(
        name="identity", pricing=PricingLinear(base=15, word=3)
    ),
    Address(5): NethermindPrecompile(
        name="modexp", pricing=PricingModexp(divisor=20)
    ),
    Address(6): NethermindPrecompile(
        name="alt_bn128_add", pricing=PricingLinear(base=500, word=0)
    ),
    Address(7): NethermindPrecompile(
        name="alt_bn128_mul", pricing=PricingLinear(base=40000, word=0)
    ),
    Address(8): NethermindPrecompile(
        name="alt_bn128_pairing",
        pricing=PricingBN128Pairing(base=100000, pair=80000),
    ),
    Address(9): NethermindPrecompile(
        name="blake2_f", pricing=PricingBlake2(gas_per_round=1)
    ),
}


class NethermindPrecompileWithActivation(BaseModel):
    """Nethermind precompile with activation definition."""

    precompile: NethermindPrecompile
    activate_at: HexNumber | None

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        precompile_dict = handler(self)
        if "activate_at" in precompile_dict:
            precompile_dict["precompile"]["builtin"]["activate_at"] = (
                precompile_dict["activate_at"]
            )
        return precompile_dict["precompile"]


class NethermindPrecompiles(EthereumTestRootModel, FromForkValidatable):
    """List of precompiles activated with the config."""

    root: Dict[Address, NethermindPrecompileWithActivation]

    @classmethod
    def from_precompiles(
        cls,
        to_precompiles: List[Address],
        from_precompiles: Set[Address] | None = None,
        activation_time: int = 0,
    ) -> Self:
        """Get the precompiles in the genesis config for a given fork."""
        if from_precompiles is None:
            from_precompiles = set()
        precompiles = {}
        for precompile in to_precompiles:
            if precompile not in PRECOMPILES:
                continue
            activation: int | None = None
            if int.from_bytes(precompile) > 4:
                activation = (
                    0 if precompile in from_precompiles else activation_time
                )
            precompiles[precompile] = NethermindPrecompileWithActivation(
                precompile=PRECOMPILES[precompile], activate_at=activation
            )
        return cls(precompiles)

    @classmethod
    def from_fork(cls, fork: Fork) -> Self:
        """Get the precompiles in the genesis config for a given fork."""
        return cls.from_precompiles(fork.precompiles())

    @classmethod
    def from_transition_fork(cls, transition_fork: TransitionFork) -> Self:
        """Get the precompiles in the genesis config for a given fork."""
        return cls.from_precompiles(
            transition_fork.transitions_to().precompiles(),
            set(transition_fork.transitions_from().precompiles()),
            transition_fork.at_timestamp or transition_fork.at_block,
        )


class NethermindGenesisConfig(GenesisConfig):
    """Nethermind's genesis `config` block."""

    ethash: Dict[str, str] = Field(default_factory=dict, exclude=True)
    terminal_total_difficulty: int | None = Field(None, exclude=True)
    chain_id: HexNumber = Field(
        serialization_alias="chainID",
        validation_alias=AliasChoices("chainID", "chainId"),
    )
    fork_activation_times: NethermindEIPActivationTimes = Field(...)
    blob_schedule: NethermindGenesisConfigBlobSchedule = Field(
        ..., exclude_if=lambda v: not v.root
    )  # type: ignore[assignment]
    deposit_contract_address: Address = Address(
        0x00000000219AB540356CBB839CBE05303D7705FA
    )
    maximum_extra_data_size: HexNumber = HexNumber(0x400)

    precompiles: NethermindPrecompiles

    @computed_field(alias="maxCodeSize")  # type: ignore[prop-decorator]
    @property
    def _max_code_size(self) -> int:
        return self.fork().max_code_size()

    @computed_field(alias="maxCodeSizeTransition")  # type: ignore[prop-decorator]
    @property
    def _max_code_size_timestamp(self) -> HexNumber:
        return HexNumber(0)


class NethermindConfigGenesis(FixtureHeader):
    """Fixture header using nethermind specifications."""

    fee_recipient: Address = Field(..., serialization_alias="author")

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        serialized = handler(self)
        serialized["seal"] = {
            "ethereum": {
                "nonce": serialized.pop("nonce"),
                "mixHash": serialized.pop("mixHash"),
            }
        }
        serialized.pop("bloom")
        serialized.pop("gasUsed")
        serialized.pop("hash")
        serialized.pop("number")
        serialized.pop("receiptTrie")
        serialized.pop("stateRoot")
        serialized.pop("transactionsTrie")
        serialized.pop("uncleHash")
        serialized.pop("withdrawalsRoot", None)
        serialized.pop("requestsHash", None)
        serialized.pop("blockAccessListHash", None)
        serialized.pop("slotNumber", None)

        return serialized


class NethermindChainSpec(CamelModel):
    """Nethermind chain spec using Nethermind's config format."""

    version: Number = Field(default=Number(1))
    header: NethermindConfigGenesis = Field(serialization_alias="genesis")
    alloc: Alloc = Field(serialization_alias="accounts")
    config: NethermindGenesisConfig = Field(serialization_alias="params")

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        serialized = handler(self)
        serialized["engine"] = {
            "Ethash": {
                "params": {
                    "minimumDifficulty": "0x20000",
                    "difficultyBoundDivisor": "0x800",
                    "durationLimit": "0x0d",
                    "homesteadTransition": "0x0",
                    "eip100bTransition": "0x0",
                    "daoHardforkBeneficiary": (
                        "0xbf4ed7b27f1d666546e30d74d50d173d20bca754"
                    ),
                    "blockReward": {"0x0": "0x1BC16D674EC80000"},
                    "difficultyBombDelays": {"0x0": 700000},
                }
            }
        }
        serialized["accounts"] = serialized["accounts"] | serialized[
            "params"
        ].pop("precompiles")

        return serialized


class NethermindNodeConfigModel(BaseModel):
    """Base for Nethermind's own PascalCase-keyed node `config.json`."""

    model_config = ConfigDict(
        alias_generator=to_pascal,
        populate_by_name=True,
        validate_default=True,
        extra="forbid",
    )


class NethermindInitConfig(NethermindNodeConfigModel):
    """Nethermind's `Init` config section."""

    web_sockets_enabled: bool = True
    use_mem_db: bool = True
    chain_spec_path: str = "/chainspec/test.json"
    base_db_path: str = "nethermind_db/hive"
    log_file_name: str = "/hive.logs.txt"


class NethermindJsonRpcConfig(NethermindNodeConfigModel):
    """Nethermind's `JsonRpc` config section."""

    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8545
    gas_cap: int = 50_000_000
    web_sockets_port: int = 8546
    jwt_secret_file: str = "/jwt.secret"
    enabled_modules: List[str] = [
        "Debug",
        "Eth",
        "Subscribe",
        "Trace",
        "TxPool",
        "Web3",
        "Personal",
        "Proof",
        "Net",
        "Parity",
        "Health",
        "Admin",
        "Testing",
    ]
    additional_rpc_urls: List[str] = [
        "http://0.0.0.0:8550|http;ws|debug;net;eth;subscribe;engine;"
        "web3;client;admin|no-auth",
        "http://0.0.0.0:8551|http;ws|debug;net;eth;subscribe;engine;"
        "web3;client;admin",
    ]


class NethermindNetworkConfig(NethermindNodeConfigModel):
    """Nethermind's `Network` config section."""

    discovery_port: int = 30303
    p2p_port: int = 30303
    external_ip: str = "127.0.0.1"


class NethermindHiveConfig(NethermindNodeConfigModel):
    """Nethermind's `Hive` config section."""

    chain_file: str = "/chain.rlp"
    genesis_file_path: str = "/genesis.json"
    blocks_dir: str = "/blocks"
    keys_dir: str = "/keys"


class NethermindSyncConfig(NethermindNodeConfigModel):
    """Nethermind's `Sync` config section."""

    snap_serving_enabled: bool = True
    snap_sync: bool = False


class NethermindDiscoveryConfig(NethermindNodeConfigModel):
    """Nethermind's `Discovery` config section."""

    discovery_version: str = "All"


class NethermindMergeConfig(NethermindNodeConfigModel):
    """Nethermind's `Merge` config section."""

    enabled: bool = True
    terminal_total_difficulty: str = "0"


class NethermindTxPoolConfig(NethermindNodeConfigModel):
    """Nethermind's `TxPool` config section."""

    blobs_support: str = "StorageWithReorgs"


class NethermindNodeConfig(NethermindNodeConfigModel, FromForkValidatable):
    """
    Nethermind's own node `config.json`, passed to the client via
    `--config` and pointing it at the chain spec produced alongside it.
    """

    init: NethermindInitConfig = Field(default_factory=NethermindInitConfig)
    json_rpc: NethermindJsonRpcConfig = Field(
        default_factory=NethermindJsonRpcConfig
    )
    network: NethermindNetworkConfig = Field(
        default_factory=NethermindNetworkConfig
    )
    hive: NethermindHiveConfig = Field(default_factory=NethermindHiveConfig)
    sync: NethermindSyncConfig = Field(default_factory=NethermindSyncConfig)
    discovery: NethermindDiscoveryConfig = Field(
        default_factory=NethermindDiscoveryConfig
    )
    merge: NethermindMergeConfig = Field(default_factory=NethermindMergeConfig)
    tx_pool: NethermindTxPoolConfig | None = Field(
        None, exclude_if=lambda v: v is None
    )

    @classmethod
    def from_fork_or_transition(cls, fork: Fork | TransitionFork) -> Self:
        """
        Build the node config for `fork`, enabling `TxPool` once the fork
        supports blobs.
        """
        target_fork = fork.transitions_to()
        return cls(
            tx_pool=(
                NethermindTxPoolConfig()
                if target_fork.supports_blobs()
                else None
            )
        )


class NethermindExportableGenesis(ExportableGenesis):
    """Genesis exporter matching Nethermind's hive `mapper.jq`."""

    client_name: ClassVar[str] = "nethermind"

    @computed_field(alias="chainspec.json")  # type: ignore[prop-decorator]
    @property
    def chainspec(self) -> NethermindChainSpec:
        """Construct Nethermind's native genesis model."""
        return NethermindChainSpec(
            header=self.header.model_dump(mode="python"),
            alloc=self.alloc.model_dump(mode="python"),
            config=NethermindGenesisConfig.from_fork_or_transition(
                fork=self.fork,
                chain_id=self.chain_id,
                precompiles=self.fork,
            ),
        )

    @computed_field(alias="config.json")  # type: ignore[prop-decorator]
    @property
    def config(self) -> NethermindNodeConfig:
        """Construct Nethermind's own node config, passed via `--config`."""
        return NethermindNodeConfig.model_validate(self.fork)
