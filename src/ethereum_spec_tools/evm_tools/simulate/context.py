"""
Adapt a fork's execution machinery to `eth_simulateV1`.

The spike this module descends from carried three process-global
substitutions here, because the specification could not express an
asserted sender, a contract sending a transaction, or a precompile at a
different address. All three now have real mechanisms — `asserted_sender`
on `check_transaction`, the EOA check guarded by it, and
`BlockEnvironment.precompiles` — so what is left is construction: a fork
declares slightly different `BlockEnvironment` and `Header` fields at
each revision, and a simulated block has to fill in whichever set the
fork in question wants.

Everything below `ForkLoad` is the specification's own answer.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from ethereum_types.bytes import Bytes, Bytes8, Bytes20
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum_spec_tools.forks import Hardfork

from ..loaders.fork_loader import ForkLoad

EMPTY_OMMERS_HASH = Hash32(
    bytes.fromhex(
        "1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
    )
)
"""
Keccak of the RLP-encoded empty ommers list.

Every simulated block carries it, because none of them has ommers.
"""


@dataclass
class CallOutcome:
    """What a single simulated call produced."""

    error: Optional[BaseException]
    reverted: bool
    """
    Whether the call reverted rather than halting some other way.

    The two are different results: a revert reports code 3 and carries
    the revert data, while any other halt reports -32015 and carries
    nothing. Only the code is assertable — execution-apis states plainly
    that the messages are suggestions.
    """
    return_data: Bytes
    logs: Tuple[Any, ...]
    gas_used: Uint
    """Gas charged to the sender, which the response reports as `gasUsed`."""
    max_used_gas: Uint
    """
    Gas consumed before refunds, reported as `maxUsedGas`.

    Taken from the fork's own settlement rather than reconstructed from
    an intrinsic cost and a tracer's running total. That distinction
    matters from Amsterdam, where a transaction draws on two gas pools
    and no arithmetic over a single figure would come out right.
    """


class SimulateFork:
    """
    A fork's machinery, arranged for building blocks that never existed.

    Wraps [`ForkLoad`], which already resolves the fork's classes and
    functions, and adds the construction a simulated block needs: a
    `BlockEnvironment` and a `Header` populated for whichever fields the
    fork declares, and a call executed as an ordinary transaction in the
    block.

    [`ForkLoad`]: ref:ethereum_spec_tools.evm_tools.loaders.fork_loader.ForkLoad
    """  # noqa: E501

    def __init__(self, hardfork: Hardfork) -> None:
        self.hardfork = hardfork
        self.load = ForkLoad(hardfork)

    # Construction, which papers over per-fork field sets.

    @staticmethod
    def _build(cls: Any, arguments: Dict[str, Any]) -> Any:
        """
        Construct `cls` from whichever of `arguments` it declares.

        Callers pass the union of every field any supported fork wants;
        each fork takes the subset it knows about. That is deliberately
        the opposite arrangement to `build_block_environment`, which
        asks a predicate per field: here the caller has a value for
        every field regardless, so filtering is cheaper than branching.
        """
        accepted = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in arguments.items() if k in accepted})

    def block_environment(
        self,
        *,
        pre_state: Any,
        chain_id: U64,
        block_gas_limit: Uint,
        block_hashes: List[Hash32],
        coinbase: Bytes20,
        number: Uint,
        base_fee_per_gas: Uint,
        time: U256,
        prev_randao: Any,
        excess_blob_gas: U64,
        parent_beacon_block_root: Hash32,
        precompiles: Optional[Mapping[Bytes20, Callable]] = None,
    ) -> Any:
        """Build the fork's `BlockEnvironment` for a simulated block."""
        arguments: Dict[str, Any] = {
            "chain_id": chain_id,
            "state": self.load.BlockState(pre_state=pre_state),
            "block_gas_limit": block_gas_limit,
            "block_hashes": list(block_hashes),
            "coinbase": coinbase,
            "number": number,
            "base_fee_per_gas": base_fee_per_gas,
            "time": time,
            "prev_randao": prev_randao,
            # A simulated block is never mined, so the pre-merge
            # difficulty is the same nothing `prevRandao` is.
            "difficulty": Uint(0),
            "excess_blob_gas": excess_blob_gas,
            "parent_beacon_block_root": parent_beacon_block_root,
            "slot_number": U64(0),
        }
        if self.load.has_hash_block_access_list:
            arguments["block_access_list_builder"] = (
                self.load.BlockAccessListBuilder()
            )
        if precompiles is not None:
            arguments["precompiles"] = precompiles
        return self._build(self.load.BlockEnvironment, arguments)

    def header(self, **fields: Any) -> Any:
        """Build the fork's `Header` with simulate's fixed defaults."""
        arguments: Dict[str, Any] = {
            "ommers_hash": EMPTY_OMMERS_HASH,
            "difficulty": Uint(0),
            "extra_data": Bytes(b""),
            "nonce": Bytes8(b"\0" * 8),
            "slot_number": U64(0),
            **fields,
        }
        return self._build(self.load.Header, arguments)

    def block(
        self,
        header: Any,
        transactions: Tuple[Any, ...],
        withdrawals: Tuple[Any, ...] = (),
    ) -> Any:
        """Build the fork's `Block` around a header and its contents."""
        arguments: Dict[str, Any] = {
            "header": header,
            "transactions": tuple(
                self.load.encode_transaction(tx) for tx in transactions
            ),
            "ommers": (),
            "withdrawals": withdrawals,
        }
        return self._build(self.load.Block, arguments)

    def withdrawal(
        self, index: int, validator_index: int, address: Bytes20, amount: int
    ) -> Any:
        """Build the fork's `Withdrawal` from an override's fields."""
        return self.load.Withdrawal(
            U64(index), U64(validator_index), address, U64(amount)
        )

    # Reads.

    def get_account(self, block_state: Any, address: Bytes20) -> Any:
        """
        Return an account as of the current point in the block.

        Reads through the block's committed writes so that a call sees
        the nonce the calls before it left, which is what makes the
        default nonce increment across a `blockStateCall`.
        """
        state_tracker = self.hardfork.module("state_tracker")
        return state_tracker.get_account(
            self.load.TransactionState(parent=block_state), address
        )

    def relocated_precompiles(
        self, moves: Mapping[Bytes20, Bytes20]
    ) -> Mapping[Bytes20, Callable]:
        """
        Return the fork's precompiles with `movePrecompileToAddress`
        applied.

        A precompile is not an account with code, so no state override
        can shadow one and no state write can move one. The mapping the
        interpreter dispatches from is instead a field of the block
        environment, which is what makes this an ordinary rearrangement
        of a dictionary rather than surgery on a module constant.

        Every source is removed before any target is added, so moving
        two precompiles past each other does not depend on the order the
        caller listed them in.
        """
        relocated = dict(self.load.PRE_COMPILED_CONTRACTS)
        moved = {
            source: relocated.pop(source)
            for source in moves
            if source in relocated
        }
        for source, target in moves.items():
            if source in moved:
                relocated[target] = moved[source]
        return relocated

    # Execution.

    def run_system_calls(self, block_env: Any) -> None:
        """
        Run the system contracts a simulated block begins with.

        Nothing in execution-apis says whether a simulated block runs
        them. It is not observable in the `calls` array — system calls
        consume no block gas — but it moves the state root, and the
        state root is in the response, so the answer has to be decided
        one way or the other. Measured against go-ethereum at Cancun:
        without the beacon-roots call every root was wrong and with it
        every root was right, so the client runs them.
        """
        if self.load.has_compute_requests_hash:
            self.load.process_unchecked_system_transaction(
                block_env=block_env,
                target_address=self.load.HISTORY_STORAGE_ADDRESS,
                data=block_env.block_hashes[-1],
            )
        if self.load.has_beacon_roots_address:
            self.load.process_unchecked_system_transaction(
                block_env=block_env,
                target_address=self.load.BEACON_ROOTS_ADDRESS,
                data=block_env.parent_beacon_block_root,
            )

    def finalize_block(
        self,
        block_env: Any,
        block_output: Any,
        transaction_count: int,
        withdrawals: Tuple[Any, ...],
    ) -> None:
        """
        Run the operations a block performs after its transactions.

        The same sequence `t8n` runs, minus the block reward: a
        simulated block is post-merge by construction, since the method
        did not exist before it.
        """
        if self.load.has_hash_block_access_list:
            block_env.block_access_list_builder.block_access_index = (
                self.load.BlockAccessIndex(Uint(transaction_count) + Uint(1))
            )
        if self.load.has_withdrawal:
            self.load.process_withdrawals(block_env, block_output, withdrawals)
        if self.load.has_compute_requests_hash:
            self.load.process_general_purpose_requests(block_env, block_output)
        if self.load.has_hash_block_access_list:
            block_output.block_access_list = self.load.build_block_access_list(
                block_env.block_access_list_builder, block_env.state
            )

    def process_call(
        self,
        block_env: Any,
        block_output: Any,
        transaction: Any,
        index: Uint,
        sender: Bytes20,
    ) -> CallOutcome:
        """
        Execute one simulated call as a transaction in the block.

        The spec's own `process_transaction` does the work, so gas
        accounting, receipts, logs, the transactions trie and the state
        changes are all the specification's answer rather than a
        reimplementation of it. Only the sender is arranged from
        outside, and `asserted_sender` is the parameter for saying so:
        it stands in for the recovery a signature would have supplied
        and, with it, waives the rule that a sender may not have code,
        which `eth_simulateV1` allows a caller to break.
        """
        logs_before = len(block_output.block_logs)
        result = self.load.process_transaction(
            block_env,
            block_output,
            transaction,
            index,
            asserted_sender=sender,
        )
        return CallOutcome(
            error=result.error,
            reverted=isinstance(result.error, self.load.Revert),
            return_data=result.return_data,
            logs=tuple(block_output.block_logs[logs_before:]),
            gas_used=result.gas_used,
            max_used_gas=result.gas_used_before_refund,
        )


def resolve_simulate_fork(name: str) -> SimulateFork:
    """Return the execution machinery for the named fork."""
    return SimulateFork(Hardfork.by_short_name(name))


__all__ = [
    "CallOutcome",
    "EMPTY_OMMERS_HASH",
    "SimulateFork",
    "resolve_simulate_fork",
]
