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

from pydantic import BaseModel

from config import EnvConfig
from ethereum_test_base_types import Hash, HexNumber
from ethereum_test_rpc import BlockNumberType, DebugRPC, EthRPC
from ethereum_test_types import Transaction


class RPCRequest:
    """Interface for the RPC interaction with remote node."""

    class RemoteTransaction(Transaction):
        """Model that represents a transaction."""

        block_number: HexNumber
        tx_hash: Hash

    class RemoteBlock(BaseModel):
        """Model that represents a block."""

        coinbase: str
        difficulty: str
        gas_limit: str
        number: str
        timestamp: str

    node_url: str
    headers: dict[str, str]

    def __init__(self):
        """Initialize the RequestManager with specific client config."""
        node_config = EnvConfig().remote_nodes[0]
        self.node_url = node_config.node_url
        headers = node_config.rpc_headers
        self.rpc = EthRPC(node_config.node_url, extra_headers=headers)
        self.debug_rpc = DebugRPC(node_config.node_url, extra_headers=headers)

    def eth_get_transaction_by_hash(self, transaction_hash: Hash) -> RemoteTransaction:
        """Get transaction data."""
        res = self.rpc.get_transaction_by_hash(transaction_hash)
        block_number = res.block_number
        assert block_number is not None, "Transaction does not seem to be included in any block"

        assert (
            res.ty == 0
        ), f"Transaction has type {res.ty}: Currently only type 0 transactions are supported."

        return RPCRequest.RemoteTransaction(
            block_number=block_number,
            tx_hash=res.transaction_hash,
            ty=res.ty,
            gas_limit=res.gas_limit,
            gas_price=res.gas_price,
            data=res.data,
            nonce=res.nonce,
            sender=res.from_address,
            to=res.to_address,
            value=res.value,
            v=res.v,
            r=res.r,
            s=res.s,
            protected=True if res.v > 30 else False,
        )

    def eth_get_block_by_number(self, block_number: BlockNumberType) -> RemoteBlock:
        """Get block by number."""
        res = self.rpc.get_block_by_number(block_number)

        return RPCRequest.RemoteBlock(
            coinbase=res["miner"],
            number=res["number"],
            difficulty=res["difficulty"],
            gas_limit=res["gasLimit"],
            timestamp=res["timestamp"],
        )

    def debug_trace_call(self, transaction: RemoteTransaction) -> Dict[str, dict]:
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
