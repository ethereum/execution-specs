"""
Loader for code from the relevant fork.
"""

import importlib
from typing import Any

from ethereum_spec_tools.forks import Hardfork


class ForkLoad:
    """
    Load the functions and classes from the relevant fork.
    """

    _fork_module: str
    _forks: Any

    def __init__(self, fork_module: str):
        self._fork_module = fork_module
        self._forks = Hardfork.discover()

    @property
    def fork_module(self) -> str:
        """Module that contains the fork code"""
        return self._fork_module

    def _module(self, name: str) -> Any:
        """Imports a module from the fork"""
        return importlib.import_module(f"ethereum.{self._fork_module}.{name}")

    @property
    def proof_of_stake(self) -> bool:
        """Whether the fork is proof of stake"""
        for fork in self._forks:
            if fork.name == "ethereum." + self._fork_module:
                return fork.consensus.is_pos()
        raise Exception(f"fork {self._fork_module} not discovered")

    def is_after_fork(self, target_fork_name: str) -> bool:
        """Check if the fork is after the target fork"""
        return_value = False
        for fork in self._forks:
            if fork.name == target_fork_name:
                return_value = True
            if fork.name == "ethereum." + self._fork_module:
                break
        return return_value

    @property
    def calculate_block_difficulty(self) -> Any:
        """calculate_block_difficulty function of the given fork."""
        return self._module("fork").calculate_block_difficulty

    @property
    def calculate_base_fee_per_gas(self) -> Any:
        """calculate_base_fee_per_gas function of the given fork."""
        return self._module("fork").calculate_base_fee_per_gas

    @property
    def logs_bloom(self) -> Any:
        """logs_bloom function of the given fork."""
        return self._module("bloom").logs_bloom

    @property
    def BlockChain(self) -> Any:
        """Block chain class of the fork"""
        return self._module("fork").BlockChain

    @property
    def state_transition(self) -> Any:
        """state_transition function of the fork"""
        return self._module("fork").state_transition

    @property
    def apply_body(self) -> Any:
        """apply_body function of the fork"""
        return self._module("fork").apply_body

    @property
    def create_block_output(self) -> Any:
        """create_block_output function of the fork"""
        return self._module("fork").create_block_output

    @property
    def signing_hash(self) -> Any:
        """signing_hash function of the fork"""
        return self._module("transactions").signing_hash

    @property
    def signing_hash_pre155(self) -> Any:
        """signing_hash_pre155 function of the fork"""
        return self._module("transactions").signing_hash_pre155

    @property
    def signing_hash_155(self) -> Any:
        """signing_hash_155 function of the fork"""
        return self._module("transactions").signing_hash_155

    @property
    def signing_hash_2930(self) -> Any:
        """signing_hash_2930 function of the fork"""
        return self._module("transactions").signing_hash_2930

    @property
    def signing_hash_1559(self) -> Any:
        """signing_hash_1559 function of the fork"""
        return self._module("transactions").signing_hash_1559

    @property
    def signing_hash_7702(self) -> Any:
        """signing_hash_7702 function of the fork"""
        return self._module("transactions").signing_hash_7702

    @property
    def signing_hash_4844(self) -> Any:
        """signing_hash_4844 function of the fork"""
        return self._module("transactions").signing_hash_4844

    @property
    def process_transaction(self) -> Any:
        """process_transaction function of the fork"""
        return self._module("fork").process_transaction

    @property
    def MAX_BLOB_GAS_PER_BLOCK(self) -> Any:
        """MAX_BLOB_GAS_PER_BLOCK parameter of the fork"""
        return self._module("fork").MAX_BLOB_GAS_PER_BLOCK

    @property
    def Block(self) -> Any:
        """Block class of the fork"""
        return self._module("blocks").Block

    @property
    def compute_requests_hash(self) -> Any:
        """compute_requests_hash function of the fork"""
        return self._module("requests").compute_requests_hash

    @property
    def Bloom(self) -> Any:
        """Bloom class of the fork"""
        return self._module("fork_types").Bloom

    @property
    def Header(self) -> Any:
        """Header class of the fork"""
        return self._module("blocks").Header

    @property
    def Account(self) -> Any:
        """Account class of the fork"""
        return self._module("fork_types").Account

    @property
    def Transaction(self) -> Any:
        """Transaction class of the fork"""
        return self._module("transactions").Transaction

    @property
    def LegacyTransaction(self) -> Any:
        """Legacytransaction class of the fork"""
        return self._module("transactions").LegacyTransaction

    @property
    def AccessListTransaction(self) -> Any:
        """Access List transaction class of the fork"""
        return self._module("transactions").AccessListTransaction

    @property
    def FeeMarketTransaction(self) -> Any:
        """Fee Market transaction class of the fork"""
        return self._module("transactions").FeeMarketTransaction

    @property
    def BlobTransaction(self) -> Any:
        """Blob transaction class of the fork"""
        return self._module("transactions").BlobTransaction

    @property
    def SetCodeTransaction(self) -> Any:
        """Set code transaction class of the fork"""
        return self._module("transactions").SetCodeTransaction

    @property
    def Withdrawal(self) -> Any:
        """Withdrawal class of the fork"""
        return self._module("blocks").Withdrawal

    @property
    def encode_transaction(self) -> Any:
        """encode_transaction function of the fork"""
        return self._module("transactions").encode_transaction

    @property
    def decode_transaction(self) -> Any:
        """decode_transaction function of the fork"""
        return self._module("transactions").decode_transaction

    @property
    def State(self) -> Any:
        """State class of the fork"""
        return self._module("state").State

    @property
    def set_account(self) -> Any:
        """set_account function of the fork"""
        return self._module("state").set_account

    @property
    def set_storage(self) -> Any:
        """set_storage function of the fork"""
        return self._module("state").set_storage

    @property
    def state_root(self) -> Any:
        """state_root function of the fork"""
        return self._module("state").state_root

    @property
    def close_state(self) -> Any:
        """close_state function of the fork"""
        return self._module("state").close_state

    @property
    def root(self) -> Any:
        """Root function of the fork"""
        return self._module("trie").root

    @property
    def copy_trie(self) -> Any:
        """copy_trie function of the fork"""
        return self._module("trie").copy_trie

    @property
    def hex_to_address(self) -> Any:
        """hex_to_address function of the fork"""
        return self._module("utils.hexadecimal").hex_to_address

    @property
    def hex_to_root(self) -> Any:
        """hex_to_root function of the fork"""
        return self._module("utils.hexadecimal").hex_to_root

    @property
    def BlockEnvironment(self) -> Any:
        """Block environment class of the fork"""
        return self._module("vm").BlockEnvironment

    @property
    def Authorization(self) -> Any:
        """Authorization class of the fork"""
        return self._module("fork_types").Authorization

    @property
    def TARGET_BLOB_GAS_PER_BLOCK(self) -> Any:
        """TARGET_BLOB_GAS_PER_BLOCK of the fork"""
        return self._module("vm.gas").TARGET_BLOB_GAS_PER_BLOCK

    @property
    def apply_dao(self) -> Any:
        """apply_dao function of the fork"""
        return self._module("dao").apply_dao
