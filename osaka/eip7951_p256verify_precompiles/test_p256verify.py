"""
abstract: Tests [EIP-7951: Precompile for secp256r1 Curve Support](https://eips.ethereum.org/EIPS/eip-7951)
    Test cases for [EIP-7951: Precompile for secp256r1 Curve Support](https://eips.ethereum.org/EIPS/eip-7951)].
"""

import pytest

from ethereum_test_tools import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from .helpers import vectors_from_file
from .spec import H, R, S, Spec, X, Y, ref_spec_7951

REFERENCE_SPEC_GIT_PATH = ref_spec_7951.git_path
REFERENCE_SPEC_VERSION = ref_spec_7951.version

pytestmark = [
    pytest.mark.valid_from("Osaka"),
]


@pytest.mark.parametrize(
    "input_data,expected_output,vector_gas_value",
    vectors_from_file("secp256r1_test.json"),
    # Test vectors generated from Wycheproof's ECDSA secp256r1 SHA-256 test suite
    # Source: https://github.com/C2SP/wycheproof/blob/main/testvectors/ecdsa_secp256r1_sha256_test.json
)
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
@pytest.mark.eip_checklist("precompile/test/call_contexts/normal")
@pytest.mark.eip_checklist("precompile/test/inputs/valid")
def test_valid(state_test: StateTestFiller, pre: Alloc, post: dict, tx: Transaction):
    """Test P256Verify precompile."""
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(b"", id="zero_length_input"),
        pytest.param(
            b"\x00" + Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            id="input_too_long",
        ),
        pytest.param(
            (Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0)[:-1],
            id="input_too_short",
        ),
        pytest.param(
            H(0) + R(0) + S(0) + X(0) + Y(0),
            id="input_all_zeros",
        ),
        pytest.param(
            Spec.H0 + R(0) + Spec.S0 + Spec.X0 + Spec.Y0,
            id="r_eq_to_zero",
        ),
        pytest.param(
            Spec.H0 + R(Spec.N) + Spec.S0 + Spec.X0 + Spec.Y0,
            id="r_eq_to_n",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + S(0) + Spec.X0 + Spec.Y0,
            id="s_eq_to_zero",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + S(Spec.N) + Spec.X0 + Spec.Y0,
            id="s_eq_to_n",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + X(Spec.P) + Spec.Y0,
            id="x_eq_to_p",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Y(Spec.P),
            id="y_eq_to_p",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + X(0) + Y(0),
            id="point_on_infinity",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + X(Spec.X0.value + 1) + Spec.Y0,
            id="point_not_on_curve_x",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Y(Spec.Y0.value + 1),
            id="point_not_on_curve_y",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.Y0 + Spec.X0,
            id="x_and_y_reversed",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Y(Spec.P + 1),
            id="y_greater_than_p",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + X(Spec.P + 1) + Spec.Y0,
            id="x_greater_than_p",
        ),
        pytest.param(
            Spec.H0
            + R(0x813EF79CCEFA9A56F7BA805F0E478584FE5F0DD5F567BC09B5123CCBC9832365)
            + S(0x900E75AD233FCC908509DBFF5922647DB37C21F4AFD3203AE8DC4AE7794B0F87)
            + X(0xB838FF44E5BC177BF21189D0766082FC9D843226887FC9760371100B7EE20A6F)
            + Y(0xF0C9D75BFBA7B31A6BCA1974496EEB56DE357071955D83C4B1BADAA0B21832E9),
            id="valid_secp256k1_inputs",
        ),
        pytest.param(
            H(0x235060CAFE19A407880C272BC3E73600E3A12294F56143ED61929C2FF4525ABB)
            + R(0x182E5CBDF96ACCB859E8EEA1850DE5FF6E430A19D1D9A680ECD5946BBEA8A32B)
            + S(0x76DDFAE6797FA6777CAAB9FA10E75F52E70A4E6CEB117B3C5B2F445D850BD64C)
            + X(0x3828736CDFC4C8696008F71999260329AD8B12287846FEDCEDE3BA1205B12729)
            + Y(0x3E5141734E971A8D55015068D9B3666760F4608A49B11F92E500ACEA647978C7),
            id="wrong_endianness",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID_RETURN_VALUE], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
