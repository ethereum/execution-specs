"""
Mainnet marked execute checklist tests for
[EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883).
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
from .spec import Spec, ref_spec_7883

REFERENCE_SPEC_GIT_PATH = ref_spec_7883.git_path
REFERENCE_SPEC_VERSION = ref_spec_7883.version

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
                base="ff" * 31 + "fc",
                exponent="02",
                modulus="05",
                declared_base_length=32,
                declared_exponent_length=1,
                declared_modulus_length=1,
            ),
            ModExpOutput(
                call_success=True,
                returned_data="0x04",
            ),
            id="32-bytes-long-base",
        ),
        pytest.param(
            ModExpInput(
                base="ff" * 32 + "fb",
                exponent="02",
                modulus="05",
                declared_base_length=33,
                declared_exponent_length=1,
                declared_modulus_length=1,
            ),
            ModExpOutput(
                call_success=True,
                returned_data="0x01",
            ),
            id="33-bytes-long-base",  # higher cost than 32 bytes
        ),
        pytest.param(
            ModExpInput(
                base="ee" * 32,
                exponent="ff" * Spec.MAX_LENGTH_BYTES,  # 1024 is upper limit
                modulus="03",
                declared_base_length=32,
                declared_exponent_length=1024,
                declared_modulus_length=1,
            ),
            ModExpOutput(
                call_success=True,
                returned_data="0x02",
            ),
            id="1024-bytes-long-exp",
        ),
        pytest.param(
            ModExpInput(
                base="e09ad9675465c53a109fac66a445c91b292d2bb2c5268addb30cd82f80fcb0033ff97c80a5fc6f39193ae969c6ede6710a6b7ac27078a06d90ef1c72e5c85fb5",
                exponent="010001",
                modulus="fc9e1f6beb81516545975218075ec2af118cd8798df6e08a147c60fd6095ac2bb02c2908cf4dd7c81f11c289e4bce98f3553768f392a80ce22bf5c4f4a248c6b",
                declared_base_length=64,
                declared_exponent_length=3,
                declared_modulus_length=64,
            ),
            ModExpOutput(
                call_success=True,
                returned_data=(
                    "0xc36d804180c35d4426b57b50c5bfcca5c01856d104564cd513b461d3c8b8409128a5573e416d0ebe38f5f736766d9dc27143e4da981dfa4d67f7dc474cbee6d2"
                ),
            ),
            id="nagydani-1-pow0x10001",
        ),
        pytest.param(
            ModExpInput(
                base="8d74b1229cc36912165d7ed62334d5ce0683ad12dbade86cdbd705f46693d6c0",
                exponent="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                modulus="8f70e8f94c5ad28ed971e258ea3854ebf57131ae4c842e5cafe1c70db8272caf",
                declared_base_length=32,
                declared_exponent_length=64,
                declared_modulus_length=32,
            ),
            ModExpOutput(
                call_success=True,
                returned_data=(
                    "0x0000000000000000000000000000000000000000000000000000000000000001"
                ),
            ),
            id="zero-exponent-64bytes",
        ),
    ],
)
def test_modexp_different_base_lengths(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """Mainnet test for triggering gas cost increase."""
    state_test(pre=pre, tx=tx, post=post)
