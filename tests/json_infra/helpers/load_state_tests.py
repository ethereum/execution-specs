import json
import os
import sys
from glob import glob
from io import StringIO
from typing import Dict, Generator

import pytest

from ethereum.exceptions import StateWithEmptyAccount
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.statetest import read_test_cases
from ethereum_spec_tools.evm_tools.t8n import T8N

from .. import FORKS
from .exceptional_test_patterns import exceptional_state_test_patterns

parser = create_parser()


def fetch_state_tests(json_fork: str) -> Generator:
    """
    Fetches all the general state tests from the given directory
    """
    # Filter FORKS based on fork_option parameter
    eels_fork = FORKS[json_fork]["eels_fork"]
    test_dirs = FORKS[json_fork]["state_test_dirs"]

    test_patterns = exceptional_state_test_patterns(json_fork, eels_fork)

    # Get all the files to iterate over from both eest_tests_path and ethereum_tests_path
    all_jsons = []
    for test_dir in test_dirs:
        all_jsons.extend(
            glob(os.path.join(test_dir, "**/*.json"), recursive=True)
        )

    for test_file_path in all_jsons:
        test_cases = read_test_cases(test_file_path)

        for test_case in test_cases:
            if test_case.fork_name != json_fork:
                continue

            test_case_dict = {
                "test_file": test_case.path,
                "test_key": test_case.key,
                "index": test_case.index,
                "json_fork": json_fork,
            }

            if any(x.search(test_case.key) for x in test_patterns.slow):
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


def run_state_test(test_case: Dict[str, str]) -> None:
    """
    Runs a single general state test
    """
    test_file = test_case["test_file"]
    test_key = test_case["test_key"]
    index = test_case["index"]
    json_fork = test_case["json_fork"]
    with open(test_file) as f:
        tests = json.load(f)

    env = tests[test_key]["env"]
    try:
        env["blockHashes"] = {"0": env["previousHash"]}
    except KeyError:
        env["blockHashes"] = {}
    env["withdrawals"] = []

    alloc = tests[test_key]["pre"]

    post = tests[test_key]["post"][json_fork][index]
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
