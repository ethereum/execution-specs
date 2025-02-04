import json
import os
from glob import glob
from typing import Dict, Generator, Tuple

import pytest

from ethereum.osaka.vm.eof import ContainerContext
from ethereum.osaka.vm.eof.validation import validate_eof_container
from ethereum.osaka.vm.exceptions import InvalidEof
from ethereum.utils.hexadecimal import hex_to_bytes

TEST_DIRS = (
    "tests/fixtures/latest_fork_tests/osaka/eof/eof_tests/eip7692_eof_v1",
    "tests/fixtures/ethereum_tests/EOFTests/",
    "tests/fixtures/latest_fork_tests/osaka/eof/evmone_tests/eof_tests",
)


def fetch_eof_tests(test_dirs: Tuple[str, ...]) -> Generator:
    for test_dir in test_dirs:
        all_jsons = [
            y
            for x in os.walk(test_dir)
            for y in glob(os.path.join(x[0], "*.json"))
        ]

        for full_path in all_jsons:
            # Read the json file and yield the test cases
            with open(full_path, "r") as file:
                data = json.load(file)
                for test in data.keys():
                    try:
                        keys = data[test]["vectors"].keys()
                    except AttributeError:
                        continue
                    for key in keys:
                        yield {
                            "test_file": full_path,
                            "test_name": test,
                            "test_key": key,
                        }


# Test case Identifier
def idfn(test_case: Dict) -> str:
    if isinstance(test_case, dict):
        return (
            test_case["test_file"]
            + " - "
            + test_case["test_name"]
            + " - "
            + test_case["test_key"]
        )


# Run the tests
@pytest.mark.parametrize(
    "test_case",
    fetch_eof_tests(TEST_DIRS),
    ids=idfn,
)
def test_eof(test_case: Dict) -> None:
    test_file = test_case["test_file"]
    test_name = test_case["test_name"]
    test_key = test_case["test_key"]

    with open(test_file, "r") as f:
        test_data = json.load(f)
        test_vector = test_data[test_name]["vectors"][test_key]

    # Extract the test data
    code = hex_to_bytes(test_vector["code"])
    if test_vector.get("containerKind") == "INITCODE":
        context = ContainerContext.INIT
    else:
        context = ContainerContext.RUNTIME

    # TODO: This has to eventually be just Osaka
    try:
        prague_validation = test_vector["results"]["Osaka"]
    except KeyError:
        prague_validation = test_vector["results"]["Prague"]

    if "exception" in prague_validation and prague_validation["result"]:
        raise Exception("Test case has both exception and result")

    if "exception" in prague_validation:
        with pytest.raises(InvalidEof):
            validate_eof_container(code, context)
    else:
        validate_eof_container(code, context)
