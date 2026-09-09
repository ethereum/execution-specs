"""
Loader for code from the relevant fork.
"""

from importlib import import_module
from inspect import signature
from typing import Any, Final

from ethereum.state import EMPTY_ACCOUNT
from ethereum_spec_tools.forks import Hardfork


class ForkLoad:
    """
    Load the functions and classes from the relevant fork.
    """

    hardfork: Final[Hardfork]

    def __init__(self, hardfork: Hardfork):
        self.hardfork = hardfork

    def _module(self, name: str) -> Any:
        """Imports a module from the fork."""
        return self.hardfork.module(name)

    def tx_types(self) -> list[int]:
        """Return the transaction types supported by the given fork."""
        transactions = self._module("transactions")
        tx_types = [0]

        for tx_type, attribute in (
            (1, "AccessListTransaction"),
            (2, "FeeMarketTransaction"),
            (3, "BlobTransaction"),
            (4, "SetCodeTransaction"),
        ):
            if hasattr(transactions, attribute):
                tx_types.append(tx_type)

        return tx_types

    def supports_tx_type(self, tx_type: int) -> bool:
        """Return whether the given fork supports the provided tx type."""
        return tx_type in self.tx_types()

    @property
    def proof_of_stake(self) -> bool:
        """Whether the fork is proof of stake."""
        return self.hardfork.consensus.is_pos()

    @property
    def BEACON_ROOTS_ADDRESS(self) -> Any:
        """BEACON_ROOTS_ADDRESS of the given fork."""
        return self._module("fork").BEACON_ROOTS_ADDRESS

    @property
    def has_beacon_roots_address(self) -> bool:
        """Check if the fork has a `BEACON_ROOTS_ADDRESS` constant."""
        return hasattr(self._module("fork"), "BEACON_ROOTS_ADDRESS")

    @property
    def HISTORY_STORAGE_ADDRESS(self) -> Any:
        """HISTORY_STORAGE_ADDRESS of the given fork."""
        return self._module("fork").HISTORY_STORAGE_ADDRESS

    @property
    def BLOCK_REWARD(self) -> Any:
        """BLOCK_REWARD of the given fork."""
        return self._module("fork").BLOCK_REWARD

    @property
    def process_general_purpose_requests(self) -> Any:
        """process_general_purpose_requests function of the given fork."""
        return self._module("fork").process_general_purpose_requests

    @property
    def process_unchecked_system_transaction(self) -> Any:
        """process_unchecked_system_transaction function of the given fork."""
        return self._module("fork").process_unchecked_system_transaction

    @property
    def process_withdrawals(self) -> Any:
        """process_withdrawals function of the given fork."""
        return self._module("fork").process_withdrawals

    @property
    def calculate_block_difficulty(self) -> Any:
        """calculate_block_difficulty function of the given fork."""
        return self._module("fork").calculate_block_difficulty

    @property
    def calculate_block_difficulty_arity(self) -> int:
        """Number of parameters required by `calculate_block_difficulty`."""
        inspected = signature(self._module("fork").calculate_block_difficulty)
        return len(inspected.parameters)

    @property
    def calculate_base_fee_per_gas(self) -> Any:
        """calculate_base_fee_per_gas function of the given fork."""
        return self._module("fork").calculate_base_fee_per_gas

    @property
    def has_calculate_base_fee_per_gas(self) -> bool:
        """Check if the fork has a `calculate_base_fee_per_gas` function."""
        return hasattr(self._module("fork"), "calculate_base_fee_per_gas")

    @property
    def logs_bloom(self) -> Any:
        """logs_bloom function of the given fork."""
        return self._module("bloom").logs_bloom

    @property
    def BlockChain(self) -> Any:
        """Block chain class of the fork."""
        return self._module("fork").BlockChain

    @property
    def state_transition(self) -> Any:
        """state_transition function of the fork."""
        return self._module("fork").state_transition

    @property
    def has_block_start_transition(self) -> bool:
        """Whether this fork defines a block-start state transition."""
        return hasattr(self._module("fork"), "apply_block_start_transition")

    @property
    def apply_block_start_transition(self) -> Any:
        """Block-start state transition function of the fork."""
        return self._module("fork").apply_block_start_transition

    @property
    def signing_hash(self) -> Any:
        """signing_hash function of the fork."""
        return self._module("transactions").signing_hash

    @property
    def signing_hash_pre155(self) -> Any:
        """signing_hash_pre155 function of the fork."""
        return self._module("transactions").signing_hash_pre155

    @property
    def signing_hash_155(self) -> Any:
        """signing_hash_155 function of the fork."""
        return self._module("transactions").signing_hash_155

    @property
    def build_block_access_list(self) -> Any:
        """build_block_access_list function of the fork."""
        return self._module("block_access_lists").build_block_access_list

    @property
    def hash_block_access_list(self) -> Any:
        """hash_block_access_list function of the fork."""
        return self._module("block_access_lists").hash_block_access_list

    @property
    def has_hash_block_access_list(self) -> bool:
        """Check if the fork has a `hash_block_access_list` function."""
        try:
            module = self._module("block_access_lists")
        except ModuleNotFoundError:
            return False
        return hasattr(module, "hash_block_access_list")

    @property
    def BlockAccessIndex(self) -> Any:
        """BlockAccessIndex type of the fork."""
        return self._module("block_access_lists").BlockAccessIndex

    @property
    def BlockAccessListBuilder(self) -> Any:
        """BlockAccessListBuilder class of the fork."""
        return self._module("block_access_lists").BlockAccessListBuilder

    @property
    def validate_block_access_list_gas_limit(self) -> Any:
        """validate_block_access_list_gas_limit function of the fork."""
        return self._module(
            "block_access_lists"
        ).validate_block_access_list_gas_limit

    @property
    def signing_hash_2930(self) -> Any:
        """signing_hash_2930 function of the fork."""
        return self._module("transactions").signing_hash_2930

    @property
    def signing_hash_1559(self) -> Any:
        """signing_hash_1559 function of the fork."""
        return self._module("transactions").signing_hash_1559

    @property
    def signing_hash_7702(self) -> Any:
        """signing_hash_7702 function of the fork."""
        return self._module("transactions").signing_hash_7702

    @property
    def signing_hash_4844(self) -> Any:
        """signing_hash_4844 function of the fork."""
        return self._module("transactions").signing_hash_4844

    @property
    def get_transaction_hash(self) -> Any:
        """get_transaction_hash function of the fork."""
        return self._module("transactions").get_transaction_hash

    @property
    def process_transaction(self) -> Any:
        """process_transaction function of the fork."""
        return self._module("fork").process_transaction

    @property
    def Block(self) -> Any:
        """Block class of the fork."""
        return self._module("blocks").Block

    @property
    def decode_receipt(self) -> Any:
        """decode_receipt function of the fork."""
        return self._module("blocks").decode_receipt

    @property
    def compute_requests_hash(self) -> Any:
        """compute_requests_hash function of the fork."""
        return self._module("requests").compute_requests_hash

    @property
    def has_compute_requests_hash(self) -> bool:
        """Check if the fork has a `compute_requests_hash` function."""
        try:
            module = self._module("requests")
        except ModuleNotFoundError:
            return False
        return hasattr(module, "compute_requests_hash")

    @property
    def Bloom(self) -> Any:
        """Bloom class of the fork."""
        return self._module("fork_types").Bloom

    @property
    def EMPTY_ACCOUNT(self) -> Any:
        """EMPTY_ACCOUNT of the fork."""
        return EMPTY_ACCOUNT

    @property
    def Header(self) -> Any:
        """Header class of the fork."""
        return self._module("blocks").Header

    @property
    def Account(self) -> Any:
        """Account class of the fork."""
        return self._module("fork_types").Account

    @property
    def Transaction(self) -> Any:
        """Transaction class of the fork."""
        return self._module("transactions").Transaction

    @property
    def LegacyTransaction(self) -> Any:
        """Legacytransaction class of the fork."""
        return self._module("transactions").LegacyTransaction

    @property
    def Access(self) -> Any:
        """Access class of the fork."""
        return self._module("transactions").Access

    @property
    def AccessListTransaction(self) -> Any:
        """Access List transaction class of the fork."""
        return self._module("transactions").AccessListTransaction

    @property
    def FeeMarketTransaction(self) -> Any:
        """Fee Market transaction class of the fork."""
        return self._module("transactions").FeeMarketTransaction

    @property
    def BlobTransaction(self) -> Any:
        """Blob transaction class of the fork."""
        return self._module("transactions").BlobTransaction

    @property
    def SetCodeTransaction(self) -> Any:
        """Set code transaction class of the fork."""
        return self._module("transactions").SetCodeTransaction

    @property
    def Withdrawal(self) -> Any:
        """Withdrawal class of the fork."""
        return self._module("blocks").Withdrawal

    @property
    def has_withdrawal(self) -> bool:
        """Check if the fork has a `Withdrawal` class."""
        return hasattr(self._module("blocks"), "Withdrawal")

    @property
    def has_slot_number(self) -> bool:
        """Check if the fork supports the SLOTNUM opcode (EIP-7843)."""
        try:
            block_env = self._module("vm").BlockEnvironment
            return "slot_number" in block_env.__dataclass_fields__
        except (ModuleNotFoundError, AttributeError):
            return False

    @property
    def decode_transaction(self) -> Any:
        """decode_transaction function of the fork."""
        return self._module("transactions").decode_transaction

    @property
    def state_provider(self) -> Any:
        """
        Module implementing the fork's state provider.

        Resolved through the ``State`` class the fork's ``fork``
        module imports, so each fork selects its own commitment
        scheme (``ethereum.state_mpt``, ``ethereum.state_pbt``, ...).
        """
        return import_module(self._module("fork").State.__module__)

    @property
    def BlockState(self) -> Any:
        """BlockState class of the fork."""
        return self._module("state_tracker").BlockState

    @property
    def TransactionState(self) -> Any:
        """TransactionState class of the fork."""
        return self._module("state_tracker").TransactionState

    @property
    def incorporate_tx_into_block(self) -> Any:
        """incorporate_tx_into_block function of the fork."""
        return self._module("state_tracker").incorporate_tx_into_block

    @property
    def extract_block_diff(self) -> Any:
        """extract_block_diff function of the fork."""
        return self._module("state_tracker").extract_block_diff

    @property
    def create_ether(self) -> Any:
        """create_ether function of the fork."""
        return self._module("state_tracker").create_ether

    @property
    def hex_to_address(self) -> Any:
        """hex_to_address function of the fork."""
        return self._module("utils.hexadecimal").hex_to_address

    @property
    def hex_to_root(self) -> Any:
        """hex_to_root function of the fork."""
        return self._module("utils.hexadecimal").hex_to_root

    @property
    def BlockEnvironment(self) -> Any:
        """Block environment class of the fork."""
        return self._module("vm").BlockEnvironment

    @property
    def BlockOutput(self) -> Any:
        """Block output class of the fork."""
        return self._module("vm").BlockOutput

    @property
    def Authorization(self) -> Any:
        """Authorization class of the fork."""
        return self._module("fork_types").Authorization

    @property
    def calculate_excess_blob_gas(self) -> Any:
        """calculate_excess_blob_gas of the fork."""
        return self._module("vm.gas").calculate_excess_blob_gas

    @property
    def calculate_blob_gas_price(self) -> Any:
        """calculate_blob_gas_price of the fork."""
        return self._module("vm.gas").calculate_blob_gas_price

    @property
    def apply_dao(self) -> Any:
        """apply_dao function of the fork."""
        return self._module("dao").apply_dao
