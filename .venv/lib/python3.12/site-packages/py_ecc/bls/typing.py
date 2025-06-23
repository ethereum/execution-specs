from typing import (
    NewType,
    Tuple,
)

from py_ecc.fields import (
    optimized_bls12_381_FQ,
    optimized_bls12_381_FQ2,
)
from py_ecc.typing import (
    Optimized_Point3D,
)

G1Uncompressed = Optimized_Point3D[optimized_bls12_381_FQ]
G1Compressed = NewType("G1Compressed", int)

G2Uncompressed = Optimized_Point3D[optimized_bls12_381_FQ2]
G2Compressed = NewType("G2Compressed", Tuple[int, int])
