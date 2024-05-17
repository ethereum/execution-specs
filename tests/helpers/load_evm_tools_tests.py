import json
import os
import sys
from io import StringIO
from typing import Dict, Generator, Optional, Tuple

import pytest

from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.statetest import read_test_cases
from ethereum_spec_tools.evm_tools.t8n import T8N

parser = create_parser()


def fetch_evm_tools_tests(
    test_dir: str,
    fork_name: str,
    slow_tests: Optional[Tuple[str, ...]] = None,
) -> Generator:
    """
    Fetches all the general state tests from the given directory
    """
    if slow_tests is None:
        slow_tests = tuple()

    for root, _, files in os.walk(test_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            test_file_path = os.path.join(root, filename)
            test_cases = read_test_cases(test_file_path)
            for test_case in test_cases:
                if test_case.fork_name != fork_name:
                    continue

                test_case_dict = {
                    "test_file": test_case.path,
                    "test_key": test_case.key,
                    "index": test_case.index,
                }

                if test_case.key in slow_tests:
                    yield pytest.param(test_case_dict, marks=pytest.mark.slow)
                else:
                    yield test_case_dict


def idfn(test_case: Dict) -> str:
    """
    Identify the test case
    """
    if isinstance(test_case, dict):
        folder_name = test_case["test_file"].split("/")[-2]
        test_key = test_case["test_key"]
        index = test_case["index"]

        return f"{folder_name} - {test_key} - {index}"


def load_evm_tools_test(test_case: Dict[str, str], fork_name: str) -> None:
    """
    Runs a single general state test
    """
    test_file = test_case["test_file"]
    test_key = test_case["test_key"]
    index = test_case["index"]
    with open(test_file) as f:
        tests = json.load(f)

    env = tests[test_key]["env"]
    try:
        env["blockHashes"] = {"0": env["previousHash"]}
    except KeyError:
        env["blockHashes"] = {}
    env["withdrawals"] = []

    alloc = tests[test_key]["pre"]

    post = tests[test_key]["post"][fork_name][index]
    post_hash = post["hash"]
    d = post["indexes"]["data"]
    g = post["indexes"]["gas"]
    v = post["indexes"]["value"]

    tx = {}
    for k, value in tests[test_key]["transaction"].items():
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
        f"{fork_name}",
    ]
    t8n_options = parser.parse_args(t8n_args)

    t8n = T8N(t8n_options, sys.stdout, in_stream)
    t8n.apply_body()

    assert hex_to_bytes(post_hash) == t8n.result.state_root
