"""revm `revme` transition tool — drives the `revme t8n` subcommand.

This module also owns the base [`RevmExceptionMapper`]: the substring
and regex patterns that match `revm::context_interface::result::
InvalidTransaction`'s `Display` output. Any client that wraps revm
(reth, foundry, anvil, revme, …) inherits from this base and adds only
its own node-layer / validator-layer strings on top.
"""

import re
import subprocess
from pathlib import Path
from typing import ClassVar, Dict, List, Optional

from execution_testing.client_clis.ethereum_cli import EthereumCLI
from execution_testing.client_clis.transition_tool import TransitionTool
from execution_testing.exceptions import (
    BlockException,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.forks import Fork


class RevmExceptionMapper(ExceptionMapper):
    """
    Base mapper for any t8n / client built on revm.

    Entries here match revm's [`InvalidTransaction`] `Display` output
    (see ``revm/crates/context/interface/src/result.rs``). Clients that
    add validator-layer error wrapping (e.g. reth's payload validator
    or consensus engine) inherit and override the relevant entries —
    they never need to redeclare the revm-core strings.
    """

    # revm collapses several framework exception *subtypes* onto a
    # single Display string — most notably the EIP-7623/7976/7981
    # intrinsic-vs-floor gas family, where the same
    # "gas floor (X) exceeds the gas limit (Y)" message must map to
    # either INTRINSIC_GAS_TOO_LOW or INTRINSIC_GAS_BELOW_FLOOR_GAS_COST
    # depending on whether the floor or the intrinsic cost is the
    # binding constraint (a distinction revm doesn't surface). Mark the
    # mapper not-reliable so the framework still enforces correct
    # accept/reject and rejects undefined exceptions, but relaxes the
    # exact-subtype check it cannot satisfy from one string.
    reliable: ClassVar[bool] = False

    mapping_substring = {
        # revm: RejectCallerWithCode
        TransactionException.SENDER_NOT_EOA: (
            "reject transactions from senders with deployed code"
        ),
        # revm: LackOfFundForMaxFee — phrasing "lack of funds (BAL) for
        # max fee (FEE)" — substring match handles both reth's terse
        # "lack of funds" and revm's parenthesised form.
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "lack of funds",
        # revm: CreateInitCodeSizeLimit
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "create initcode size limit"
        ),
        # revm: GasPriceLessThanBasefee
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "gas price is less than basefee"
        ),
        # revm: PriorityFeeGreaterThanMaxFee
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "priority fee is greater than max fee"
        ),
        # revm: OverflowPaymentInTransaction — tightened from a bare
        # "overflow" substring (which over-matched "nonce overflow")
        # to the full Display string. Tx-fee field overflows on the
        # builder side (e.g. tx with gas_price > u128::MAX) map here
        # too; the underlying error in all cases is that
        # gas_limit * gas_price doesn't fit a u128.
        # (Moved to a regex below to cover both the validation-side
        # and builder-side phrasings.)
        # revm: NonceOverflowInTransaction — fires when a sender's
        # nonce is already at u64::MAX. Maps to NONCE_IS_MAX (the
        # framework's name for the same scenario).
        TransactionException.NONCE_IS_MAX: "nonce overflow in transaction",
        # revm: tx_gas_limit overflows u64 — the framework supplied
        # gas > u64::MAX which can't fit in revm's gas counter.
        TransactionException.GASLIMIT_OVERFLOW: "tx gas overflows u64",
        # revme TxEnv builder rejects gas-price fields > u128::MAX with
        # our `"<field> overflows u128"` strings. Semantically the
        # same as OverflowPaymentInTransaction (gas_limit * gas_price
        # would overflow), which is GASLIMIT_PRICE_PRODUCT_OVERFLOW.
        # revm: BlobVersionNotSupported
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "blob version not supported"
        ),
        # revm: BlobCreateTransaction ("blob create transaction") via
        # validation OR MissingTargetForEip4844 ("missing target for
        # EIP-4844") via the TxEnv builder — both fire for a type-3
        # blob tx with no `to`. Moved to a regex below.
        # revm: EmptyAuthorizationList ("empty authorization list") —
        # moved to a regex below so the equivalent
        # MissingAuthorizationListForEip7702 (TxEnv-builder side) is
        # covered too.
        # revm: DeriveTxTypeError::MissingTargetForEip7702 — fires
        # when a type-4 tx is built without a `to` address. Maps to
        # TYPE_4_TX_CONTRACT_CREATION (a type-4 tx must specify a
        # target; contract creation is not allowed for set-code txs).
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "missing target for EIP-7702"
        ),
        # revm: Eip4844NotSupported. The actual rejection path at
        # pre-Cancun forks goes through `Eip4844NotSupported` (which
        # Displays "Eip4844 is not supported") rather than
        # `BlobVersionedHashesNotSupported`. The latter is reachable in
        # some code paths but in practice the framework hits the former.
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "Eip4844 is not supported"
        ),
        # revm: Eip7702NotSupported (pre-Prague).
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "Eip7702 is not supported"
        ),
        # revm: Eip2930NotSupported (pre-Berlin).
        TransactionException.TYPE_1_TX_PRE_FORK: (
            "Eip2930 is not supported"
        ),
        # revm: Eip1559NotSupported (pre-London).
        TransactionException.TYPE_2_TX_PRE_FORK: (
            "Eip1559 is not supported"
        ),
        # revm: AuthorizationListInvalidFields
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE: (
            "authorization list tx has invalid fields"
        ),
    }

    mapping_regex = {
        # revm: EmptyBlobs Display ("empty blobs") OR
        # TxEnv builder error for a type-3 tx with no blob hashes
        # ("missing blob hashes for EIP-4844"). Both are
        # zero-blobs-on-a-blob-tx conditions.
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            r"empty blobs|missing blob hashes for EIP-4844"
        ),
        # revm: NonceTooLow / NonceTooHigh
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            r"nonce \d+ too low, expected \d+"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            r"nonce \d+ too high, expected \d+"
        ),
        # revm: BlobGasPriceGreaterThanMax
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price \(\d+\) is greater than "
            r"max fee per blob gas \(\d+\)"
        ),
        # revm: CallGasCostMoreThanGasLimit
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"call gas cost \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        # revm: GasFloorMoreThanGasLimit
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"gas floor \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        # revm: OverflowPaymentInTransaction OR revme TxEnv builder
        # field-overflow errors (gas_price/max_fee_per_gas/etc.
        # > u128::MAX, max_fee_per_blob_gas > u128::MAX). All mean the
        # same thing: gas_limit * gas_price would overflow.
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            r"overflow payment in transaction|"
            r"(gas_price|max_fee_per_gas|max_priority_fee_per_gas|"
            r"max_fee_per_blob_gas) overflows u128"
        ),
        # revm: TooManyBlobs
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"too many blobs, have \d+, max \d+"
        ),
        # revm: EmptyAuthorizationList (validation) OR
        # MissingAuthorizationListForEip7702 (builder). Both fire for
        # a type-4 tx with an empty authorization list.
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            r"empty authorization list|"
            r"missing authorization list for EIP-7702"
        ),
        # revm: BlobCreateTransaction (validation) OR
        # MissingTargetForEip4844 (builder). Both fire for a type-3
        # blob tx that attempts contract creation.
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            r"blob create transaction|missing target for EIP-4844"
        ),
        # revme t8n's block-level blob budget rejection. Same wording
        # as reth's blob-allowance checker so the regex can sit here in
        # the base — reth's RethExceptionMapper still overrides it
        # (with the identical pattern) to keep clis/reth.py
        # self-documenting about which exceptions it cares about.
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        # revme t8n emits this when an EIP-7002/EIP-7251 post-block
        # system call reverts or halts. Mirrors geth's
        # "system call failed to execute" path and lands in the same
        # exception bucket reth uses.
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"failed to apply (withdrawal|consolidation) requests contract call"
        ),
        # revme t8n emits this when a Prague+ block's predeploy
        # system contract address has no code (e.g. fork activation
        # block before the deploy tx ran). Matches the per-client
        # phrasing convention (evmone says "system contract empty or
        # failed", revme says "system contract empty").
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"system contract empty"
        ),
        # revme t8n emits this when an EIP-6110 deposit log has a
        # malformed ABI layout (offsets or length headers diverge from
        # the canonical `DepositEvent(bytes,bytes,bytes,bytes,bytes)`
        # encoding). The block is rejected with
        # INVALID_DEPOSIT_EVENT_LAYOUT.
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"failed to decode deposit requests from receipts"
        ),
        # revme t8n emits this when the EIP-7928 block access list
        # exceeds its size budget (`bal_items` >
        # `block_gas_limit // BLOCK_ACCESS_LIST_ITEM`). Matches geth's
        # phrasing for the same rejection.
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            r"block access list exceeds gas limit"
        ),
        # revm: TxGasLimitGreaterThanCap
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"transaction gas limit \(\d+\) is greater than the cap \(\d+\)"
        ),
        # revm: CallerGasLimitMoreThanBlock — reth's tx-pool string
        # differs ("transaction gas limit N is more than blocks
        # available gas M") and is overridden in RethExceptionMapper.
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"caller gas limit exceeds the block gas limit"
        ),
    }


