"""
Create a transition tool for the given fork.
"""

import argparse
import json
import os
from functools import partial
from typing import Any, TextIO

from ethereum_rlp import rlp
from ethereum_types.numeric import U64, Uint

from ethereum import trace
from ethereum.exceptions import EthereumException
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
from .evm_trace import evm_trace
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
                evm_trace,
                trace_memory=trace_memory,
                trace_stack=trace_stack,
                trace_return_data=trace_return_data,
                output_basedir=self.options.output_basedir,
            )
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

    def block_environment(self) -> Any:
        """
        Create the environment for the transaction. The keyword
        arguments are adjusted according to the fork.
        """
        kw_arguments = {
            "block_hashes": self.env.block_hashes,
            "coinbase": self.env.coinbase,
            "number": self.env.block_number,
            "time": self.env.block_timestamp,
            "state": self.alloc.state,
            "block_gas_limit": self.env.block_gas_limit,
            "chain_id": self.chain_id,
        }

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
        block_gas_limit = self.env.block_gas_limit

        gas_available = block_gas_limit
        transactions_trie = self.fork.Trie(secured=False, default=None)
        receipts_trie = self.fork.Trie(secured=False, default=None)
        block_logs = ()
        blob_gas_used = U64(0)

        if (
            self.fork.is_after_fork("ethereum.cancun")
            and self.env.parent_beacon_block_root is not None
        ):
            beacon_block_roots_contract_code = self.fork.get_account(
                self.alloc.state, self.BEACON_ROOTS_ADDRESS
            ).code

            system_tx_message = self.fork.Message(
                caller=self.SYSTEM_ADDRESS,
                target=self.BEACON_ROOTS_ADDRESS,
                gas=self.SYSTEM_TRANSACTION_GAS,
                value=U256(0),
                data=self.env.parent_beacon_block_root,
                code=beacon_block_roots_contract_code,
                depth=Uint(0),
                current_target=self.BEACON_ROOTS_ADDRESS,
                code_address=self.BEACON_ROOTS_ADDRESS,
                should_transfer_value=False,
                is_static=False,
                accessed_addresses=set(),
                accessed_storage_keys=set(),
                parent_evm=None,
            )

            system_tx_env = self.fork.Environment(
                caller=self.SYSTEM_ADDRESS,
                origin=self.SYSTEM_ADDRESS,
                block_hashes=self.env.block_hashes,
                coinbase=self.env.coinbase,
                number=self.env.block_number,
                gas_limit=self.env.block_gas_limit,
                base_fee_per_gas=self.env.base_fee_per_gas,
                gas_price=self.env.base_fee_per_gas,
                time=self.env.block_timestamp,
                prev_randao=self.env.prev_randao,
                state=self.alloc.state,
                chain_id=self.chain_id,
                traces=[],
                excess_blob_gas=self.env.excess_blob_gas,
                blob_versioned_hashes=(),
                transient_storage=self.fork.TransientStorage(),
            )

            system_tx_output = self.fork.process_message_call(
                system_tx_message, system_tx_env
            )

            self.fork.destroy_touched_empty_accounts(
                system_tx_env.state, system_tx_output.touched_accounts
            )

        for i, tx in zip(self.txs.successfully_parsed, self.txs.transactions):
            self.backup_state()
            try:
                env = self.environment(tx, gas_available)

                process_transaction_return = self.fork.process_transaction(
                    env, tx
                )

                if self.fork.is_after_fork("ethereum.cancun"):
                    blob_gas_used += U64(self.fork.calculate_total_blob_gas(tx))
                    if blob_gas_used > U64(self.fork.MAX_BLOB_GAS_PER_BLOCK):
                        raise InvalidBlock
            except EthereumException as e:
                self.txs.rejected_txs[i] = f"Failed transaction: {e!r}"
                self.restore_state()
                self.logger.warning(f"Transaction {i} failed: {e!r}")

        if not self.fork.is_after_fork("ethereum.paris"):
            self.fork.pay_rewards(
                block_env.state,
                block_env.number,
                block_env.coinbase,
                self.env.ommers,
            )

        if self.fork.is_after_fork("ethereum.shanghai"):
            self.fork.process_withdrawals(
                block_env, block_output, self.env.withdrawals
            )

        if self.fork.is_after_fork("ethereum.prague"):
            self.fork.process_general_purpose_requests(block_env, block_output)

        self.result.update(self, block_env, block_output)
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
