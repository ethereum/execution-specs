"""Test the ecpairing precompiled contract."""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .spec import PointG1, Spec, ref_spec_197

REFERENCE_SPEC_GIT_PATH = ref_spec_197.git_path
REFERENCE_SPEC_VERSION = ref_spec_197.version

pytestmark = [
    pytest.mark.valid_from("Byzantium"),
    pytest.mark.parametrize(
        "precompile_address", [Spec.ECPAIRING], ids=["ecpairing"]
    ),
]


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            b"",
            Spec.PAIRING_TRUE,
            id="empty",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.G2,
            Spec.PAIRING_TRUE,
            id="one_pair_g1_zero",
        ),
        pytest.param(
            Spec.G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            id="one_pair_g2_zero",
        ),
        pytest.param(
            Spec.G1 + Spec.G2 + Spec.NEG_G1 + Spec.G2,
            Spec.PAIRING_TRUE,
            id="two_pairs_negated_g1",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_empty_dataFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g1_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g2_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_1Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test valid inputs where the pairing check succeeds."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            Spec.G1 + Spec.G2,
            Spec.PAIRING_FALSE,
            id="one_pair",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_failFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test valid inputs where the pairing check fails."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            (Spec.G1 + Spec.G2)[:191],
            Spec.INVALID,
            id="bad_length_191",
        ),
        pytest.param(
            Spec.G1 + Spec.G2 + b"\x00",
            Spec.INVALID,
            id="bad_length_193",
        ),
        pytest.param(
            PointG1(1, 3) + Spec.G2,
            Spec.INVALID,
            id="g1_not_on_curve",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_bad_length_191Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_bad_length_193Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test invalid inputs to the ecpairing precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
