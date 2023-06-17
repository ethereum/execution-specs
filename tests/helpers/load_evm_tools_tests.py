import json
import os
import sys
from io import StringIO
from typing import Dict, Generator, Tuple

import pytest

from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools import parser, subparsers
from ethereum_spec_tools.evm_tools.t8n import T8N, t8n_arguments
from ethereum_spec_tools.evm_tools.utils import FatalException

t8n_arguments(subparsers)


def fetch_evm_tools_tests(
    test_dir: str,
    fork_name: str,
    slow_tests: Tuple[str, ...] = None,
) -> Generator:
    """
    Fetches all the general state tests from the given directory
    """
    if slow_tests is None:
        slow_tests = tuple()

    for root, _, files in os.walk(test_dir):
        for filename in files:
            if filename.endswith(".json"):
                test_file_path = os.path.join(root, filename)
                with open(test_file_path) as test_file:
                    tests = json.load(test_file)

                for key, test in tests.items():
                    slow = True if key in slow_tests else False
                    if fork_name in test["post"]:
                        for transition in test["post"][fork_name]:
                            post_hash = transition["hash"]
                            exception = transition.get("expectException")
                            indexes = transition["indexes"]
                            d = indexes["data"]
                            g = indexes["gas"]
                            v = indexes["value"]

                            test_case = {
                                "test_file": test_file_path,
                                "test_key": key,
                                "d": d,
                                "g": g,
                                "v": v,
                                "post_hash": post_hash,
                                "exception": exception,
                            }
                            if slow:
                                yield pytest.param(
                                    test_case, marks=pytest.mark.slow
                                )
                            else:
                                yield test_case


def idfn(test_case: Dict) -> str:
    """Identify the test case"""

    if isinstance(test_case, dict):
        folder_name = test_case["test_file"].split("/")[-2]
        test_key = test_case["test_key"]
        d = test_case["d"]
        g = test_case["g"]
        v = test_case["v"]

        return f"{folder_name} - {test_key} - d{d}g{g}v{v}"


def load_evm_tools_test(test_case: Dict[str, str], fork_name: str) -> None:
    """
    Runs a single general state test
    """
    test_file = test_case["test_file"]
    test_key = test_case["test_key"]
    post_hash = test_case["post_hash"]
    exception = test_case.get("exception")
    d = test_case["d"]
    g = test_case["g"]
    v = test_case["v"]
    with open(test_file) as f:
        test = json.load(f)

    env = test[test_key]["env"]
    env["blockHashes"] = {"0": env["previousHash"]}
    env["withdrawals"] = []

    tx = {}
    for k, value in test[test_key]["transaction"].items():
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

    sys.stdin = StringIO(
        json.dumps(
            {
                "env": env,
                "alloc": test[test_key]["pre"],
                "txs": [tx],
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
        f"{fork_name}",
    ]
    t8n_options = parser.parse_args(t8n_args)

    t8n = T8N(t8n_options)
    # An unsupported transaction cannot be signed
    # so the t8n tool throws an exception
    if exception == "TR_TypeNotSupported":
        with pytest.raises(FatalException):
            t8n.apply_body()
    else:
        t8n.apply_body()
        assert hex_to_bytes(post_hash) == t8n.result.state_root
