"""
Create a transition tool for the given fork.
"""

import json
import sys
from typing import Any

from ethereum import rlp
from ethereum.base_types import U64, U256, Uint
from ethereum.crypto.hash import keccak256
from ethereum_spec_tools.forks import Hardfork

from ..fixture_loader import Load
from ..utils import (
    FatalException,
    get_module_name,
    get_stream_logger,
    read_hex_or_int,
)
from .t8n_types import Alloc, Env, Result, Txs


class T8N(Load):
    """The class that carries out the transition"""

    def __init__(self, options: Any) -> None:
        self.options = options
        self.forks = Hardfork.discover()

        fork_module = get_module_name(self.forks, self.options.state_fork)

        self.logger = get_stream_logger("T8N")

        super().__init__(
            self.options.state_fork,
            fork_module,
        )

        self.chain_id = read_hex_or_int(self.options.state_chainid, U64)
        self.alloc = Alloc(self)
        self.env = Env(self)
        self.txs = Txs(self)
        self.result = Result(self.env)

    @property
    def fork(self) -> Any:
        """The fork module of the given fork."""
        return self._module("fork")

    @property
    def fork_types(self) -> Any:
        """The fork_types model of the given fork."""
        return self._module("fork_types")

    @property
    def fork_state(self) -> Any:
        """The state module of the given fork."""
        return self._module("state")

    @property
    def fork_trie(self) -> Any:
        """The trie module of the given fork."""
        return self._module("trie")

    @property
    def fork_bloom(self) -> Any:
        """The bloom module of the given fork."""
        return self._module("bloom")

    @property
    def fork_vm(self) -> Any:
        """The vm module of the given fork."""
        return self._module("vm")

    @property
    def BLOCK_REWARD(self) -> Any:
        """
        For the t8n tool, the block reward is
        provided as a command line option
        """
        if self.options.state_reward < 0:
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
            "difficulty": self.env.block_difficulty,
            "state": self.alloc.state,
        }

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

        return self.fork_vm.Environment(**kw_arguments)

    def tx_trie_set(self, trie: Any, index: Any, tx: Any) -> Any:
        """Add a transaction to the trie."""
        arguments = [trie, rlp.encode(Uint(index))]
        if self.is_after_fork("ethereum.berlin"):
            arguments.append(self.fork_types.encode_transaction(tx))
        else:
            arguments.append(tx)

        self.fork_trie.trie_set(*arguments)

    def make_receipt(
        self, tx: Any, process_transaction_return: Any, gas_available: Any
    ) -> Any:
        """Create a transaction receipt."""
        arguments = [tx]

        if self.is_after_fork("ethereum.byzantium"):
            arguments.append(process_transaction_return[2])
        else:
            arguments.append(self.fork_state.state_root(self.alloc.state))

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
        self.fork_state.create_ether(state, coinbase, miner_reward)
        touched_accounts = [coinbase]

        for ommer in ommers:
            # Ommer age with respect to the current block.
            ommer_miner_reward = ((8 - ommer.delta) * self.BLOCK_REWARD) // 8
            self.fork_state.create_ether(
                state, ommer.address, ommer_miner_reward
            )
            touched_accounts.append(ommer.address)

        if self.is_after_fork("ethereum.spurious_dragon"):
            # Destroy empty accounts that were touched by
            # paying the rewards. This is only important if
            # the block rewards were zero.
            for account in touched_accounts:
                if self.fork_state.account_exists_and_is_empty(state, account):
                    self.fork_state.destroy_account(state, account)

    def backup_state(self) -> None:
        """Back up the state in order to restore in case of an error."""
        state = self.alloc.state
        self.alloc.state_backup = (
            self.fork_trie.copy_trie(state._main_trie),
            {
                k: self.fork_trie.copy_trie(t)
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
        transactions_trie = self.fork_trie.Trie(secured=False, default=None)
        receipts_trie = self.fork_trie.Trie(secured=False, default=None)
        block_logs = ()

        for i, (tx_idx, tx) in enumerate(self.txs.transactions):
            # i is the index among valid transactions
            # tx_idx is the index among all transactions. tx_idx is only used
            # to identify the transaction in the rejected_txs dictionary.
            self.backup_state()

            try:
                env = self.environment(tx, gas_available)

                # TODO: Check if there is a better way for this.
                process_transaction_return = self.process_transaction(env, tx)
            except Exception as e:
                self.txs.rejected_txs[tx_idx] = str(e)
                self.restore_state()
                self.logger.warning(f"Transaction {tx_idx} failed: {str(e)}")
                if isinstance(e, FatalException):
                    raise e
            else:
                gas_available -= process_transaction_return[0]

                self.tx_trie_set(transactions_trie, i, tx)

                receipt = self.make_receipt(
                    tx, process_transaction_return, gas_available
                )

                self.fork_trie.trie_set(
                    receipts_trie,
                    rlp.encode(Uint(i)),
                    receipt,
                )

                block_logs += process_transaction_return[1]

        if self.BLOCK_REWARD is not None:
            self.pay_rewards()

        block_gas_used = block_gas_limit - gas_available

        block_logs_bloom = self.fork_bloom.logs_bloom(block_logs)

        logs_hash = keccak256(rlp.encode(block_logs))

        self.result.state_root = self.fork_state.state_root(self.alloc.state)
        self.result.tx_root = self.fork_trie.root(transactions_trie)
        self.result.receipt_root = self.fork_trie.root(receipts_trie)
        self.result.bloom = block_logs_bloom
        self.result.logs_hash = logs_hash
        self.result.rejected = self.txs.rejected_txs
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

        if self.options.output_alloc != "stdout":
            with open(self.options.output_alloc, "w") as f:
                json.dump(json_state, f, indent=4)
            self.logger.info(f"Wrote alloc to {self.options.output_alloc}")
        else:
            print(json.dumps(json_state, indent=4), file=sys.stdout)

        if self.options.output_result != "stdout":
            with open(self.options.output_result, "w") as f:
                json.dump(json_result, f, indent=4)
            self.logger.info(f"Wrote result to {self.options.output_result}")
        else:
            print(json.dumps(json_result, indent=4), file=sys.stdout)

        return 0
