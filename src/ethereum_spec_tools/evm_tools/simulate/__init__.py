"""
Derive `eth_simulateV1` results from the Python specification.

`eth_simulateV1` executes caller-supplied message calls inside blocks
that never existed. Unlike `eth_call` the calls chain — each one sees
the state the previous one left — and the caller may override both the
block context and the account state before execution begins.

The central observation this module rests on is that a `blockStateCall`
is a *real block*. Its transactions are synthesized from the calls by a
fixed set of defaults (see `_synthesize`), and every header field the
response reports is then computed the ordinary way: the transactions
root over those synthetic transactions, the receipts root over their
receipts, the state root over the post-state. Nothing about the block is
invented, so the spec can produce it — including the block hash, which
the response carries and which a client can only agree with if the
synthetic transactions match byte for byte.

What the specification supplies and what it does not divides cleanly.
Execution is entirely the spec's: `process_transaction` fills the tries,
the logs and the state diff, and reports the return data and the
pre-refund gas the response needs. The surrounding machinery is not: the
block defaults, the twelve-second timestamp step, the filler blocks for
skipped numbers, the validation-mode switch and the error-code surface
all come from execution-apis' schema and prose, and none of it is
EL-specification material.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes20, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.merkle_patricia_trie import root
from ethereum.state import EMPTY_CODE_HASH, Account
from ethereum.state_mpt import (
    State,
    apply_changes_to_state,
    destroy_storage,
    set_account,
    set_storage,
    store_code,
)

from .context import CallOutcome, SimulateFork, resolve_simulate_fork
from .errors import SimulateError, error_code_for
from .payload import (
    AccountOverride,
    BlockOverrides,
    BlockStateCall,
    Call,
    SimulatePayload,
)
from .response import render_result
from .transfers import TRANSFER_LOG_EMITTER, transfer_logs

DEFAULT_BLOCK_TIME = 12
"""
Seconds added to the parent timestamp when a block does not override it.

Mainnet's slot time. The value is a property of the network rather than
of the EVM, which is the first sign that this method's answer is not
entirely a function of the specification.
"""

MAXIMUM_ANCESTOR_HASHES = 256
"""How far back `BLOCKHASH` can see, and so how many hashes to carry."""

LEGACY_TRANSACTION_TYPE = 0
ACCESS_LIST_TRANSACTION_TYPE = 1
FEE_MARKET_TRANSACTION_TYPE = 2
BLOB_TRANSACTION_TYPE = 3

UNSIGNED_LEGACY_SIGNATURE_PARITY = 27
"""
The `v` a synthesized pre-155 transaction carries.

Every other envelope is admitted with `r`, `s` and `yParity` all zero,
because `asserted_sender` stands in for the recovery those fields would
have driven. A pre-155 transaction cannot be: `check_transaction` reads
the chain id out of `v` *before* it consults the asserted sender, and
`v = 0` is neither a chain id nor the pre-155 marker, so the
specification rejects it as a bad signature.

That is the same shape of problem `asserted_sender` was introduced to
solve, one layer further down, and the same fix would answer it —
guarding the chain-id read the way the recovery is guarded. Until then
the lowest `v` the specification accepts is the pre-155 marker, which
is at least honest about what the envelope says: this transaction names
no chain.

**Not verified against a client.** `v` is in the transaction's RLP, so
if go-ethereum synthesizes a different one the transaction hash, the
transactions root and the block hash all differ. The conformance
harness is where that gets settled.
"""


@dataclass
class BaseBlock:
    """The existing block a simulation starts from."""

    number: Uint
    timestamp: U256
    gas_limit: Uint
    base_fee_per_gas: Uint
    excess_blob_gas: U64
    block_hash: Hash32
    parent_beacon_block_root: Hash32 = Hash32(b"\0" * 32)
    prev_randao: Bytes32 = Bytes32(b"\0" * 32)


@dataclass
class CallResult:
    """One entry of a simulated block's `calls` array."""

    status: int
    reverted: bool
    return_data: Bytes
    gas_used: Uint
    logs: Tuple[Any, ...]
    transaction_hash: Hash32
    transaction_index: int
    sender: Bytes20
    max_used_gas: Uint
    first_log_index: int
    """
    Position of this call's first log within the block, not the call.

    `logIndex` counts across the whole block, so a call cannot number
    its own logs without knowing how many the calls before it emitted.
    """


