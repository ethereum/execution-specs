"""
abstract: Tests [EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883)
    Test cases for [EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883).
"""

from typing import Dict

import pytest

from ethereum_test_tools import (
    Alloc,
    StateTestFiller,
    Transaction,
)

from .helpers import Vector
from .spec import ref_spec_7883

REFERENCE_SPEC_GIT_PATH = ref_spec_7883.git_path
REFERENCE_SPEC_VERSION = ref_spec_7883.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize("vector", Vector.from_file("vectors.json"), ids=lambda v: v.name)
def test_vectors_from_file(
    vector: Vector,
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp gas cost using the test vectors from EIP-7883."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )
