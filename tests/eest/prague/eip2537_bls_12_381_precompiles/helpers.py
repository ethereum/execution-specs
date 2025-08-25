"""Helper functions for the EIP-2537 BLS12-381 precompiles tests."""

import hashlib
import os
from typing import Annotated, Any, List, Optional

import pytest
from joblib import Memory
from py_ecc.bls12_381 import FQ, FQ2, add, field_modulus, multiply
from pydantic import BaseModel, BeforeValidator, ConfigDict, RootModel, TypeAdapter
from pydantic.alias_generators import to_pascal

from .spec import FP, FP2, PointG1, PointG2, Spec


def current_python_script_directory(*args: str) -> str:
    """Get the current Python script directory, optionally appending additional path components."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)


class Vector(BaseModel):
    """Test vector for the BLS12-381 precompiles."""

    input: Annotated[bytes, BeforeValidator(bytes.fromhex)]
    expected: Annotated[bytes, BeforeValidator(bytes.fromhex)]
    gas: int
    name: str

    model_config = ConfigDict(alias_generator=to_pascal)

    def to_pytest_param(self):
        """Convert the test vector to a tuple that can be used as a parameter in a pytest test."""
        return pytest.param(self.input, self.expected, self.gas, id=self.name)


class FailVector(BaseModel):
    """Test vector for the BLS12-381 precompiles."""

    input: Annotated[bytes, BeforeValidator(bytes.fromhex)]
    expected_error: str
    name: str

    model_config = ConfigDict(alias_generator=to_pascal)

    def to_pytest_param(self):
        """Convert the test vector to a tuple that can be used as a parameter in a pytest test."""
        return pytest.param(self.input, id=self.name)


class VectorList(RootModel):
    """List of test vectors for the BLS12-381 precompiles."""

    root: List[Vector | FailVector]


VectorListAdapter = TypeAdapter(VectorList)


def vectors_from_file(filename: str) -> List:
    """Load test vectors from a file."""
    with open(
        current_python_script_directory(
            "vectors",
            filename,
        ),
        "rb",
    ) as f:
        return [v.to_pytest_param() for v in VectorListAdapter.validate_json(f.read()).root]


def add_points_g1(point_a: PointG1, point_b: PointG1) -> PointG1:
    """
    Add two points in G1 using standard formulas.
    For points P = (x, y) and Q = (u, v), compute R = P + Q.
    """
    if point_a.x == 0 and point_a.y == 0:
        return point_b
    if point_b.x == 0 and point_b.y == 0:
        return point_a
    py_ecc_point_a = (FQ(point_a.x), FQ(point_a.y))
    py_ecc_point_b = (FQ(point_b.x), FQ(point_b.y))
    result = add(py_ecc_point_a, py_ecc_point_b)
    if result is None:
        return Spec.INF_G1
    return PointG1(int(result[0]), int(result[1]))


def add_points_g2(point_a: PointG2, point_b: PointG2) -> PointG2:
    """
    Add two points in G2 using standard formulas.
    For points P = ((x_0, x_1), (y_0, y_1)) and Q = ((u_0, u_1), (v_0, v_1)), compute R = P + Q.
    """
    if point_a.x == (0, 0) and point_a.y == (0, 0):
        return point_b
    if point_b.x == (0, 0) and point_b.y == (0, 0):
        return point_a
    py_ecc_point_a = (FQ2(point_a.x), FQ2(point_a.y))
    py_ecc_point_b = (FQ2(point_b.x), FQ2(point_b.y))
    result = add(py_ecc_point_a, py_ecc_point_b)
    if result is None:
        return Spec.INF_G2
    new_x = (int(result[0].coeffs[0]), int(result[0].coeffs[1]))
    new_y = (int(result[1].coeffs[0]), int(result[1].coeffs[1]))
    return PointG2(new_x, new_y)


class BLSPointGenerator:
    """
    Generator for points on the BLS12-381 curve with various properties.

    Provides methods to generate points with specific properties:
        - on the standard curve
        - in the correct r-order subgroup or not
        - on the curve or not
        - on an isomorphic curve (not standard curve) but in the correct r-order subgroup

    Additional resource that helped the class implementation:
        https://hackmd.io/@benjaminion/bls12-381
    """

    # Constants for G1 curve equations
    # The b-coefficient in the elliptic curve equation y^2 = x^3 + b

    # Standard BLS12-381 G1 curve uses b=4
    # This is a known parameter of the BLS12-381 curve specification
    STANDARD_B_G1 = Spec.B_COEFFICIENT

    # Isomorphic G1 curve uses b=24 (can be any b value for an isomorphic curve)
    ISOMORPHIC_B_G1 = 24  # Isomorphic curve: y^2 = x^3 + 24

    # Constants for G2 curve equations
    # Standard BLS12-381 G2 curve uses b=(4,4)
    STANDARD_B_G2 = (Spec.B_COEFFICIENT, Spec.B_COEFFICIENT)

    # Isomorphic G2 curve uses b=(24,24)
    ISOMORPHIC_B_G2 = (24, 24)

    # Cofactors for G1 and G2
    # These are known constants for the BLS12-381 curve.

    # G1 cofactor h₁: (x-1)²/3 where x is the BLS parameter
    G1_COFACTOR = 0x396C8C005555E1568C00AAAB0000AAAB

    # G2 cofactor h₂: (x⁸ - 4x⁷ + 5x⁶ - 4x⁴ + 6x³ - 4x² - 4x + 13)/9
    G2_COFACTOR = 0x5D543A95414E7F1091D50792876A202CD91DE4547085ABAA68A205B2E5A7DDFA628F1CB4D9E82EF21537E293A6691AE1616EC6E786F0C70CF1C38E31C7238E5  # noqa: E501

    # Memory cache for expensive functions
    memory = Memory(location=".cache", verbose=0)

    @staticmethod
    def is_on_curve_g1(x: int, y: int) -> bool:
        """Check if point (x,y) is on the BLS12-381 G1 curve."""
        x_fq = FQ(x)
        y_fq = FQ(y)
        return y_fq * y_fq == x_fq * x_fq * x_fq + FQ(Spec.B_COEFFICIENT)

    @staticmethod
    def is_on_curve_g2(x: tuple, y: tuple) -> bool:
        """Check if point (x,y) is on the BLS12-381 G2 curve."""
        x_fq2 = FQ2(x)
        y_fq2 = FQ2(y)
        return y_fq2 * y_fq2 == x_fq2 * x_fq2 * x_fq2 + FQ2(
            (Spec.B_COEFFICIENT, Spec.B_COEFFICIENT)
        )

    @staticmethod
    def check_in_g1_subgroup(point: PointG1) -> bool:
        """Check if a G1 point is in the correct r-order subgroup."""
        try:
            # Check q*P = O where q is the subgroup order
            x = FQ(point.x)
            y = FQ(point.y)
            result = multiply((x, y), Spec.Q)
            # If point is in the subgroup, q*P should be infinity
            return result is None
        except Exception:
            return False

    @staticmethod
    def check_in_g2_subgroup(point: PointG2) -> bool:
        """Check if a G2 point is in the correct r-order subgroup."""
        try:
            # Check q*P = O where q is the subgroup order
            x = FQ2(point.x)
            y = FQ2(point.y)
            result = multiply((x, y), Spec.Q)
            # If point is in the subgroup, q*P should be infinity
            return result is None
        except Exception:
            return False

    @staticmethod
    def sqrt_fq(a: FQ) -> Optional[FQ]:
        """
        Compute smallest square root of FQ element (if it exists). Used when finding valid
        y-coordinates for a given x-coordinate on the G1 curve.
        """
        assert field_modulus % 4 == 3, "This sqrt method requires p % 4 == 3"
        candidate = a ** ((field_modulus + 1) // 4)
        if candidate * candidate == a:
            if int(candidate) > field_modulus // 2:
                return -candidate
            return candidate
        return None

    @staticmethod
    def sqrt_fq2(a: FQ2) -> Optional[FQ2]:
        """
        Compute square root of FQ2 element (if it exists). Used when finding valid
        y-coordinates for a given x-coordinate on the G2 curve.
        """
        if a == FQ2([0, 0]):
            return FQ2([0, 0])
        candidate = a ** ((field_modulus**2 + 7) // 16)
        if candidate * candidate == a:
            int_c0, int_c1 = int(candidate.coeffs[0]), int(candidate.coeffs[1])
            if int_c1 > 0 or (int_c1 == 0 and int_c0 > field_modulus // 2):
                return -candidate
            return candidate
        return None

    @classmethod
    def multiply_by_cofactor(cls, point: Any, is_g2: bool = False):
        """
        Multiply a point by the cofactor to ensure it's in the correct r-order subgroup.
        Used for creating points in the correct r-order subgroup when using isomorphic curves.
        """
        cofactor = cls.G2_COFACTOR if is_g2 else cls.G1_COFACTOR
        try:
            if is_g2:
                # For G2, the point is given in this form: ((x0, x1), (y0, y1))
                x = FQ2([point[0][0], point[0][1]])
                y = FQ2([point[1][0], point[1][1]])
                base_point = (x, y)
                result = multiply(base_point, cofactor)
                return (
                    (int(result[0].coeffs[0]), int(result[0].coeffs[1])),  # type: ignore
                    (int(result[1].coeffs[0]), int(result[1].coeffs[1])),  # type: ignore
                )
            else:
                # For G1, the point is given as (x, y).
                x = FQ(point[0])  # type: ignore
                y = FQ(point[1])  # type: ignore
                base_point = (x, y)
                result = multiply(base_point, cofactor)
                return (int(result[0]), int(result[1]))  # type: ignore
        except Exception as e:
            raise ValueError("Failed to multiply point by cofactor") from e

    @classmethod
    @memory.cache
    def find_g1_point_by_x(cls, x_value: int, in_subgroup: bool, on_curve: bool = True) -> PointG1:
        """
        Find a G1 point with x-coordinate at or near the given value,
        with the specified subgroup membership and curve membership.
        """
        max_offset = 5000
        isomorphic_b = cls.ISOMORPHIC_B_G1

        for offset in range(max_offset + 1):
            for direction in [1, -1]:
                if offset == 0 and direction == -1:
                    continue

                try_x = (x_value + direction * offset) % Spec.P

                try:
                    x = FQ(try_x)

                    # Calculate y² = x³ + b (standard curve or isomorphic curve)
                    b_value = cls.STANDARD_B_G1 if on_curve else isomorphic_b
                    y_squared = x**3 + FQ(b_value)

                    # Try to find y such that y² = x³ + b
                    y = cls.sqrt_fq(y_squared)
                    if y is None:
                        continue  # No valid y exists for this x

                    # Create the initial points on either curve
                    raw_point = (int(x), int(y))
                    raw_point2 = (int(x), Spec.P - int(y))

                    # For isomorphic curve points in subgroup, apply cofactor multiplication
                    if not on_curve and in_subgroup:
                        try:
                            subgroup_point = cls.multiply_by_cofactor(raw_point, is_g2=False)
                            point1 = PointG1(subgroup_point[0], subgroup_point[1])
                        except ValueError:
                            continue  # Skip if fails
                    else:
                        point1 = PointG1(int(x), int(y))
                    if not on_curve and in_subgroup:
                        try:
                            subgroup_point2 = cls.multiply_by_cofactor(raw_point2, is_g2=False)
                            point2 = PointG1(subgroup_point2[0], subgroup_point2[1])
                        except ValueError:
                            continue  # Skip if fails
                    else:
                        point2 = PointG1(int(x), Spec.P - int(y))

                    # Verify points have the required properties
                    point1_on_curve = cls.is_on_curve_g1(point1.x, point1.y)
                    point2_on_curve = cls.is_on_curve_g1(point2.x, point2.y)
                    point1_in_subgroup = cls.check_in_g1_subgroup(point1)
                    point2_in_subgroup = cls.check_in_g1_subgroup(point2)

                    # Return required point if found based on properties
                    if on_curve == point1_on_curve and in_subgroup == point1_in_subgroup:
                        return point1
                    if on_curve == point2_on_curve and in_subgroup == point2_in_subgroup:
                        return point2

                except Exception:
                    continue

        raise ValueError(
            (
                f"Failed to find G1 point by x={x_value},",
                "in_subgroup={in_subgroup},",
                "on_curve={on_curve}",
            )
        )

    @classmethod
    @memory.cache
    def find_g2_point_by_x(
        cls, x_value: tuple, in_subgroup: bool, on_curve: bool = True
    ) -> PointG2:
        """
        Find a G2 point with x-coordinate at or near the given value,
        with the specified subgroup membership and curve membership.
        """
        max_offset = 5000
        isomorphic_b = cls.ISOMORPHIC_B_G2

        for offset in range(max_offset + 1):
            for direction in [1, -1]:
                if offset == 0 and direction == -1:
                    continue

                try_x0 = (x_value[0] + direction * offset) % Spec.P
                try_x = (try_x0, x_value[1])  # Keep x1 the same

                try:
                    x = FQ2(try_x)

                    # Calculate y² = x³ + b (standard curve or isomorphic curve)
                    b_value = cls.STANDARD_B_G2 if on_curve else isomorphic_b
                    y_squared = x**3 + FQ2(b_value)

                    # Try to find y such that y² = x³ + b
                    y = cls.sqrt_fq2(y_squared)
                    if y is None:
                        continue  # No valid y exists for this x

                    # Create the initial points on either curve
                    raw_point = (
                        (int(x.coeffs[0]), int(x.coeffs[1])),
                        (int(y.coeffs[0]), int(y.coeffs[1])),
                    )
                    raw_point2 = (
                        (int(x.coeffs[0]), int(x.coeffs[1])),
                        (Spec.P - int(y.coeffs[0]), Spec.P - int(y.coeffs[1])),
                    )

                    # For isomorphic curve points in subgroup, apply cofactor multiplication
                    if not on_curve and in_subgroup:
                        try:
                            subgroup_point = cls.multiply_by_cofactor(raw_point, is_g2=True)
                            point1 = PointG2(subgroup_point[0], subgroup_point[1])
                        except ValueError:
                            continue  # Skip if fails
                    else:
                        point1 = PointG2(
                            (int(x.coeffs[0]), int(x.coeffs[1])),
                            (int(y.coeffs[0]), int(y.coeffs[1])),
                        )
                    if not on_curve and in_subgroup:
                        try:
                            subgroup_point2 = cls.multiply_by_cofactor(raw_point2, is_g2=True)
                            point2 = PointG2(subgroup_point2[0], subgroup_point2[1])
                        except ValueError:
                            continue  # Skip if fails
                    else:
                        point2 = PointG2(
                            (int(x.coeffs[0]), int(x.coeffs[1])),
                            (Spec.P - int(y.coeffs[0]), Spec.P - int(y.coeffs[1])),
                        )

                    # Verify points have the required properties
                    point1_on_curve = cls.is_on_curve_g2(point1.x, point1.y)
                    point2_on_curve = cls.is_on_curve_g2(point2.x, point2.y)
                    point1_in_subgroup = cls.check_in_g2_subgroup(point1)
                    point2_in_subgroup = cls.check_in_g2_subgroup(point2)

                    # Return required point if found based on properties
                    if on_curve == point1_on_curve and in_subgroup == point1_in_subgroup:
                        return point1
                    if on_curve == point2_on_curve and in_subgroup == point2_in_subgroup:
                        return point2

                except Exception:
                    continue

        raise ValueError(
            (
                f"Failed to find G2 point by x={x_value},",
                "in_subgroup={in_subgroup},",
                "on_curve={on_curve}",
            )
        )

    # G1 points by x coordinate (near or on the x value)
    @classmethod
    def generate_g1_point_in_subgroup_by_x(cls, x_value: int) -> PointG1:
        """G1 point that is in the r-order subgroup with x-coordinate by/on the given value."""
        return cls.find_g1_point_by_x(x_value, in_subgroup=True, on_curve=True)

    @classmethod
    def generate_g1_point_not_in_subgroup_by_x(cls, x_value: int) -> PointG1:
        """G1 point that is NOT in the r-order subgroup with x-coordinate by/on the given value."""
        return cls.find_g1_point_by_x(x_value, in_subgroup=False, on_curve=True)

    @classmethod
    def generate_g1_point_not_on_curve_by_x(cls, x_value: int) -> PointG1:
        """G1 point that is NOT on the curve with x-coordinate by/on the given value."""
        return cls.find_g1_point_by_x(x_value, in_subgroup=False, on_curve=False)

    @classmethod
    def generate_g1_point_on_isomorphic_curve_by_x(cls, x_value: int) -> PointG1:
        """
        G1 point that is on an isomorphic curve (not standard curve)
        but in the r-order subgroup with x-coordinate by/on the given value.

        Uses cofactor multiplication to ensure the point is in the correct subgroup.
        """
        return cls.find_g1_point_by_x(x_value, in_subgroup=True, on_curve=False)

    # G1 random points required to be generated with a seed
    @classmethod
    def generate_random_g1_point_in_subgroup(cls, seed: int) -> PointG1:
        """Generate a random G1 point that is in the r-order subgroup."""
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"in_subgroup").digest()
        x_value = int.from_bytes(hash_output, "big") % Spec.P
        return cls.generate_g1_point_in_subgroup_by_x(x_value)

    @classmethod
    def generate_random_g1_point_not_in_subgroup(cls, seed: int) -> PointG1:
        """Generate a random G1 point that is NOT in the r-order subgroup."""
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"not_in_subgroup").digest()
        x_value = int.from_bytes(hash_output, "big") % Spec.P
        return cls.generate_g1_point_not_in_subgroup_by_x(x_value)

    @classmethod
    def generate_random_g1_point_not_on_curve(cls, seed: int) -> PointG1:
        """Generate a random G1 point that is NOT on the curve."""
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"not_on_curve").digest()
        x_value = int.from_bytes(hash_output, "big") % Spec.P
        return cls.generate_g1_point_not_on_curve_by_x(x_value)

    @classmethod
    def generate_random_g1_point_on_isomorphic_curve(cls, seed: int) -> PointG1:
        """
        Generate a random G1 point that is on an isomorphic curve (not standard curve)
        but in the r-order subgroup.

        Uses cofactor multiplication to ensure the point is in the correct subgroup.
        """
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"on_isomorphic_curve").digest()
        x_value = int.from_bytes(hash_output, "big") % Spec.P
        return cls.generate_g1_point_on_isomorphic_curve_by_x(x_value)

    # G2 point generators - by x coordinate (near or on the x value)
    @classmethod
    def generate_g2_point_in_subgroup_by_x(cls, x_value: tuple) -> PointG2:
        """G2 point that is in the r-order subgroup with x-coordinate by/on the given value."""
        return cls.find_g2_point_by_x(x_value, in_subgroup=True, on_curve=True)

    @classmethod
    def generate_g2_point_not_in_subgroup_by_x(cls, x_value: tuple) -> PointG2:
        """G2 point that is NOT in the r-order subgroup with x-coordinate by/on the given value."""
        return cls.find_g2_point_by_x(x_value, in_subgroup=False, on_curve=True)

    @classmethod
    def generate_g2_point_not_on_curve_by_x(cls, x_value: tuple) -> PointG2:
        """G2 point that is NOT on the curve with x-coordinate by/on the given value."""
        return cls.find_g2_point_by_x(x_value, in_subgroup=False, on_curve=False)

    @classmethod
    def generate_g2_point_on_isomorphic_curve_by_x(cls, x_value: tuple) -> PointG2:
        """
        G2 point that is on an isomorphic curve (not standard curve)
        but in the r-order subgroup with x-coordinate near the given value.

        Uses cofactor multiplication to ensure the point is in the correct subgroup.
        """
        return cls.find_g2_point_by_x(x_value, in_subgroup=True, on_curve=False)

    # G2 random points required to be generated with a seed
    @classmethod
    def generate_random_g2_point_in_subgroup(cls, seed: int) -> PointG2:
        """Generate a random G2 point that is in the r-order subgroup."""
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"g2_in_subgroup").digest()
        hash_len = len(hash_output)
        half_len = hash_len // 2
        x0 = int.from_bytes(hash_output[:half_len], "big") % Spec.P
        x1 = int.from_bytes(hash_output[half_len:], "big") % Spec.P
        return cls.generate_g2_point_in_subgroup_by_x((x0, x1))

    @classmethod
    def generate_random_g2_point_not_in_subgroup(cls, seed: int) -> PointG2:
        """Generate a random G2 point that is NOT in the r-order subgroup."""
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"g2_not_in_subgroup").digest()
        hash_len = len(hash_output)
        half_len = hash_len // 2
        x0 = int.from_bytes(hash_output[:half_len], "big") % Spec.P
        x1 = int.from_bytes(hash_output[half_len:], "big") % Spec.P
        return cls.generate_g2_point_not_in_subgroup_by_x((x0, x1))

    @classmethod
    def generate_random_g2_point_not_on_curve(cls, seed: int) -> PointG2:
        """Generate a random G2 point that is NOT on the curve."""
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"g2_not_on_curve").digest()
        hash_len = len(hash_output)
        half_len = hash_len // 2
        x0 = int.from_bytes(hash_output[:half_len], "big") % Spec.P
        x1 = int.from_bytes(hash_output[half_len:], "big") % Spec.P
        return cls.generate_g2_point_not_on_curve_by_x((x0, x1))

    @classmethod
    def generate_random_g2_point_on_isomorphic_curve(cls, seed: int) -> PointG2:
        """
        Generate a random G2 point that is on an isomorphic curve (not standard curve)
        but in the r-order subgroup.
        Uses cofactor multiplication to ensure the point is in the correct subgroup.
        """
        seed_bytes = seed.to_bytes(32, "big")
        hash_output = hashlib.sha384(seed_bytes + b"g2_on_isomorphic_curve").digest()
        hash_len = len(hash_output)
        half_len = hash_len // 2
        x0 = int.from_bytes(hash_output[:half_len], "big") % Spec.P
        x1 = int.from_bytes(hash_output[half_len:], "big") % Spec.P
        return cls.generate_g2_point_on_isomorphic_curve_by_x((x0, x1))

    # G1 map to curve 11-isogeny kernel point generator
    @classmethod
    def generate_g1_map_isogeny_kernel_points(cls) -> List[FP]:
        """
        Return precomputed kernel points for the BLS12-381 G1 map to curve function. These map to
        the G1 identity point `Spec.INF_G1`. They are generated using sage math externally with the
        following script as its significantly faster than using `py_ecc` (200-1000x faster).

        For reference we can imagine the map to curve function as a simple 2 step process, where an
        input t value is mapped to a point on the auxiliary curve via a SWU map, and then that
        point is mapped to the BLS curve via an 11-isogeny. For reference:
        - https://eips.ethereum.org/assets/eip-2537/field_to_curve

        Note we cannot use sage math directly within EEST as it is not a pure python library and
        requires an external dependency to be installed on the system machine.

        Thanks to @petertdavies (Peter Miller) for the sage math script to generate these points:
        ```sage
        q = 0x1A0111EA397FE69A4B1BA7B6434BACD764774B84F38512BF6730D2A0F6B0F6241EABFFFEB153FFFFB9FEFFFFFFFFAAAB
        Fq = GF(q)
        E1 = EllipticCurve(Fq, (0, 4)) # BLS12-381 curve
        ISO_11_A = Fq(0x144698A3B8E9433D693A02C96D4982B0EA985383EE66A8D8E8981AEFD881AC98936F8DA0E0F97F5CF428082D584C1D)
        ISO_11_B = Fq(0x12E2908D11688030018B12E8753EEE3B2016C1F0F24F4070A0B9C14FCEF35EF55A23215A316CEAA5D1CC48E98E172BE0)
        ISO_11_Z = Fq(11)
        Ei = EllipticCurve(Fq, (ISO_11_A, ISO_11_B))
        iso = EllipticCurveIsogeny(E=E1, kernel=None, codomain=Ei, degree=11).dual()
        for (x, _) in iso.kernel_polynomial().roots():
            discriminant = 1 - 4 / (ISO_11_A / ISO_11_B * x + 1)
            if not discriminant.is_square():
                continue
            for sign in [1, -1]:
                zt2 = (-1 + sign * discriminant.sqrt()) / 2
                t2 = zt2 / ISO_11_Z
                if t2.is_square():
                    t = t2.sqrt()
                    assert x == -ISO_11_B / ISO_11_A * (1 + 1 / (ISO_11_Z**2 * t**4 + ISO_11_Z * t**2))
                    print(t)
        ```

        To reproduce, add the script contents to a file called `points.sage`, then run `sage points.sage`!

        Please see the sage math installation guide to replicate:
            - https://doc.sagemath.org/html/en/installation/index.html

        As G1 uses an 11-degree isogeny, its kernel contains exactly 11 points on the auxiliary
        curve that maps to the point at infinity on the BLS curve. This includes the point at
        infinity (doesn't concern us as the initial SWU map can never output infinity from any int
        t) and 10 other unique kernel points.

        These 10 other kernel points correspond to 5 x-coords on the curve (since each x-coord
        yields two points with y and -y). However, not all of these kernel points can be reached by
        the SWU map, which is why we only have 4 unique t values below.

        The kernel polynomial has 5 roots (x-coords), and each root can potentially yield two
        t values that map to kernel points via the SWU function. Analysis shows that only 2 of
        these roots yield valid t values because the other 3 roots fail either the discriminant
        square check or the t^2 square check in the SWU inverse calculation. From these 2 valid
        roots, we get the 4 unique t values listed below.

        The roots and their properties are as follows:
        - Root 1 (x=3447232547282837364692125741875673748077489238391001187748258124039623697289612052402753422028380156396811587142615):
            Fails because its discriminant is not a square.
        - Root 2 (x=3086251397349454634226049654186198282625136597600255705376316455943570106637401671127489553534256598630507009270951):
            Fails because its discriminant is not a square.
        - Root 3 (x=2512099095366387796245759085729510986367032014959769672734622752070562589059815523018960565849753051338812932816014):
            Has a square discriminant, but both sign options yield t^2 values that are not squares.
        - Root 4 (x=2077344747421819657086473418925078480898358265217674456436079722467637536216749299440611432676849905020722484031356):
            Yields two valid t values:
            - 1731081574565817469321317449275278355306982786154072576198758675751495027640363897075486577327802192163339186341827
            - 861410691052762088300790587394810074303505896628048305535645284922135116676755956131724844456716837983264353875219
        - Root 5 (x=162902306530757011687648381458039960905879760854007434532151803806422383239905014872915974221245198317567396330740):
            Yields two valid t values:
            - 1006044755431560595281793557931171729984964515682961911911398807521437683216171091013202870577238485832047490326971
            - 1562001338336877267717400325455189014780228097985596277514975439801739125527323838522116502949589758528550231396418

        Additionally we also have the additive inverses of these t values, which are also valid
        kernel (non-unique) points. These are generated using the relationship:
        `(-t) mod p === (p - t) mod p`
        """  # noqa: E501
        unique_kernel_ts = [
            1731081574565817469321317449275278355306982786154072576198758675751495027640363897075486577327802192163339186341827,
            861410691052762088300790587394810074303505896628048305535645284922135116676755956131724844456716837983264353875219,
            1006044755431560595281793557931171729984964515682961911911398807521437683216171091013202870577238485832047490326971,
            1562001338336877267717400325455189014780228097985596277514975439801739125527323838522116502949589758528550231396418,
        ]
        additive_inverses = [(Spec.P - t) % Spec.P for t in unique_kernel_ts]
        return [FP(t) for t in (unique_kernel_ts + additive_inverses)]

    # G2 map to curve 3-isogeny kernel point generator
    @classmethod
    def generate_g2_map_isogeny_kernel_points(cls) -> List[FP2]:
        """
        Return precomputed kernel points for the BLS12-381 G2 map to curve function. These map to
        the G2 identity point `Spec.INF_G2`. They are generated using sage math externally with the
        following script as its significantly faster than using `py_ecc` (200-1000x faster).

        For reference we can imagine the map to curve function as a simple 2 step process, where an
        input t value is mapped to a point on the auxiliary curve via a SWU map, and then that
        point is mapped to the BLS curve via a 3-isogeny. For reference:
        - https://eips.ethereum.org/assets/eip-2537/field_to_curve

        Note we cannot use sage math directly within EEST as it is not a pure python library and
        requires an external dependency to be installed on the system machine.

        ```sage
        q = 0x1A0111EA397FE69A4B1BA7B6434BACD764774B84F38512BF6730D2A0F6B0F6241EABFFFEB153FFFFB9FEFFFFFFFFAAAB
        Fp = GF(q)
        R.<x> = PolynomialRing(Fp)
        Fp2.<u> = Fp.extension(x^2 + 1)
        E2 = EllipticCurve(Fp2, [0, 4*(1+u)])
        ISO_3_A = 240 * u
        ISO_3_B = 1012 * (1 + u)
        ISO_3_Z = -(2 + u)
        Ei = EllipticCurve(Fp2, [ISO_3_A, ISO_3_B])
        iso = EllipticCurveIsogeny(E=E2, kernel=None, codomain=Ei, degree=3).dual()
        x_den_k0 = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaa63 * u
        x_den_k1 = 0xc + 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaa9f * u
        for (x, _) in iso.kernel_polynomial().roots():
            y_squared = x^3 + ISO_3_A * x + ISO_3_B
            is_on_curve = y_squared.is_square()
            print("Root is on curve:" if is_on_curve else "Warning: Root is not on the curve")
            inv_factor = (x * ISO_3_A / -ISO_3_B) - 1
            if inv_factor == 0:
                continue
            discriminant = 1 + 4 / inv_factor
            if not discriminant.is_square():
                continue
            for sign in [1, -1]:
                zt2 = (-1 + sign * discriminant.sqrt()) / 2
                t2 = zt2 / ISO_3_Z
                if t2.is_square():
                    t = t2.sqrt()
                    # Perform the proper SWU mapping
                    tv1_num = ISO_3_Z^2 * t^4 + ISO_3_Z * t^2
                    tv1 = 1 / tv1_num
                    x1 = (-ISO_3_B / ISO_3_A) * (1 + tv1)
                    gx1 = x1^3 + ISO_3_A * x1 + ISO_3_B
                    x2 = ISO_3_Z * t^2 * x1
                    swu_x = x1 if gx1.is_square() else x2
                    x_den_value = swu_x^2 + x_den_k1 * swu_x + x_den_k0
                    is_kernel_point = (x_den_value == 0)
                    print("Is a kernel point:", is_kernel_point)
                    print(t)
        ```

        Add the script contents to a file called `points.sage`, run `sage points.sage`!

        Please see the sage math installation guide to replicate:
            - https://doc.sagemath.org/html/en/installation/index.html

        As G2 uses an 3-degree isogeny, its kernel contains exactly 3 points on the auxiliary
        curve that maps to the point at infinity on the BLS curve. This includes the point at
        infinity (doesn't concern us as the initial SWU map can never output infinity from any int
        t) and 2 other kernel points.

        These 2 other kernel points correspond to 1 x-coord on the curve (since each x-coord
        yields two points with y and -y). Note that this root yields two equal t values due
        to specific properties of the isogeny in Fp2.

        However, the G2 case is different from G1 and requires additional verification for y, we
        must check that the computed y^2 actually has a square root in Fp2. Unlike G1, the G2
        singular isogeny kernel polynomial root does not correspond to a valid point on the
        auxiliary curve due to the failure of the additional check.

        - Root 1 (x=6*u + 4002409555221667393417789825735904156556882819939007885332058136124031650490837864442687629129015664037894272559781):
            Fails because its y^2 is not a square in Fp2.

        Due to the failure of the first root, we have no valid kernel points in G2 that map to the
        point at infinity on the BLS curve. This is why we return an empty list here. It is kept
        for consistency with the G1 case, and documentation purposes.
        """  # noqa: E501
        return []