@dataclass
class SimulatedBlock:
    """A block that never existed, and the results of the calls in it."""

    header: Any
    transactions: Tuple[Any, ...]
    withdrawals: Tuple[Any, ...]
    call_results: List[CallResult]
    block_hash: Hash32
    size: int


@dataclass
class BlockContext:
    """Resolved block context for one simulated block."""

    number: Uint
    timestamp: U256
    gas_limit: Uint
    base_fee_per_gas: Uint
    prev_randao: Bytes32
    fee_recipient: Bytes20
    excess_blob_gas: U64


@dataclass
class EthSimulate:
    """
    Execute an `eth_simulateV1` payload against a pre-state.

    The state is advanced in place across blocks, which is what makes
    the calls chain: block *n*'s post-state is block *n+1*'s pre-state,
    exactly as it would be on chain.
    """

    fork: SimulateFork
    chain_id: U64
    state: State
    base_block: BaseBlock
    payload: SimulatePayload
    ancestor_hashes: List[Hash32] = field(default_factory=list)
    """
    Hashes of the blocks before the base block, oldest first.

    `BLOCKHASH` reaches back through these, and from Prague the history
    contract is seeded with the parent hash out of the same list, so an
    empty one is only correct when the base block is genesis.
    """

    def run(self) -> List[SimulatedBlock]:
        """Execute every `blockStateCall` and return the simulated blocks."""
        parent = self.base_block
        block_hashes = list(self.ancestor_hashes)
        block_hashes.append(self.base_block.block_hash)
        results: List[SimulatedBlock] = []
        # Relocations accumulate the way state overrides do: a caller
        # that moved a precompile in the first block does not have to
        # say so again in the second.
        moves: Dict[Bytes20, Bytes20] = {}

        for entry in self._expand():
            context = self._resolve_context(parent, entry.block_overrides)
            self._check_ordering(parent, context)
            moves.update(self._apply_state_overrides(entry.state_overrides))
            block = self._execute_block(
                entry,
                context,
                block_hashes[-MAXIMUM_ANCESTOR_HASHES:],
                self.fork.relocated_precompiles(moves) if moves else None,
            )
            results.append(block)
            block_hashes.append(block.block_hash)
            parent = BaseBlock(
                number=context.number,
                timestamp=context.timestamp,
                gas_limit=context.gas_limit,
                base_fee_per_gas=context.base_fee_per_gas,
                excess_blob_gas=context.excess_blob_gas,
                block_hash=block.block_hash,
                prev_randao=context.prev_randao,
            )
        return results

    def result(self) -> List[Dict[str, Any]]:
        """
        Run the payload and render the `EthSimulateResult` for it.

        The rendering choice the payload carries — whether
        `transactions` holds hashes or whole objects — belongs here
        rather than at the call site, since it is part of the request.
        """
        return render_result(
            self.run(),
            full_transactions=self.payload.return_full_transactions,
        )

    def _expand(self) -> Iterator[BlockStateCall]:
        """
        Yield the payload's entries with the implied empty blocks
        inserted.

        A caller may skip block numbers, and the gap is filled with
        empty blocks that *do* appear in the result and *do* advance the
        timestamp — which is why the ordering checks cannot run on the
        request as written. Skipping to block 20 from block 0 puts 19
        filler blocks in between, each twelve seconds later, so an
        overridden timestamp of 200 on block 20 is rejected against the
        228 the fillers reached rather than against the parent's 0.
        """
        number = int(self.base_block.number)
        for entry in self.payload.block_state_calls:
            requested = entry.block_overrides.number
            if requested is not None and int(requested) > number + 1:
                for filler in range(number + 1, int(requested)):
                    yield BlockStateCall(
                        block_overrides=BlockOverrides(number=filler)
                    )
                number = int(requested) - 1
            number = int(requested) if requested is not None else number + 1
            yield entry

    def _check_ordering(
        self, parent: BaseBlock, context: BlockContext
    ) -> None:
        """
        Reject a block that does not follow its parent in number or time.

        Checked after the defaults are resolved, per the execution-apis
        notes: the caller may leave either field out on some blocks, so
        only the fully-constructed sequence can be validated.
        """
        if context.number <= parent.number:
            raise SimulateError(
                -38020,
                f"block numbers must be in increasing order: "
                f"{int(context.number)} <= {int(parent.number)}",
            )
        if context.timestamp <= parent.timestamp:
            raise SimulateError(
                -38021,
                f"block timestamps must be in order: "
                f"{int(context.timestamp)} <= {int(parent.timestamp)}",
            )

    def _resolve_context(
        self, parent: BaseBlock, overrides: BlockOverrides
    ) -> BlockContext:
        """
        Fill in the block fields the caller did not set.

        The defaults come from the execution-apis notes rather than from
        any EL specification: the number and timestamp increment, the
        fee recipient and `prevRandao` are zero, and the gas limit is
        inherited. The base fee is the interesting one — with validation
        off it is *forced to zero* so that calls are free, and with
        validation on it follows EIP-1559 from the parent.
        """
        number = (
            Uint(int(overrides.number))
            if overrides.number is not None
            else parent.number + Uint(1)
        )
        timestamp = (
            U256(int(overrides.time))
            if overrides.time is not None
            else parent.timestamp + U256(DEFAULT_BLOCK_TIME)
        )
        gas_limit = (
            Uint(int(overrides.gas_limit))
            if overrides.gas_limit is not None
            else parent.gas_limit
        )
        if overrides.base_fee_per_gas is not None:
            base_fee = Uint(int(overrides.base_fee_per_gas))
        elif self.payload.validation:
            base_fee = self.fork.load.calculate_base_fee_per_gas(
                gas_limit,
                parent.gas_limit,
                Uint(0),
                parent.base_fee_per_gas,
            )
        else:
            base_fee = Uint(0)

        return BlockContext(
            number=number,
            timestamp=timestamp,
            gas_limit=gas_limit,
            base_fee_per_gas=base_fee,
            prev_randao=(
                Bytes32(int(overrides.prev_randao).to_bytes(32, "big"))
                if overrides.prev_randao is not None
                else Bytes32(b"\0" * 32)
            ),
            fee_recipient=(
                overrides.fee_recipient
                if overrides.fee_recipient is not None
                else Bytes20(b"\0" * 20)
            ),
            excess_blob_gas=parent.excess_blob_gas,
        )

    def _apply_state_overrides(
        self, overrides: Dict[Bytes20, AccountOverride]
    ) -> Dict[Bytes20, Bytes20]:
        """
        Replace account state before the block executes.

        `state` and `stateDiff` differ: the former drops the account's
        existing storage entirely, the latter merges.

        `movePrecompileToAddress` is the one override that is not a
        state write at all, because a precompile is not an account with
        code, so it is returned for the caller to hand to the block
        environment rather than applied here. Note that only the
        precompile moves: the account sitting at its address, if any,
        stays where it is, which is what go-ethereum does.
        """
        for address, override in overrides.items():
            account = self.state.get_account_optional(address) or Account(
                nonce=Uint(0), balance=U256(0), code_hash=EMPTY_CODE_HASH
            )
            code_hash = account.code_hash
            if override.code is not None:
                code_hash = store_code(self.state, override.code)
            set_account(
                self.state,
                address,
                Account(
                    nonce=(
                        Uint(int(override.nonce))
                        if override.nonce is not None
                        else account.nonce
                    ),
                    balance=(
                        U256(int(override.balance))
                        if override.balance is not None
                        else account.balance
                    ),
                    code_hash=code_hash,
                ),
            )
            if override.state is not None:
                # A full replacement, so the existing storage goes first.
                destroy_storage(self.state, address)
                for key, value in override.state.items():
                    set_storage(self.state, address, key, value)
            for key, value in (override.state_diff or {}).items():
                set_storage(self.state, address, key, value)

        return self._resolve_precompile_moves(overrides)

    def _resolve_precompile_moves(
        self, overrides: Dict[Bytes20, AccountOverride]
    ) -> Dict[Bytes20, Bytes20]:
        """
        Collect the requested relocations, rejecting the two the notes
        forbid.

        Both rules are properties of the request rather than of
        execution, so they are decided before anything runs. Note that
        go-ethereum agrees with neither: it answers a self-move with
        `-32000` and accepts two moves to the same address outright. The
        recorded corpus sides with the client, and two of its vectors
        are named for the codes below while carrying something else.
        """
        moves: Dict[Bytes20, Bytes20] = {}
        for address, override in overrides.items():
            target = override.move_precompile_to_address
            if target is None:
                continue
            if target == address:
                raise SimulateError(
                    -38022, "MovePrecompileToAddress referenced itself"
                )
            if target in moves.values():
                raise SimulateError(
                    -38023,
                    "multiple MovePrecompileToAddress to the same address",
                )
            moves[address] = target
        return moves

    def _execute_block(
        self,
        entry: BlockStateCall,
        context: BlockContext,
        block_hashes: List[Hash32],
        precompiles: Any,
    ) -> SimulatedBlock:
        """Build and execute one simulated block."""
        fork = self.fork
        parent_hash = block_hashes[-1]
        block_env = fork.block_environment(
            pre_state=self.state,
            chain_id=self.chain_id,
            block_gas_limit=context.gas_limit,
            block_hashes=block_hashes,
            coinbase=context.fee_recipient,
            number=context.number,
            base_fee_per_gas=context.base_fee_per_gas,
            time=context.timestamp,
            prev_randao=context.prev_randao,
            excess_blob_gas=context.excess_blob_gas,
            parent_beacon_block_root=Hash32(b"\0" * 32),
            precompiles=precompiles,
        )
        block_output = fork.load.BlockOutput()
        fork.run_system_calls(block_env)

        transactions: List[Any] = []
        call_results: List[CallResult] = []
        gas_used_so_far = Uint(0)
        logs_so_far = 0

        for index, call in enumerate(entry.calls):
            transaction = self._synthesize(
                call, context, block_env, gas_used_so_far
            )
            transactions.append(transaction)
            outcome = self._process_call(
                block_env, block_output, transaction, Uint(index), call
            )
            logs = self._with_transfer_logs(call, outcome)
            call_results.append(
                CallResult(
                    status=0 if outcome.error is not None else 1,
                    reverted=outcome.reverted,
                    return_data=outcome.return_data,
                    gas_used=outcome.gas_used,
                    logs=logs,
                    transaction_hash=fork.load.get_transaction_hash(
                        fork.load.encode_transaction(transaction)
                    ),
                    transaction_index=index,
                    sender=call.sender,
                    max_used_gas=outcome.max_used_gas,
                    first_log_index=logs_so_far,
                )
            )
            logs_so_far += len(logs)
            gas_used_so_far += outcome.gas_used

        withdrawals = self._withdrawals(entry.block_overrides)
        fork.finalize_block(
            block_env, block_output, len(transactions), withdrawals
        )

        diff = fork.load.extract_block_diff(block_env.state)
        state_root = self.state.compute_state_root(diff)
        apply_changes_to_state(self.state, diff)

        header = fork.header(
            parent_hash=parent_hash,
            coinbase=context.fee_recipient,
            state_root=state_root,
            transactions_root=root(block_output.transactions_trie),
            receipt_root=root(block_output.receipts_trie),
            bloom=fork.load.logs_bloom(block_output.block_logs),
            number=context.number,
            gas_limit=context.gas_limit,
            gas_used=block_output.block_gas_used,
            timestamp=context.timestamp,
            prev_randao=context.prev_randao,
            base_fee_per_gas=context.base_fee_per_gas,
            withdrawals_root=root(block_output.withdrawals_trie),
            blob_gas_used=block_output.blob_gas_used,
            excess_blob_gas=context.excess_blob_gas,
            parent_beacon_block_root=Hash32(b"\0" * 32),
            **self._closing_header_fields(block_output),
        )
        block = fork.block(header, tuple(transactions), withdrawals)
        block_hash = keccak256(rlp.encode(header))

        return SimulatedBlock(
            header=header,
            transactions=tuple(transactions),
            withdrawals=withdrawals,
            call_results=call_results,
            block_hash=block_hash,
            size=len(rlp.encode(block)),
        )

    def _closing_header_fields(self, block_output: Any) -> Dict[str, Any]:
        """
        Return the header commitments a fork adds after execution.

        Both are computed rather than stubbed, because both are inputs
        to the block hash the response reports. Neither has been checked
        against a client: no client implements `eth_simulateV1` at a
        fork that has them.
        """
        fields: Dict[str, Any] = {}
        if self.fork.load.has_compute_requests_hash:
            fields["requests_hash"] = self.fork.load.compute_requests_hash(
                block_output.requests
            )
        if self.fork.load.has_hash_block_access_list:
            fields["block_access_list_hash"] = (
                self.fork.load.hash_block_access_list(
                    block_output.block_access_list
                )
            )
        return fields

    def _withdrawals(self, overrides: BlockOverrides) -> Tuple[Any, ...]:
        """Build the withdrawals a `blockOverrides` asked to be paid."""
        if not self.fork.load.has_withdrawal or not overrides.withdrawals:
            return ()
        return tuple(
            self.fork.withdrawal(
                entry.index,
                entry.validator_index,
                entry.address,
                entry.amount,
            )
            for entry in overrides.withdrawals
        )

    def _process_call(
        self,
        block_env: Any,
        block_output: Any,
        transaction: Any,
        index: Uint,
        call: Call,
    ) -> CallOutcome:
        """
        Run one call, translating an inadmissible one into a request
        failure.

        A call the block would not accept at all is not a failed entry
        in the `calls` array: `eth_simulateV1` abandons the whole
        request for it, with a code naming the rule that was broken.
        """
        try:
            return self.fork.process_call(
                block_env, block_output, transaction, index, call.sender
            )
        except SimulateError:
            raise
        except Exception as exception:
            code = error_code_for(exception)
            if code is None:
                raise
            raise SimulateError(code, str(exception)) from exception

    def _with_transfer_logs(
        self, call: Call, outcome: CallOutcome
    ) -> Tuple[Any, ...]:
        """
        Prepend the synthetic transfer log for a call's own value, if
        asked.

        Only the top-level transfer is covered before Amsterdam, and
        from Amsterdam nothing is: see [`transfers`] for why the option
        becomes a no-op once ETH transfers are consensus logs.

        [`transfers`]: ref:ethereum_spec_tools.evm_tools.simulate.transfers
        """
        if not self.payload.trace_transfers:
            return outcome.logs
        if self.emits_consensus_transfer_logs:
            return outcome.logs
        if outcome.error is not None or call.to is None or not call.value:
            return outcome.logs
        synthetic = transfer_logs(
            self.fork.load.Log, call.sender, call.to, call.value
        )
        return synthetic + outcome.logs

    @property
    def emits_consensus_transfer_logs(self) -> bool:
        """
        Whether the fork already logs ETH transfers of its own accord.

        True from Amsterdam, where EIP-7708 makes a nonzero transfer to
        a different account emit a log that reaches the receipts whether
        or not `traceTransfers` was set.
        """
        return hasattr(self.fork.hardfork.module("vm"), "emit_transfer_log")

    def _synthesize(
        self,
        call: Call,
        context: BlockContext,
        block_env: Any,
        gas_used: Uint,
    ) -> Any:
        """
        Build the transaction a client would put in the block for this
        call.

        Every default here is observable: the nonce and gas limit change
        the transaction's RLP, which changes its hash, which changes the
        transactions root and therefore the block hash the response
        reports. Getting them wrong produces a plausible answer that no
        client agrees with.
        """
        if call.nonce is not None:
            nonce = U256(call.nonce)
        else:
            account = self.fork.get_account(block_env.state, call.sender)
            nonce = U256(account.nonce)
        if call.gas is not None:
            gas = Uint(call.gas)
        else:
            gas = context.gas_limit - gas_used

        # A creation is the empty `to`, not a null one: the RLP has no
        # representation for absence.
        common: Dict[str, Any] = {
            "nonce": nonce,
            "gas": gas,
            "to": call.to if call.to is not None else Bytes0(),
            "value": U256(call.value or 0),
            "data": call.data,
            "r": U256(0),
            "s": U256(0),
        }
        transaction_type = self._transaction_type(call)
        if transaction_type == LEGACY_TRANSACTION_TYPE:
            return self.fork.load.LegacyTransaction(
                gas_price=Uint(call.gas_price or 0),
                v=U256(UNSIGNED_LEGACY_SIGNATURE_PARITY),
                **common,
            )

        common["chain_id"] = self.chain_id
        common["y_parity"] = U256(0)
        common["access_list"] = self._access_list(call)
        if transaction_type == ACCESS_LIST_TRANSACTION_TYPE:
            return self.fork.load.AccessListTransaction(
                gas_price=Uint(call.gas_price or 0), **common
            )

        common["max_priority_fee_per_gas"] = Uint(
            call.max_priority_fee_per_gas or 0
        )
        common["max_fee_per_gas"] = Uint(call.max_fee_per_gas or 0)
        if transaction_type == BLOB_TRANSACTION_TYPE:
            return self.fork.load.BlobTransaction(
                max_fee_per_blob_gas=U256(call.max_fee_per_blob_gas or 0),
                blob_versioned_hashes=call.blob_versioned_hashes or (),
                **common,
            )
        return self.fork.load.FeeMarketTransaction(**common)

    def _transaction_type(self, call: Call) -> int:
        """
        Decide which envelope a call is carried in.

        A payload that names `type` gets what it asked for. Otherwise
        the fields present imply it, in the order go-ethereum resolves
        them: blob hashes make it a blob transaction, the EIP-1559 fee
        fields make it a fee-market one, a `gasPrice` drops it to a
        pre-1559 envelope, and an access list without a `gasPrice`
        raises it back to fee-market since that envelope carries one
        too. A call that names none of them is fee-market, which is what
        a client synthesizes for the overwhelmingly common payload that
        specifies nothing.
        """
        if call.call_type is not None:
            return call.call_type
        if call.blob_versioned_hashes is not None:
            return BLOB_TRANSACTION_TYPE
        if (
            call.max_fee_per_gas is not None
            or call.max_priority_fee_per_gas is not None
        ):
            return FEE_MARKET_TRANSACTION_TYPE
        if call.gas_price is not None:
            if call.access_list is not None:
                return ACCESS_LIST_TRANSACTION_TYPE
            return LEGACY_TRANSACTION_TYPE
        return FEE_MARKET_TRANSACTION_TYPE

    def _access_list(self, call: Call) -> Tuple[Any, ...]:
        """Build the fork's access list entries for a call."""
        if not call.access_list:
            return ()
        return tuple(
            self.fork.load.Access(
                account=entry.address, slots=entry.storage_keys
            )
            for entry in call.access_list
        )


