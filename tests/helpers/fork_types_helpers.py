import json
import os
from typing import Any, Dict

from ethereum.utils.hexadecimal import hex_to_bytes


def load_test_transaction(
    test_dir: str, test_file: str, network: str
) -> Dict[str, Any]:
    pure_test_file = os.path.basename(test_file)
    test_name = os.path.splitext(pure_test_file)[0]
    path = os.path.join(test_dir, test_file)

    with open(path, "r") as fp:
        json_data = json.load(fp)[f"{test_name}"]

    tx_rlp = hex_to_bytes(json_data["txbytes"])

    test_result = json_data["result"][network]

    return {"tx_rlp": tx_rlp, "test_result": test_result}
