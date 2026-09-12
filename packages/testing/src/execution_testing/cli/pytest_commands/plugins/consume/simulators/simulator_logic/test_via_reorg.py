"""
A hive based simulator that executes `blockchain_test_engine_reorg` fixtures.

The fixture is a DAG of payloads plus an ordered list of steps. The simulator
resolves block labels to hashes, sends each Engine API request verbatim,
selects the first listed outcome that matches the observed response, logs it,
runs that outcome's branch steps, and fails on the first step whose observed
result matches none of its listed outcomes. There is no runtime policy: every
decision is in the fixture.

Steps may target additional clients (``on``) declared in ``fixture.clients``;
those are started peered with the main client so reorgs can also be delivered
by sync.
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from hive.client import Client

from execution_testing.base_types import Bytes, Hash
from execution_testing.fixtures import BlockchainEngineReorgFixture
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.fixtures.reorg import (
    LATEST_VALID_HASH_ANY,
    LATEST_VALID_HASH_NULL,
    MAIN_CLIENT,
    AssertCanonicalStep,
    AssertHeadStep,
    AssertLogsStep,
    AssertReceiptStep,
    AssertStateStep,
    AssertTxStatusStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    SendRawTransactionStep,
    Step,
    TxRef,
    WaitForHeadStep,
)
from execution_testing.logging import get_logger
from execution_testing.rpc import EngineRPC, EthRPC
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    JSONRPCError,
    PayloadAttributes,
)

from ..helpers.exceptions import LoggedError
from ..helpers.genesis import (
    send_forkchoice_update_to_genesis,
    verify_genesis_block_hash,
)
from ..helpers.timing import TimingData

logger = get_logger(__name__)


@dataclass
class Observed:
    """Normalized observation of an Engine API response."""

    status: str | None = None
    latest_valid_hash: Hash | None = None
    validation_error: Any = None
    error_code: int | None = None
    error_message: str | None = None
    payload_id: Bytes | None = None
    head_moved: bool | None = None

    def describe(self) -> str:
        """Human-readable summary."""
        if self.error_code is not None:
            return f"error {self.error_code}: {self.error_message}"
        return (
            f"status={self.status} latestValidHash={self.latest_valid_hash} "
            f"validationError={self.validation_error!r}"
            + (f" payloadId={self.payload_id}" if self.payload_id else "")
            + (
                f" headMoved={self.head_moved}"
                if self.head_moved is not None
                else ""
            )
        )


@dataclass
class ClientRPC:
    """RPC endpoints of one client."""

    name: str
    eth: EthRPC
    engine: EngineRPC


@dataclass
class BoundPayload:
    """A client-built payload bound to a label by ``getPayload``."""

    payload: FixtureExecutionPayload
    versioned_hashes: List[Hash]
    parent_beacon_block_root: Hash | None
    execution_requests: List[Bytes] | None
    label_parent: str


class StepRunner:
    """Executes fixture steps against one or more clients."""

    def __init__(
        self,
        fixture: BlockchainEngineReorgFixture,
        clients: Dict[str, ClientRPC],
        timing_data: TimingData,
    ) -> None:
        """Initialize with the fixture and per-client RPC endpoints."""
        self.fixture = fixture
        self.clients = clients
        self.timing_data = timing_data
        self.labels_by_hash = fixture.labels_by_hash()
        self.bound: Dict[str, BoundPayload] = {}
        self.last_payload_id: Dict[str, Bytes | None] = {}
        self.last_payload_attributes: Dict[str, PayloadAttributes | None] = {}
        self.matched: List[str] = []
        """Log of ``<step>:<outcome id>`` selections, for offline analysis."""

    # -- helpers ---------------------------------------------------------

    def rpc(self, on: str) -> ClientRPC:
        """RPC endpoints of a named client."""
        if on not in self.clients:
            raise LoggedError(f"step targets unknown client {on!r}")
        return self.clients[on]

    def resolve(self, label: str) -> Hash | None:
        """Resolve a static or bound label to a hash."""
        if label in self.bound:
            return self.bound[label].payload.block_hash
        return self.fixture.resolve(label)

    def label_of(self, block_hash: Hash | str | None) -> str:
        """Block label for a hash (or the hash itself if unknown)."""
        if block_hash is None:
            return "null"
        h = Hash(block_hash)
        return self.labels_by_hash.get(h, str(h))

    def block_number(self, label: str) -> int:
        """Height of a labeled block."""
        if label == "genesis":
            return int(self.fixture.genesis.number)
        if label in self.bound:
            return int(self.bound[label].payload.number)
        return int(self.fixture.blocks[label].payload.params[0].number)

    def block_timestamp(self, label: str) -> int:
        """Timestamp of a labeled block."""
        if label == "genesis":
            return int(self.fixture.genesis.timestamp)
        if label in self.bound:
            return int(self.bound[label].payload.timestamp)
        return int(self.fixture.blocks[label].payload.params[0].timestamp)

    def tx_hash(self, ref: TxRef) -> Hash:
        """Hash of a referenced transaction (fixture or bound block)."""
        if ref.block in self.bound:
            return Hash(
                self.bound[ref.block]
                .payload.transactions[ref.index]
                .keccak256()
            )
        return self.fixture.tx_hash(ref)

    def tx_rlp(self, ref: TxRef) -> Bytes:
        """Raw bytes of a referenced transaction."""
        if ref.block in self.bound:
            return self.bound[ref.block].payload.transactions[ref.index]
        return self.fixture.tx_rlp(ref)

    def matches(self, outcome: Outcome, observed: Observed) -> bool:
        """Whether an observed response satisfies an outcome's constraints."""
        if outcome.error_code is not None:
            return observed.error_code == outcome.error_code
        if outcome.any_error:
            return observed.error_code is not None
        if observed.error_code is not None:
            return False
        if outcome.status is not None and observed.status != outcome.status:
            return False
        if outcome.latest_valid_hash is not None:
            want = outcome.latest_valid_hash
            if want == LATEST_VALID_HASH_NULL:
                if observed.latest_valid_hash is not None:
                    return False
            elif want != LATEST_VALID_HASH_ANY:
                if observed.latest_valid_hash != self.resolve(want):
                    return False
        if outcome.validation_error == "required":
            if observed.validation_error is None:
                return False
        elif outcome.validation_error == "none":
            if observed.validation_error is not None:
                return False
        if outcome.payload_id == "nonNull" and observed.payload_id is None:
            return False
        if outcome.payload_id == "null" and observed.payload_id is not None:
            return False
        if (
            outcome.head_moved is not None
            and observed.head_moved != outcome.head_moved
        ):
            return False
        return True

    def select(
        self, step_name: str, expect: List[Outcome], observed: Observed
    ) -> Outcome:
        """Pick the first matching outcome or fail."""
        if not expect:
            raise LoggedError(
                f"{step_name}: fixture step has no expected outcomes "
                "(unannotated fixture)"
            )
        for outcome in expect:
            if self.matches(outcome, observed):
                note = (
                    f" (disputed: {outcome.disputed})"
                    if outcome.disputed
                    else ""
                )
                logger.info(
                    f"{step_name}: observed {observed.describe()} -> "
                    f"outcome '{outcome.id}'{note}"
                )
                self.matched.append(f"{step_name}:{outcome.id}")
                return outcome
        legal = ", ".join(
            f"{o.id}(status={o.status}, lvh={o.latest_valid_hash}, "
            f"error={o.error_code})"
            for o in expect
        )
        raise LoggedError(
            f"{step_name}: observed {observed.describe()} matches none of "
            f"the legal outcomes [{legal}]"
        )

    # -- steps -----------------------------------------------------------

    def run(self, steps: List[Step], depth: int = 0) -> None:
        """Run a step list, recursing into selected branches."""
        for i, step in enumerate(steps):
            on = "" if step.on == MAIN_CLIENT else f"@{step.on} "
            name = f"{'  ' * depth}step {i + 1}/{len(steps)} {on}{step.type}"
            if isinstance(step, NewPayloadStep):
                self.new_payload(name, step, depth)
            elif isinstance(step, ForkchoiceUpdatedStep):
                self.forkchoice_updated(name, step, depth)
            elif isinstance(step, GetPayloadStep):
                self.get_payload(name, step)
            elif isinstance(step, AssertHeadStep):
                self.assert_head(name, step)
            elif isinstance(step, WaitForHeadStep):
                self.wait_for_head(name, step)
            elif isinstance(step, AssertCanonicalStep):
                self.assert_canonical(name, step)
            elif isinstance(step, AssertStateStep):
                self.assert_state(name, step)
            elif isinstance(step, AssertReceiptStep):
                self.assert_receipt(name, step)
            elif isinstance(step, AssertLogsStep):
                self.assert_logs(name, step)
            elif isinstance(step, SendRawTransactionStep):
                self.send_raw_transaction(name, step)
            elif isinstance(step, AssertTxStatusStep):
                self.assert_tx_status(name, step)
            else:  # pragma: no cover - schema is closed
                raise LoggedError(f"{name}: unsupported step type")

    def _new_payload_params(self, label: str) -> tuple[list, int]:
        """(params, version) for a fixture or bound block."""
        if label not in self.bound:
            payload = self.fixture.blocks[label].payload
            return list(payload.params), int(payload.new_payload_version)
        bound = self.bound[label]
        fork = self.fixture.fork.fork_at(
            block_number=int(bound.payload.number),
            timestamp=int(bound.payload.timestamp),
        )
        version = fork.engine_new_payload_version()
        assert version is not None
        params: list = [bound.payload]
        if fork.engine_new_payload_blob_hashes():
            params.append(bound.versioned_hashes)
        if fork.engine_new_payload_beacon_root():
            params.append(bound.parent_beacon_block_root)
        if fork.engine_new_payload_requests():
            params.append(bound.execution_requests or [])
        return params, version

    def new_payload(self, name: str, step: NewPayloadStep, depth: int) -> None:
        """Send ``engine_newPayloadVX`` and check the outcome."""
        rpc = self.rpc(step.on)
        params, version = self._new_payload_params(step.block)
        name = f"{name}({step.block})"
        with self.timing_data.time(
            f"engine_newPayloadV{version} {step.block}"
        ):
            try:
                response = rpc.engine.new_payload(*params, version=version)
                observed = Observed(
                    status=response.status.value,
                    latest_valid_hash=response.latest_valid_hash,
                    validation_error=response.validation_error,
                )
            except JSONRPCError as e:
                observed = Observed(error_code=e.code, error_message=e.message)
        outcome = self.select(name, step.expect, observed)
        self.run(step.branches.get(outcome.id, []), depth + 1)

    def forkchoice_updated(
        self, name: str, step: ForkchoiceUpdatedStep, depth: int
    ) -> None:
        """Send ``engine_forkchoiceUpdatedVX`` and check the outcome."""
        rpc = self.rpc(step.on)
        name = (
            f"{name}(head={step.head}, safe={step.safe}, fin={step.finalized})"
        )
        if step.version is None:
            raise LoggedError(f"{name}: fixture step has no version")
        state = ForkchoiceState(
            head_block_hash=self.resolve(step.head),
            safe_block_hash=self.resolve(step.safe),
            finalized_block_hash=self.resolve(step.finalized),
        )
        attributes: PayloadAttributes | None = None
        if step.payload_attributes is not None:
            attributes = PayloadAttributes(
                **step.payload_attributes.model_dump(exclude_none=True)
            )
        with self.timing_data.time(f"engine_forkchoiceUpdatedV{step.version}"):
            try:
                response = rpc.engine.forkchoice_updated(
                    forkchoice_state=state,
                    payload_attributes=attributes,
                    version=step.version,
                )
                ps = response.payload_status
                observed = Observed(
                    status=ps.status.value,
                    latest_valid_hash=ps.latest_valid_hash,
                    validation_error=ps.validation_error,
                    payload_id=response.payload_id,
                )
                self.last_payload_id[step.on] = response.payload_id
                self.last_payload_attributes[step.on] = attributes
            except JSONRPCError as e:
                observed = Observed(error_code=e.code, error_message=e.message)
        if observed.error_code is None and any(
            o.head_moved is not None for o in step.expect
        ):
            observed.head_moved = self._head_hash(
                rpc, "latest"
            ) == self.resolve(step.head)
        outcome = self.select(name, step.expect, observed)
        self.run(step.branches.get(outcome.id, []), depth + 1)

    def get_payload(self, name: str, step: GetPayloadStep) -> None:
        """Retrieve the payload built after the last FCU and bind it."""
        rpc = self.rpc(step.on)
        name = f"{name}(bind={step.bind})"
        payload_id = self.last_payload_id.get(step.on)
        if payload_id is None:
            raise LoggedError(
                f"{name}: no payloadId from previous forkchoiceUpdated"
            )
        if step.version is None:
            raise LoggedError(f"{name}: fixture step has no version")
        if step.delay > 0:
            time.sleep(step.delay)
        with self.timing_data.time(f"engine_getPayloadV{step.version}"):
            response = rpc.engine.get_payload(payload_id, version=step.version)
        payload = response.execution_payload
        want_parent = self.resolve(step.parent)
        if payload.parent_hash != want_parent:
            raise LoggedError(
                f"{name}: built payload parent is "
                f"{self.label_of(payload.parent_hash)}, expected {step.parent}"
            )
        included = {Hash(tx.keccak256()) for tx in payload.transactions}
        for ref in step.transactions_include:
            if self.tx_hash(ref) not in included:
                raise LoggedError(
                    f"{name}: built payload misses tx {ref.block}:{ref.index}"
                )
        for ref in step.transactions_exclude:
            if self.tx_hash(ref) in included:
                raise LoggedError(
                    f"{name}: built payload includes excluded tx "
                    f"{ref.block}:{ref.index}"
                )
        versioned_hashes: List[Hash] = []
        if response.blobs_bundle is not None:
            versioned_hashes = [
                Hash(bytes([1]) + hashlib.sha256(bytes(c)).digest()[1:])
                for c in response.blobs_bundle.commitments
            ]
        attributes = self.last_payload_attributes.get(step.on)
        self.bound[step.bind] = BoundPayload(
            payload=payload,
            versioned_hashes=versioned_hashes,
            parent_beacon_block_root=(
                attributes.parent_beacon_block_root if attributes else None
            ),
            execution_requests=response.execution_requests,
            label_parent=step.parent,
        )
        self.labels_by_hash[payload.block_hash] = step.bind
        logger.info(
            f"{name}: bound block {payload.number} {payload.block_hash} "
            f"({len(payload.transactions)} txs) on {step.parent}"
        )

    def _head_hash(self, rpc: ClientRPC, tag: str) -> Hash | None:
        try:
            block = rpc.eth.get_block_by_number(tag)  # type: ignore[arg-type]
        except JSONRPCError as e:
            logger.info(
                f"eth_getBlockByNumber({tag!r}) error {e.code}: {e.message}"
            )
            return None
        return Hash(block["hash"]) if block else None

    def assert_head(self, name: str, step: AssertHeadStep) -> None:
        """Check latest/safe/finalized via ``eth_getBlockByNumber``."""
        rpc = self.rpc(step.on)
        for tag, label in (
            ("latest", step.latest),
            ("safe", step.safe),
            ("finalized", step.finalized),
        ):
            if label is None:
                continue
            got = self._head_hash(rpc, tag)
            want = self.resolve(label)
            if got != want:
                raise LoggedError(
                    f"{name}: '{tag}' is {self.label_of(got)} ({got}), "
                    f"expected {label} ({want})"
                )
            logger.info(f"{name}: {tag} == {label}")

    def wait_for_head(self, name: str, step: WaitForHeadStep) -> None:
        """Poll ``latest`` until it equals the label or time runs out."""
        rpc = self.rpc(step.on)
        want = self.resolve(step.latest)
        deadline = time.monotonic() + step.timeout
        got: Hash | None = None
        while time.monotonic() < deadline:
            got = self._head_hash(rpc, "latest")
            if got == want:
                logger.info(f"{name}: latest == {step.latest}")
                return
            time.sleep(1.0)
        raise LoggedError(
            f"{name}: timed out after {step.timeout}s; latest is "
            f"{self.label_of(got)}, expected {step.latest}"
        )

    def assert_canonical(self, name: str, step: AssertCanonicalStep) -> None:
        """Check the block at each height via ``eth_getBlockByNumber``."""
        rpc = self.rpc(step.on)
        for number, label in step.blocks.items():
            block = rpc.eth.get_block_by_number(int(number))
            got = Hash(block["hash"]) if block else None
            want = None if label is None else self.resolve(label)
            if got != want:
                raise LoggedError(
                    f"{name}: block {int(number)} is {self.label_of(got)} "
                    f"({got}), expected {label} ({want})"
                )
            logger.info(f"{name}: block {int(number)} == {label}")

    def assert_state(self, name: str, step: AssertStateStep) -> None:
        """Check account fields via ``eth_getBalance`` and friends."""
        rpc = self.rpc(step.on)
        at: Any = (
            "latest" if step.at == "latest" else self.block_number(step.at)
        )
        for address, expected in step.accounts.items():
            if expected.balance is not None:
                got_balance = rpc.eth.get_balance(address, at)
                if got_balance != int(expected.balance):
                    raise LoggedError(
                        f"{name}: balance of {address} at {step.at} is "
                        f"{got_balance}, expected {int(expected.balance)}"
                    )
            if expected.nonce is not None:
                got_nonce = rpc.eth.get_transaction_count(address, at)
                if got_nonce != int(expected.nonce):
                    raise LoggedError(
                        f"{name}: nonce of {address} at {step.at} is "
                        f"{got_nonce}, expected {int(expected.nonce)}"
                    )
            if expected.storage:
                for key, value in expected.storage.items():
                    got = rpc.eth.get_storage_at(address, key, at)
                    if got != value:
                        raise LoggedError(
                            f"{name}: storage {key} of {address} at {step.at} "
                            f"is {got}, expected {value}"
                        )
        logger.info(f"{name}: state at {step.at} matches")

    def assert_receipt(self, name: str, step: AssertReceiptStep) -> None:
        """Check ``eth_getTransactionReceipt`` block hash (or absence)."""
        rpc = self.rpc(step.on)
        tx_hash = self.tx_hash(step.tx)
        receipt = rpc.eth.get_transaction_receipt(tx_hash)
        ref = f"{step.tx.block}:{step.tx.index}"
        if step.block is None:
            if receipt is not None:
                raise LoggedError(
                    f"{name}: tx {ref} has a receipt in block "
                    f"{self.label_of(receipt.get('blockHash'))}, expected none"
                )
            logger.info(f"{name}: tx {ref} has no receipt")
            return
        if receipt is None:
            raise LoggedError(
                f"{name}: tx {ref} has no receipt, expected block {step.block}"
            )
        got = Hash(receipt["blockHash"])
        if got != self.resolve(step.block):
            raise LoggedError(
                f"{name}: tx {ref} receipt is in {self.label_of(got)}, "
                f"expected {step.block}"
            )
        if step.status is not None and int(receipt["status"], 16) != int(
            step.status
        ):
            raise LoggedError(
                f"{name}: tx {ref} receipt status {receipt['status']}, "
                f"expected {int(step.status)}"
            )
        logger.info(f"{name}: tx {ref} receipt in {step.block}")

    def assert_logs(self, name: str, step: AssertLogsStep) -> None:
        """Check ``eth_getLogs`` returns exactly the expected blocks' logs."""
        rpc = self.rpc(step.on)
        params: Dict[str, Any] = {
            "fromBlock": step.from_block
            if isinstance(step.from_block, str)
            else hex(int(step.from_block)),
            "toBlock": step.to_block
            if isinstance(step.to_block, str)
            else hex(int(step.to_block)),
        }
        if step.address is not None:
            params["address"] = f"{step.address}"
        from execution_testing.rpc.rpc_types import RPCCall

        logs = rpc.eth.post_request(
            request=RPCCall(method="getLogs", params=[params])
        ).result_or_raise()
        got = sorted(self.label_of(log["blockHash"]) for log in logs)
        want = sorted(step.blocks)
        if got != want:
            raise LoggedError(
                f"{name}: eth_getLogs returned logs from {got}, "
                f"expected {want}"
            )
        logger.info(f"{name}: logs from {want}")

    def send_raw_transaction(
        self, name: str, step: SendRawTransactionStep
    ) -> None:
        """Send a fixture transaction and check acceptance."""
        rpc = self.rpc(step.on)
        ref = f"{step.tx.block}:{step.tx.index}"
        try:
            rpc.eth.send_raw_transaction(self.tx_rlp(step.tx))
            result = "accepted"
            detail = ""
        except JSONRPCError as e:
            result = "rejected"
            detail = f" ({e.code}: {e.message})"
        if result not in step.expect:
            raise LoggedError(
                f"{name}: tx {ref} {result}{detail}, expected {step.expect}"
            )
        logger.info(f"{name}: tx {ref} {result}{detail}")
        self.matched.append(f"{name}:{result}")

    def assert_tx_status(self, name: str, step: AssertTxStatusStep) -> None:
        """Check ``eth_getTransactionByHash`` pool/chain status."""
        rpc = self.rpc(step.on)
        ref = f"{step.tx.block}:{step.tx.index}"
        tx = rpc.eth.get_transaction_by_hash(self.tx_hash(step.tx))
        if tx is None:
            status = "dropped"
        elif tx.block_hash is None:
            status = "pending"
        else:
            status = "included"
        if status not in step.expect:
            raise LoggedError(
                f"{name}: tx {ref} is {status}, expected {step.expect}"
            )
        if status == "included" and step.included_in is not None:
            assert tx is not None and tx.block_hash is not None
            if tx.block_hash != self.resolve(step.included_in):
                raise LoggedError(
                    f"{name}: tx {ref} included in "
                    f"{self.label_of(tx.block_hash)}, "
                    f"expected {step.included_in}"
                )
        logger.info(f"{name}: tx {ref} is {status}")
        self.matched.append(f"{name}:{status}")


