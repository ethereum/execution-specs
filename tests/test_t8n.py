import json
import os
from typing import Any, Dict, List

import pytest

from ethereum.base_types import U64, U256, Uint
from ethereum.utils.hexadecimal import (
    Hash32,
    hex_to_bytes,
    hex_to_u256,
    hex_to_uint,
)
from ethereum_spec_tools.evm_tools import parser
from ethereum_spec_tools.evm_tools.t8n import T8N
from ethereum_spec_tools.evm_tools.utils import FatalException

testdata_dir = "tests/t8n_testdata"


def find_test_fixtures() -> Any:
    with open(os.path.join(testdata_dir, "commands.json")) as f:
        data = json.load(f)

    for key, value in data.items():

        final_args = []
        for arg in value["args"]:
            if "__BASEDIR__" in arg:
                final_args.append(arg.replace("__BASEDIR__", testdata_dir))
            else:
                final_args.append(arg)
        yield {
            "name": key,
            "args": final_args,
            "expected": os.path.join(testdata_dir, key),
            "success": value["success"],
        }


def idfn(test_case: Dict) -> str:
    return test_case["name"]


def get_rejected_indices(rejected: Dict) -> List[int]:
    rejected_indices = []
    for item in rejected:
        rejected_indices.append(item["index"])
    return rejected_indices


def t8n_tool_test(test_case: Dict) -> None:
    options = parser.parse_args(test_case["args"])

    try:
        t8n_tool = T8N(options)
        t8n_tool.apply_body()
    except Exception as e:
        raise FatalException

    json_result = t8n_tool.result.to_json()
    with open(test_case["expected"], "r") as f:
        data = json.load(f)

    # with open("temp.json", "w") as f:
    #     json.dump(json_state, f, indent=4)

    if "rejected" in data["result"] and len(data["result"]["rejected"]) != 0:
        assert len(json_result["rejected"]) != 0

        rejected_indices = get_rejected_indices(json_result["rejected"])
        expected_rejected_indices = get_rejected_indices(
            data["result"]["rejected"]
        )

        assert sorted(rejected_indices) == sorted(expected_rejected_indices)
    else:
        assert len(json_result["rejected"]) == 0

    assert t8n_tool.hex_to_root(
        json_result["stateRoot"]
    ) == t8n_tool.hex_to_root(data["result"]["stateRoot"])
    assert t8n_tool.hex_to_root(json_result["txRoot"]) == t8n_tool.hex_to_root(
        data["result"]["txRoot"]
    )
    assert t8n_tool.hex_to_root(
        json_result["receiptsRoot"]
    ) == t8n_tool.hex_to_root(data["result"]["receiptsRoot"])
    assert t8n_tool.Bloom(
        hex_to_bytes(json_result["logsBloom"])
    ) == t8n_tool.Bloom(hex_to_bytes(data["result"]["logsBloom"]))
    assert hex_to_u256(json_result["gasUsed"]) == hex_to_u256(
        data["result"]["gasUsed"]
    )
    assert hex_to_uint(json_result["currentDifficulty"]) == hex_to_uint(
        data["result"]["currentDifficulty"]
    )


@pytest.mark.parametrize(
    "test_case",
    find_test_fixtures(),
    ids=idfn,
)
def test_t8n(test_case: Dict) -> None:
    if test_case["success"]:
        t8n_tool_test(test_case)
    else:
        with pytest.raises(FatalException):
            t8n_tool_test(test_case)