class RevmeCLI(EthereumCLI):
    """revme base — wraps the `revme` binary."""

    default_binary: ClassVar[Path] = Path("revme")
    detect_binary_pattern: ClassVar[re.Pattern] = re.compile(
        r"^revme \d+\.\d+\.\d+"
    )
    version_flag: ClassVar[str] = "--version"
    cached_version: Optional[str] = None

    def __init__(
        self,
        binary: Optional[Path] = None,
    ):
        """Initialize the RevmeCLI class."""
        self.binary = binary if binary else self.default_binary
        self._info_metadata: Optional[Dict[str, object]] = {}

    def _run_command(
        self, command: List[str]
    ) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            raise Exception("Unexpected exception calling revme.") from e


class RevmTransitionTool(RevmeCLI, TransitionTool):
    """`revme t8n` transition tool driver."""

    subcommand: Optional[str] = "t8n"
    t8n_use_stream: ClassVar[bool] = True
    supports_opcode_count: ClassVar[bool] = False
    supports_blob_params: ClassVar[bool] = True

    def __init__(
        self,
        *,
        exception_mapper: Optional[ExceptionMapper] = None,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the RevmTransitionTool class."""
        if not exception_mapper:
            exception_mapper = RevmExceptionMapper()
        RevmeCLI.__init__(self, binary=binary)
        TransitionTool.__init__(
            self,
            binary=binary,
            exception_mapper=exception_mapper,
            trace=trace,
        )

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        Until revme's `t8n` subcommand stabilises its supported-fork
        surface, accept all forks the framework asks about and let the
        binary error out on unsupported ones.
        """
        del fork
        return True
