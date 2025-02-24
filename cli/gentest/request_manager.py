"""
A request manager Ethereum  RPC calls.

The RequestManager handles transactions and block data retrieval from a remote Ethereum node,
utilizing Pydantic models to define the structure of transactions and blocks.

Classes:
- RequestManager: The main class for managing RPC requests and responses.
- RemoteTransaction: A Pydantic model representing a transaction retrieved from the node.
- RemoteBlock: A Pydantic model representing a block retrieved from the node.
"""

from typing import Dict

from config import EnvConfig
from ethereum_test_base_types import Hash
from ethereum_test_rpc import BlockNumberType, DebugRPC, EthRPC
from ethereum_test_rpc.types import TransactionByHashResponse
from ethereum_test_types import Environment


class RPCRequest:
    """Interface for the RPC interaction with remote node."""

    node_url: str
    headers: dict[str, str]

    def __init__(self):
        """Initialize the RequestManager with specific client config."""
        node_config = EnvConfig().remote_nodes[0]
        self.node_url = node_config.node_url
        headers = node_config.rpc_headers
        self.rpc = EthRPC(node_config.node_url, extra_headers=headers)
        self.debug_rpc = DebugRPC(node_config.node_url, extra_headers=headers)

    def eth_get_transaction_by_hash(self, transaction_hash: Hash) -> TransactionByHashResponse:
        """Get transaction data."""
        res = self.rpc.get_transaction_by_hash(transaction_hash)
        block_number = res.block_number
        assert block_number is not None, "Transaction does not seem to be included in any block"

        return res

    def eth_get_block_by_number(self, block_number: BlockNumberType) -> Environment:
        """Get block by number."""
        res = self.rpc.get_block_by_number(block_number)

        return Environment(
            fee_recipient=res["miner"],
            number=res["number"],
            difficulty=res["difficulty"],
            gas_limit=res["gasLimit"],
            timestamp=res["timestamp"],
        )

    def debug_trace_call(self, transaction: TransactionByHashResponse) -> Dict[str, dict]:
        """Get pre-state required for transaction."""
        assert transaction.sender is not None
        assert transaction.to is not None

        return self.debug_rpc.trace_call(
            {
                "from": transaction.sender.hex(),
                "to": transaction.to.hex(),
                "data": transaction.data.hex(),
            },
            f"{transaction.block_number}",
        )
