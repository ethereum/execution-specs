"""Test cases for the execution_testing.fixtures.base module."""

from typing import List

import pytest

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
)
from execution_testing.forks import Fork, Prague, TransitionFork
from execution_testing.test_types import Transaction

from ..base import BaseFixture, LabeledFixtureFormat
from ..blockchain import (
    BlockchainEngineFixture,
    BlockchainEngineStatefulFixture,
    BlockchainFixture,
    FixtureConfig,
    FixtureEngineNewPayload,
    FixtureHeader,
)
from ..file import Fixtures
from ..state import FixtureEnvironment, FixtureTransaction, StateFixture
from ..transaction import FixtureResult, TransactionFixture


def test_json_dict() -> None:
    """Test that the json_dict property does not include the info field."""
    fixture = TransactionFixture(
        transaction="0x1234",
        result={"Paris": FixtureResult(intrinsic_gas=0)},
    )
    assert "_info" not in fixture.json_dict, (
        "json_dict should exclude the 'info' field"
    )


@pytest.mark.parametrize(
    "fixture",
    [
        pytest.param(
            StateFixture(
                env=FixtureEnvironment(),
                transaction=FixtureTransaction(
                    nonce=0,
                    gas_limit=[0],
                    value=[0],
                    data=[b""],
                ),
                pre={},
                post={},
                config={},
            ),
            id="StateFixture",
        ),
        pytest.param(
            TransactionFixture(
                transaction="0x1234",
                result={"Paris": FixtureResult(intrinsic_gas=0)},
            ),
            id="TransactionFixture",
        ),
        pytest.param(
            BlockchainEngineStatefulFixture(
                fork=Prague,
                last_block_hash=Hash(1),
                post_state_hash=Hash(2),
                config=FixtureConfig(fork=Prague),
                snapshot_block_number=0,
                snapshot_block_hash=Hash(0),
                start_block_number=0,
                start_block_hash=Hash(0),
                setup_payloads=[
                    FixtureEngineNewPayload.from_fixture_header(
                        fork=Prague,
                        header=FixtureHeader(
                            parent_hash=Hash(0),
                            ommers_hash=Hash(1),
                            fee_recipient=Address(2),
                            state_root=Hash(3),
                            transactions_trie=Hash(4),
                            receipts_root=Hash(5),
                            logs_bloom=Bloom(6),
                            difficulty=7,
                            number=1,
                            gas_limit=9,
                            gas_used=10,
                            timestamp=11,
                            extra_data=Bytes([12]),
                            prev_randao=Hash(13),
                            nonce=HeaderNonce(14),
                            base_fee_per_gas=15,
                            withdrawals_root=Hash(16),
                            blob_gas_used=17,
                            excess_blob_gas=18,
                            parent_beacon_block_root=19,
                            requests_hash=20,
                        ),
                        transactions=[
                            Transaction(
                                gas_limit=0x5208,
                                max_fee_per_gas=7,
                            ).with_signature_and_sender(),
                        ],
                        withdrawals=[],
                        requests=[],
                    ),
                ],
                payloads=[
                    FixtureEngineNewPayload.from_fixture_header(
                        fork=Prague,
                        header=FixtureHeader(
                            parent_hash=Hash(10),
                            ommers_hash=Hash(1),
                            fee_recipient=Address(2),
                            state_root=Hash(3),
                            transactions_trie=Hash(4),
                            receipts_root=Hash(5),
                            logs_bloom=Bloom(6),
                            difficulty=7,
                            number=2,
                            gas_limit=9,
                            gas_used=10,
                            timestamp=12,
                            extra_data=Bytes([12]),
                            prev_randao=Hash(13),
                            nonce=HeaderNonce(14),
                            base_fee_per_gas=15,
                            withdrawals_root=Hash(16),
                            blob_gas_used=17,
                            excess_blob_gas=18,
                            parent_beacon_block_root=19,
                            requests_hash=20,
                        ),
                        transactions=[
                            Transaction(
                                gas_limit=0x5208,
                                max_fee_per_gas=7,
                            ).with_signature_and_sender(),
                        ],
                        withdrawals=[],
                        requests=[],
                    ),
                ],
            ),
            id="BlockchainEngineStatefulFixture",
        ),
    ],
)
def test_base_fixtures_parsing(fixture: BaseFixture) -> None:
    """Test that the Fixtures generic model can validate any fixture format."""
    fixture.fill_info(
        "t8n-version",
        "test_case_description",
        fixture_source_url="fixture_source_url",
        ref_spec=None,
        _info_metadata={},
    )
    json_dump = fixture.json_dict_with_info()
    assert json_dump is not None
    Fixtures.model_validate({"fixture": json_dump})


