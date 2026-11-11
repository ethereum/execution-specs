"""Test suite for invalid blocks in ``fill-stateful`` benchmarks."""

from types import SimpleNamespace
from typing import Any, Dict

import pytest

from execution_testing.base_types import Bloom, Bytes, Hash
from execution_testing.client_clis.cli_types import (
    LazyAllocJson,
    Result,
    TransitionToolOutput,
)
from execution_testing.exceptions import BlockException
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import Osaka, Requests
from execution_testing.test_types import (
    Alloc,
    BlockAccessListExpectation,
    Environment,
    TestPhase,
    Transaction,
    Withdrawal,
)
from execution_testing.test_types.receipt_types import TransactionReceipt

from ..blockchain import (
    Block,
    BlockchainTest,
    BuiltBlock,
    Header,
    validate_stateful_blocks,
)

FORK = Osaka
CLIENT_GAS_LIMIT = 30_000_000
ENV_GAS_LIMIT = 36_000_000
GAS_USED = 21_000


class _Backend:
    """
    Stand-in for a filler backend whose ``Result`` reports ``reported``
    on top of a fixed execution outcome.
    """

    exception_mapper = SimpleNamespace(reliable=True)
    attests_block_access_list_hash = True

    def __init__(self, *, imported: bool = True, **reported: Any) -> None:
        self.imported = imported
        self.reported = reported

    def get_traces(self) -> None:
        """Return no traces."""
        return None

    def evaluate(self, **_kwargs: Any) -> TransitionToolOutput:
        """Return the fixed outcome; receipts only if it was imported."""
        result = Result(
            state_root=Hash(0),
            transactions_trie=Hash(0),
            receipts_root=Hash(0),
            logs_hash=Hash(0),
            logs_bloom=Bloom(0),
            receipts=(
                [TransactionReceipt(cumulative_gas_used=GAS_USED)]
                if self.imported
                else []
            ),
            gas_used=GAS_USED,
            base_fee_per_gas=7,
            excess_blob_gas=0,
            withdrawals_root=Hash(Withdrawal.list_root([])),
            requests=[],
            requests_hash=Hash(Requests()),
            **self.reported,
        )
        return TransitionToolOutput(
            alloc=LazyAllocJson(raw={}, _state_root=Hash(0)), result=result
        )


def _tx(phase: TestPhase) -> Transaction:
    """Build a transaction tagged with ``phase``."""
    return Transaction(test_phase=phase)


def _valid_block(**fields: Any) -> Block:
    """Build an execution block."""
    return Block(txs=[_tx(TestPhase.EXECUTION)], **fields)


def _invalid_block(**modifier_fields: Any) -> Block:
    """Build an execution block whose header understates ``gas_used``."""
    return _valid_block(
        rlp_modifier=Header(gas_used=GAS_USED - 1, **modifier_fields),
        exception=BlockException.INVALID_GAS_USED,
    )


def _build(block: Block, backend: _Backend) -> BuiltBlock:
    """Run ``generate_block_data`` for ``block`` on top of block 1."""
    return BlockchainTest(
        fork=FORK, pre=Alloc(), post=Alloc(), blocks=[]
    ).generate_block_data(
        t8n=backend,  # type: ignore[arg-type]
        block=block,
        previous_env=Environment(
            parent_gas_limit=ENV_GAS_LIMIT,
            parent_timestamp=12,
            parent_base_fee_per_gas=7,
            parent_gas_used=GAS_USED,
            parent_excess_blob_gas=0,
            parent_blob_gas_used=0,
            block_hashes={1: Hash(1)},
        ),
        previous_alloc=Alloc(),
    )


def _client_header(**changes: Any) -> FixtureHeader:
    """
    Return the header a client seals for an execution block: fill's own
    header, except for the gas limit the client chose.
    """
    fill_header = _build(_valid_block(), _Backend()).header
    return fill_header.copy(gas_limit=CLIENT_GAS_LIMIT, fork=FORK, **changes)


def _client(*, imported: bool = True, **header_changes: Any) -> _Backend:
    """
    Return a backend reporting the block a client sealed; a client only
    imports, and so only has receipts for, a block that is not corrupted.
    """
    header = _client_header(**header_changes)
    reported: Dict[str, Any] = {
        "gas_limit": header.gas_limit,
        "block_hash": header.block_hash,
    }
    return _Backend(imported=imported, **reported)


def test_header_takes_the_fields_the_backend_reports() -> None:
    """The built header is the block the client sealed."""
    built = _build(_valid_block(), _client())

    assert built.header.gas_limit == CLIENT_GAS_LIMIT
    assert built.header.block_hash == _client_header().block_hash


def test_a_field_the_test_sets_must_reach_the_block() -> None:
    """A backend that overrides what the test asked for is refused."""
    with pytest.raises(Exception, match="sets `gas_limit`"):
        _build(_valid_block(gas_limit=ENV_GAS_LIMIT), _client())


