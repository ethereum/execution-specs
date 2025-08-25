"""Defines models for interacting with JSON fixture files."""

import json
from pathlib import Path
from typing import Any, Dict

from filelock import FileLock
from pydantic import SerializeAsAny

from ethereum_test_base_types import EthereumTestRootModel

from .base import BaseFixture


class Fixtures(EthereumTestRootModel):
    """
    A base class for defining top-level models that encapsulate multiple test
    fixtures. Each fixture is stored in a dictionary, where each key is a string
    (typically the fixture name) and its corresponding value is a fixture object.
    This is the structure used for blockchain and state JSON fixture files.

    This class implements dunder methods and other common functionality to allow
    interaction with the model's fixtures as if they were being accessed directly
    from a dictionary.
    """

    root: Dict[str, SerializeAsAny[BaseFixture]]

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
        lock_file_path = file_path.with_suffix(".lock")
        with FileLock(lock_file_path):
            if file_path.exists():
                with open(file_path, "r") as f:
                    json_fixtures = json.load(f)
            for name, fixture in self.items():
                json_fixtures[name] = fixture.json_dict_with_info()

            with open(file_path, "w") as f:
                json.dump(dict(sorted(json_fixtures.items())), f, indent=4)