class VetoingLabel(LabeledFixtureFormat):
    """A label that vetoes itself for every fork and marker set."""

    def supports_fork(self, fork: Fork | TransitionFork) -> bool:
        """Refuse every fork."""
        del fork
        return False

    def discard_fixture_format_by_marks(
        self,
        fork: Fork | TransitionFork,
        markers: List[pytest.Mark],
    ) -> bool:
        """Discard for every marker set."""
        del fork, markers
        return True


def test_with_label_suffix_on_plain_format() -> None:
    """Test that a plain format derives its label from `format_id()`."""
    derived = BlockchainFixture.with_label_suffix("from_state_test")

    assert derived.format_id() == "blockchain_test_from_state_test"
    assert derived.format_class() is BlockchainFixture
    assert derived.base is None
    assert (
        derived.transition_tool_cache_key
        == BlockchainFixture.transition_tool_cache_key
    )


def test_with_label_suffix_keeps_labels_distinct() -> None:
    """
    Test that every label of one format derives its own distinct label.

    Deriving from `format_name` instead of `format_id()` would collapse both
    onto the format name, and the two derived labels would then compare equal
    and register only once.
    """
    one = LabeledFixtureFormat(
        BlockchainFixture, "alt_one", "d", transition_tool_cache_key=""
    )
    two = LabeledFixtureFormat(
        BlockchainFixture, "alt_two", "d", transition_tool_cache_key="other"
    )

    derived_one = one.with_label_suffix("from_state_test")
    derived_two = two.with_label_suffix("from_state_test")

    assert derived_one.format_id() == "alt_one_from_state_test"
    assert derived_two.format_id() == "alt_two_from_state_test"
    assert derived_one != derived_two
    for derived in (derived_one, derived_two):
        assert LabeledFixtureFormat.registered_labels[derived.label] is derived


def test_with_label_suffix_keeps_transition_tool_cache_key() -> None:
    """
    Test that a derived label keeps the cache key of the label it came from.

    Reverting to the wrapped format's key would make a label that opted out of
    caching share cached transition tool output once it is re-labeled.
    """
    opted_out = LabeledFixtureFormat(
        BlockchainFixture, "opted_out", "d", transition_tool_cache_key=""
    )
    own_key = LabeledFixtureFormat(
        BlockchainFixture, "own_key", "d", transition_tool_cache_key="own"
    )

    assert (
        opted_out.with_label_suffix(
            "from_state_test"
        ).transition_tool_cache_key
        == ""
    )
    assert (
        own_key.with_label_suffix("from_state_test").transition_tool_cache_key
        == "own"
    )


def test_with_label_suffix_own_transition_tool_cache_key() -> None:
    """
    Test that a suffix can set its own cache key, overriding what it derives
    from.

    A variant whose fixture asks the transition tool for something different
    needs its own key so it does not share cached output with the format or
    label it was derived from.
    """
    variant = BlockchainEngineFixture.with_label_suffix(
        "inclusion_list",
        transition_tool_cache_key="blockchain_test_inclusion_list",
    )

    assert variant.format_id() == "blockchain_test_engine_inclusion_list"
    assert variant.format_class() is BlockchainEngineFixture
    assert (
        variant.transition_tool_cache_key == "blockchain_test_inclusion_list"
    )
    assert (
        variant.transition_tool_cache_key
        != BlockchainEngineFixture.transition_tool_cache_key
    )

    # The key survives a further re-label, and can be overridden again.
    derived = variant.with_label_suffix("from_state_test")
    assert (
        derived.transition_tool_cache_key == "blockchain_test_inclusion_list"
    )
    assert (
        variant.with_label_suffix(
            "from_state_test", transition_tool_cache_key=""
        ).transition_tool_cache_key
        == ""
    )


