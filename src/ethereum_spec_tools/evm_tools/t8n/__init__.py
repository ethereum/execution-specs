"""
Create a transition tool for the given fork.
"""

import argparse
import json
import os
from functools import partial
from typing import Any, TextIO

from ethereum import rlp, trace
from ethereum.base_types import U64, U256, Uint
from ethereum.exceptions import EthereumException
from ethereum_spec_tools.evm_tools.t8n import evm_trace
from ethereum_spec_tools.forks import Hardfork

from ..loaders.fixture_loader import Load
from ..loaders.fork_loader import ForkLoad
from ..utils import (
    FatalException,
    get_module_name,
    get_stream_logger,
    parse_hex_or_int,
)
from .env import Env
from .t8n_types import Alloc, Result, Txs


def t8n_arguments(subparsers: argparse._SubParsersAction) -> None:
    """
    Adds the arguments for the t8n tool subparser.
    """
    t8n_parser = subparsers.add_parser("t8n", help="This is the t8n tool.")

    t8n_parser.add_argument(
        "--input.alloc", dest="input_alloc", type=str, default="alloc.json"
    )
    t8n_parser.add_argument(
        "--input.env", dest="input_env", type=str, default="env.json"
    )
    t8n_parser.add_argument(
        "--input.txs", dest="input_txs", type=str, default="txs.json"
    )
    t8n_parser.add_argument(
        "--output.alloc", dest="output_alloc", type=str, default="alloc.json"
    )
    t8n_parser.add_argument(
        "--output.basedir", dest="output_basedir", type=str, default="."
    )
    t8n_parser.add_argument("--output.body", dest="output_body", type=str)
    t8n_parser.add_argument(
        "--output.result",
        dest="output_result",
        type=str,
        default="result.json",
    )
    t8n_parser.add_argument(
        "--state.chainid", dest="state_chainid", type=int, default=1
    )
    t8n_parser.add_argument(
        "--state.fork", dest="state_fork", type=str, default="Frontier"
    )
    t8n_parser.add_argument(
        "--state.reward", dest="state_reward", type=int, default=0
    )
    t8n_parser.add_argument("--trace", action="store_true")
    t8n_parser.add_argument("--trace.memory", action="store_true")
    t8n_parser.add_argument("--trace.nomemory", action="store_true")
    t8n_parser.add_argument("--trace.noreturndata", action="store_true")
    t8n_parser.add_argument("--trace.nostack", action="store_true")
    t8n_parser.add_argument("--trace.returndata", action="store_true")

    t8n_parser.add_argument("--state-test", action="store_true")


