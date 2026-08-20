"""Models used to generate Besu style genesis files."""

from typing import ClassVar, Dict, List, Set

from pydantic import AliasChoices, Field, computed_field

from execution_testing.cli.pytest_commands.plugins.execute.eth_config.execute_types import (  # noqa: E501
    ForkActivationTimes,
)
from execution_testing.forks import (
    ConstantinopleFix,
    Fork,
    Paris,
    SpuriousDragon,
    TangerineWhistle,
)

from ..exportable_genesis import (
    ExportableGenesis,
    Genesis,
    GenesisConfigSystemContracts,
)


class BesuForkActivationTimes(ForkActivationTimes):
    """Fork activation times for Besu."""

    # Fork config key overrides.
    _CONFIG_KEY_OVERRIDES: ClassVar[Dict[Fork, str | List[str]]] = {
        TangerineWhistle: "eip150Block",
        SpuriousDragon: ["eip155Block", "eip158Block"],
        Paris: "mergeNetsplitBlock",
        ConstantinopleFix: "constantinopleFixBlock",
    }


class BesuGenesisConfig(GenesisConfigSystemContracts):
    """Besu's genesis `config` block."""

    chain_id: int = Field(
        serialization_alias="chainID",
        validation_alias=AliasChoices("chainID", "chainId"),
    )
    fork_activation_times: BesuForkActivationTimes = Field(...)

    _EXCLUDED_SYSTEM_CONTRACT_LABELS: ClassVar[Set[str]] = {
        "BEACON_ROOTS_ADDRESS",
        "HISTORY_STORAGE_ADDRESS",
    }

    _SYSTEM_CONTRACT_KEY_OVERRIDES: ClassVar[Dict[str, str]] = {
        "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": (
            "withdrawalRequestContractAddress"
        ),
        "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": (
            "consolidationRequestContractAddress"
        ),
        "BUILDER_DEPOSIT_CONTRACT_ADDRESS": (
            "builderDepositRequestContractAddress"
        ),
        "BUILDER_EXIT_CONTRACT_ADDRESS": ("builderExitRequestContractAddress"),
    }


class BesuGenesis(Genesis[BesuGenesisConfig]):
    """Besu genesis using besu's config format."""

    pass


class BesuExportableGenesis(ExportableGenesis):
    """Genesis exporter matching Besu's hive `mapper.jq`."""

    client_name: ClassVar[str] = "besu"

    @computed_field(alias="genesis.json")  # type: ignore[prop-decorator]
    @property
    def genesis(self) -> BesuGenesis:
        """Construct Besu's native genesis model."""
        return BesuGenesis(
            header=self.header,
            alloc=self.alloc.model_dump(mode="json"),
            config=BesuGenesisConfig.from_fork_or_transition(
                fork=self.fork, chain_id=self.chain_id
            ),
        )
