"""Defines models for interacting with JSON fixture files."""

import json
from pathlib import Path
from typing import Annotated, Any, Dict, Optional

from pydantic import Discriminator, Tag

from ethereum_test_base_types import EthereumTestRootModel

from .base import FixtureFormat
from .blockchain import EngineFixture as BlockchainEngineFixture
from .blockchain import Fixture as BlockchainFixture
from .eof import Fixture as EOFFixture
from .state import Fixture as StateFixture
from .transaction import Fixture as TransactionFixture

FixtureModel = (
    BlockchainFixture | BlockchainEngineFixture | StateFixture | EOFFixture | TransactionFixture
)


class BaseFixturesRootModel(EthereumTestRootModel):
    """
    A base class for defining top-level models that encapsulate multiple test
    fixtures. Each fixture is stored in a dictionary, where each key is a string
    (typically the fixture name) and its corresponding value is a fixture object.
    This is the structure used for blockchain and state JSON fixture files.

    This class implements dunder methods and other common functionality to allow
    interaction with the model's fixtures as if they were being accessed directly
    from a dictionary.
    """

    root: Dict[str, Any]

    def __setitem__(self, key: str, value: Any):  # noqa: D105
        self.root[key] = value

    def __getitem__(self, item):  # noqa: D105
        return self.root[item]

    def __iter__(self):  # noqa: D105
        return iter(self.root)

    def __contains__(self, item):  # noqa: D105
        return item in self.root

    def __len__(self):  # noqa: D105
        return len(self.root)

    def keys(self):  # noqa: D102
        return self.root.keys()

    def values(self):  # noqa: D102
        return self.root.values()

    def items(self):  # noqa: D102
        return self.root.items()

    def collect_into_file(self, file_path: Path):
        """
        For all formats, we join the fixtures as json into a single file.

        Note: We don't use pydantic model_dump_json() on the Fixtures object as we
        add the hash to the info field on per-fixture basis.
        """
        json_fixtures: Dict[str, Dict[str, Any]] = {}
        for name, fixture in self.items():
            json_fixtures[name] = fixture.json_dict_with_info()
        with open(file_path, "w") as f:
            json.dump(json_fixtures, f, indent=4)

    @classmethod
    def from_file(
        cls,
        file_path: Path,
        fixture_format: Optional[FixtureFormat] = None,
    ) -> "BaseFixturesRootModel":
        """
        Dynamically create a fixture model from the specified json file and,
        optionally, model format.
        """
        with open(file_path, "r") as f:
            json_data = json.load(f)
        return cls.from_json_data(json_data, fixture_format)

    @classmethod
    def from_json_data(
        cls,
        json_data: Dict[str, Any],
        fixture_format: Optional[FixtureFormat] = None,
    ) -> "BaseFixturesRootModel":
        """
        Dynamically create a fixture model from the specified json data and,
        optionally, model format.

        If no format is provided, pydantic attempts to infer the appropriate model.

        If json_data only contains fixtures of one model type, specifying the
        fixture_format will provide a speed-up.
        """
        model_mapping = {
            BlockchainFixture: BlockchainFixtures,
            BlockchainEngineFixture: BlockchainEngineFixtures,
            StateFixture: StateFixtures,
            TransactionFixture: TransactionFixtures,
            EOFFixture: EOFFixtures,
        }

        if fixture_format is not None:
            if fixture_format not in model_mapping:
                raise TypeError(f"Unsupported fixture format: {fixture_format}")
            model_class = model_mapping[fixture_format]
        else:
            model_class = cls

        return model_class(root=json_data)


def fixture_format_discriminator(v: Any) -> str | None:
    """Discriminator function that returns the model type as a string."""
    if v is None:
        return None
    if isinstance(v, dict):
        info_dict = v["_info"]
    elif hasattr(v, "info"):
        info_dict = v.info
    return info_dict.get("fixture_format")


class Fixtures(BaseFixturesRootModel):
    """A model that can contain any fixture type."""

    root: Dict[
        str,
        Annotated[
            Annotated[BlockchainFixture, Tag(BlockchainFixture.fixture_format_name)]
            | Annotated[BlockchainEngineFixture, Tag(BlockchainEngineFixture.fixture_format_name)]
            | Annotated[StateFixture, Tag(StateFixture.fixture_format_name)]
            | Annotated[TransactionFixture, Tag(TransactionFixture.fixture_format_name)],
            Discriminator(fixture_format_discriminator),
        ],
    ]


class BlockchainFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple blockchain test fixtures in a
    dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for blockchain tests.
    """

    root: Dict[str, BlockchainFixture]


class BlockchainEngineFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple blockchain engine test fixtures in
    a dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for blockchain engine tests.
    """

    root: Dict[str, BlockchainEngineFixture]


class StateFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple state test fixtures in a
    dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for state tests.
    """

    root: Dict[str, StateFixture]


class TransactionFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple transaction test fixtures in a
    dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for transaction tests.
    """

    root: Dict[str, TransactionFixture]


class EOFFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple state test fixtures in a
    dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for EOF tests.
    """

    root: Dict[str, EOFFixture]
