"""Models used to generate Geth style genesis files."""

from typing import ClassVar, Dict, List, Set

from pydantic import Field, computed_field

from execution_testing import Address
from execution_testing.cli.pytest_commands.plugins.execute.eth_config.execute_types import (  # noqa: E501
    ForkActivationTimes,
    GenesisConfigBlobSchedule,
)
from execution_testing.forks import (
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


class GethForkActivationTimes(ForkActivationTimes):
    """Fork activation times for Geth."""

    # Fork config key overrides.
    _CONFIG_KEY_OVERRIDES: ClassVar[Dict[Fork, str | List[str]]] = {
        TangerineWhistle: "eip150Block",
        SpuriousDragon: ["eip155Block", "eip158Block"],
        Paris: [],
    }


class GethGenesisConfigBlobSchedule(GenesisConfigBlobSchedule):
    """Blob schedule appearing in the genesis config."""

    exclude_identical_schedules: ClassVar[bool] = True


class GethGenesisConfig(GenesisConfigSystemContracts):
    """Geth's genesis `config` block."""

    dao_fork_support: bool = True
    terminal_total_difficulty_passed: bool = Field(True, exclude=False)
    deposit_contract_address: Address = Address(
        0x00000000219AB540356CBB839CBE05303D7705FA
    )
    fork_activation_times: GethForkActivationTimes = Field(...)
    blob_schedule: GethGenesisConfigBlobSchedule = Field(
        ..., exclude_if=lambda v: not v
    )

    _EXCLUDED_SYSTEM_CONTRACT_LABELS: ClassVar[Set[str]] = {
        "BEACON_ROOTS_ADDRESS",
        "HISTORY_STORAGE_ADDRESS",
        "BUILDER_DEPOSIT_CONTRACT_ADDRESS",
        "BUILDER_EXIT_CONTRACT_ADDRESS",
        "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS",
        "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS",
    }


class GethGenesis(Genesis[GethGenesisConfig]):
    """Geth genesis using Geth's config format."""

    pass


class GethExportableGenesis(ExportableGenesis):
    """Genesis exporter matching Geth's hive `mapper.jq`."""

    client_name: ClassVar[str] = "go-ethereum"

    @computed_field(alias="genesis.json")  # type: ignore[prop-decorator]
    @property
    def genesis(self) -> GethGenesis:
        """Construct Geth's native genesis model."""
        return GethGenesis(
            header=self.header,
            alloc=self.alloc.model_dump(mode="json"),
            config=GethGenesisConfig.from_fork_or_transition(
                fork=self.fork, chain_id=self.chain_id
            ),
        )
