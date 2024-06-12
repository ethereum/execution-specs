import importlib
import json
import os.path
import re
from glob import glob
from typing import Any, Dict, Generator, Tuple, Union, cast
from unittest.mock import call, patch

import pytest
from _pytest.mark.structures import ParameterSet

from ethereum import rlp
from ethereum.base_types import U64
from ethereum.exceptions import InvalidBlock
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools.loaders.fixture_loader import Load


class NoTestsFound(Exception):
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

    genesis_block = load.fork.Block(*parameters)

    genesis_header_hash = hex_to_bytes(json_data["genesisBlockHeader"]["hash"])
    assert rlp.rlp_hash(genesis_header) == genesis_header_hash
    # FIXME: Re-enable this assertion once the genesis block RLP is
    # correctly encoded for Shanghai.
    # See https://github.com/ethereum/execution-spec-tests/issues/64
    # assert (
    #     rlp.encode(cast(rlp.RLP, genesis_block))
    #     == test_data["genesis_block_rlp"]
    # )

    chain = load.fork.BlockChain(
        blocks=[genesis_block],
        state=load.json_to_state(json_data["pre"]),
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
            with pytest.raises(InvalidBlock):
                add_block_to_chain(chain, json_block, load, mock_pow)
            return
        else:
            add_block_to_chain(chain, json_block, load, mock_pow)

    last_block_hash = hex_to_bytes(json_data["lastblockhash"])
    assert rlp.rlp_hash(chain.blocks[-1].header) == last_block_hash

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

    assert rlp.rlp_hash(block.header) == block_header_hash
    assert rlp.encode(cast(rlp.RLP, block)) == block_rlp

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
def load_json_fixture(test_file: str, network: str) -> Generator:
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

            if test["network"] == network:
                found_keys.append(key)

        if not any(found_keys):
            raise NoTestsFound

        for _key in found_keys:
            yield {
                "test_file": test_file,
                "test_key": _key,
            }


def fetch_state_test_files(
    test_dir: str,
    network: str,
    only_in: Tuple[str, ...] = (),
    slow_list: Tuple[str, ...] = (),
    big_memory_list: Tuple[str, ...] = (),
    ignore_list: Tuple[str, ...] = (),
) -> Generator[Union[Dict, ParameterSet], None, None]:
    all_slow = [re.compile(x) for x in slow_list]
    all_big_memory = [re.compile(x) for x in big_memory_list]
    all_ignore = [re.compile(x) for x in ignore_list]

    # Get all the files to iterate over
    # Maybe from the custom file list or entire test_dir
    files_to_iterate = []
    if len(only_in):
        # Get file list from custom list, if one is specified
        for test_path in only_in:
            files_to_iterate.append(os.path.join(test_dir, test_path))
    else:
        # If there isn't a custom list, iterate over the test_dir
        all_jsons = [
            y
            for x in os.walk(test_dir)
            for y in glob(os.path.join(x[0], "*.json"))
        ]

        for full_path in all_jsons:
            if not any(x.search(full_path) for x in all_ignore):
                # If a file or folder is marked for ignore,
                # it can already be dropped at this stage
                files_to_iterate.append(full_path)

    # Start yielding individual test cases from the file list
    for _test_file in files_to_iterate:
        try:
            for _test_case in load_json_fixture(_test_file, network):
                # _identifier could identify files, folders through test_file
                #  individual cases through test_key
                _identifier = (
                    "("
                    + _test_case["test_file"]
                    + "|"
                    + _test_case["test_key"]
                    + ")"
                )
                if any(x.search(_identifier) for x in all_ignore):
                    continue
                elif any(x.search(_identifier) for x in all_slow):
                    yield pytest.param(_test_case, marks=pytest.mark.slow)
                elif any(x.search(_identifier) for x in all_big_memory):
                    yield pytest.param(_test_case, marks=pytest.mark.bigmem)
                else:
                    yield _test_case
        except NoTestsFound:
            # file doesn't contain tests for the given fork
            continue


# Test case Identifier
def idfn(test_case: Dict) -> str:
    if isinstance(test_case, dict):
        folder_name = test_case["test_file"].split("/")[-2]
        # Assign Folder name and test_key to identify tests in output
        return folder_name + " - " + test_case["test_key"]