class T8N(Load):
    """The class that carries out the transition"""

    def __init__(
        self, options: Any, out_file: TextIO, in_file: TextIO
    ) -> None:
        self.out_file = out_file
        self.in_file = in_file
        self.options = options
        self.forks = Hardfork.discover()

        if "stdin" in (
            options.input_env,
            options.input_alloc,
            options.input_txs,
        ):
            stdin = json.load(in_file)
        else:
            stdin = None

        fork_module, self.fork_block = get_module_name(
            self.forks, self.options, stdin
        )
        self.fork = ForkLoad(fork_module)

        if self.options.trace:
            trace_memory = getattr(self.options, "trace.memory", False)
            trace_stack = not getattr(self.options, "trace.nostack", False)
            trace_return_data = getattr(self.options, "trace.returndata")
            trace.evm_trace = partial(
                evm_trace.evm_trace,
                trace_memory=trace_memory,
                trace_stack=trace_stack,
                trace_return_data=trace_return_data,
            )
            evm_trace.OUTPUT_DIR = self.options.output_basedir
        self.logger = get_stream_logger("T8N")

        super().__init__(
            self.options.state_fork,
            fork_module,
        )

        self.chain_id = parse_hex_or_int(self.options.state_chainid, U64)
        self.alloc = Alloc(self, stdin)
        self.env = Env(self, stdin)
        self.txs = Txs(self, stdin)
        self.result = Result(
            self.env.block_difficulty, self.env.base_fee_per_gas
        )

    @property
    def BLOCK_REWARD(self) -> Any:
        """
        For the t8n tool, the block reward is
        provided as a command line option
        """
        if self.options.state_reward < 0 or self.fork.is_after_fork(
            "ethereum.paris"
        ):
            return None
        else:
            return U256(self.options.state_reward)

    def check_transaction(self, tx: Any, gas_available: Any) -> Any:
        """
        Implements the check_transaction function of the fork.
        The arguments to be passed are adjusted according to the fork.
        """
        # TODO: The current PR changes the signature of the check_transaction
        # in cancun only. Once this is approved and ported over to the
        # the other forks in PR #890, this function has to be updated.
        # This is a temporary change to make the tool work for cancun.
        if self.fork.is_after_fork("ethereum.cancun"):
            return self.fork.check_transaction(
                self.alloc.state,
                tx,
                gas_available,
                self.chain_id,
                self.env.base_fee_per_gas,
                self.env.excess_blob_gas,
            )
        arguments = [tx]

        if self.fork.is_after_fork("ethereum.london"):
            arguments.append(self.env.base_fee_per_gas)

        arguments.append(gas_available)

        if self.fork.is_after_fork("ethereum.spurious_dragon"):
            arguments.append(self.chain_id)

        return self.fork.check_transaction(*arguments)

    def block_environment(self) -> Any:
        """
        Create the environment for the transaction. The keyword
        arguments are adjusted according to the fork.
        """
        kw_arguments = {
            "block_hashes": self.env.block_hashes,
            "coinbase": self.env.coinbase,
            "number": self.env.block_number,
            "gas_limit": self.env.block_gas_limit,
            "time": self.env.block_timestamp,
            "state": self.alloc.state,
            "block_gas_limit": self.env.block_gas_limit,
        }

        if self.fork.is_after_fork("ethereum.istanbul"):
            kw_arguments["chain_id"] = self.chain_id

        if self.fork.is_after_fork("ethereum.london"):
            kw_arguments["base_fee_per_gas"] = self.env.base_fee_per_gas

        if self.fork.is_after_fork("ethereum.paris"):
            kw_arguments["prev_randao"] = self.env.prev_randao
        else:
            kw_arguments["difficulty"] = self.env.block_difficulty

        if self.fork.is_after_fork("ethereum.cancun"):
            kw_arguments[
                "parent_beacon_block_root"
            ] = self.env.parent_beacon_block_root
            kw_arguments["excess_blob_gas"] = self.env.excess_blob_gas

        return self.fork.BlockEnvironment(**kw_arguments)

    def tx_trie_set(self, trie: Any, index: Any, tx: Any) -> Any:
        """Add a transaction to the trie."""
        arguments = [trie, rlp.encode(Uint(index))]
        if self.fork.is_after_fork("ethereum.berlin"):
            arguments.append(self.fork.encode_transaction(tx))
        else:
            arguments.append(tx)

        self.fork.trie_set(*arguments)

    def make_receipt(
        self, tx: Any, process_transaction_return: Any, gas_available: Any
    ) -> Any:
        """Create a transaction receipt."""
        arguments = [tx]

        if self.fork.is_after_fork("ethereum.byzantium"):
            arguments.append(process_transaction_return[2])
        else:
            arguments.append(self.fork.state_root(self.alloc.state))

        arguments.append((self.env.block_gas_limit - gas_available))
        arguments.append(process_transaction_return[1])

        return self.fork.make_receipt(*arguments)

    def pay_rewards(self) -> None:
        """
        Pay the miner and the ommers.
        This function is re-implemented since the uncle header
        might not be available in the t8n tool.
        """
        coinbase = self.env.coinbase
        ommers = self.env.ommers
        state = self.alloc.state

        miner_reward = self.BLOCK_REWARD + (
            len(ommers) * (self.BLOCK_REWARD // 32)
        )
        self.fork.create_ether(state, coinbase, miner_reward)
        touched_accounts = [coinbase]

        for ommer in ommers:
            # Ommer age with respect to the current block.
            ommer_miner_reward = ((8 - ommer.delta) * self.BLOCK_REWARD) // 8
            self.fork.create_ether(state, ommer.address, ommer_miner_reward)
            touched_accounts.append(ommer.address)

        if self.fork.is_after_fork("ethereum.spurious_dragon"):
            # Destroy empty accounts that were touched by
            # paying the rewards. This is only important if
            # the block rewards were zero.
            for account in touched_accounts:
                if self.fork.account_exists_and_is_empty(state, account):
                    self.fork.destroy_account(state, account)

    def backup_state(self) -> None:
        """Back up the state in order to restore in case of an error."""
        state = self.alloc.state
        self.alloc.state_backup = (
            self.fork.copy_trie(state._main_trie),
            {
                k: self.fork.copy_trie(t)
                for (k, t) in state._storage_tries.items()
            },
        )

    def restore_state(self) -> None:
        """Restore the state from the backup."""
        state = self.alloc.state
        state._main_trie, state._storage_tries = self.alloc.state_backup

    def run_state_test(self) -> Any:
        """
        Apply a single transaction on pre-state. No system operations
        are performed.
        """
        block_env = self.block_environment()
        self.backup_state()
        try:
            tx = self.txs.transactions[0]
            gas_available = block_env.block_gas_limit
            blob_gas_available = self.fork.MAX_BLOB_GAS_PER_BLOCK
            output = self.fork.process_transaction(
                block_env, tx, Uint(0), gas_available, blob_gas_available
            )
        except EthereumException as e:
            self.restore_state()
            self.txs.rejected_txs[0] = f"Failed transaction: {str(e)}"
            self.logger.warning(f"Transaction {0} failed: {str(e)}")
        else:
            self.result.gas_used = output[0]

        self.result.state_root = self.fork.state_root(self.alloc.state)
        self.result.rejected = self.txs.rejected_txs

    def run_blockchain_test(self) -> None:
        """
        Apply a block on the pre-state. Also includes system operations.
        """
        block_env = self.block_environment()
        self.backup_state()
        try:
            txs = self.txs.transactions
            output = self.fork.apply_body(block_env, txs, self.env.withdrawals)
            self.result.gas_used = output.block_gas_used
        except EthereumException as e:
            self.restore_state()
            self.txs.rejected_txs[0] = f"Failed transaction: {str(e)}"
            self.logger.warning(f"Transaction {0} failed: {str(e)}")

        self.result.state_root = self.fork.state_root(self.alloc.state)
        self.result.rejected = self.txs.rejected_txs

    def run(self) -> int:
        """Run the transition and provide the relevant outputs"""
        # Clean out files from the output directory
        for file in os.listdir(self.options.output_basedir):
            if file.endswith(".json") or file.endswith(".jsonl"):
                os.remove(os.path.join(self.options.output_basedir, file))

        try:
            if self.options.state_test:
                self.run_state_test()
            else:
                self.run_blockchain_test()
        except FatalException as e:
            self.logger.error(str(e))
            return 1

        json_state = self.alloc.to_json()
        json_result = self.result.to_json()

        json_output = {}

        if self.options.output_body == "stdout":
            txs_rlp = "0x" + rlp.encode(self.txs.all_txs).hex()
            json_output["body"] = txs_rlp
        elif self.options.output_body is not None:
            txs_rlp_path = os.path.join(
                self.options.output_basedir,
                self.options.output_body,
            )
            txs_rlp = "0x" + rlp.encode(self.txs.all_txs).hex()
            with open(txs_rlp_path, "w") as f:
                json.dump(txs_rlp, f)
            self.logger.info(f"Wrote transaction rlp to {txs_rlp_path}")

        if self.options.output_alloc == "stdout":
            json_output["alloc"] = json_state
        else:
            alloc_output_path = os.path.join(
                self.options.output_basedir,
                self.options.output_alloc,
            )
            with open(alloc_output_path, "w") as f:
                json.dump(json_state, f, indent=4)
            self.logger.info(f"Wrote alloc to {alloc_output_path}")

        if self.options.output_result == "stdout":
            json_output["result"] = json_result
        else:
            result_output_path = os.path.join(
                self.options.output_basedir,
                self.options.output_result,
            )
            with open(result_output_path, "w") as f:
                json.dump(json_result, f, indent=4)
            self.logger.info(f"Wrote result to {result_output_path}")

        if json_output:
            json.dump(json_output, self.out_file, indent=4)

        return 0
