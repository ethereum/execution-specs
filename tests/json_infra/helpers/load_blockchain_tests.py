import importlib
import json
import os.path
from glob import glob
from typing import Any, Dict, Generator
from unittest.mock import call, patch

import pytest
from _pytest.mark.structures import ParameterSet
from ethereum_rlp import rlp
from ethereum_rlp.exceptions import RLPException
from ethereum_types.numeric import U64

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import EthereumException, StateWithEmptyAccount
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools.loaders.fixture_loader import Load

from .. import FORKS
from .exceptional_test_patterns import exceptional_blockchain_test_patterns


class NoTestsFoundError(Exception):
    """
    An exception thrown when the test for a particular fork isn't
    available in the json fixture
    """


def run_blockchain_st_test(test_case: Dict, load: Load) -> None:
    test_file = test_case["test_file"]
    test_key = test_case["test_key"]

    with open(test_file, "r") as fp:
        data = json.load(fp)

    json_data = data[test_key]

    if "postState" not in json_data:
        pytest.xfail(f"{test_case} doesn't have post state")

    genesis_header = load.json_to_header(json_data["genesisBlockHeader"])
    parameters = [
        genesis_header,
        (),
        (),
    ]
    if hasattr(genesis_header, "withdrawals_root"):
        parameters.append(())

    if hasattr(genesis_header, "requests_root"):
        parameters.append(())

    genesis_block = load.fork.Block(*parameters)

    genesis_header_hash = hex_to_bytes(json_data["genesisBlockHeader"]["hash"])
    assert keccak256(rlp.encode(genesis_header)) == genesis_header_hash
    genesis_rlp = hex_to_bytes(json_data["genesisRLP"])
    assert rlp.encode(genesis_block) == genesis_rlp

    try:
        state = load.json_to_state(json_data["pre"])
    except StateWithEmptyAccount as e:
        pytest.xfail(str(e))

    chain = load.fork.BlockChain(
        blocks=[genesis_block],
        state=state,
        chain_id=U64(json_data["genesisBlockHeader"].get("chainId", 1)),
    )

    mock_pow = (
        json_data["sealEngine"] == "NoProof" and not load.fork.proof_of_stake
    )

    for json_block in json_data["blocks"]:
        block_exception = None
        for key, value in json_block.items():
            if key.startswith("expectException"):
                block_exception = value
                break

        if block_exception:
            # TODO: Once all the specific exception types are thrown,
            #       only `pytest.raises` the correct exception type instead of
            #       all of them.
            with pytest.raises((EthereumException, RLPException)):
                add_block_to_chain(chain, json_block, load, mock_pow)
            return
        else:
            add_block_to_chain(chain, json_block, load, mock_pow)

    last_block_hash = hex_to_bytes(json_data["lastblockhash"])
    assert keccak256(rlp.encode(chain.blocks[-1].header)) == last_block_hash

    expected_post_state = load.json_to_state(json_data["postState"])
    assert chain.state == expected_post_state
    load.fork.close_state(chain.state)
    load.fork.close_state(expected_post_state)


def add_block_to_chain(
    chain: Any, json_block: Any, load: Load, mock_pow: bool
) -> None:
    (
        block,
        block_header_hash,
        block_rlp,
    ) = load.json_to_block(json_block)

    assert keccak256(rlp.encode(block.header)) == block_header_hash
    assert rlp.encode(block) == block_rlp

    if not mock_pow:
        load.fork.state_transition(chain, block)
    else:
        fork_module = importlib.import_module(
            f"ethereum.{load.fork.fork_module}.fork"
        )
        with patch.object(
            fork_module,
            "validate_proof_of_work",
            autospec=True,
        ) as mocked_pow_validator:
            load.fork.state_transition(chain, block)
            mocked_pow_validator.assert_has_calls(
                [call(block.header)],
                any_order=False,
            )


# Functions that fetch individual test cases
def load_json_fixture(test_file: str, json_fork: str) -> Generator:
    # Extract the pure basename of the file without the path to the file.
    # Ex: Extract "world.json" from "path/to/file/world.json"
    # Extract the filename without the extension. Ex: Extract "world" from
    # "world.json"
    with open(test_file, "r") as fp:
        data = json.load(fp)

        # Search tests by looking at the `network` attribute
        found_keys = []
        for key, test in data.items():
            if "network" not in test:
                continue

            if test["network"] == json_fork:
                found_keys.append(key)

        if not any(found_keys):
            raise NoTestsFoundError

        for _key in found_keys:
            yield {
                "test_file": test_file,
                "test_key": _key,
                "json_fork": json_fork,
            }


def fetch_blockchain_tests(
    json_fork: str,
) -> Generator[Dict | ParameterSet, None, None]:
    # Filter FORKS based on fork_option parameter
    eels_fork = FORKS[json_fork]["eels_fork"]
    test_dirs = FORKS[json_fork]["blockchain_test_dirs"]

    test_patterns = exceptional_blockchain_test_patterns(json_fork, eels_fork)

    # Get all the files to iterate over from both eest_tests_path and ethereum_tests_path
    all_jsons = []
    for test_dir in test_dirs:
        all_jsons.extend(
            glob(os.path.join(test_dir, "**/*.json"), recursive=True)
        )

    files_to_iterate = []
    for full_path in all_jsons:
        if not any(x.search(full_path) for x in test_patterns.expected_fail):
            # If a file or folder is marked for ignore,
            # it can already be dropped at this stage
            files_to_iterate.append(full_path)

    # Start yielding individual test cases from the file list
    for _test_file in files_to_iterate:
        try:
            for _test_case in load_json_fixture(_test_file, json_fork):
                # _identifier could identify files, folders through test_file
                #  individual cases through test_key
                _identifier = (
                    "("
                    + _test_case["test_file"]
                    + "|"
                    + _test_case["test_key"]
                    + ")"
                )
                _test_case["eels_fork"] = eels_fork
                if any(
                    x.search(_identifier) for x in test_patterns.expected_fail
                ):
                    continue
                elif any(x.search(_identifier) for x in test_patterns.slow):
                    yield pytest.param(_test_case, marks=pytest.mark.slow)
                elif any(
                    x.search(_identifier) for x in test_patterns.big_memory
                ):
                    yield pytest.param(_test_case, marks=pytest.mark.bigmem)
                else:
                    yield _test_case
        except NoTestsFoundError:
            # file doesn't contain tests for the given fork
            continue


# Test case Identifier
def idfn(test_case: Dict) -> str:
    if isinstance(test_case, dict):
        folder_name = test_case["test_file"].split("/")[-2]
        # Assign Folder name and test_key to identify tests in output
        return folder_name + " - " + test_case["test_key"]
