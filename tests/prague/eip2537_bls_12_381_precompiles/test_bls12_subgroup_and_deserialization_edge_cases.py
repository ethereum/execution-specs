"""
Tests for EIP-2537 BLS12-381 Precompiles: Subgroup Checks and Field Deserialization Edge Cases.

Negative and boundary tests targeting:
1. Strict canonical field coordinate encoding (rejection of non-zero padding in top 16 bytes,
   rejection of coordinate values >= p including p, p+1, 2^381-1, 2^384-1).
2. Subgroup membership verification in BLS12_PAIRING (rejection of points on the curve
   whose order divides cofactors h1 or h2 and does not equal r).
3. Non-trivial small-order points (e.g. order 3 point (0, 2) on E(Fp)) in pairing and add.
4. Combinatorial multi-pair invalid permutations in BLS12_PAIRING.
"""

import pytest

from ethereum_test_tools import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .conftest import (
    G1_POINTS_NOT_IN_SUBGROUP,
    G2_POINTS_NOT_IN_SUBGROUP,
)
from .spec import PointG1, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
]

# Modulus values and boundary constants
P = Spec.P
TWO_POW_381_MINUS_1 = (1 << 381) - 1
TWO_POW_384_MINUS_1 = (1 << 384) - 1

# Order 3 point on E(Fp): x = 0, y^2 = 4 => y = 2
ORDER_3_POINT_G1 = PointG1(0, 2)
ORDER_3_POINT_G1_NEG = PointG1(0, P - 2)


def make_field_element(value: int, top_padding: bytes = b"\x00" * 16) -> bytes:
    """Constructs a 64-byte field element with customizable 16-byte padding and 48-byte value."""
    assert len(top_padding) == 16, "top padding must be exactly 16 bytes"
    val_bytes = value.to_bytes(48, byteorder="big")
    return top_padding + val_bytes


# ---------------------------------------------------------------------------
# Section 1: Strict Coordinate Deserialization & Modulus Overflow Tests
# ---------------------------------------------------------------------------


def generate_canonical_field_overflow_vectors():
    """Generate vectors where coordinates violate the 0 <= x < p canonical rule."""
    vectors = []

    # Non-canonical values for a 48-byte coordinate
    overflow_vals = [
        ("exact_p", P),
        ("p_plus_1", P + 1),
        ("p_plus_2_pow_128", P + (1 << 128)),
        ("max_381_bit", TWO_POW_381_MINUS_1),
        ("max_384_bit", TWO_POW_384_MINUS_1),
    ]

    # G1: Corrupt X coordinate
    for label, val in overflow_vals:
        corrupted_g1 = make_field_element(val) + bytes(Spec.G1)[64:]
        vectors.append(
            pytest.param(
                corrupted_g1 + Spec.INF_G2,
                id=f"g1_x_overflow_{label}",
            )
        )

    # G1: Corrupt Y coordinate
    for label, val in overflow_vals:
        corrupted_g1 = bytes(Spec.G1)[:64] + make_field_element(val)
        vectors.append(
            pytest.param(
                corrupted_g1 + Spec.INF_G2,
                id=f"g1_y_overflow_{label}",
            )
        )

    # G2: Corrupt X.c0 coordinate
    for label, val in overflow_vals:
        corrupted_g2 = (
            make_field_element(val)
            + bytes(Spec.G2)[64:128]
            + bytes(Spec.G2)[128:192]
            + bytes(Spec.G2)[192:256]
        )
        vectors.append(
            pytest.param(
                Spec.INF_G1 + corrupted_g2,
                id=f"g2_x_c0_overflow_{label}",
            )
        )

    # G2: Corrupt Y.c1 coordinate
    for label, val in overflow_vals:
        corrupted_g2 = (
            bytes(Spec.G2)[0:64]
            + bytes(Spec.G2)[64:128]
            + bytes(Spec.G2)[128:192]
            + make_field_element(val)
        )
        vectors.append(
            pytest.param(
                Spec.INF_G1 + corrupted_g2,
                id=f"g2_y_c1_overflow_{label}",
            )
        )

    # Padding violations (non-zero bytes in top 16 bytes)
    padding_corruptions = [
        ("byte0_0x80", b"\x80" + b"\x00" * 15),
        ("byte0_0x01", b"\x01" + b"\x00" * 15),
        ("byte15_0x01", b"\x00" * 15 + b"\x01"),
        ("byte15_0xff", b"\x00" * 15 + b"\xff"),
        ("all_0xff", b"\xff" * 16),
    ]

    for label, pad in padding_corruptions:
        corrupted_g1 = make_field_element(Spec.G1.x, top_padding=pad) + bytes(Spec.G1)[64:]
        vectors.append(
            pytest.param(
                corrupted_g1 + Spec.INF_G2,
                id=f"g1_x_top16_padding_{label}",
            )
        )

    return vectors


