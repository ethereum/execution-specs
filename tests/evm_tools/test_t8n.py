import json
import os
import sys
from typing import Any, Dict, List

import pytest

from ethereum import rlp
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_u256, hex_to_uint
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.t8n import T8N
from ethereum_spec_tools.evm_tools.utils import FatalException
from tests.helpers import TEST_FIXTURES

T8N_TEST_PATH = TEST_FIXTURES["evm_tools_testdata"]["fixture_path"]

IGNORE_TESTS = [
    "t8n/fixtures/expected/26/Merge.json",
]


def find_test_fixtures() -> Any:
    with open(os.path.join(T8N_TEST_PATH, "t8n_commands.json")) as f:
        data = json.load(f)

    for key, value in data.items():
        final_args = []
        for arg in value["args"]:
            final_args.append(arg.replace("__BASEDIR__", T8N_TEST_PATH))
        yield {
            "name": key,
            "args": final_args,
            "expected": os.path.join(T8N_TEST_PATH, key),
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
    parser = create_parser()
    options = parser.parse_args(test_case["args"])

    try:
        t8n_tool = T8N(options, sys.stdout, sys.stdin)
        t8n_tool.apply_body()
    except Exception as e:
        raise FatalException(e) from e

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

    assert t8n_tool.fork.hex_to_root(
        json_result["stateRoot"]
    ) == t8n_tool.fork.hex_to_root(data["result"]["stateRoot"])
    assert t8n_tool.fork.hex_to_root(
        json_result["txRoot"]
    ) == t8n_tool.fork.hex_to_root(data["result"]["txRoot"])
    assert t8n_tool.fork.hex_to_root(
        json_result["receiptsRoot"]
    ) == t8n_tool.fork.hex_to_root(data["result"]["receiptsRoot"])
    assert t8n_tool.fork.Bloom(
        hex_to_bytes(json_result["logsBloom"])
    ) == t8n_tool.fork.Bloom(hex_to_bytes(data["result"]["logsBloom"]))
    assert hex_to_u256(json_result["gasUsed"]) == hex_to_u256(
        data["result"]["gasUsed"]
    )
    assert rlp.encode(t8n_tool.txs.all_txs) == hex_to_bytes(data["txs_rlp"])
    if not t8n_tool.fork.is_after_fork("ethereum.paris"):
        assert hex_to_uint(json_result["currentDifficulty"]) == hex_to_uint(
            data["result"]["currentDifficulty"]
        )
    if t8n_tool.fork.is_after_fork("ethereum.shanghai"):
        assert t8n_tool.fork.hex_to_root(
            json_result["withdrawalsRoot"]
        ) == t8n_tool.fork.hex_to_root(data["result"]["withdrawalsRoot"])

    if "receipts" in data["result"]:
        assert len(json_result["receipts"]) == len(data["result"]["receipts"])
        for t8n_receipt, expected_receipt in zip(
            json_result["receipts"], data["result"]["receipts"]
        ):
            assert t8n_receipt["gasUsed"] == expected_receipt["gasUsed"]
            assert (
                t8n_receipt["transactionHash"]
                == expected_receipt["transactionHash"]
            )


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    find_test_fixtures(),
    ids=idfn,
)
def test_t8n(test_case: Dict) -> None:
    if test_case["name"] in IGNORE_TESTS:
        pytest.xfail("Undefined behavior for specs")
    elif test_case["success"]:
        t8n_tool_test(test_case)
    else:
        with pytest.raises(FatalException):
            t8n_tool_test(test_case)
