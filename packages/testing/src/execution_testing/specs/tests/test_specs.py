"""Test specs from execution_testing.specs."""

from typing import ClassVar, Dict, Protocol, Sequence, Tuple, Type

import pytest

from execution_testing.fixtures import (
    BaseFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)

from ..base import BaseTest


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
    """
    keys: Dict[Tuple[Type[BaseFixture], str], str] = dict()
    for fixture_format in spec.supported_fixture_formats:
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
