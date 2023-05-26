import json
import sys
from io import StringIO
from typing import Any, Dict, List

import pytest

from ethereum import rlp
from ethereum.base_types import U256, Bytes20, Bytes32, Bytes256, Uint
from ethereum.crypto.hash import Hash32
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_bytes8
from ethereum_spec_tools.evm_tools import parser, subparsers
from ethereum_spec_tools.evm_tools.b11r import B11R, b11r_arguments
from ethereum_spec_tools.evm_tools.t8n import T8N, t8n_arguments
from ethereum_spec_tools.evm_tools.utils import parse_hex_or_int

t8n_arguments(subparsers)
b11r_arguments(subparsers)


def get_uncle_rlps(uncles: List[Dict[str, Any]]) -> List[str]:
    uncles_rlp = []
    for uncle in uncles:

        header = [
            Hash32(hex_to_bytes(uncle["parentHash"])),
            Hash32(hex_to_bytes(uncle["uncleHash"])),
            Bytes20(hex_to_bytes(uncle["coinbase"])),
            Hash32(hex_to_bytes(uncle["stateRoot"])),
            Hash32(hex_to_bytes(uncle["transactionsTrie"])),
            Hash32(hex_to_bytes(uncle["receiptTrie"])),
            Bytes256(hex_to_bytes(uncle["bloom"])),
            parse_hex_or_int(uncle["difficulty"], Uint),
            parse_hex_or_int(uncle["number"], Uint),
            parse_hex_or_int(uncle["gasLimit"], Uint),
            parse_hex_or_int(uncle["gasUsed"], Uint),
            parse_hex_or_int(uncle["timestamp"], U256),
            hex_to_bytes(uncle.get("extraData", "0x")),
            Bytes32(hex_to_bytes(uncle["mixHash"])),
            hex_to_bytes8(uncle.get("nonce", "0x0000000000000000")),
        ]

        uncle_block = [
            header,
            [],
            [],
        ]

        try:
            header.append(hex_to_bytes(uncle["baseFeePerGas"]))
        except KeyError:
            pass

        try:
            header.append(hex_to_bytes(uncle["withdrawalsRoot"]))
            uncle_block.append([])
        except KeyError:
            pass

        uncles_rlp.append("0x" + rlp.encode(uncle_block).hex())

    return uncles_rlp


def load_evm_tools_test(
    test_case: Dict,
    fork_name: str,
    block_reward: int = None,
) -> None:
    test_file = test_case["test_file"]
    test_key = test_case["test_key"]

    with open(test_file, "r") as fp:
        data = json.load(fp)

    json_data = data[test_key]

    alloc = json_data["pre"]

    block_hashes = {}

    for block in json_data["blocks"]:

        if "blockHeader" not in block:
            pytest.skip("Skipping test case with no block header")

        # Assemble the environment for the t8n tool
        current_number = block["blockHeader"]["number"]
        # The t8n tool expects block hashes in the form {number: hash}
        # number being in str
        block_hashes[
            str(parse_hex_or_int(block["blockHeader"]["number"], Uint) - 1)
        ] = block["blockHeader"]["parentHash"]

        env = {
            "currentCoinbase": block["blockHeader"]["coinbase"],
            "currentDifficulty": block["blockHeader"]["difficulty"],
            "currentGasLimit": block["blockHeader"]["gasLimit"],
            "currentNumber": block["blockHeader"]["number"],
            "currentTimestamp": block["blockHeader"]["timestamp"],
            "blockHashes": block_hashes,
        }

        try:
            env["currentBaseFee"] = block["blockHeader"]["baseFeePerGas"]
            # Starting paris, randomness is availavle in the difficulty
            # field of the fixture. T8N will just ignore it if it is
            # before paris
            env["currentRandom"] = block["blockHeader"]["mixHash"]
            env["withdrawals"] = block["withdrawals"]
        except KeyError:
            pass

        env_ommers = []
        for uncle in block["uncleHeaders"]:
            delta = parse_hex_or_int(
                block["blockHeader"]["number"], Uint
            ) - parse_hex_or_int(uncle["number"], Uint)
            env_ommers.append(
                {
                    "delta": delta,
                    "address": uncle["coinbase"],
                }
            )

        if len(env_ommers):
            env["ommers"] = env_ommers

        # Assemble the transactions for the t8n tool
        txs = []
        for tx in block["transactions"]:
            tx["input"] = tx["data"]
            tx["gas"] = tx["gasLimit"]
            txs.append(tx)

        sys.stdin = StringIO(
            json.dumps(
                {
                    "env": env,
                    "alloc": alloc,
                    "txs": txs,
                }
            )
        )

        # Run the t8n tool
        t8n_args = [
            "t8n",
            "--input.alloc",
            "stdin",
            "--input.env",
            "stdin",
            "--input.txs",
            "stdin",
            "--state.fork",
            f"{fork_name}",
        ]
        if block_reward:
            t8n_args += ["--state.reward", f"{block_reward}"]
        t8n_options = parser.parse_args(t8n_args)

        t8n = T8N(t8n_options)
        t8n.apply_body()

        # Update the state for the next block
        alloc = t8n.alloc.to_json()
        # Assemble the transactions rlp for the b11r tool
        txs_rlp = rlp.encode(t8n.txs.successful_txs)

        # Assemble the header for the b11r tool
        header = {
            "parentHash": block["blockHeader"]["parentHash"],
            "miner": block["blockHeader"]["coinbase"],
            "stateRoot": "0x" + t8n.result.state_root.hex(),
            "transactionsRoot": "0x" + t8n.result.tx_root.hex(),
            "receiptsRoot": "0x" + t8n.result.receipt_root.hex(),
            "logsBloom": "0x" + t8n.result.bloom.hex(),
            "difficulty": block["blockHeader"]["difficulty"],
            "number": block["blockHeader"]["number"],
            "gasLimit": block["blockHeader"]["gasLimit"],
            "gasUsed": t8n.result.gas_used,
            "timestamp": block["blockHeader"]["timestamp"],
            "extraData": block["blockHeader"]["extraData"],
            "mixHash": block["blockHeader"]["mixHash"],
            "nonce": block["blockHeader"]["nonce"],
        }

        try:
            header["baseFeePerGas"] = block["blockHeader"]["baseFeePerGas"]
        except KeyError:
            pass

        if t8n.result.withdrawals_root:
            header["withdrawalsRoot"] = (
                "0x" + t8n.result.withdrawals_root.hex()
            )

        ommers: List[Any] = get_uncle_rlps(block["uncleHeaders"])

        stdin_data = {
            "header": header,
            "ommers": ommers,
            "txs": "0x" + txs_rlp.hex(),
        }

        b11r_args = [
            "b11r",
            "--input.header",
            "stdin",
            "--input.ommers",
            "stdin",
            "--input.txs",
            "stdin",
        ]

        if t8n.result.withdrawals_root:
            b11r_args += ["--input.withdrawals", "stdin"]
            stdin_data["withdrawals"] = env["withdrawals"]

        sys.stdin = StringIO(json.dumps(stdin_data))

        # Run the b11r tool
        b11r_options = parser.parse_args(b11r_args)

        b11r = B11R(b11r_options)
        b11r.build_block()

        assert b11r.block_rlp == hex_to_bytes(block["rlp"])


# Test case Identifier
def idfn(test_case: Dict) -> str:
    if isinstance(test_case, dict):
        folder_name = test_case["test_file"].split("/")[-2]
        # Assign Folder name and test_key to identify tests in output
        return folder_name + " - " + test_case["test_key"] + " - evm_tools"
