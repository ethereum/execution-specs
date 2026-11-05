"""Generate hive-compatible genesis files from pre-alloc groups."""

import json
from pathlib import Path
from typing import Self

from pydantic import (
    BaseModel,
    Field,
    SerializerFunctionWrapHandler,
    ValidationError,
    model_serializer,
)

from execution_testing.base_types import Alloc
from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.ruleset import (  # noqa: E501
    ruleset,
)
from execution_testing.fixtures.blockchain import (
    BlockchainEngineFixture,
    BlockchainFixtureCommon,
    FixtureHeader,
)
from execution_testing.fixtures.file import Fixtures
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroup
from execution_testing.forks import Fork


class GenesisState(BaseModel):
    """Model representing genesis state for hive clients."""

    header: FixtureHeader
    alloc: Alloc
    chain_id: int = Field(exclude=True)
    fork: Fork = Field(exclude=True)

    @model_serializer(mode="wrap")
    def serialize_model(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        """Serialize the genesis state model to a dictionary."""
        serialized = handler(self)
        output = serialized["header"]
        output["alloc"] = {
            k.replace("0x", ""): v for k, v in serialized["alloc"].items()
        }
        return output

    @classmethod
    def from_fixture(cls, fixture_path: Path) -> Self:
        """Create a client genesis state from a fixture file."""
        fixture_bytes = fixture_path.read_bytes()

        try:
            fixtures = Fixtures.model_validate_json(fixture_bytes)
            for _, base_fixture in fixtures.items():
                if isinstance(
                    base_fixture,
                    (
                        BlockchainFixtureCommon,
                        BlockchainEngineFixture,
                    ),
                ):
                    return cls(
                        header=base_fixture.genesis,
                        alloc=base_fixture.pre,
                        chain_id=int(base_fixture.config.chain_id),
                        fork=base_fixture.config.fork,
                    )
            raise ValueError(
                f"Fixture {fixture_path} does not contain a genesis"
            )
        except ValidationError:
            pass

        try:
            pre_alloc_group = PreAllocGroup.model_validate_json(fixture_bytes)
            return cls(
                header=pre_alloc_group.genesis,
                alloc=pre_alloc_group.pre,
                chain_id=int(pre_alloc_group.chain_id),
                fork=pre_alloc_group.fork,
            )
        except ValidationError:
            pass

        raise ValueError(
            f"File {fixture_path} does not have a recognizable format."
        )

    def get_client_environment(self) -> dict:
        """Get the env vars to start a client with a fixture."""
        if self.fork not in ruleset:
            raise ValueError(f"Fork '{self.fork}' not found in hive ruleset")

        return {
            "HIVE_CHAIN_ID": str(self.chain_id),
            "HIVE_FORK_DAO_VOTE": "1",
            "HIVE_NODETYPE": "full",
            "HIVE_CHECK_LIVE_PORT": "8545",
            **{k: f"{v:d}" for k, v in ruleset[self.fork].items()},
        }


def generate_hive_files(pre_alloc_folder: Path, hive_folder: Path) -> int:
    """
    Generate hive genesis files from merged pre-alloc groups.

    For each ``{hash}.json`` in *pre_alloc_folder*, write a
    ``{hash}.json`` to *hive_folder* containing::

        {
            "genesis": { ... generic genesis ... },
            "environment": { "HIVE_CHAIN_ID": "1", ... }
        }

    Return the number of files generated.
    """
    hive_folder.mkdir(parents=True, exist_ok=True)
    count = 0

    for group_file in sorted(pre_alloc_folder.glob("*.json")):
        genesis_state = GenesisState.from_fixture(group_file)

        hive_data = {
            "genesis": genesis_state.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
            "environment": (genesis_state.get_client_environment()),
        }

        hive_file = hive_folder / group_file.name
        hive_file.write_text(json.dumps(hive_data, indent=2))
        count += 1

    return count