def simulate(
    fork_name: str,
    chain_id: U64,
    state: State,
    base_block: BaseBlock,
    payload: Dict[str, Any],
    ancestor_hashes: Optional[List[Hash32]] = None,
) -> List[Dict[str, Any]]:
    """Run a raw `eth_simulateV1` payload and render its result."""
    return EthSimulate(
        fork=resolve_simulate_fork(fork_name),
        chain_id=chain_id,
        state=state,
        base_block=base_block,
        payload=SimulatePayload.parse(payload),
        ancestor_hashes=list(ancestor_hashes or []),
    ).result()


__all__ = [
    "ACCESS_LIST_TRANSACTION_TYPE",
    "BLOB_TRANSACTION_TYPE",
    "BaseBlock",
    "BlockContext",
    "CallResult",
    "DEFAULT_BLOCK_TIME",
    "EthSimulate",
    "FEE_MARKET_TRANSACTION_TYPE",
    "LEGACY_TRANSACTION_TYPE",
    "MAXIMUM_ANCESTOR_HASHES",
    "SimulateError",
    "SimulateFork",
    "SimulatePayload",
    "SimulatedBlock",
    "TRANSFER_LOG_EMITTER",
    "UNSIGNED_LEGACY_SIGNATURE_PARITY",
    "error_code_for",
    "render_result",
    "resolve_simulate_fork",
    "simulate",
    "transfer_logs",
]
