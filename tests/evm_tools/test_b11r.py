import json
import os
import sys
from typing import Any, Dict, List

import pytest

from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.b11r import B11R
from ethereum_spec_tools.evm_tools.utils import FatalException
from tests.helpers import TEST_FIXTURES

B11R_TEST_PATH = TEST_FIXTURES["evm_tools_testdata"]["fixture_path"]

IGNORE_TESTS: List[str] = []

parser = create_parser()


def find_test_fixtures() -> Any:
    with open(os.path.join(B11R_TEST_PATH, "b11r_commands.json")) as f:
        data = json.load(f)

    for key, value in data.items():
        final_args = []
        for arg in value["args"]:
            final_args.append(arg.replace("__BASEDIR__", B11R_TEST_PATH))
        yield {
            "name": key,
            "args": final_args,
            "expected": os.path.join(B11R_TEST_PATH, key),
            "success": value["success"],
        }


def idfn(test_case: Dict) -> str:
    return test_case["name"]


def get_rejected_indices(rejected: Dict) -> List[int]:
    rejected_indices = []
    for item in rejected:
        rejected_indices.append(item["index"])
    return rejected_indices


def b11r_tool_test(test_case: Dict) -> None:
    options = parser.parse_args(test_case["args"])

    try:
        b11r_tool = B11R(options, sys.stdout, sys.stdin)
        b11r_tool.build_block()
    except Exception as e:
        raise FatalException(e)

    # json_result = b11r_tool.result.to_json()
    with open(test_case["expected"], "r") as f:
        data = json.load(f)

    assert hex_to_bytes(data["rlp"]) == b11r_tool.block_rlp
    assert hex_to_bytes(data["hash"]) == b11r_tool.block_hash


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    find_test_fixtures(),
    ids=idfn,
)
def test_b11r(test_case: Dict) -> None:
    if test_case["name"] in IGNORE_TESTS:
        pytest.xfail("Undefined behavior for specs")
    elif test_case["success"]:
        b11r_tool_test(test_case)
    else:
        with pytest.raises(FatalException):
            b11r_tool_test(test_case)
