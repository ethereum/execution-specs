"""Types used in the transition tool interactions."""

from typing import List

from pydantic import Field

from ethereum_test_base_types import Bloom, Bytes, CamelModel, Hash, HexNumber
from ethereum_test_types import Alloc, Environment, Transaction, TransactionReceipt


class RejectedTransaction(CamelModel):
    """Rejected transaction."""

    index: HexNumber
    error: str


class Result(CamelModel):
    """Result of a transition tool output."""

    state_root: Hash
    ommers_hash: Hash | None = Field(None, validation_alias="sha3Uncles")
    transactions_trie: Hash = Field(..., alias="txRoot")
    receipts_root: Hash
    logs_hash: Hash
    logs_bloom: Bloom
    receipts: List[TransactionReceipt]
    rejected_transactions: List[RejectedTransaction] = Field(
        default_factory=list, alias="rejected"
    )
    difficulty: HexNumber | None = Field(None, alias="currentDifficulty")
    gas_used: HexNumber
    base_fee_per_gas: HexNumber | None = Field(None, alias="currentBaseFee")
    withdrawals_root: Hash | None = None
    excess_blob_gas: HexNumber | None = Field(None, alias="currentExcessBlobGas")
    blob_gas_used: HexNumber | None = None
    requests_hash: Hash | None = None
    requests: List[Bytes] | None = None


class TransitionToolInput(CamelModel):
    """Transition tool input."""

    alloc: Alloc
    txs: List[Transaction]
    env: Environment


class TransitionToolOutput(CamelModel):
    """Transition tool output."""

    alloc: Alloc
    result: Result
    body: Bytes | None = None


class TransitionToolContext(CamelModel):
    """Transition tool context."""

    fork: str
    chain_id: int = Field(..., alias="chainid")
    reward: int


class TransitionToolRequest(CamelModel):
    """Transition tool server request data."""

    state: TransitionToolContext
    input: TransitionToolInput