@pytest.mark.eip_checklist("precompile/test/inputs/all_zeros")
@pytest.mark.eip_checklist("precompile/test/inputs/invalid")
@pytest.mark.eip_checklist("precompile/test/inputs/invalid/crypto")
@pytest.mark.eip_checklist("precompile/test/inputs/invalid/corrupted")
@pytest.mark.eip_checklist("precompile/test/input_lengths/zero")
@pytest.mark.eip_checklist("precompile/test/input_lengths/static/correct")
@pytest.mark.eip_checklist("precompile/test/input_lengths/static/too_short")
@pytest.mark.eip_checklist("precompile/test/input_lengths/static/too_long")
def test_invalid(state_test: StateTestFiller, pre: Alloc, post: dict, tx: Transaction):
    """Negative tests for the P256VERIFY precompile."""
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "input_data,expected_output,precompile_gas_modifier,call_succeeds",
    [
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            Spec.SUCCESS_RETURN_VALUE,
            1,
            True,
            id="extra_gas",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            Spec.INVALID_RETURN_VALUE,
            -1,
            False,
            id="insufficient_gas",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            Spec.INVALID_RETURN_VALUE,
            -6900,
            False,
            id="zero_gas",
        ),
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            Spec.INVALID_RETURN_VALUE,
            -3450,
            False,
            id="3450_gas",
        ),
    ],
)
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
@pytest.mark.eip_checklist("precompile/test/gas_usage/constant/exact")
@pytest.mark.eip_checklist("precompile/test/gas_usage/constant/oog")
def test_gas(state_test: StateTestFiller, pre: Alloc, post: dict, tx: Transaction):
    """Test P256Verify precompile gas requirements."""
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "call_opcode",
    [
        Op.STATICCALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
    ],
)
@pytest.mark.parametrize(
    "input_data,expected_output",
    [
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            Spec.SUCCESS_RETURN_VALUE,
            id="valid_call",
        ),
    ],
)
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
@pytest.mark.eip_checklist("precompile/test/call_contexts/delegate")
@pytest.mark.eip_checklist("precompile/test/call_contexts/static")
@pytest.mark.eip_checklist("precompile/test/call_contexts/callcode")
def test_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test P256Verify precompile using different call types."""
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "input_data,call_contract_address,post",
    [
        pytest.param(
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            Spec.P256VERIFY,
            {},
            id="valid_entry_point",
        ),
    ],
)
@pytest.mark.eip_checklist("precompile/test/call_contexts/tx_entry")
def test_precompile_as_tx_entry_point(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test P256Verify precompile entry point."""
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "input_data,expected_output",
    [
        # Test case where computed x-coordinate exceeds curve order N
        # This tests the modular comparison: r' ≡ r (mod N)
        pytest.param(
            Spec.H0
            # R: A value that when used in ECDSA verification produces an x-coordinate > N
            + R(0x000000000000000000000000000000004319055358E8617B0C46353D039CDAAB)
            + S(0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC63254E)
            # X, Y: Public key coordinates that will produce x-coordinate > N during verification
            + X(0x0AD99500288D466940031D72A9F5445A4D43784640855BF0A69874D2DE5FE103)
            + Y(0xC5011E6EF2C42DCD50D5D3D29F99AE6EBA2C80C9244F4C5422F0979FF0C3BA5E),
            Spec.SUCCESS_RETURN_VALUE,
            id="modular_comparison_x_coordinate_exceeds_n",
        ),
        pytest.param(
            Spec.H0
            + R(Spec.N + 1)  # R = N + 1 ≡ 1 (mod N)
            + Spec.S0
            + Spec.X0
            + Spec.Y0,
            Spec.INVALID_RETURN_VALUE,  # Should fail because R = 1 is not a valid signature
            id="r_equals_n_plus_one",
        ),
        pytest.param(
            Spec.H0
            + R(Spec.N + 2)  # R = N + 2 ≡ 2 (mod N)
            + Spec.S0
            + Spec.X0
            + Spec.Y0,
            Spec.INVALID_RETURN_VALUE,  # Should fail because R = 2 is not a valid signature
            id="r_equals_n_plus_two",
        ),
    ],
)
@pytest.mark.parametrize("precompile_address", [Spec.P256VERIFY], ids=[""])
@pytest.mark.eip_checklist("precompile/test/inputs/valid")
@pytest.mark.eip_checklist("precompile/test/inputs/invalid/crypto")
def test_modular_comparison(state_test: StateTestFiller, pre: Alloc, post: dict, tx: Transaction):
    """
    Test the modular comparison condition for secp256r1 precompile.

    This tests that when the x-coordinate of R' exceeds the curve order N,
    the verification should use modular arithmetic:
    r' ≡ r (mod N) instead of direct equality r' == r.
    """
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
