"""
Tests for EIP-2537 BLS12-381 Precompiles: Subgroup Checks and Field
Deserialization Edge Cases.

Negative and boundary tests targeting:
1. Strict canonical field coordinate encoding (rejection of non-zero padding
   in top 16 bytes, rejection of coordinate values >= p including p, p+1,
   2^381-1, 2^384-1).
2. Subgroup membership verification in BLS12_PAIRING (rejection of points on
   the curve whose order divides cofactors h1 or h2 and does not equal r).
3. Non-trivial small-order points (e.g. order 3 point (0, 2) on E(Fp)) in
   pairing and add.
4. Combinatorial multi-pair invalid permutations in BLS12_PAIRING.
5. Strict canonical field encoding and dirty top-16 byte padding in
   BLS12_G1MSM and BLS12_G2MSM.
6. Subgroup membership verification in BLS12_G1MSM and BLS12_G2MSM
   (including order-3 points under zero and non-zero scalars to prevent
   scalar-0 bypass).
7. Calldata length alignment and truncation edge cases for MSM precompiles.
8. Multi-Scalar Multiplication boundary scalars (s = r, r+1, 2^256-1) and
   non-trivial cancellations to identity.
"""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .conftest import (
    G1_POINTS_NOT_IN_SUBGROUP,
    G2_POINTS_NOT_IN_SUBGROUP,
)
from .spec import PointG1, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
]

# Modulus values and boundary constants
P = Spec.P
TWO_POW_381_MINUS_1 = (1 << 381) - 1
TWO_POW_384_MINUS_1 = (1 << 384) - 1

UINT256_MAX = (1 << 256) - 1
REM_MAX = UINT256_MAX % Spec.Q
SCALAR_CANCELLATION = Spec.Q - REM_MAX

# Order 3 point on E(Fp): x = 0, y^2 = 4 => y = 2
ORDER_3_POINT_G1 = PointG1(0, 2)
ORDER_3_POINT_G1_NEG = PointG1(0, P - 2)


def make_field_element(value: int, top_padding: bytes = b"\x00" * 16) -> bytes:
    """Construct a 64-byte field element with padding and 48-byte value."""
    assert len(top_padding) == 16, "top padding must be exactly 16 bytes"
    val_bytes = value.to_bytes(48, byteorder="big")
    return top_padding + val_bytes


# ---------------------------------------------------------------------------
# Section 1: Strict Coordinate Deserialization & Modulus Overflow Tests
# ---------------------------------------------------------------------------


def generate_canonical_field_overflow_vectors():
    """Generate vectors where coordinates violate 0 <= x < p rule."""
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
        corrupted_g1 = (
            make_field_element(Spec.G1.x, top_padding=pad)
            + bytes(Spec.G1)[64:]
        )
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
    Generate test vectors with points on curve but not in r-subgroup.
    EIP-2537 requires PAIRING to fail if any point is outside G1 or G2.
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
            Spec.G1
            + Spec.G2
            + ORDER_3_POINT_G1
            + Spec.G2
            + (-Spec.G1)
            + Spec.G2,
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
    """Verify that BLS12_PAIRING rejects points outside r-subgroup."""
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
        # Adding order 3 point and its inverse results in identity (0, 0)
        # Note: G1ADD does NOT require subgroup checks, only on-curve checks.
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
    Verify that G1ADD correctly accepts valid on-curve points even if
    outside G1 subgroup, and computes group law on E(Fp).
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


# ---------------------------------------------------------------------------
# Section 4: MSM Field Deserialization & Dirty Padding Rejection
# ---------------------------------------------------------------------------


