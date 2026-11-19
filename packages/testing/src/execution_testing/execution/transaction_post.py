"""Simple transaction-send then post-check execution format."""

from itertools import groupby
from typing import Any, ClassVar, Dict, List

import pytest
from pytest import FixtureRequest

from execution_testing.base_types import Address, Hash
from execution_testing.forks import Fork
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    SendTransactionExceptionError,
)
from execution_testing.test_types import (
    Account,
    Alloc,
    BlockAccessList,
    BlockAccessListExpectation,
    Environment,
    NetworkWrappedTransaction,
    PostStateContext,
    TestPhase,
    Transaction,
    TransactionReceipt,
    TransactionTestMetadata,
    verify_transaction_receipt,
)
from execution_testing.test_types.balance_expectations import (
    TransactionKey,
    TransactionLanding,
    transaction_key,
)

from .base import BaseExecute, ExecuteResult

logger = get_logger(__name__)


class RPCTransactionLanding(TransactionLanding):
    """
    Landing of a transaction on a live network, fetched piece by piece.

    The receipt is requested the first time any value is needed; the block
    is requested only for the base fee or the fee recipient, so a sender's
    `GasFee` costs a single receipt request.
    """

    _context: "RPCPostStateContext"
    _tx_hash: Hash
    _receipt: Dict[str, Any] | None

    def __init__(
        self, *, context: "RPCPostStateContext", tx_hash: Hash
    ) -> None:
        """Track the transaction `tx_hash`, without fetching anything yet."""
        self._context = context
        self._tx_hash = tx_hash
        self._receipt = None

    def receipt(self) -> Dict[str, Any]:
        """Return the transaction receipt, fetching it on first use."""
        if self._receipt is None:
            receipt = self._context.eth_rpc.get_transaction_receipt(
                self._tx_hash
            )
            assert receipt is not None, f"missing receipt for {self._tx_hash}"
            self._receipt = receipt
        return self._receipt

    def block(self) -> Dict[str, Any]:
        """Return the block the transaction landed in."""
        return self._context.block(Hash(self.receipt()["blockHash"]))

    def effective_gas_price(self) -> int:
        """Return the price per gas the transaction paid."""
        return int(self.receipt()["effectiveGasPrice"], 16)

    def base_fee_per_gas(self) -> int:
        """Return the block base fee, or zero before the London fork."""
        base_fee = self.block().get("baseFeePerGas")
        return int(base_fee, 16) if base_fee else 0

    def blob_gas_price(self) -> int | None:
        """Return the blob gas price the transaction paid, if any."""
        blob_gas_price = self.receipt().get("blobGasPrice")
        return int(blob_gas_price, 16) if blob_gas_price else None

    def fee_recipient(self) -> Address:
        """Return the block fee recipient."""
        return Address(self.block()["miner"])


class RPCPostStateContext(PostStateContext):
    """
    Context for execute, where transactions land on a live network.

    Nothing is fetched up front: each landing requests its receipt and block
    only when an expectation needs them, and each block is fetched at most
    once however many of the transactions landed in it.
    """

    eth_rpc: EthRPC
    _landings: Dict[TransactionKey, RPCTransactionLanding]
    _blocks: Dict[Hash, Dict[str, Any]]

    def __init__(self, *, eth_rpc: EthRPC, txs: List[Transaction]) -> None:
        """Track the sent `txs`, without fetching anything yet."""
        self.eth_rpc = eth_rpc
        self._landings = {
            transaction_key(tx): RPCTransactionLanding(
                context=self, tx_hash=tx.hash
            )
            for tx in txs
        }
        self._blocks = {}

    def block(self, block_hash: Hash) -> Dict[str, Any]:
        """Return the block `block_hash`, fetching it on first use."""
        if block_hash not in self._blocks:
            block = self.eth_rpc.get_block_by_hash(block_hash, full_txs=False)
            assert block is not None, f"block {block_hash} not found"
            self._blocks[block_hash] = block
        return self._blocks[block_hash]

    def landing(self, key: TransactionKey) -> TransactionLanding:
        """Return the landing of the transaction `key`."""
        if key not in self._landings:
            raise PostStateContext.TransactionNotLandedError(key)
        return self._landings[key]


