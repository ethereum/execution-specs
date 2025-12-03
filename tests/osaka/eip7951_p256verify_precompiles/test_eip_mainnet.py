"""
Mainnet marked execute checklist tests for
[EIP-7951: Precompile for secp256r1 Curve Support](https://eips.ethereum.org/EIPS/eip-7951).
"""

import pytest
from execution_testing import Alloc, StateTestFiller, Transaction

from .spec import H, R, S, Spec, X, Y, ref_spec_7951

REFERENCE_SPEC_GIT_PATH = ref_spec_7951.git_path
REFERENCE_SPEC_VERSION = ref_spec_7951.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "expected_output", [Spec.SUCCESS_RETURN_VALUE], ids=[""]
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            H(  # 'hello world' r1 signed with private key 0xd946578401d1980aba1fc85df2a1ddc0d2d618aadd37b213f7f7f91a553b1499  # noqa: E501
                0xB94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9
            )
            + R(
                0x434287FA699FF2BE2A4475CCD9C063D1A22A424B6AB357D9BB0B31F7A71307B9
            )
            + S(
                0xBE6AF716032D408183C53F6F76945363144555FAD2A5FF7854159166E52FC1D0
            )
            + X(
                0xDA3C553A4215893E6D95D5818DF2519E13233A1E0E56E0EA7B4817A92A6973F9
            )
            + Y(
                0xD8C8877A49383E20C3FDC21D4E8E280EF1FEEB72C333036770369A4387168D33
            ),
            id="valid_r1_sig",
        ),
    ],
)
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
def test_valid(
    state_test: StateTestFiller, pre: Alloc, post: dict, tx: Transaction
) -> None:
    """Positive mainnet test for the P256VERIFY precompile."""
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "expected_output", [Spec.INVALID_RETURN_VALUE], ids=[""]
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            H(  # 'hello world' k1 signed (with eth prefix) with private key 0xd946578401d1980aba1fc85df2a1ddc0d2d618aadd37b213f7f7f91a553b1499  # noqa: E501
                0xD9EBA16ED0ECAE432B71FE008C98CC872BB4CC214D3220A36F365326CF807D68
            )
            + R(
                0x69CCCD84CA870C08D49D596342F464017F2A05B0BE539682EAA7529E4BE2DE36
            )
            + S(
                0x2CDB85FE13CB7DE39C1C7385BE9F38E8BDE9963CCBECD96281C4DF3ACA38F537
            )
            + X(
                0x82AE98A95AE76E389354F0EC660CF071309EA2D2CB14ADB6543106B790BE27FD
            )
            + Y(
                0x77B2CDC82C3AA8F2CF21E6257C197D75F84DCD0BC2FF8875C3E245C0E0874751
            ),
            id="invalid_r1_sig_but_valid_k1_sig",
        ),
    ],
)
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
def test_invalid(
    state_test: StateTestFiller, pre: Alloc, post: dict, tx: Transaction
) -> None:
    """
    Negative mainnet test for the P256VERIFY precompile.

    The signature actually is a valid secp256k1 signature,
    so this is an interesting test case.
    """
    state_test(pre=pre, post=post, tx=tx)
