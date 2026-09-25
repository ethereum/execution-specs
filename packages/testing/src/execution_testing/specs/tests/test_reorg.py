"""Tests for the ``ReorgTest`` spec: DAG filling and fixture emission."""

from typing import Any, Callable, Tuple

import pytest
from pydantic import ValidationError

from execution_testing.base_types import Account, Address, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.exceptions import BlockException, EngineAPIError
from execution_testing.fixtures import BlockchainEngineReorgFixture
from execution_testing.fixtures.blockchain import PayloadAttributes
from execution_testing.fixtures.reorg import (
    AssertHeadStep,
    AssertReceiptStep,
    AssertStateStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    TxRef,
)
from execution_testing.forks import (
    Amsterdam,
    BPO2ToAmsterdamAtTime15k,
    Cancun,
    Fork,
    Prague,
)
from execution_testing.test_types import Alloc, Environment, Transaction

from ..blockchain import Header
from ..reorg import ReorgBlock, ReorgTest

SENDER = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
RECIPIENT = Address(0xC0DE)


def pre_alloc() -> Alloc:
    """Funded sender."""
    return Alloc({SENDER: Account(balance=10**21, nonce=0)})


def tx(nonce: int, value: int) -> Transaction:
    """Simple value transfer from the funded sender."""
    return Transaction(
        nonce=nonce,
        to=RECIPIENT,
        value=value,
        gas_limit=21_000,
        gas_price=10,
        secret_key=Hash(
            0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
        ),
    )


@pytest.mark.parametrize("fork", [Cancun, Prague])
def test_fill_sibling_and_invalid_child(
    fork: Fork, default_t8n: TransitionTool
) -> None:
    r"""
    Fill a DAG with a sibling block and a block built on an invalid parent.

    genesis <- a1 <- a2
                 \\- b2 (same height as a2, different tx)
                 \\- i2 (invalid state root) <- i3 (valid child of invalid)
    """
    test = ReorgTest(
        fork=fork,
        genesis_environment=Environment(),
        pre=pre_alloc(),
        blocks=[
            ReorgBlock(label="a1", txs=[tx(0, 1)]),
            ReorgBlock(label="a2", txs=[tx(1, 2)]),
            ReorgBlock(label="b2", parent="a1", txs=[tx(1, 3)]),
            ReorgBlock(
                label="i2",
                parent="a1",
                txs=[tx(1, 4)],
                rlp_modifier=Header(state_root=Hash(1)),
                exception=[
                    BlockException.INVALID_STATE_ROOT,
                    BlockException.INVALID_BLOCK_HASH,
                ],
            ),
            ReorgBlock(label="i3", parent="i2", txs=[tx(2, 5)]),
        ],
        steps=[
            NewPayloadStep(block="a1"),
            ForkchoiceUpdatedStep(head="a1"),
            NewPayloadStep(block="a2"),
            ForkchoiceUpdatedStep(head="a2"),
            NewPayloadStep(block="b2"),
            NewPayloadStep(block="i2"),
            NewPayloadStep(block="i3"),
            # b2's multi-outcome switch is last: i2/i3 above never
            # reference b2 or model.head, so nothing downstream depends on
            # which of applied/refused actually occurs here.
            ForkchoiceUpdatedStep(head="b2"),
        ],
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)

    blocks = fixture.blocks
    assert set(blocks) == {"a1", "a2", "b2", "i2", "i3"}
    p = {k: v.payload.params[0] for k, v in blocks.items()}

    # Parent links follow the labeled DAG, not list order.
    assert p["a2"].parent_hash == p["a1"].block_hash
    assert p["b2"].parent_hash == p["a1"].block_hash
    assert p["i2"].parent_hash == p["a1"].block_hash
    assert p["i3"].parent_hash == p["i2"].block_hash
    # Siblings occupy the same height with distinct hashes.
    assert p["a2"].number == p["b2"].number == 2
    assert p["a2"].block_hash != p["b2"].block_hash
    # Invalid block carries the corrupted state root; its child is built on
    # the correct post-state so its own header is internally consistent.
    assert p["i2"].state_root == Hash(1)
    assert p["i3"].state_root != Hash(1)
    # Stored block payloads carry only the newPayload request (params and
    # version); response/fill-time-internal fields are not serialized.
    dumped_payload = fixture.json_dict_with_info()["blocks"]["i2"]["payload"]
    assert set(dumped_payload) == {"params", "newPayloadVersion"}

    # Model annotations.
    steps = fixture.steps
    np_b2 = steps[4]
    assert isinstance(np_b2, NewPayloadStep)
    assert [o.id for o in np_b2.expect] == ["valid", "accepted"]
    np_i2 = steps[5]
    assert isinstance(np_i2, NewPayloadStep)
    assert [o.id for o in np_i2.expect] == ["invalid"]
    assert np_i2.expect[0].latest_valid_hash == "a1"
    np_i3 = steps[6]
    assert isinstance(np_i3, NewPayloadStep)
    assert [o.id for o in np_i3.expect] == ["invalid", "syncing"]
    fcu_b2 = steps[7]
    assert isinstance(fcu_b2, ForkchoiceUpdatedStep)
    assert [o.id for o in fcu_b2.expect] == ["applied", "refused"]
    assert fcu_b2.version == fork.engine_forkchoice_updated_version()
    assert isinstance(fcu_b2.branches["applied"][-1], AssertHeadStep)

    # Round-trip through JSON keeps the discriminated step union intact.
    reloaded = BlockchainEngineReorgFixture.model_validate(
        fixture.json_dict_with_info()
    )
    assert reloaded.resolve("b2") == p["b2"].block_hash
    assert reloaded.resolve("genesis") == fixture.genesis.block_hash
    assert isinstance(reloaded.steps[7], ForkchoiceUpdatedStep)


