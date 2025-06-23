from typing import (
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from py_ecc.fields import (
    bls12_381_FQ,
    bls12_381_FQ2,
    bls12_381_FQ12,
    bls12_381_FQP,
    bn128_FQ,
    bn128_FQ2,
    bn128_FQ12,
    bn128_FQP,
    optimized_bls12_381_FQ,
    optimized_bls12_381_FQ2,
    optimized_bls12_381_FQ12,
    optimized_bls12_381_FQP,
    optimized_bn128_FQ,
    optimized_bn128_FQ2,
    optimized_bn128_FQ12,
    optimized_bn128_FQP,
)
from py_ecc.fields.field_elements import (
    FQ,
    FQ2,
    FQ12,
    FQP,
)
from py_ecc.fields.optimized_field_elements import (
    FQ as Optimized_FQ,
    FQ2 as Optimized_FQ2,
    FQ12 as Optimized_FQ12,
    FQP as Optimized_FQP,
)

#
# These types are wrt Normal Integers
#
PlainPoint2D = Tuple[int, int]
PlainPoint3D = Tuple[int, int, int]


#
# Types for the normal curves and fields
#
Field = TypeVar(
    "Field",
    # General
    FQ,
    FQP,
    FQ2,
    FQ12,
    # bn128
    bn128_FQ,
    bn128_FQP,
    bn128_FQ2,
    bn128_FQ12,
    # bls12_381
    bls12_381_FQ,
    bls12_381_FQP,
    bls12_381_FQ2,
    bls12_381_FQ12,
)
Point2D = Optional[Tuple[Field, Field]]  # Point at infinity is encoded as a None
Point3D = Optional[Tuple[Field, Field, Field]]  # Point at infinity is encoded as a None
GeneralPoint = Union[Point2D[Field], Point3D[Field]]


#
# Types For optimized curves and fields
#
Optimized_Field = TypeVar(
    "Optimized_Field",
    # General
    Optimized_FQ,
    Optimized_FQP,
    Optimized_FQ2,
    Optimized_FQ12,
    # bn128
    optimized_bn128_FQ,
    optimized_bn128_FQP,
    optimized_bn128_FQ2,
    optimized_bn128_FQ12,
    # bls12_381
    optimized_bls12_381_FQ,
    optimized_bls12_381_FQP,
    optimized_bls12_381_FQ2,
    optimized_bls12_381_FQ12,
)
Optimized_Point2D = Tuple[Optimized_Field, Optimized_Field]
Optimized_Point3D = Tuple[Optimized_Field, Optimized_Field, Optimized_Field]
Optimized_GeneralPoint = Union[
    Optimized_Point2D[Optimized_Field],
    Optimized_Point3D[Optimized_Field],
]

#
# Miscellaneous types
#
FQ2_modulus_coeffs_type = Tuple[int, int]
FQ12_modulus_coeffs_type = Tuple[
    int, int, int, int, int, int, int, int, int, int, int, int
]
