"""Client-native genesis export for hive test clients."""

import json
from pathlib import Path
from typing import Any, ClassVar, Dict, Generic, List, Self, Set, TypeVar

from pydantic import (
    BaseModel,
    Field,
    SerializerFunctionWrapHandler,
    ValidationError,
    computed_field,
    model_serializer,
)

from execution_testing.base_types import Address, Alloc, CamelModel
from execution_testing.cli.pytest_commands.plugins.execute.eth_config.execute_types import (  # noqa: E501
    GenesisConfig,
)
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainFixtureCommon,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.fixtures.file import Fixtures
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroupBuilder
from execution_testing.forks import Fork, TransitionFork


class GenesisAlloc(Alloc):
    """Alloc that removes `0x` prefix from every address it contains."""

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        serialized = {}
        for addr, account in handler(self).items():
            serialized[addr.replace("0x", "")] = account
        return serialized


ClientGenesisConfigT = TypeVar("ClientGenesisConfigT", bound=BaseModel)


class Genesis(CamelModel, Generic[ClientGenesisConfigT]):
    """Besu's plain genesis.json."""

    header: FixtureHeader
    alloc: GenesisAlloc
    config: ClientGenesisConfigT

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        serialized = handler(self)
        header = serialized.pop("header")
        for k in header:
            serialized[k] = header[k]
        return serialized


def _label_to_camel_case(label: str) -> str:
    """Camel-case a SCREAMING_SNAKE_CASE system contract label."""
    words = label.split("_")
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


class GenesisConfigSystemContracts(GenesisConfig):
    """
    Model that can be inherited to add system contracts at the root level.
    """

    # System contract labels excluded from `system_contracts()`.
    _EXCLUDED_SYSTEM_CONTRACT_LABELS: ClassVar[Set[str]] = {
        "BEACON_ROOTS_ADDRESS",
    }

    # System contract config key overrides.
    _SYSTEM_CONTRACT_KEY_OVERRIDES: ClassVar[Dict[str, str]] = {}

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler
    ) -> Dict[str, object]:
        serialized = super()._serialize(handler)
        if "systemContracts" in serialized:
            system_contracts = serialized.pop("systemContracts")
            assert isinstance(system_contracts, dict)
            for key, address in system_contracts.items():
                serialized[key] = str(address)
        return serialized

    @computed_field  # type: ignore[prop-decorator]
    @property
    def system_contracts(self) -> Dict[str, Address]:
        """Return `{config_key: address}` for the fork's system contracts."""
        contracts: Dict[str, Address] = {}
        for contract in self.fork().system_contracts():
            label = contract.label
            if label is None or label in self._EXCLUDED_SYSTEM_CONTRACT_LABELS:
                continue
            key = self._SYSTEM_CONTRACT_KEY_OVERRIDES.get(
                label, _label_to_camel_case(label)
            )
            contracts[key] = self.system_contract_overrides.get(
                label, contract
            )
        return contracts


class ExportableGenesis(BaseModel):
    """Loads a filled EEST fixture into a client-native genesis model."""

    client_name: ClassVar[str]

    header: FixtureHeader = Field(..., exclude=True)
    alloc: Alloc = Field(..., exclude=True)
    chain_id: int = Field(..., exclude=True)
    fork: Fork | TransitionFork = Field(..., exclude=True)

    @classmethod
    def from_fixture(cls, fixture_path: Path) -> Self:
        """Build an exportable genesis from a filled EEST fixture file."""
        fixture_bytes = fixture_path.read_bytes()

        kwargs: Dict[str, Any] = {}
        try:
            fixtures = Fixtures.model_validate_json(fixture_bytes)
            for _, base_fixture in fixtures.items():
                if isinstance(
                    base_fixture,
                    (BlockchainFixtureCommon, BlockchainEngineFixture),
                ):
                    kwargs = {
                        "header": base_fixture.genesis.model_dump(
                            mode="python"
                        ),
                        "alloc": base_fixture.pre,
                        "chain_id": int(base_fixture.config.chain_id),
                        "fork": base_fixture.config.fork,
                    }
                    break
        except ValidationError:
            pass

        if not kwargs:
            try:
                builder = PreAllocGroupBuilder.model_validate_json(
                    fixture_bytes
                )
                pre_alloc_group = builder.build()
                kwargs = {
                    "header": pre_alloc_group.genesis.model_dump(
                        mode="python"
                    ),
                    "alloc": pre_alloc_group.pre,
                    "chain_id": pre_alloc_group.chain_id,
                    "fork": pre_alloc_group.fork,
                }
            except ValidationError:
                pass

        if not kwargs:
            raise ValueError(
                f"File {fixture_path} does not have a recognizable format."
            )
        return cls.model_validate(kwargs)

    def export_to_folder(self, output_dir: Path) -> List[Path]:
        """Write the client's native genesis files to `output_dir`."""
        output_dir.mkdir(parents=True, exist_ok=True)
        written_paths = []
        for file_name, content in self.model_dump(
            mode="json", by_alias=True, exclude_none=True
        ).items():
            path = output_dir / file_name
            path.write_text(json.dumps(content, indent=4))
            written_paths.append(path)
        return written_paths