def test_dag_validation_rejects_unknown_parent() -> None:  # noqa: D103
    with pytest.raises(ValueError, match="unknown parent"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[ReorgBlock(label="a1", parent="nope")],
            steps=[],
        ).validate_dag()


def test_dag_validation_rejects_duplicate_and_reserved_labels() -> None:  # noqa: D103
    with pytest.raises(ValueError, match="duplicate"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[ReorgBlock(label="a"), ReorgBlock(label="a")],
            steps=[],
        ).validate_dag()
    with pytest.raises(ValueError, match="reserved"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[ReorgBlock(label="genesis")],
            steps=[],
        ).validate_dag()


def test_step_validation_rejects_unknown_label() -> None:  # noqa: D103
    with pytest.raises(ValueError, match="unknown label"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[ReorgBlock(label="a1")],
            steps=[ForkchoiceUpdatedStep(head="a9")],
        ).validate_dag()


def test_step_validation_rejects_negative_tx_index() -> None:  # noqa: D103
    with pytest.raises(ValueError, match="negative transaction index"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[ReorgBlock(label="a1", txs=[tx(0, 1)])],
            steps=[
                AssertReceiptStep(tx=TxRef(block="a1", index=-1), block="a1")
            ],
        ).validate_dag()


def test_step_validation_rejects_out_of_range_tx_index() -> None:  # noqa: D103
    with pytest.raises(ValueError, match="has only 1 transaction"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[ReorgBlock(label="a1", txs=[tx(0, 1)])],
            steps=[
                AssertReceiptStep(tx=TxRef(block="a1", index=1), block="a1")
            ],
        ).validate_dag()


