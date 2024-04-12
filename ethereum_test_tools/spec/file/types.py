"""
Defines models for interacting with JSON fixture files.
"""
import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import RootModel

from evm_transition_tool import FixtureFormats

from ..blockchain.types import Fixture as BlockchainFixture
from ..blockchain.types import HiveFixture as BlockchainHiveFixture
from ..state.types import Fixture as StateFixture

FixtureFormatsValues = Literal[
    "blockchain_test_hive", "blockchain_test", "state_test", "unset_test_format"
]


class BaseFixturesRootModel(RootModel):
    """
    A base class for defining top-level models that encapsulate multiple test
    fixtures. Each fixture is stored in a dictionary, where each key is a string
    (typically the fixture name) and its corresponding value is a fixture object.
    This is the structure used for blockchain and state JSON fixture files

    This class implements dunder methods and other common functionality to allow
    interaction with the model's fixtures as if they were being accessed directly
    from a dictionary.
    """

    root: Dict[str, Any]

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

    @classmethod
    def from_file(
        cls,
        file_path: Path,
        fixture_format: Optional[FixtureFormats | FixtureFormatsValues] = None,
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
        fixture_format: Optional[FixtureFormats | FixtureFormatsValues] = None,
    ) -> "BaseFixturesRootModel":
        """
        Dynamically create a fixture model from the specified json data and,
        optionally, model format.

        If no format is provided, pydantic attempts to infer the appropriate model.

        If json_data only contains fixtures of one model type, specifying the
        fixture_format will provide a speed-up.
        """
        model_mapping = {
            FixtureFormats.BLOCKCHAIN_TEST: BlockchainFixtures,
            FixtureFormats.BLOCKCHAIN_TEST_HIVE: BlockchainHiveFixtures,
            FixtureFormats.STATE_TEST: StateFixtures,
            FixtureFormats.BLOCKCHAIN_TEST.value: BlockchainFixtures,
            FixtureFormats.BLOCKCHAIN_TEST_HIVE.value: BlockchainHiveFixtures,
            FixtureFormats.STATE_TEST.value: StateFixtures,
        }

        if fixture_format is not None:
            if fixture_format not in model_mapping:
                raise TypeError(f"Unsupported fixture format: {fixture_format}")
            model_class = model_mapping[fixture_format]
        else:
            model_class = cls

        return model_class(root=json_data)


class Fixtures(BaseFixturesRootModel):
    """
    A model that can contain any fixture type.
    """

    root: Dict[str, BlockchainFixture | BlockchainHiveFixture | StateFixture]


class BlockchainFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple blockchain test fixtures in a
    dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for blockchain tests.
    """

    root: Dict[str, BlockchainFixture]


class BlockchainHiveFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple blockchain hive test fixtures in
    a dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for blockchain hive tests.
    """

    root: Dict[str, BlockchainHiveFixture]


class StateFixtures(BaseFixturesRootModel):
    """
    Defines a top-level model containing multiple state test fixtures in a
    dictionary of (fixture-name, fixture) pairs. This is the format used in JSON
    fixture files for state tests.
    """

    root: Dict[str, StateFixture]
