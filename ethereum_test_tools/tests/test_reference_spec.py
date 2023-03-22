"""
Test suite for `ethereum_test_tools.common.reference_spec` module.
"""

# import pytest

import re

import pytest

from ..reference_spec.git_reference_spec import GitReferenceSpec
from ..reference_spec.reference_spec import NoLatestKnownVersion


def test_git_reference_spec():
    """
    Test Git reference spec.
    """
    ref_spec = GitReferenceSpec(
        SpecPath="EIPS/eip-100.md",
    )
    latest_spec = ref_spec._get_latest_spec()
    assert latest_spec is not None
    assert "sha" in latest_spec
    assert re.match(r"^[0-9a-f]{40}$", latest_spec["sha"])
    with pytest.raises(NoLatestKnownVersion):
        # `is_outdated` method raises here because known version is unset
        ref_spec.is_outdated()
    ref_spec.SpecVersion = "0000000000000000000000000000000000000000"
    assert ref_spec.is_outdated()