def test_header_must_hash_to_the_sealed_block() -> None:
    """A field the backend does not report must match its own."""
    backend = _client(parent_beacon_block_root=Hash(1))

    with pytest.raises(Exception, match="hashes to"):
        _build(_valid_block(), backend)


def test_valid_block_payload_is_the_sealed_block() -> None:
    """A valid block's payload hashes to what the client sealed."""
    payload = _build(
        _valid_block(), _client()
    ).get_fixture_engine_new_payload()

    assert payload.params[0].block_hash == _client_header().block_hash
    assert payload.validation_error is None


def test_corruption_only_touches_the_modified_field() -> None:
    """The rest of the payload stays as the client sealed it."""
    valid = _build(_valid_block(), _client())
    invalid = _build(_invalid_block(), _client(imported=False))

    sealed = valid.get_fixture_engine_new_payload().params[0]
    payload = invalid.get_fixture_engine_new_payload().params[0]

    untouched = {"gas_used", "block_hash"}
    assert payload.gas_used == GAS_USED - 1
    assert payload.gas_limit == CLIENT_GAS_LIMIT
    assert payload.model_dump(
        mode="json", by_alias=True, exclude=untouched
    ) == sealed.model_dump(mode="json", by_alias=True, exclude=untouched)


def test_corrupted_payload_hashes_to_the_corrupted_block() -> None:
    """
    The payload hashes to the client's block with the field rewritten, so
    a client has to reach the corrupted field to reject it.
    """
    payload = (
        _build(
            _invalid_block(), _client(imported=False)
        ).get_fixture_engine_new_payload()
    ).params[0]

    assert payload.block_hash == (
        _client_header(gas_used=GAS_USED - 1).block_hash
    )


def test_expected_exception_reaches_the_fixture() -> None:
    """The fixture payload names the exception and the test phase."""
    built = _build(_invalid_block(), _client(imported=False))

    payload = built.get_fixture_engine_new_payload(phase=TestPhase.EXECUTION)

    assert payload.validation_error == BlockException.INVALID_GAS_USED
    assert payload.phase == TestPhase.EXECUTION
    assert (
        payload.model_dump(mode="json", by_alias=True)["validationError"]
        == "BlockException.INVALID_GAS_USED"
    )


def test_phase_is_derived_when_not_given() -> None:
    """Without an explicit phase, the payload takes its txs' phase."""
    payload = _build(
        _valid_block(), _client()
    ).get_fixture_engine_new_payload()

    assert payload.phase == TestPhase.EXECUTION


@pytest.mark.parametrize(
    "block,reason",
    [
        pytest.param(
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                exception=BlockException.INVALID_GAS_USED,
            ),
            "no `rlp_modifier`",
            id="exception_without_modifier",
        ),
        pytest.param(
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                rlp_modifier=Header(gas_used=GAS_USED - 1),
            ),
            "no `exception`",
            id="modifier_without_exception",
        ),
        pytest.param(
            _invalid_block(withdrawals_root=Hash(1)),
            "withdrawals_root",
            id="field_outside_the_payload",
        ),
        pytest.param(
            _invalid_block(blob_gas_used=Header.REMOVE_FIELD),
            "removes",
            id="removed_field",
        ),
        pytest.param(
            _invalid_block().copy(requests=[Bytes(b"\x00")]),
            "overrides `requests`",
            id="requests_override",
        ),
        pytest.param(
            _invalid_block().copy(engine_new_payload_slot_number=1),
            "engine_new_payload_slot_number",
            id="payload_only_override",
        ),
        pytest.param(
            _invalid_block().copy(
                expected_block_access_list=(
                    BlockAccessListExpectation().modify(lambda bal: bal)
                )
            ),
            "block access list",
            id="block_access_list_modifier",
        ),
        pytest.param(
            Block(
                txs=[_tx(TestPhase.SETUP)],
                rlp_modifier=Header(gas_used=GAS_USED - 1),
                exception=BlockException.INVALID_GAS_USED,
            ),
            "setup-phase",
            id="setup_phase_block",
        ),
    ],
)
def test_unfillable_block_is_refused(block: Block, reason: str) -> None:
    """An invalid block the client cannot help produce is refused."""
    with pytest.raises(NotImplementedError, match=reason):
        validate_stateful_blocks([block])


def test_refusal_names_the_block_it_cannot_fill() -> None:
    """The refusal points at the offending block."""
    blocks = [
        Block(txs=[_tx(TestPhase.SETUP)]),
        Block(
            txs=[_tx(TestPhase.EXECUTION)],
            exception=BlockException.INVALID_GAS_USED,
        ),
    ]

    with pytest.raises(NotImplementedError, match="block 1"):
        validate_stateful_blocks(blocks)


def test_fillable_blocks_pass_the_gate() -> None:
    """A header-corrupted invalid block is fillable."""
    validate_stateful_blocks(
        [Block(txs=[_tx(TestPhase.SETUP)]), _invalid_block()]
    )