def test_reorg_via_engine(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    client: Client,
    peer_rpcs: Dict[str, ClientRPC],
    fixture: BlockchainEngineReorgFixture,
    genesis_header: FixtureHeader,
) -> None:
    """
    Execute a reorg fixture against a fresh client (plus declared peers).

    1. Send an initial forkchoiceUpdated to genesis (readiness + head reset).
    2. Verify the client's genesis hash.
    3. Run the fixture's steps.
    """
    del client
    fcu_version = fixture.fork.fork_at(
        block_number=0, timestamp=int(genesis_header.timestamp)
    ).engine_forkchoice_updated_version()
    assert fcu_version is not None, "reorg fixtures require the Engine API"

    clients = {MAIN_CLIENT: ClientRPC(MAIN_CLIENT, eth_rpc, engine_rpc)}
    clients.update(peer_rpcs)

    for rpc in clients.values():
        send_forkchoice_update_to_genesis(
            rpc.engine,
            genesis_header=genesis_header,
            forkchoice_version=fcu_version,
            timing_data=timing_data,
            label=rpc.name,
        )
        verify_genesis_block_hash(
            rpc.eth, genesis_header, timing_data, label=rpc.name
        )

    runner = StepRunner(fixture, clients, timing_data)
    with timing_data.time("Steps"):
        runner.run(fixture.steps)
    logger.info(f"All steps passed. Outcomes: {runner.matched}")