def test_fill_serializes_versions_and_tx_index_as_decimal_strings(
    default_t8n: TransitionTool,
) -> None:
    """FCU/getPayload versions and TxRef.index serialize as Number strings."""
    test = ReorgTest(
        fork=Cancun,
        genesis_environment=Environment(),
        pre=pre_alloc(),
        blocks=[ReorgBlock(label="a1", txs=[tx(0, 1), tx(1, 2)])],
        steps=[
            NewPayloadStep(block="a1"),
            ForkchoiceUpdatedStep(head="a1"),
            AssertReceiptStep(tx=TxRef(block="a1", index=1), block="a1"),
        ],
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    dumped = fixture.json_dict_with_info()
    fcu_step = dumped["steps"][1]
    assert fcu_step["version"] == str(
        Cancun.engine_forkchoice_updated_version()
    )
    receipt_step = dumped["steps"][2]
    assert receipt_step["tx"]["index"] == "1"


def test_build_request_version_follows_attributes_fork(
    default_t8n: TransitionTool,
) -> None:
    """A build request across a fork boundary uses the new fork's FCU."""
    test = ReorgTest(
        fork=BPO2ToAmsterdamAtTime15k,
        pre=Alloc(),
        blocks=[ReorgBlock(label="a1")],
        steps=[
            NewPayloadStep(block="a1"),
            ForkchoiceUpdatedStep(
                head="a1",
                payload_attributes=PayloadAttributes(
                    timestamp=15_000,
                    prev_randao=Hash(0),
                    suggested_fee_recipient=Address(0),
                ),
            ),
        ],
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    fcu = fixture.steps[1]
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    assert fcu.version == Amsterdam.engine_forkchoice_updated_version()


@pytest.mark.parametrize(
    "make,rejected",
    [
        (
            lambda label: ReorgBlock(label=label),
            ("genesis", "zero", "latest", "null", "any"),
        ),
        (
            lambda label: NewPayloadStep(block=label),
            ("genesis", "zero", "latest", "null", "any"),
        ),
        # "genesis"/"zero" are legitimate FCU head values, not reserved here.
        (
            lambda label: ForkchoiceUpdatedStep(head=label),
            ("latest", "null", "any"),
        ),
        # "genesis"/"latest" are legitimate assertState.at values.
        (
            lambda label: AssertStateStep(at=label, accounts={}),
            ("zero", "null", "any"),
        ),
    ],
)
def test_block_label_rejects_reserved_names(
    make: Callable[[str], Any], rejected: Tuple[str, ...]
) -> None:
    """A ``BlockLabel`` field rejects every reserved name at construction."""
    for label in rejected:
        with pytest.raises(ValidationError, match="reserved"):
            make(label)


def test_post_field_rejects_nonempty_alloc() -> None:
    """A DAG has no single final block; fixture-wide `post` is rejected."""
    with pytest.raises(ValueError, match="fixture-wide `post`"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            post=Alloc({RECIPIENT: Account(balance=1)}),
            blocks=[ReorgBlock(label="a1")],
            steps=[],
        )


def test_engine_api_error_code_rejected_on_block() -> None:
    """A block's Engine API error belongs on the delivering step, not it."""
    with pytest.raises(ValueError, match="engine_api_error_code"):
        ReorgTest(
            fork=Cancun,
            pre=pre_alloc(),
            blocks=[
                ReorgBlock(
                    label="a1",
                    engine_api_error_code=EngineAPIError.InvalidParams,
                )
            ],
            steps=[],
        )


def test_expected_post_state_mismatch_fails_fill(
    default_t8n: TransitionTool,
) -> None:
    """A block's own `expected_post_state` is verified against its result."""
    test = ReorgTest(
        fork=Cancun,
        pre=pre_alloc(),
        blocks=[
            ReorgBlock(
                label="a1",
                txs=[tx(0, 1)],
                expected_post_state=Alloc({RECIPIENT: Account(balance=999)}),
            )
        ],
        steps=[NewPayloadStep(block="a1"), ForkchoiceUpdatedStep(head="a1")],
    )
    with pytest.raises(Account.BalanceMismatchError):
        test.generate(
            t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
        )
