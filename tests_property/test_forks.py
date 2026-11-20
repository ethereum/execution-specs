"""The fork axis covers every spec package."""

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.utils import resolve_fork

from .forks import PLACEHOLDER_FORKS, SPEC_PACKAGES


def test_every_spec_package_is_tested() -> None:
    """
    Every spec package is tested against a framework fork, apart from the
    blob-parameter-only placeholders.
    """
    tested = {spec.short_name for spec in SPEC_PACKAGES.values()}
    placeholders = {
        resolve_fork(fork.transition_tool_name()).short_name
        for fork in PLACEHOLDER_FORKS
    }
    assert not tested & placeholders
    assert tested | placeholders == {
        spec.short_name for spec in Hardfork.discover()
    }
