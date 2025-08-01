import json
import os
from typing import Any, Dict

from ethereum.utils.hexadecimal import hex_to_bytes


class NoTestsFound(Exception):
    """
    An exception thrown when the test for a particular fork isn't
    available in the json fixture
    """


def load_test_transaction(
    test_dir: str, test_file: str, network: str
) -> Dict[str, Any]:
    pure_test_file = os.path.basename(test_file)
    test_name = os.path.splitext(pure_test_file)[0]
    path = os.path.join(test_dir, test_file)

    with open(path, "r") as fp:
        json_data = json.load(fp)[f"{test_name}"]

    tx_rlp = hex_to_bytes(json_data["txbytes"])
    try:
        test_result = json_data["result"][network]
    except KeyError:
        raise NoTestsFound(f"No tests found for {network} in {test_file}")

    return {"tx_rlp": tx_rlp, "test_result": test_result}
