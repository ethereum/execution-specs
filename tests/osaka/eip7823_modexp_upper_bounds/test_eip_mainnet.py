"""
Mainnet marked execute checklist tests for
[EIP-7823: ModExp Upper Bound](https://eips.ethereum.org/EIPS/eip-7823).
"""

from typing import Dict

import pytest
from execution_testing import (
    Alloc,
    StateTestFiller,
    Transaction,
)

from ...byzantium.eip198_modexp_precompile.helpers import (
    ModExpInput,
    ModExpOutput,
)
from ..eip7883_modexp_gas_increase.spec import Spec
from .spec import ref_spec_7823

REFERENCE_SPEC_GIT_PATH = ref_spec_7823.git_path
REFERENCE_SPEC_VERSION = ref_spec_7823.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


@pytest.fixture
def call_succeeds(modexp_expected: ModExpOutput) -> bool:
    """Override `call_succeeds` to use the parametrized ModExpOutput value."""
    return modexp_expected.call_success


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            ModExpInput(
                base=b"\x01" * Spec.MAX_LENGTH_BYTES,
                exponent=b"\x00",
                modulus=b"\x02",
            ),
            ModExpOutput(
                call_success=True,
                returned_data="0x01",
            ),
            id="base-boundary-1024-bytes",
        ),
    ],
)
def test_modexp_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """
    Mainnet test at the 1024-byte boundary.

    Tests that the ModExp precompile correctly handles input at the maximum
    allowed length (1024 bytes) per EIP-7823.
    """
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            ModExpInput(
                base=b"\x01" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"\x00",
                modulus=b"\x02",
            ),
            ModExpOutput(
                call_success=False,
                returned_data="",
            ),
            id="base-over-boundary-1025-bytes",
        ),
    ],
)
def test_modexp_over_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """
    Mainnet test exceeding the 1024-byte boundary.

    Tests that the ModExp precompile correctly rejects input exceeding the
    maximum allowed length (1024 bytes) per EIP-7823. This proves the EIP
    is correctly activated.
    """
    state_test(pre=pre, tx=tx, post=post)
