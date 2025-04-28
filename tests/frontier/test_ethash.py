import json
import pkgutil
from typing import cast

import pytest

from ethereum.frontier.blocks import Header
from ethereum.frontier.fork import validate_proof_of_work
from tests.helpers.load_state_tests import Load


@pytest.mark.slow
@pytest.mark.parametrize(
    "block_file_name",
    [
        "block_1.json",
        "block_1234567.json",
        "block_12964999.json",
    ],
)
def test_pow_validation_block_headers(block_file_name: str) -> None:
    block_str_data = cast(
        bytes, pkgutil.get_data("ethereum", f"assets/blocks/{block_file_name}")
    ).decode()
    block_json_data = json.loads(block_str_data)

    load = Load("Frontier", "frontier")
    header: Header = load.json_to_header(block_json_data)
    validate_proof_of_work(header)


# TODO: Once there is a method to download blocks, test the proof-of-work
# validation for the following blocks in each hardfork (except London as the
# current PoW algo won't work from London):
#   * Start of hardfork
#   * two random blocks inside the hardfork
#   * End of hardfork
