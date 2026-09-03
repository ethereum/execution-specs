"""Test specs from execution_testing.specs."""

from typing import ClassVar, Dict, Protocol, Sequence, Tuple, Type

import pytest

from execution_testing.fixtures import (
    BaseFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
    StateFixture,
)
from execution_testing.forks import Istanbul
from execution_testing.test_types import Alloc, Environment, Transaction

from ..base import BaseTest
from ..blockchain import BlockchainTest
from ..state import StateTest


def test_spec_types() -> None:
    """Test basic spec types are visible."""
    assert len(BaseTest.spec_types.items()) > 0
    assert "state_test" in BaseTest.spec_types
    assert "blockchain_test" in BaseTest.spec_types


class SpecType(Protocol):
    """Any class that declares supported fixture formats."""

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ]


class DuplicateTransitionToolCacheKeyError(Exception):
    """
    Exception used to indicate that a single spec uses the same
    fixture format twice without making a clear distinction of their
    transition tool cache keys.
    """

    def __init__(
        self,
        *,
        spec: Type[SpecType],
        key: Tuple[Type[BaseFixture], str],
        format_id_1: str,
        format_id_2: str,
    ):
        super().__init__(
            f"Duplicate Transition Tool Cache Key: "
            f'key "{key}" is used by two different fixture formats in spec "'
            f'f"type {spec}: "{format_id_1}", "{format_id_2}"'
        )


def spec_supported_fixture_formats_verifier(spec: Type[SpecType]) -> None:
    """
    Verify that the provided spec does not break the
    format-class+transition_tool_cache_key rule.

    An empty cache key opts the format out of caching entirely (no
    `transition_tool_cache_key` mark is emitted, so the filler removes
    the cache for its tests), so two formats of the same class may both
    carry an empty key without ever sharing cached output.
    """
    keys: Dict[Tuple[Type[BaseFixture], str], str] = dict()
    for fixture_format in spec.supported_fixture_formats:
        if not fixture_format.transition_tool_cache_key:
            continue
        key = (
            fixture_format.format_class(),
            fixture_format.transition_tool_cache_key,
        )
        if key in keys:
            raise DuplicateTransitionToolCacheKeyError(
                spec=spec,
                key=key,
                format_id_1=fixture_format.format_id(),
                format_id_2=keys[key],
            )
        keys[key] = fixture_format.format_id()


class DummyIncorrectSpec1:
    """Spec type that duplicates fixture formats."""

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        BlockchainFixture,
        BlockchainFixture,
    ]


class DummyIncorrectSpec2:
    """Spec type that duplicates fixture formats."""

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        BlockchainFixture,
        LabeledFixtureFormat(
            fixture_format=BlockchainFixture,
            label="alt_blockchain_fixture",
            description="alternative blockchain fixture",
        ),
    ]


class DummyCorrectSpec:
    """Spec type that duplicates fixture formats."""

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        BlockchainFixture,
        LabeledFixtureFormat(
            fixture_format=BlockchainFixture,
            label="alt_blockchain_fixture",
            description="alternative blockchain fixture",
            transition_tool_cache_key="",
        ),
    ]


@pytest.mark.parametrize(
    "spec,correct",
    [
        pytest.param(DummyIncorrectSpec1, False),
        pytest.param(DummyIncorrectSpec2, False),
        pytest.param(DummyCorrectSpec, True),
    ],
)
def test_spec_supported_fixture_formats_verifier(
    spec: Type[SpecType],
    correct: bool,
) -> None:
    """Unit test for `spec_supported_fixture_formats_verifier`."""
    if correct:
        spec_supported_fixture_formats_verifier(spec)
    else:
        with pytest.raises(DuplicateTransitionToolCacheKeyError):
            spec_supported_fixture_formats_verifier(spec)


@pytest.mark.parametrize("spec", BaseTest.spec_types)
def test_spec_types_fixture_formats(spec: str) -> None:
    """
    Verify that none of the declared spec types contain fixture formats
    that break the format-class+transition_tool_cache_key rule.
    """
    spec_supported_fixture_formats_verifier(BaseTest.spec_types[spec])


def test_state_test_labels_every_blockchain_test_format() -> None:
    """
    Verify `StateTest` derives one label per format `BlockchainTest` fills,
    minus the sync formats, each keeping its format class and cache key.

    Deriving the label from `format_name` rather than `format_id()` would
    collapse two labels of one format onto the same derived label, and the
    duplicate would be dropped silently by `registered_labels`.

    Variant labels (e.g. the frame transaction variants) deliberately add
    further labels per format, so only plain labels count toward the
    one-label-per-format property.
    """
    derived = {
        fixture_format.format_id(): fixture_format
        for fixture_format in StateTest.supported_fixture_formats
        if isinstance(fixture_format, LabeledFixtureFormat)
        and fixture_format.format_class() is not StateFixture
        and fixture_format.variant is None
    }
    expected = [
        fixture_format
        for fixture_format in BlockchainTest.supported_fixture_formats
        if "Sync" not in fixture_format.format_class().__name__
    ]

    assert len(derived) == len(expected), (
        f"Expected one label per blockchain test format: {sorted(derived)}"
    )
    for fixture_format in expected:
        label = f"{fixture_format.format_id()}_from_state_test"
        assert label in derived, f"Missing label {label}: {sorted(derived)}"
        assert derived[label].format_class() is fixture_format.format_class()
        assert (
            derived[label].transition_tool_cache_key
            == fixture_format.transition_tool_cache_key
        )


def test_state_test_conversion_checks_the_env_first() -> None:
    """
    Verify converting a state test to a blockchain test reports an env
    field the fork lacks with the field check's message.

    The genesis derivation runs before `BlockchainTest` checks the env,
    and for a blob field on a fork without blobs it fails on the fork's
    missing blob constants instead, which does not name the field.
    """
    state_test = StateTest(
        env=Environment(excess_blob_gas=1),
        pre=Alloc(),
        post=Alloc(),
        tx=Transaction(),
        fork=Istanbul,
    )
    with pytest.raises(ValueError, match="excess_blob_gas"):
        state_test.generate_blockchain_test()