def test_with_label_suffix_keeps_vetoes() -> None:
    """
    Test that a derived label keeps the fork and marker vetoes of its base.

    A re-labeled format that deferred to the plain format instead would fill
    for forks and markers the inner label had already refused.
    """
    veto = VetoingLabel(
        BlockchainFixture, "veto", "d", transition_tool_cache_key=""
    )

    derived = veto.with_label_suffix("from_state_test")

    assert derived.base is veto
    assert not derived.supports_fork(Prague)
    assert derived.discard_fixture_format_by_marks(Prague, [])


def mark_names(
    fixture_format: LabeledFixtureFormat | type[BaseFixture],
) -> List[str]:
    """Return the names of the marks a fixture format asks for."""
    return [mark.name for mark in fixture_format.marks()]


def test_is_variant_on_plain_format() -> None:
    """Test that a plain format is never a variant."""
    assert not BlockchainEngineFixture.is_variant("inclusion_list")
    assert not BlockchainEngineFixture.with_label_suffix(
        "from_state_test"
    ).is_variant("inclusion_list")


def test_variant_survives_re_labeling() -> None:
    """
    Test that a variant label stays that variant once re-labeled.

    A spec type queries `is_variant()` rather than comparing formats, which
    cannot tell a variant from the plain format it wraps.
    """
    variant = BlockchainEngineFixture.with_label_suffix(
        "inclusion_list",
        transition_tool_cache_key="blockchain_test_inclusion_list",
        variant="inclusion_list",
    )
    derived = variant.with_label_suffix("from_state_test")

    assert variant.is_variant("inclusion_list")
    assert derived.is_variant("inclusion_list")
    assert derived.variant == "inclusion_list"
    assert not derived.is_variant("something_else")
    # The plain format it wraps is not the variant.
    assert not derived.format_class().is_variant("inclusion_list")


def test_with_label_suffix_overrides_variant() -> None:
    """Test that a passed variant replaces the one it derives from."""
    variant = BlockchainEngineFixture.with_label_suffix(
        "inclusion_list", variant="inclusion_list"
    )

    overridden = variant.with_label_suffix(
        "narrowed", variant="narrowed_inclusion_list"
    )

    assert overridden.variant == "narrowed_inclusion_list"
    assert not overridden.is_variant("inclusion_list")


def test_marks_include_every_derived_label() -> None:
    """
    Test that a label is marked with every label it was derived from.

    Selecting the variant's own label must also select the labels other spec
    types derived from it, so `-m <variant>` does not silently miss them.
    """
    variant = BlockchainEngineFixture.with_label_suffix(
        "inclusion_list",
        transition_tool_cache_key="blockchain_test_inclusion_list",
        variant="inclusion_list",
    )
    derived = variant.with_label_suffix("from_state_test")

    assert mark_names(variant) == [
        "blockchain_test_engine",
        "transition_tool_cache_key",
        "blockchain_test_engine_inclusion_list",
    ]
    assert mark_names(derived) == [
        "blockchain_test_engine",
        "transition_tool_cache_key",
        "blockchain_test_engine_inclusion_list",
        "blockchain_test_engine_inclusion_list_from_state_test",
    ]
    assert derived.labels() == [
        "blockchain_test_engine_inclusion_list",
        "blockchain_test_engine_inclusion_list_from_state_test",
    ]


def test_marks_of_label_over_plain_format() -> None:
    """Test that a label over a plain format marks only its own label."""
    derived = BlockchainFixture.with_label_suffix("from_state_test")

    assert derived.labels() == ["blockchain_test_from_state_test"]
    assert mark_names(derived) == [
        "blockchain_test",
        "transition_tool_cache_key",
        "blockchain_test_from_state_test",
    ]