class TransactionPost(BaseExecute):
    """
    Represents a simple transaction-send then post-check execution format.
    """

    blocks: List[List[Transaction]]
    post: Alloc
    expected_block_access_list: BlockAccessListExpectation | None = None

    format_name: ClassVar[str] = "transaction_post_test"
    description: ClassVar[str] = (
        "Simple transaction sending, then post-check after all transactions "
        "are included"
    )

    def prepare_transactions(
        self,
        *,
        env: Environment,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
        fork: Fork,
    ) -> None:
        """Prepare transactions by setting their final gas properties."""
        for block in self.blocks:
            max_tx_gas_limit = Transaction.calculate_max_gas_limit(
                txs=block,
                env_gas_limit=int(env.gas_limit),
                transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                transaction_total_gas_limit_cap=(
                    fork.transaction_total_gas_limit_cap()
                ),
            )
            for tx in block:
                tx.set_gas_limit(
                    max_gas_limit=max_tx_gas_limit,
                    transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                    state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                    transaction_total_gas_limit_cap=(
                        fork.transaction_total_gas_limit_cap()
                    ),
                )
                tx.set_gas_price(
                    gas_price=gas_price,
                    max_fee_per_gas=max_fee_per_gas,
                    max_priority_fee_per_gas=max_priority_fee_per_gas,
                    max_fee_per_blob_gas=max_fee_per_blob_gas,
                )

    def get_required_sender_balances(
        self, *, fork: Fork
    ) -> Dict[Address, int]:
        """Get the required sender balances."""
        balances: Dict[Address, int] = {}
        for block in self.blocks:
            for tx in block:
                sender = tx.sender
                assert sender is not None, "Sender is None"
                if sender not in balances:
                    balances[sender] = 0
                balances[sender] += tx.signer_minimum_balance(fork=fork)
        return balances

    def snapshot_pre_state(self, eth_rpc: EthRPC) -> Alloc:
        """
        Fetch the live state of the post accounts that expect changes.

        The test's `pre` is not authoritative on a live network: senders are
        topped up to cover their transactions, and accounts the test did not
        create (fee recipients, precompiles, system contracts) may already
        hold a balance.
        """
        relative_fields = {"balance_change", "nonce_change"}
        relative = Alloc(
            {
                address: Account()
                for address, account in self.post.root.items()
                if account is not None
                and relative_fields & account.model_fields_set
            }
        )
        return eth_rpc.get_alloc(relative, skip_code=True)

    def verify_receipts(
        self, eth_rpc: EthRPC, tx_groups: List[List[Transaction]]
    ) -> None:
        """
        Verify the receipts of the landed transactions of every group.

        A group is the set of transactions the test declared together, not a
        network block: the node is free to spread them over several blocks,
        and to pack transactions of its own alongside them. So
        `cumulative_gas_used` is re-derived by adding up the gas used by the
        test's own transactions, in the order the test declared them, and
        restarts at every group.
        """
        for tx_group in tx_groups:
            last_expecting = -1
            for tx_index, tx in enumerate(tx_group):
                if tx.expected_receipt is not None:
                    last_expecting = tx_index
            if last_expecting < 0:
                continue
            verified_txs = tx_group[: last_expecting + 1]
            receipts = eth_rpc.get_transaction_receipts(
                [tx.hash for tx in verified_txs]
            )
            cumulative_gas_used = 0
            for tx_index, (tx, receipt_data) in enumerate(
                zip(verified_txs, receipts, strict=True)
            ):
                assert receipt_data is not None, (
                    f"Failed to get receipt for transaction {tx.hash}"
                )
                receipt = TransactionReceipt.model_validate(receipt_data)
                assert receipt.gas_used is not None, (
                    f"Receipt of transaction {tx.hash} has no gas used"
                )
                previous_cumulative_gas_used = cumulative_gas_used
                cumulative_gas_used += receipt.gas_used
                verify_transaction_receipt(
                    transaction_index=tx_index,
                    previous_cumulative_gas_used=previous_cumulative_gas_used,
                    expected_receipt=tx.expected_receipt,
                    actual_receipt=receipt.copy(
                        cumulative_gas_used=cumulative_gas_used
                    ),
                )

    def verify_block_access_list(
        self, eth_rpc: EthRPC, tx_groups: List[List[Transaction]]
    ) -> None:
        """Verify the block access list of the landed transaction's block."""
        expectation = self.expected_block_access_list
        if expectation is None:
            return
        txs = [tx for tx_group in tx_groups for tx in tx_group]
        assert len(txs) == 1, (
            "Block access list verification expects a single transaction, "
            f"got {len(txs)}"
        )
        receipt = eth_rpc.get_transaction_receipt(txs[0].hash)
        assert receipt is not None, (
            f"Failed to get receipt for transaction {txs[0].hash}"
        )
        transaction_index = int(receipt["transactionIndex"], 16)

        def live_index(index: int) -> int:
            """
            Return the place a block access index takes on a live network.

            A test numbers its indices for a block holding only its own
            transaction: zero is the block's system operations, which do
            not move; one is the transaction, which does.
            """
            if index > 1:
                raise NotImplementedError(
                    f"Block access index {index} cannot be located on a "
                    "live network: only a block's system operations (0) "
                    "and the test's own transaction (1) can be."
                )
            return 0 if index == 0 else transaction_index + 1

        block_hash = Hash(receipt["blockHash"])
        block_access_list = eth_rpc.get_block_access_list(block_hash)
        assert block_access_list is not None, (
            f"Node served no block access list for block {block_hash}"
        )
        expectation.with_remapped_indices(live_index).verify_against(
            BlockAccessList.from_rpc(block_access_list)
        )

    def verify_blob_txs_wrapped(self) -> None:
        """Assert every blob transaction arrived together with its blobs."""
        for block in self.blocks:
            for tx in block:
                if not isinstance(tx, NetworkWrappedTransaction):
                    assert tx.ty != 3, (
                        "Unwrapped transaction type 3 is not supported in "
                        "execute mode."
                    )

    @staticmethod
    def sign_and_annotate(
        block: List[Transaction], request: FixtureRequest
    ) -> List[Transaction]:
        """Sign every transaction of a group and tag it for reporting."""
        signed_txs: List[Transaction] = []
        for tx_index, tx in enumerate(block):
            tx = tx.with_signature_and_sender()
            to_address = tx.to
            label = (
                to_address.label if isinstance(to_address, Address) else None
            )
            phase = (
                tx.test_phase
                if tx.test_phase is not None
                else TestPhase.EXECUTION
            )
            tx.metadata = TransactionTestMetadata(
                test_id=request.node.nodeid,
                phase=phase,
                target=label,
                tx_index=tx_index,
            )
            signed_txs.append(tx)
        return signed_txs

    @staticmethod
    def send_group(
        eth_rpc: EthRPC, signed_txs: List[Transaction]
    ) -> List[Hash]:
        """
        Send a group of transactions and return the hashes that landed.

        A transaction the test expects to be rejected never lands, so the
        transactions declared before it are sent and waited for first: the
        ones that do land have to land in the order the test declared them.
        """
        landed_hashes: List[Hash] = []
        for sendable, run in groupby(
            signed_txs, key=lambda tx: tx.error is None
        ):
            txs = list(run)
            if sendable:
                eth_rpc.send_wait_transactions(txs)
                landed_hashes.extend(tx.hash for tx in txs)
                continue
            for tx in txs:
                logger.info(
                    "Sending transaction expecting rejection "
                    f"(expected error: {tx.error})..."
                )
                with pytest.raises(SendTransactionExceptionError) as exc_info:
                    eth_rpc.send_transaction(tx)
                logger.info(
                    f"Transaction rejected as expected: {exc_info.value}"
                )
        return landed_hashes

    @staticmethod
    def landed_transactions(
        signed_txs: List[Transaction],
    ) -> List[Transaction]:
        """Return the transactions of a group that are expected to land."""
        return [
            tx.tx if isinstance(tx, NetworkWrappedTransaction) else tx
            for tx in signed_txs
            if tx.error is None
        ]

    @staticmethod
    def total_gas_used(eth_rpc: EthRPC, tx_hashes: List[Hash]) -> int:
        """Return the gas the given transactions used in total."""
        receipts = eth_rpc.get_transaction_receipts(tx_hashes)
        gas_used = 0
        for tx_hash, receipt in zip(tx_hashes, receipts, strict=True):
            assert receipt is not None, (
                f"Failed to get receipt for transaction {tx_hash}"
            )
            gas_used += int(receipt["gasUsed"], 16)
        return gas_used

    @staticmethod
    def verify_account_empty(address: Address, account: Account) -> None:
        """Assert an account the test excluded from the post state is empty."""
        assert account.balance == 0, (
            f"Balance of {address} is {account.balance}, expected 0."
        )
        assert account.code == b"", (
            f"Code of {address} is {account.code}, expected 0x."
        )
        assert account.nonce == 0, (
            f"Nonce of {address} is {account.nonce}, expected 0."
        )

    def verify_post(
        self,
        eth_rpc: EthRPC,
        landed_tx_groups: List[List[Transaction]],
        pre_state: Alloc,
    ) -> None:
        """Verify the post state of every account the test named."""
        actual_alloc = eth_rpc.get_alloc(self.post)
        context = RPCPostStateContext(
            eth_rpc=eth_rpc,
            txs=[tx for group in landed_tx_groups for tx in group],
        )
        for address, expected_account in self.post.root.items():
            actual_account = actual_alloc.root[address]
            assert actual_account is not None
            if expected_account is None:
                self.verify_account_empty(address, actual_account)
            else:
                expected_account.check_alloc(
                    address=address,
                    pre_account=pre_state.root.get(address),
                    account=actual_account,
                    context=context,
                )

    def execute(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        request: FixtureRequest,
    ) -> ExecuteResult:
        """Execute the format."""
        del fork
        del engine_rpc

        self.verify_blob_txs_wrapped()
        pre_state = self.snapshot_pre_state(eth_rpc)

        landed_tx_groups: List[List[Transaction]] = []
        last_group_hashes: List[Hash] = []
        for block in self.blocks:
            signed_txs = self.sign_and_annotate(block, request)
            last_group_hashes = self.send_group(eth_rpc, signed_txs)
            landed_tx_groups.append(self.landed_transactions(signed_txs))

        self.verify_receipts(eth_rpc, landed_tx_groups)
        self.verify_block_access_list(eth_rpc, landed_tx_groups)

        benchmark_gas_used: int | None = None
        if self.benchmark_mode:
            benchmark_gas_used = self.total_gas_used(
                eth_rpc, last_group_hashes
            )

        self.verify_post(eth_rpc, landed_tx_groups, pre_state)

        return ExecuteResult(
            benchmark_gas_used=benchmark_gas_used,
        )