def generate_msm_canonical_and_padding_rejection_vectors():
    """Generate invalid coordinate and padding test vectors for MSM."""
    vectors = []

    padding_corruptions = [
        ("byte0_0x80", b"\x80" + b"\x00" * 15),
        ("byte0_0x01", b"\x01" + b"\x00" * 15),
        ("byte15_0x01", b"\x00" * 15 + b"\x01"),
        ("byte15_0xff", b"\x00" * 15 + b"\xff"),
        ("all_0xff", b"\xff" * 16),
    ]

    overflow_vals = [
        ("exact_p", P),
        ("p_plus_1", P + 1),
        ("max_381_bit", TWO_POW_381_MINUS_1),
        ("max_384_bit", TWO_POW_384_MINUS_1),
    ]

    # G1MSM: Dirty top-16 byte padding in X coordinate
    for label, pad in padding_corruptions:
        corrupted_point = (
            make_field_element(Spec.G1.x, top_padding=pad)
            + bytes(Spec.G1)[64:]
        )
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                corrupted_point + Scalar(1),
                id=f"g1msm_x_top16_padding_{label}",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                Spec.G1
                + Scalar(1)
                + corrupted_point
                + Scalar(2)
                + Spec.G1
                + Scalar(3),
                id=f"g1msm_batch3_middle_x_padding_{label}",
            )
        )

    # G1MSM: Dirty top-16 byte padding in Y coordinate
    for label, pad in padding_corruptions:
        corrupted_point = bytes(Spec.G1)[:64] + make_field_element(
            Spec.G1.y, top_padding=pad
        )
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                corrupted_point + Scalar(1),
                id=f"g1msm_y_top16_padding_{label}",
            )
        )

    # G1MSM: Coordinate overflow (>= p) in single and multi-pair batches
    for label, val in overflow_vals:
        corrupted_point = make_field_element(val) + bytes(Spec.G1)[64:]
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                corrupted_point + Scalar(1),
                id=f"g1msm_x_overflow_{label}",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                Spec.G1
                + Scalar(1)
                + corrupted_point
                + Scalar(2)
                + Spec.G1
                + Scalar(3),
                id=f"g1msm_batch3_middle_x_overflow_{label}",
            )
        )

    # G2MSM: Dirty top-16 byte padding in X.c0 coordinate
    for label, pad in padding_corruptions:
        corrupted_g2 = (
            make_field_element(Spec.G2.x[0], top_padding=pad)
            + bytes(Spec.G2)[64:128]
            + bytes(Spec.G2)[128:192]
            + bytes(Spec.G2)[192:256]
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                corrupted_g2 + Scalar(1),
                id=f"g2msm_x_c0_top16_padding_{label}",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                Spec.G2 + Scalar(1) + corrupted_g2 + Scalar(2),
                id=f"g2msm_batch2_second_x_c0_padding_{label}",
            )
        )

    # G2MSM: Dirty top-16 byte padding in Y.c1 coordinate
    for label, pad in padding_corruptions:
        corrupted_g2 = (
            bytes(Spec.G2)[0:64]
            + bytes(Spec.G2)[64:128]
            + bytes(Spec.G2)[128:192]
            + make_field_element(Spec.G2.y[1], top_padding=pad)
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                corrupted_g2 + Scalar(1),
                id=f"g2msm_y_c1_top16_padding_{label}",
            )
        )

    # G2MSM: Coordinate overflow (>= p) in X.c0 and multi-pair batches
    for label, val in overflow_vals:
        corrupted_g2 = (
            make_field_element(val)
            + bytes(Spec.G2)[64:128]
            + bytes(Spec.G2)[128:192]
            + bytes(Spec.G2)[192:256]
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                corrupted_g2 + Scalar(1),
                id=f"g2msm_x_c0_overflow_{label}",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                Spec.G2 + Scalar(1) + corrupted_g2 + Scalar(2),
                id=f"g2msm_batch2_second_x_c0_overflow_{label}",
            )
        )

    return vectors


