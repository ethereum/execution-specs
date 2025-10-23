"""Helper functions to load and run general state tests for Ethereum forks."""

import json
import sys
from io import StringIO
from typing import Any, Dict, Iterable

import pytest
from _pytest.nodes import Item
from pytest import Collector

from ethereum.exceptions import StateWithEmptyAccount
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.statetest import TestCase as StateTestCase
from ethereum_spec_tools.evm_tools.statetest import (
    read_test_case as read_state_test_case,
)
from ethereum_spec_tools.evm_tools.t8n import T8N

from .. import FORKS
from .exceptional_test_patterns import (
    exceptional_state_test_patterns,
)
from .fixtures import Fixture

parser = create_parser()


class StateTest(Item):
    """Single state test case item."""

    test_case: StateTestCase
    test_dict: Dict[str, Any]

    def __init__(
        self,
        *args: Any,
        test_case: StateTestCase,
        test_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Initialize a single test case item."""
        super().__init__(*args, **kwargs)
        self.test_case = test_case
        self.test_dict = test_dict
        self.add_marker(pytest.mark.fork(self.test_case.fork_name))
        self.add_marker("evm_tools")
        self.add_marker("json_state_tests")
        eels_fork = FORKS[test_case.fork_name]["eels_fork"]
        test_patterns = exceptional_state_test_patterns(
            test_case.fork_name, eels_fork
        )
        if any(x.search(test_case.key) for x in test_patterns.slow):
            self.add_marker("slow")

    def runtest(self) -> None:
        """
        Runs a single general state test.
        """
        index = self.test_case.index
        json_fork = self.test_case.fork_name
        test_dict = self.test_dict

        env = test_dict["env"]
        try:
            env["blockHashes"] = {"0": env["previousHash"]}
        except KeyError:
            env["blockHashes"] = {}
        env["withdrawals"] = []

        alloc = test_dict["pre"]

        post = test_dict["post"][json_fork][index]
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

    def collect(self) -> Iterable[Item | Collector]:
        """Collect state test cases inside of this fixture."""
        for test_case in read_state_test_case(
            test_file_path=self.test_file,
            key=self.test_key,
            test=self.test_dict,
        ):
            if test_case.fork_name not in FORKS:
                continue
            name = f"{test_case.index}"
            yield StateTest.from_parent(
                parent=self,
                name=name,
                test_case=test_case,
                test_dict=self.test_dict,
            )