@pytest.mark.parametrize("precompile_address", [Spec.PAIRING], ids=["pairing"])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=["revert"])
@pytest.mark.parametrize(
    "input_data",
    generate_canonical_field_overflow_vectors(),
)
def test_pairing_field_canonical_encoding_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """
    Verify that BLS12_PAIRING strictly rejects coordinates violating canonical
    field encoding.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


# ---------------------------------------------------------------------------
# Section 2: Rigorous Subgroup Check Rejection in PAIRING
# ---------------------------------------------------------------------------


def generate_subgroup_rejection_vectors():
    """
    Generate test vectors with points on the curve but not in the r-torsion subgroup.
    EIP-2537 requires PAIRING precompile to fail if any point is outside G1 or G2.
    """
    vectors = [
        # Single pair with G1 point not in subgroup
        pytest.param(
            ORDER_3_POINT_G1 + Spec.G2,
            id="single_pair_order3_g1_with_valid_g2",
        ),
        pytest.param(
            ORDER_3_POINT_G1_NEG + Spec.G2,
            id="single_pair_order3_neg_g1_with_valid_g2",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Spec.G2,
            id="single_pair_p1_not_in_subgroup_with_valid_g2",
        ),
        # Single pair with G2 point not in subgroup
        pytest.param(
            Spec.G1 + Spec.P2_NOT_IN_SUBGROUP,
            id="single_pair_valid_g1_with_p2_not_in_subgroup",
        ),
        # Both points on curve but not in subgroup
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Spec.P2_NOT_IN_SUBGROUP,
            id="single_pair_both_not_in_subgroup",
        ),
        # 2-pair: Valid pair followed by G1 invalid subgroup
        pytest.param(
            Spec.G1 + Spec.G2 + Spec.P1_NOT_IN_SUBGROUP + Spec.G2,
            id="multi_pair_2nd_g1_not_in_subgroup",
        ),
        # 2-pair: Valid pair followed by G2 invalid subgroup
        pytest.param(
            Spec.G1 + Spec.G2 + Spec.G1 + Spec.P2_NOT_IN_SUBGROUP,
            id="multi_pair_2nd_g2_not_in_subgroup",
        ),
        # 2-pair: First G1 invalid subgroup followed by valid pair
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Spec.G2 + Spec.G1 + Spec.G2,
            id="multi_pair_1st_g1_not_in_subgroup",
        ),
        # 2-pair: First G2 invalid subgroup followed by valid pair
        pytest.param(
            Spec.G1 + Spec.P2_NOT_IN_SUBGROUP + Spec.G1 + Spec.G2,
            id="multi_pair_1st_g2_not_in_subgroup",
        ),
        # 3-pair: Middle pair has G1 point not in subgroup
        pytest.param(
            Spec.G1 + Spec.G2 + ORDER_3_POINT_G1 + Spec.G2 + (-Spec.G1) + Spec.G2,
            id="multi_pair_3pairs_middle_g1_order3",
        ),
    ]

    # Incorporate cached pseudo-random points not in subgroup from conftest
    for i, p1 in enumerate(G1_POINTS_NOT_IN_SUBGROUP):
        vectors.append(
            pytest.param(
                p1 + Spec.G2,
                id=f"rand_g1_not_in_subgroup_{i}_with_g2",
            )
        )
    for j, p2 in enumerate(G2_POINTS_NOT_IN_SUBGROUP):
        vectors.append(
            pytest.param(
                Spec.G1 + p2,
                id=f"rand_g2_not_in_subgroup_{j}_with_g1",
            )
        )

    return vectors


@pytest.mark.parametrize("precompile_address", [Spec.PAIRING], ids=["pairing"])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=["revert"])
@pytest.mark.parametrize(
    "input_data",
    generate_subgroup_rejection_vectors(),
)
def test_pairing_subgroup_check_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """Verify that BLS12_PAIRING strictly rejects points not belonging to the r-order subgroup."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


# ---------------------------------------------------------------------------
# Section 3: Point at Infinity & Subgroup Interaction in G1ADD
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("precompile_address", [Spec.G1ADD], ids=["g1add"])
@pytest.mark.parametrize(
    "input_data,expected_output",
    [
        # Adding order 3 point and its inverse results in the identity point (0, 0)
        # Note: G1ADD does NOT require subgroup checks, only on-curve validation.
        pytest.param(
            ORDER_3_POINT_G1 + ORDER_3_POINT_G1_NEG,
            Spec.INF_G1,
            id="order3_point_plus_negation_yields_infinity",
        ),
        # Adding order 3 point to infinity yields itself
        pytest.param(
            ORDER_3_POINT_G1 + Spec.INF_G1,
            ORDER_3_POINT_G1,
            id="order3_point_plus_inf_yields_itself",
        ),
    ],
)
def test_g1add_on_curve_not_in_subgroup_arithmetic(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """
    Verify that G1ADD correctly accepts valid on-curve points even if outside G1 subgroup,
    and accurately computes the group law on E(Fp).
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
