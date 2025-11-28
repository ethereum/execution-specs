"""
Mainnet marked tests for
[EIP-7823: ModExp Upper Bound](https://eips.ethereum.org/EIPS/eip-7823).
"""

from typing import Dict

import pytest
from execution_testing import (
    Alloc,
    StateTestFiller,
    Transaction,
    # TransactionException,
)
from execution_testing.base_types.base_types import Bytes
from execution_testing.test_types.block_types import Environment

from ...byzantium.eip198_modexp_precompile.helpers import (
    ModExpInput,
    ModExpOutput,
)
from .spec import ref_spec_7823

REFERENCE_SPEC_GIT_PATH = ref_spec_7823.git_path
REFERENCE_SPEC_VERSION = ref_spec_7823.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


# overwrite the conftest fixture
@pytest.fixture
def call_succeeds(modexp_expected: ModExpOutput) -> bool:
    """Override call_succeeds to use the parametrized ModExpOutput value."""
    return modexp_expected.call_success


# @pytest.mark.exception_test
@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            ModExpInput(
                base="ca" * 3070,
                exponent="ca",
                modulus="fe",
                declared_base_length=3070,
                declared_exponent_length=1,
                declared_modulus_length=1,
            ),
            ModExpOutput(
                call_success=False,
                returned_data=Bytes(),
            ),
            id="3070-bytes-long-base",
        ),
        pytest.param(
            ModExpInput(
                base="cd",
                exponent="ca" * 3070,
                modulus="dc",
                declared_base_length=1,
                declared_exponent_length=3070,
                declared_modulus_length=1,
            ),
            ModExpOutput(
                call_success=False,
                returned_data=Bytes(),
            ),
            id="3070-bytes-long-exp",
        ),
        pytest.param(
            ModExpInput(
                base="cd",
                exponent="cf",
                modulus="ee" * 3070,
                declared_base_length=1,
                declared_exponent_length=1,
                declared_modulus_length=3070,
            ),
            ModExpOutput(
                call_success=False,
                returned_data=Bytes(),
            ),
            id="3070-bytes-long-mod",
        ),
    ],
)
def test_modexp_different_base_lengths(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
    modexp_input: ModExpInput,
    modexp_expected: ModExpOutput,
    call_succeeds: bool,
) -> None:
    """
    Mainnet test for triggering gas cost increase.
    Upper bound per length param: 1024 bytes
    There are 3 length params: base, e, mod
    3*1024 = 3072
    Therefore, we can do negative tests for 3070+1+1 for each of those three.
    """
    state_test(env=Environment(), pre=pre, tx=tx, post=post)