@pytest.mark.parametrize("precompile_gas_modifier", [100_000], ids=[""])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=["revert"])
@pytest.mark.parametrize(
    "precompile_address,input_data",
    generate_msm_canonical_and_padding_rejection_vectors(),
)
def test_msm_field_canonical_encoding_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """
    Verify that G1MSM and G2MSM strictly reject coordinates with
    non-canonical values or dirty padding.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


# ---------------------------------------------------------------------------
# Section 5: Rigorous Subgroup Check Rejection in G1MSM & G2MSM
# ---------------------------------------------------------------------------


def generate_msm_subgroup_rejection_vectors():
    """
    Generate test vectors with points on the curve but not in the prime
    subgroup for G1MSM/G2MSM under zero and non-zero scalars.
    """
    vectors = []

    # G1MSM with Order-3 small order point (0, 2)
    # Testing both scalar=1 and scalar=0 (verifies no bypass when s=0)
    vectors.extend(
        [
            pytest.param(
                Spec.G1MSM,
                ORDER_3_POINT_G1 + Scalar(1),
                id="g1msm_order3_scalar_1",
            ),
            pytest.param(
                Spec.G1MSM,
                ORDER_3_POINT_G1 + Scalar(0),
                id="g1msm_order3_scalar_0_rejection",
            ),
            pytest.param(
                Spec.G1MSM,
                ORDER_3_POINT_G1_NEG + Scalar(1),
                id="g1msm_order3_neg_scalar_1",
            ),
            pytest.param(
                Spec.G1MSM,
                ORDER_3_POINT_G1_NEG + Scalar(0),
                id="g1msm_order3_neg_scalar_0_rejection",
            ),
            # Multi-pair batch (k=3): Middle pair has order-3 point, scalar 0
            pytest.param(
                Spec.G1MSM,
                Spec.G1
                + Scalar(1)
                + ORDER_3_POINT_G1
                + Scalar(0)
                + Spec.G1
                + Scalar(2),
                id="g1msm_batch3_middle_order3_scalar_0",
            ),
            # Multi-pair batch (k=3): Middle pair has order-3 point, scalar 1
            pytest.param(
                Spec.G1MSM,
                Spec.G1
                + Scalar(1)
                + ORDER_3_POINT_G1
                + Scalar(1)
                + Spec.G1
                + Scalar(2),
                id="g1msm_batch3_middle_order3_scalar_1",
            ),
            # Multi-pair batch (k=2): First pair order-3, second valid
            pytest.param(
                Spec.G1MSM,
                ORDER_3_POINT_G1 + Scalar(1) + Spec.G1 + Scalar(2),
                id="g1msm_batch2_first_order3",
            ),
            # Multi-pair batch (k=2): First valid, second order-3
            pytest.param(
                Spec.G1MSM,
                Spec.G1 + Scalar(1) + ORDER_3_POINT_G1 + Scalar(2),
                id="g1msm_batch2_second_order3",
            ),
        ]
    )

    # G1MSM with cached pseudo-random points not in subgroup
    for i, p1 in enumerate(G1_POINTS_NOT_IN_SUBGROUP):
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                p1 + Scalar(0),
                id=f"g1msm_rand_not_in_subgroup_{i}_scalar_0",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                p1 + Scalar(1),
                id=f"g1msm_rand_not_in_subgroup_{i}_scalar_1",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G1MSM,
                Spec.G1 + Scalar(1) + p1 + Scalar(2),
                id=f"g1msm_batch2_second_rand_not_in_subgroup_{i}",
            )
        )

    # G2MSM with cached pseudo-random points not in subgroup
    for j, p2 in enumerate(G2_POINTS_NOT_IN_SUBGROUP):
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                p2 + Scalar(0),
                id=f"g2msm_rand_not_in_subgroup_{j}_scalar_0",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                p2 + Scalar(1),
                id=f"g2msm_rand_not_in_subgroup_{j}_scalar_1",
            )
        )
        vectors.append(
            pytest.param(
                Spec.G2MSM,
                Spec.G2 + Scalar(1) + p2 + Scalar(2),
                id=f"g2msm_batch2_second_rand_not_in_subgroup_{j}",
            )
        )

    return vectors


@pytest.mark.parametrize("precompile_gas_modifier", [100_000], ids=[""])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=["revert"])
@pytest.mark.parametrize(
    "precompile_address,input_data",
    generate_msm_subgroup_rejection_vectors(),
)
def test_msm_subgroup_check_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """
    Verify that G1MSM and G2MSM strictly reject points not in the
    prime-order subgroup.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


# ---------------------------------------------------------------------------
# Section 6: MSM Calldata Alignment & Truncation Edge Cases
# ---------------------------------------------------------------------------


def generate_msm_unaligned_calldata_vectors():
    """Generate unaligned and truncated calldata inputs for G1MSM and G2MSM."""
    vectors = [
        # G1MSM: Valid pair is 160 bytes
        pytest.param(Spec.G1MSM, bytes([0]) * 1, id="g1msm_calldata_1_byte"),
        pytest.param(
            Spec.G1MSM, bytes([0]) * 159, id="g1msm_calldata_159_bytes"
        ),
        pytest.param(
            Spec.G1MSM,
            (Spec.G1 + Scalar(1)) + bytes([0]),
            id="g1msm_calldata_161_bytes",
        ),
        pytest.param(
            Spec.G1MSM,
            (Spec.G1 + Scalar(1)) * 2 + bytes([0]),
            id="g1msm_calldata_321_bytes",
        ),
        # G2MSM: Valid pair is 288 bytes
        pytest.param(Spec.G2MSM, bytes([0]) * 1, id="g2msm_calldata_1_byte"),
        pytest.param(
            Spec.G2MSM, bytes([0]) * 287, id="g2msm_calldata_287_bytes"
        ),
        pytest.param(
            Spec.G2MSM,
            (Spec.G2 + Scalar(1)) + bytes([0]),
            id="g2msm_calldata_289_bytes",
        ),
        pytest.param(
            Spec.G2MSM,
            (Spec.G2 + Scalar(1)) * 2 + bytes([0]),
            id="g2msm_calldata_577_bytes",
        ),
    ]
    return vectors


