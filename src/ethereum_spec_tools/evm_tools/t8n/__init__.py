"""
Create a transition tool for the given fork.
"""

import argparse
import json
import os
import sys
from functools import partial
from typing import Any

from ethereum import rlp, trace
from ethereum.base_types import U64, U256, Uint
from ethereum.crypto.hash import keccak256
from ethereum_spec_tools.forks import Hardfork

from ..fixture_loader import Load
from ..utils import (
    FatalException,
    get_module_name,
    get_stream_logger,
    parse_hex_or_int,
)
from .env import Env
from .evm_trace import evm_trace, output_traces
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


class T8N(Load):
    """The class that carries out the transition"""

    def __init__(self, options: Any) -> None:
        self.options = options
        self.forks = Hardfork.discover()

        if "stdin" in (
            options.input_env,
            options.input_alloc,
            options.input_txs,
        ):
            stdin = json.load(sys.stdin)
        else:
            stdin = None

        fork_module, self.fork_block = get_module_name(
            self.forks, self.options, stdin
        )

        if self.options.trace:
            trace_memory = getattr(self.options, "trace.memory", False)
            trace_stack = not getattr(self.options, "trace.nostack", False)
            trace_return_data = getattr(self.options, "trace.returndata")
            trace.evm_trace = partial(
                evm_trace,
                trace_memory=trace_memory,
                trace_stack=trace_stack,
                trace_return_data=trace_return_data,
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

    @property
    def fork(self) -> Any:
        """The fork module of the given fork."""
        return self._module("fork")

    @property
    def fork_types(self) -> Any:
        """The fork_types model of the given fork."""
        return self._module("fork_types")

    @property
    def state(self) -> Any:
        """The state module of the given fork."""
        return self._module("state")

    @property
    def trie(self) -> Any:
        """The trie module of the given fork."""
        return self._module("trie")

    @property
    def bloom(self) -> Any:
        """The bloom module of the given fork."""
        return self._module("bloom")

    @property
    def vm(self) -> Any:
        """The vm module of the given fork."""
        return self._module("vm")

    @property
    def BLOCK_REWARD(self) -> Any:
        """
        For the t8n tool, the block reward is
        provided as a command line option
        """
        if self.options.state_reward < 0 or self.is_after_fork(
            "ethereum.paris"
        ):
            return None
        else:
            return U256(self.options.state_reward)

    def is_after_fork(self, target_fork_name: str) -> bool:
        """Check if the fork is after the target fork"""
        return_value = False
        for fork in self.forks:
            if fork.name == target_fork_name:
                return_value = True
            if fork.name == "ethereum." + self._fork_module:
                break
        return return_value

    def check_transaction(self, tx: Any, gas_available: Any) -> Any:
        """
        Implements the check_transaction function of the fork.
        The arguments to be passed are adjusted according to the fork.
        """
        arguments = [tx]

        if self.is_after_fork("ethereum.london"):
            arguments.append(self.env.base_fee_per_gas)

        arguments.append(gas_available)

        if self.is_after_fork("ethereum.spurious_dragon"):
            arguments.append(self.chain_id)

        return self.fork.check_transaction(*arguments)

    def environment(self, tx: Any, gas_available: Any) -> Any:
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
        }

        if self.is_after_fork("ethereum.paris"):
            kw_arguments["prev_randao"] = self.env.prev_randao
        else:
            kw_arguments["difficulty"] = self.env.block_difficulty

        if self.is_after_fork("ethereum.istanbul"):
            kw_arguments["chain_id"] = self.chain_id

        if self.is_after_fork("ethereum.london"):
            sender_address, effective_gas_price = self.fork.check_transaction(
                tx,
                self.env.base_fee_per_gas,
                gas_available,
                self.chain_id,
            )
            kw_arguments["base_fee_per_gas"] = self.env.base_fee_per_gas
            kw_arguments["caller"] = kw_arguments["origin"] = sender_address
            kw_arguments["gas_price"] = effective_gas_price
        elif self.is_after_fork("ethereum.spurious_dragon"):
            sender_address = self.fork.check_transaction(
                tx, gas_available, self.chain_id
            )
            kw_arguments["caller"] = kw_arguments["origin"] = sender_address
            kw_arguments["gas_price"] = tx.gas_price
        else:
            sender_address = self.fork.check_transaction(tx, gas_available)
            kw_arguments["caller"] = kw_arguments["origin"] = sender_address
            kw_arguments["gas_price"] = tx.gas_price

        kw_arguments["traces"] = []

        return self.vm.Environment(**kw_arguments)

    def tx_trie_set(self, trie: Any, index: Any, tx: Any) -> Any:
        """Add a transaction to the trie."""
        arguments = [trie, rlp.encode(Uint(index))]
        if self.is_after_fork("ethereum.berlin"):
            arguments.append(self.fork_types.encode_transaction(tx))
        else:
            arguments.append(tx)

        self.trie.trie_set(*arguments)

    def make_receipt(
        self, tx: Any, process_transaction_return: Any, gas_available: Any
    ) -> Any:
        """Create a transaction receipt."""
        arguments = [tx]

        if self.is_after_fork("ethereum.byzantium"):
            arguments.append(process_transaction_return[2])
        else:
            arguments.append(self.state.state_root(self.alloc.state))

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
        self.state.create_ether(state, coinbase, miner_reward)
        touched_accounts = [coinbase]

        for ommer in ommers:
            # Ommer age with respect to the current block.
            ommer_miner_reward = ((8 - ommer.delta) * self.BLOCK_REWARD) // 8
            self.state.create_ether(state, ommer.address, ommer_miner_reward)
            touched_accounts.append(ommer.address)

        if self.is_after_fork("ethereum.spurious_dragon"):
            # Destroy empty accounts that were touched by
            # paying the rewards. This is only important if
            # the block rewards were zero.
            for account in touched_accounts:
                if self.state.account_exists_and_is_empty(state, account):
                    self.state.destroy_account(state, account)

    def backup_state(self) -> None:
        """Back up the state in order to restore in case of an error."""
        state = self.alloc.state
        self.alloc.state_backup = (
            self.trie.copy_trie(state._main_trie),
            {
                k: self.trie.copy_trie(t)
                for (k, t) in state._storage_tries.items()
            },
        )

    def restore_state(self) -> None:
        """Restore the state from the backup."""
        state = self.alloc.state
        state._main_trie, state._storage_tries = self.alloc.state_backup

    def apply_body(self) -> None:
        """
        The apply body function is seen as the entry point of
        the t8n tool into the designated fork. The function has been
        re-implemented here to account for the differences in the
        transaction processing between the forks. However, the general
        structure of the function is the same.
        """
        block_gas_limit = self.env.block_gas_limit

        gas_available = block_gas_limit
        transactions_trie = self.trie.Trie(secured=False, default=None)
        receipts_trie = self.trie.Trie(secured=False, default=None)
        block_logs = ()

        for i, (tx_idx, tx) in enumerate(self.txs.transactions):
            # i is the index among valid transactions
            # tx_idx is the index among all transactions. tx_idx is only used
            # to identify the transaction in the rejected_txs dictionary.
            self.backup_state()

            try:
                env = self.environment(tx, gas_available)

                process_transaction_return = self.process_transaction(env, tx)
            except Exception as e:
                # The tf tools expects some non-blank error message
                # even in case e is blank.
                self.txs.rejected_txs[tx_idx] = f"Failed transaction: {str(e)}"
                self.restore_state()
                self.logger.warning(f"Transaction {tx_idx} failed: {str(e)}")
            else:
                self.txs.add_transaction(tx)
                gas_consumed = process_transaction_return[0]
                gas_available -= gas_consumed

                if self.options.trace:
                    tx_hash = self.txs.get_tx_hash(tx)
                    output_traces(
                        env.traces, i, tx_hash, self.options.output_basedir
                    )
                self.tx_trie_set(transactions_trie, i, tx)

                receipt = self.make_receipt(
                    tx, process_transaction_return, gas_available
                )

                self.trie.trie_set(
                    receipts_trie,
                    rlp.encode(Uint(i)),
                    receipt,
                )

                self.txs.add_receipt(tx, gas_consumed)

                block_logs += process_transaction_return[1]

                self.alloc.state._snapshots = []

        if self.BLOCK_REWARD is not None:
            self.pay_rewards()

        block_gas_used = block_gas_limit - gas_available

        block_logs_bloom = self.bloom.logs_bloom(block_logs)

        logs_hash = keccak256(rlp.encode(block_logs))

        if self.is_after_fork("ethereum.shanghai"):
            withdrawals_trie = self.trie.Trie(secured=False, default=None)

            for i, wd in enumerate(self.env.withdrawals):
                self.trie.trie_set(
                    withdrawals_trie, rlp.encode(Uint(i)), rlp.encode(wd)
                )

                self.state.process_withdrawal(self.alloc.state, wd)

                if self.state.account_exists_and_is_empty(
                    self.alloc.state, wd.address
                ):
                    self.state.destroy_account(self.alloc.state, wd.address)

            self.result.withdrawals_root = self.trie.root(withdrawals_trie)

        self.result.state_root = self.state.state_root(self.alloc.state)
        self.result.tx_root = self.trie.root(transactions_trie)
        self.result.receipt_root = self.trie.root(receipts_trie)
        self.result.bloom = block_logs_bloom
        self.result.logs_hash = logs_hash
        self.result.rejected = self.txs.rejected_txs
        self.result.receipts = self.txs.successful_receipts
        self.result.gas_used = block_gas_used

    def run(self) -> int:
        """Run the transition and provide the relevant outputs"""
        try:
            self.apply_body()
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
            json.dump(json_output, sys.stdout, indent=4)

        return 0
