"""Helper functions to load and run general state tests for Ethereum forks."""

import json
import sys
from io import StringIO
from typing import Any, Dict, Iterable, List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from pytest import Collector

from ethereum.exceptions import StateWithEmptyAccount
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.statetest import read_test_case
from ethereum_spec_tools.evm_tools.t8n import T8N

from .. import FORKS
from ..stash_keys import desired_forks_key
from .exceptional_test_patterns import (
    exceptional_state_test_patterns,
)
from .fixtures import Fixture, FixturesFile, FixtureTestItem

parser = create_parser()


class StateTest(FixtureTestItem):
    """Single state test case item."""

    index: int
    fork_name: str

    def __init__(
        self,
        *args: Any,
        index: int,
        fork_name: str,
        **kwargs: Any,
    ) -> None:
        """Initialize a single test case item."""
        super().__init__(*args, **kwargs)
        self.index = index
        self.fork_name = fork_name
        self.add_marker(pytest.mark.fork(self.fork_name))
        self.add_marker("evm_tools")
        self.add_marker("json_state_tests")
        eels_fork = FORKS[fork_name].short_name

        # Mark tests with exceptional markers
        test_patterns = exceptional_state_test_patterns(fork_name, eels_fork)
        if any(x.search(self.nodeid) for x in test_patterns.slow):
            self.add_marker("slow")

    @property
    def state_test_fixture(self) -> "StateTestFixture":
        """Return the state test fixture this test belongs to."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, StateTestFixture)
        return parent

    @property
    def test_key(self) -> str:
        """Return the key of the state test fixture in the fixture file."""
        return self.state_test_fixture.test_key

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which the test fixture was collected."""
        return self.state_test_fixture.fixtures_file

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load test from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def runtest(self) -> None:
        """
        Runs a single general state test.
        """
        json_fork = self.fork_name
        test_dict = self.test_dict

        env = test_dict["env"]
        try:
            env["blockHashes"] = {"0": env["previousHash"]}
        except KeyError:
            env["blockHashes"] = {}
        env["withdrawals"] = []

        alloc = test_dict["pre"]

        post = test_dict["post"][self.fork_name][self.index]
        post_hash = post["hash"]
        d = post["indexes"]["data"]
        g = post["indexes"]["gas"]
        v = post["indexes"]["value"]

        tx = {}
        for k, value in test_dict["transaction"].items():
            if k == "data":
                tx["input"] = value[d]
            elif k == "gasLimit":
                tx["gas"] = value[g]
            elif k == "value":
                tx[k] = value[v]
            elif k == "accessLists":
                if value[d] is not None:
                    tx["accessList"] = value[d]
            else:
                tx[k] = value

        txs = [tx]

        in_stream = StringIO(
            json.dumps(
                {
                    "env": env,
                    "alloc": alloc,
                    "txs": txs,
                }
            )
        )

        # Run the t8n tool
        t8n_args = [
            "t8n",
            "--input.alloc",
            "stdin",
            "--input.env",
            "stdin",
            "--input.txs",
            "stdin",
            "--state.fork",
            f"{json_fork}",
            "--state-test",
        ]
        t8n_options = parser.parse_args(t8n_args)

        try:
            t8n = T8N(t8n_options, sys.stdout, in_stream)
        except StateWithEmptyAccount as e:
            pytest.xfail(str(e))

        t8n.run_state_test()

        if "expectException" in post:
            assert 0 in t8n.txs.rejected_txs
            return

        assert hex_to_bytes(post_hash) == t8n.result.state_root


class StateTestFixture(Fixture, Collector):
    """
    State test fixture from a JSON file that can contain multiple test
    cases.
    """

    @classmethod
    def is_format(cls, test_dict: Dict[str, Any]) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        if "env" not in test_dict:
            return False
        if "pre" not in test_dict:
            return False
        if "transaction" not in test_dict:
            return False
        if "post" not in test_dict:
            return False
        return True

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which the test fixture was collected."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, FixturesFile)
        return parent

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load test from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def collect(self) -> Iterable[Item | Collector]:
        """Collect state test cases inside of this fixture."""
        desired_forks: List[str] = self.config.stash.get(desired_forks_key, [])
        for test_case in read_test_case(
            test_file_path=self.test_file,
            key=self.test_key,
            test=self.test_dict,
        ):
            # The has_desired_fork method is used to skip the entire
            # fixture file if it does not feature any of the desired
            # forks. The below check is performed on the individual
            # test cases within a fixture file in order to keep
            # nothing other than the desired forks.
            if test_case.fork_name not in desired_forks:
                continue
            name = f"{test_case.fork_name}::{test_case.index}"
            yield StateTest.from_parent(
                parent=self,
                name=name,
                index=test_case.index,
                fork_name=test_case.fork_name,
            )

    @classmethod
    def has_desired_fork(
        cls, test_dict: Dict[str, Any], config: Config
    ) -> bool:
        """
        Check if the collector fork list has at least
        one fork in the desired fork list.
        """
        desired_forks = config.stash.get(desired_forks_key, None)
        if desired_forks is None:
            return True

        for network in test_dict["post"].keys():
            if network in desired_forks:
                return True
        return False
