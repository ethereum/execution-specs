import json
import os
from typing import List, Sequence, Tuple, Union

import pytest
from ethereum_rlp import Extended, rlp

from ethereum.frontier.fork_types import Bytes, Uint
from ethereum.utils.hexadecimal import hex_to_bytes
from tests.helpers import TEST_FIXTURES

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]


#
# Running ethereum/tests for rlp
#


def convert_to_rlp_native(
    obj: Union[str, int, Sequence[Union[str, int]]]
) -> Extended:
    if isinstance(obj, str):
        return bytes(obj, "utf-8")
    elif isinstance(obj, int):
        return Uint(obj)

    # It's a sequence
    return [convert_to_rlp_native(element) for element in obj]


def ethtest_fixtures_as_pytest_fixtures(
    *test_files: str,
) -> List[Tuple[Extended, Bytes]]:
    base_path = f"{ETHEREUM_TESTS_PATH}/RLPTests/"

    test_data = dict()
    for test_file in test_files:
        with open(os.path.join(base_path, test_file), "r") as fp:
            test_data.update(json.load(fp))

    pytest_fixtures = []
    for test_details in test_data.values():
        if isinstance(test_details["in"], str) and test_details[
            "in"
        ].startswith("#"):
            test_details["in"] = int(test_details["in"][1:])

        pytest_fixtures.append(
            (
                convert_to_rlp_native(test_details["in"]),
                hex_to_bytes(test_details["out"]),
            )
        )

    return pytest_fixtures


@pytest.mark.parametrize(
    "raw_data, expected_encoded_data",
    ethtest_fixtures_as_pytest_fixtures("rlptest.json"),
)
def test_ethtest_fixtures_for_rlp_encoding(
    raw_data: Extended, expected_encoded_data: Bytes
) -> None:
    assert rlp.encode(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    "raw_data, encoded_data",
    ethtest_fixtures_as_pytest_fixtures("RandomRLPTests/example.json"),
)
def test_ethtest_fixtures_for_successfully_rlp_decoding(
    raw_data: Bytes, encoded_data: Bytes
) -> None:
    decoded_data = rlp.decode(encoded_data)
    assert rlp.encode(decoded_data) == encoded_data


@pytest.mark.parametrize(
    "raw_data, encoded_data",
    ethtest_fixtures_as_pytest_fixtures("invalidRLPTest.json"),
)
def test_ethtest_fixtures_for_fails_in_rlp_decoding(
    raw_data: Bytes, encoded_data: Bytes
) -> None:
    with pytest.raises(rlp.DecodingError):
        rlp.decode(encoded_data)
