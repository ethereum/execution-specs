"""
Contains various providers which generates context required to create test scripts.

Classes:
- BlockchainTestProvider: The BlockchainTestProvider class takes information about a block,
a transaction, and the associated state, and provides methods to generate various elements
needed for testing, such as module docstrings, test names, and pre-state items.

Example:
    provider = BlockchainTestProvider(block=block, transaction=transaction, state=state)
    context = provider.get_context()

"""

from typing import Any, Dict

from pydantic import BaseModel

from ethereum_test_base_types import Account, Address, ZeroPaddedHexNumber

from .request_manager import RPCRequest


class BlockchainTestProvider(BaseModel):
    """Provides context required to generate a `blockchain_test` using pytest."""

    block: RPCRequest.RemoteBlock
    transaction: RPCRequest.RemoteTransaction
    state: Dict[Address, Account]

    def _get_environment_kwargs(self) -> str:
        env_str = ""
        pad = "        "
        for field, value in self.block.dict().items():
            env_str += (
                f'{pad}{field}="{value}",\n' if field == "coinbase" else f"{pad}{field}={value},\n"
            )

        return env_str

    # TODO: Output should be dict. Formatting should happen in the template.
    def _get_pre_state_items(self) -> str:
        # Print a nice .py storage pre
        pad = "            "
        state_str = ""
        for address, account_obj in self.state.items():
            state_str += f'        "{address}": Account(\n'
            state_str += f"{pad}balance={str(account_obj.balance)},\n"
            if address == self.transaction.sender:
                state_str += f"{pad}nonce={self.transaction.nonce},\n"
            else:
                state_str += f"{pad}nonce={str(account_obj.nonce)},\n"

            if account_obj.code is None:
                state_str += f'{pad}code="0x",\n'
            else:
                state_str += f'{pad}code="{str(account_obj.code)}",\n'
            state_str += pad + "storage={\n"

            if account_obj.storage is not None:
                for record, value in account_obj.storage.root.items():
                    pad_record = ZeroPaddedHexNumber(record)
                    pad_value = ZeroPaddedHexNumber(value)
                    state_str += f'{pad}    "{pad_record}" : "{pad_value}",\n'

            state_str += pad + "}\n"
            state_str += "        ),\n"
        return state_str

    # TODO: Output should be dict. Formatting should happen in the template.
    def _get_transaction_items(self) -> str:
        """Print legacy transaction in .py."""
        pad = "            "
        tr_str = ""
        quoted_fields_array = ["data", "to"]
        hex_fields_array = ["v", "r", "s"]
        legacy_fields_array = [
            "ty",
            "chain_id",
            "nonce",
            "gas_price",
            "protected",
            "gas_limit",
            "value",
        ]
        for field, value in iter(self.transaction):
            if value is None:
                continue

            if field in legacy_fields_array:
                tr_str += f"{pad}{field}={value},\n"

            if field in quoted_fields_array:
                tr_str += f'{pad}{field}="{value}",\n'

            if field in hex_fields_array:
                tr_str += f"{pad}{field}={hex(value)},\n"

        return tr_str

    def get_context(self) -> Dict[str, Any]:
        """
        Get the context for generating a blockchain test.

        Returns:
            Dict[str, Any]: A dictionary containing module docstring, test name,
            test docstring, environment kwargs, pre-state items, and transaction items.

        """
        return {
            "environment_kwargs": self._get_environment_kwargs(),
            "pre_state_items": self._get_pre_state_items(),
            "transaction_items": self._get_transaction_items(),
            "tx_hash": self.transaction.tx_hash,
        }