@pytest.mark.parametrize("precompile_gas_modifier", [100_000], ids=[""])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=["revert"])
@pytest.mark.parametrize(
    "precompile_address,input_data",
    generate_msm_unaligned_calldata_vectors(),
)
def test_msm_unaligned_calldata_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """
    Verify that G1MSM and G2MSM strictly reject input whose length is
    not a multiple of pair size.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


# ---------------------------------------------------------------------------
# Section 7: MSM Scalar Modulo Equivalence & Non-trivial Cancellations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "precompile_address,input_data,expected_output",
    [
        # G1MSM: Scalar s = Q (group order) evaluates to point at infinity
        pytest.param(
            Spec.G1MSM,
            Spec.G1 + Scalar(Spec.Q),
            Spec.INF_G1,
            id="g1msm_scalar_equals_q_yields_infinity",
        ),
        # G1MSM: Scalar s = Q + 1 evaluates to G1 (s equiv 1 mod Q)
        pytest.param(
            Spec.G1MSM,
            Spec.G1 + Scalar(Spec.Q + 1),
            Spec.G1,
            id="g1msm_scalar_q_plus_1_yields_g1",
        ),
        # G1MSM: Linear cancellation: s1 = 1, s2 = Q - 1 => s1 + s2 = Q => INF
        pytest.param(
            Spec.G1MSM,
            Spec.G1 + Scalar(1) + Spec.G1 + Scalar(Spec.Q - 1),
            Spec.INF_G1,
            id="g1msm_scalars_sum_to_q_cancellation",
        ),
        # G1MSM: Scalar 2^256 - 1 cancelled with (Q - rem)
        pytest.param(
            Spec.G1MSM,
            Spec.G1
            + Scalar(UINT256_MAX)
            + Spec.G1
            + Scalar(SCALAR_CANCELLATION),
            Spec.INF_G1,
            id="g1msm_uint256_max_cancellation_yields_infinity",
        ),
        # G1MSM: Cancellation with opposite point: 42*P + 42*(-P) = INF
        pytest.param(
            Spec.G1MSM,
            Spec.G1 + Scalar(42) + (-Spec.G1) + Scalar(42),
            Spec.INF_G1,
            id="g1msm_opposite_point_cancellation",
        ),
        # G2MSM: Scalar s = Q evaluates to point at infinity
        pytest.param(
            Spec.G2MSM,
            Spec.G2 + Scalar(Spec.Q),
            Spec.INF_G2,
            id="g2msm_scalar_equals_q_yields_infinity",
        ),
        # G2MSM: Scalar s = Q + 1 evaluates to G2 (s equiv 1 mod Q)
        pytest.param(
            Spec.G2MSM,
            Spec.G2 + Scalar(Spec.Q + 1),
            Spec.G2,
            id="g2msm_scalar_q_plus_1_yields_g2",
        ),
        # G2MSM: Linear cancellation: s1 = 1, s2 = Q - 1 => INF
        pytest.param(
            Spec.G2MSM,
            Spec.G2 + Scalar(1) + Spec.G2 + Scalar(Spec.Q - 1),
            Spec.INF_G2,
            id="g2msm_scalars_sum_to_q_cancellation",
        ),
        # G2MSM: Scalar 2^256 - 1 cancelled with (Q - rem)
        pytest.param(
            Spec.G2MSM,
            Spec.G2
            + Scalar(UINT256_MAX)
            + Spec.G2
            + Scalar(SCALAR_CANCELLATION),
            Spec.INF_G2,
            id="g2msm_uint256_max_cancellation_yields_infinity",
        ),
        # G2MSM: Cancellation with opposite point: 42*P + 42*(-P) = INF
        pytest.param(
            Spec.G2MSM,
            Spec.G2 + Scalar(42) + (-Spec.G2) + Scalar(42),
            Spec.INF_G2,
            id="g2msm_opposite_point_cancellation",
        ),
    ],
)
def test_msm_scalar_modulo_and_cancellation(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: dict,
) -> None:
    """
    Verify that G1MSM and G2MSM correctly reduce scalars modulo r and
    compute cancellations to infinity.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
