"""
Defines EIP-2537 specification constants and functions.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Sized, SupportsBytes, Tuple


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_2537 = ReferenceSpec("EIPS/eip-2537.md", "cd0f016ad0c4c68b8b1f5c502ef61ab9353b6e5e")


class BytesConcatenation(SupportsBytes, Sized):
    """
    A class that can be concatenated with bytes.
    """

    def __len__(self) -> int:
        """Returns the length of the object when converted to bytes."""
        return len(bytes(self))

    def __add__(self, other: bytes | SupportsBytes) -> bytes:
        """Concatenates the object with another bytes object."""
        return bytes(self) + bytes(other)

    def __radd__(self, other: bytes | SupportsBytes) -> bytes:
        """Concatenates the object with another bytes object."""
        return bytes(other) + bytes(self)


@dataclass(frozen=True)
class FP(BytesConcatenation):
    """Dataclass that defines a single element of Fp."""

    x: int = 0

    def __bytes__(self) -> bytes:
        """Converts the field element to bytes."""
        return self.x.to_bytes(64, byteorder="big")


@dataclass(frozen=True)
class PointG1(BytesConcatenation):
    """Dataclass that defines a single point in G1."""

    x: int = 0
    y: int = 0

    def __bytes__(self) -> bytes:
        """Converts the point to bytes."""
        return self.x.to_bytes(64, byteorder="big") + self.y.to_bytes(64, byteorder="big")

    def __neg__(self):
        """Negates the point."""
        return PointG1(self.x, Spec.P - self.y)


@dataclass(frozen=True)
class FP2(BytesConcatenation):
    """Dataclass that defines a single element of Fp2."""

    x: Tuple[int, int] = (0, 0)

    def __bytes__(self) -> bytes:
        """Converts the field element to bytes."""
        return self.x[0].to_bytes(64, byteorder="big") + self.x[1].to_bytes(64, byteorder="big")


@dataclass(frozen=True)
class PointG2(BytesConcatenation):
    """Dataclass that defines a single point in G2."""

    x: Tuple[int, int] = (0, 0)
    y: Tuple[int, int] = (0, 0)

    def __bytes__(self) -> bytes:
        """Converts the point to bytes."""
        return (
            self.x[0].to_bytes(64, byteorder="big")
            + self.x[1].to_bytes(64, byteorder="big")
            + self.y[0].to_bytes(64, byteorder="big")
            + self.y[1].to_bytes(64, byteorder="big")
        )

    def __neg__(self):
        """Negates the point."""
        return PointG2(self.x, (Spec.P - self.y[0], Spec.P - self.y[1]))


@dataclass(frozen=True)
class Scalar(BytesConcatenation):
    """Dataclass that defines a single scalar."""

    x: int = 0

    def __bytes__(self) -> bytes:
        """Converts the scalar to bytes."""
        return self.x.to_bytes(32, byteorder="big")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-2537 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-2537
    """

    # Addresses
    G1ADD = 0x0B
    G1MUL = 0x0C
    G1MSM = 0x0D
    G2ADD = 0x0E
    G2MUL = 0x0F
    G2MSM = 0x10
    PAIRING = 0x11
    MAP_FP_TO_G1 = 0x12
    MAP_FP2_TO_G2 = 0x13

    # Gas constants
    G1ADD_GAS = 375
    G1MUL_GAS = 12_000
    G2ADD_GAS = 600
    G2MUL_GAS = 22_500
    MAP_FP_TO_G1_GAS = 5_500
    MAP_FP2_TO_G2_GAS = 23_800
    PAIRING_BASE_GAS = 37_700
    PAIRING_PER_PAIR_GAS = 32_600

    # Other constants
    B_COEFFICIENT = 0x04
    X = -0xD201000000010000
    Q = X**4 - X**2 + 1
    P = (X - 1) ** 2 * Q // 3 + X
    LEN_PER_PAIR = len(PointG1() + PointG2())
    MSM_MULTIPLIER = 1_000
    # fmt: off
    G1MSM_DISCOUNT_TABLE = [
        0,
        1000, 949, 848, 797, 764, 750, 738, 728, 719, 712, 705, 698, 692, 687, 682, 677, 673, 669,
        665, 661, 658, 654, 651, 648, 645, 642, 640, 637, 635, 632, 630, 627, 625, 623, 621, 619,
        617, 615, 613, 611, 609, 608, 606, 604, 603, 601, 599, 598, 596, 595, 593, 592, 591, 589,
        588, 586, 585, 584, 582, 581, 580, 579, 577, 576, 575, 574, 573, 572, 570, 569, 568, 567,
        566, 565, 564, 563, 562, 561, 560, 559, 558, 557, 556, 555, 554, 553, 552, 551, 550, 549,
        548, 547, 547, 546, 545, 544, 543, 542, 541, 540, 540, 539, 538, 537, 536, 536, 535, 534,
        533, 532, 532, 531, 530, 529, 528, 528, 527, 526, 525, 525, 524, 523, 522, 522, 521, 520,
        520, 519
    ]
    G2MSM_DISCOUNT_TABLE = [
        0,
        1000, 1000, 923, 884, 855, 832, 812, 796, 782, 770, 759, 749, 740, 732, 724, 717, 711, 704,
        699, 693, 688, 683, 679, 674, 670, 666, 663, 659, 655, 652, 649, 646, 643, 640, 637, 634,
        632, 629, 627, 624, 622, 620, 618, 615, 613, 611, 609, 607, 606, 604, 602, 600, 598, 597,
        595, 593, 592, 590, 589, 587, 586, 584, 583, 582, 580, 579, 578, 576, 575, 574, 573, 571,
        570, 569, 568, 567, 566, 565, 563, 562, 561, 560, 559, 558, 557, 556, 555, 554, 553, 552,
        552, 551, 550, 549, 548, 547, 546, 545, 545, 544, 543, 542, 541, 541, 540, 539, 538, 537,
        537, 536, 535, 535, 534, 533, 532, 532, 531, 530, 530, 529, 528, 528, 527, 526, 526, 525,
        524, 524
    ]
    # fmt: on

    # Test constants (from https://github.com/ethereum/bls12-381-tests/tree/eip-2537)
    P1 = PointG1(  # random point in G1
        0x112B98340EEE2777CC3C14163DEA3EC97977AC3DC5C70DA32E6E87578F44912E902CCEF9EFE28D4A78B8999DFBCA9426,  # noqa: E501
        0x186B28D92356C4DFEC4B5201AD099DBDEDE3781F8998DDF929B4CD7756192185CA7B8F4EF7088F813270AC3D48868A21,  # noqa: E501
    )
    G1 = PointG1(
        0x17F1D3A73197D7942695638C4FA9AC0FC3688C4F9774B905A14E3A3F171BAC586C55E83FF97A1AEFFB3AF00ADB22C6BB,  # noqa: E501
        0x8B3F481E3AAA0F1A09E30ED741D8AE4FCF5E095D5D00AF600DB18CB2C04B3EDD03CC744A2888AE40CAA232946C5E7E1,  # noqa: E501
    )
    # point at infinity in G1
    INF_G1 = PointG1(0, 0)
    # random point in G2
    P2 = PointG2(
        (
            0x103121A2CEAAE586D240843A398967325F8EB5A93E8FEA99B62B9F88D8556C80DD726A4B30E84A36EEABAF3592937F27,  # noqa: E501
            0x86B990F3DA2AEAC0A36143B7D7C824428215140DB1BB859338764CB58458F081D92664F9053B50B3FBD2E4723121B68,  # noqa: E501
        ),
        (
            0xF9E7BA9A86A8F7624AA2B42DCC8772E1AF4AE115685E60ABC2C9B90242167ACEF3D0BE4050BF935EED7C3B6FC7BA77E,  # noqa: E501
            0xD22C3652D0DC6F0FC9316E14268477C2049EF772E852108D269D9C38DBA1D4802E8DAE479818184C08F9A569D878451,  # noqa: E501
        ),
    )
    G2 = PointG2(
        (
            0x24AA2B2F08F0A91260805272DC51051C6E47AD4FA403B02B4510B647AE3D1770BAC0326A805BBEFD48056C8C121BDB8,  # noqa: E501
            0x13E02B6052719F607DACD3A088274F65596BD0D09920B61AB5DA61BBDC7F5049334CF11213945D57E5AC7D055D042B7E,  # noqa: E501
        ),
        (
            0xCE5D527727D6E118CC9CDC6DA2E351AADFD9BAA8CBDD3A76D429A695160D12C923AC9CC3BACA289E193548608B82801,  # noqa: E501
            0x606C4A02EA734CC32ACD2B02BC28B99CB3E287E85A763AF267492AB572E99AB3F370D275CEC1DA1AAA9075FF05F79BE,  # noqa: E501
        ),
    )
    # point at infinity in G2
    INF_G2 = PointG2((0, 0), (0, 0))

    # Other test constants
    # point not in subgroup in curve Fp
    P1_NOT_IN_SUBGROUP = PointG1(0, 2)
    P1_NOT_IN_SUBGROUP_TIMES_2 = PointG1(0, P - 2)
    # point not in subgroup in curve Fp2
    P2_NOT_IN_SUBGROUP = PointG2(
        (1, 1),
        (
            0x17FAA6201231304F270B858DAD9462089F2A5B83388E4B10773ABC1EEF6D193B9FCE4E8EA2D9D28E3C3A315AA7DE14CA,  # noqa: E501
            0xCC12449BE6AC4E7F367E7242250427C4FB4C39325D3164AD397C1837A90F0EA1A534757DF374DD6569345EB41ED76E,  # noqa: E501
        ),
    )
    P2_NOT_IN_SUBGROUP_TIMES_2 = PointG2(
        (
            0x919F97860ECC3E933E3477FCAC0E2E4FCC35A6E886E935C97511685232456263DEF6665F143CCCCB44C733333331553,  # noqa: E501
            0x18B4376B50398178FA8D78ED2654B0FFD2A487BE4DBE6B69086E61B283F4E9D58389CCCB8EDC99995718A66666661555,  # noqa: E501
        ),
        (
            0x26898F699C4B07A405AB4183A10B47F923D1C0FDA1018682DD2CCC88968C1B90D44534D6B9270CF57F8DC6D4891678A,  # noqa: E501
            0x3270414330EAD5EC92219A03A24DFA059DBCBE610868BE1851CC13DAC447F60B40D41113FD007D3307B19ADD4B0F061,  # noqa: E501
        ),
    )

    # Pairing precompile results
    PAIRING_TRUE = int.to_bytes(1, length=32, byteorder="big")
    PAIRING_FALSE = int.to_bytes(0, length=32, byteorder="big")

    # Returned on precompile failure
    INVALID = b""


class BLS12Group(Enum):
    """
    Helper enum to specify the BLS12 group in discount table helpers.
    """

    G1 = auto()
    G2 = auto()


def msm_discount(group: BLS12Group, k: int) -> int:
    """
    Returns the discount for the G1MSM and G2MSM precompiles.
    """
    assert k >= 1, "k must be greater than or equal to 1"
    match group:
        case BLS12Group.G1:
            return Spec.G1MSM_DISCOUNT_TABLE[min(k, 128)]
        case BLS12Group.G2:
            return Spec.G2MSM_DISCOUNT_TABLE[min(k, 128)]
        case _:
            raise ValueError(f"Unsupported group: {group}")


def msm_gas_func_gen(
    group: BLS12Group, len_per_pair: int, multiplication_cost: int
) -> Callable[[int], int]:
    """
    Generate a function that calculates the gas cost for the G1MSM and G2MSM precompiles.
    """

    def msm_gas(input_length: int) -> int:
        """
        Calculates the gas cost for the G1MSM and G2MSM precompiles.
        """
        k = input_length // len_per_pair
        if k == 0:
            return 0

        gas_cost = k * multiplication_cost * msm_discount(group, k) // Spec.MSM_MULTIPLIER

        return gas_cost

    return msm_gas


def pairing_gas(input_length: int) -> int:
    """
    Calculates the gas cost for the PAIRING precompile.
    """
    k = input_length // Spec.LEN_PER_PAIR
    return (Spec.PAIRING_PER_PAIR_GAS * k) + Spec.PAIRING_BASE_GAS


GAS_CALCULATION_FUNCTION_MAP = {
    Spec.G1ADD: lambda _: Spec.G1ADD_GAS,
    Spec.G1MUL: lambda _: Spec.G1MUL_GAS,
    Spec.G1MSM: msm_gas_func_gen(BLS12Group.G1, len(PointG1() + Scalar()), Spec.G1MUL_GAS),
    Spec.G2ADD: lambda _: Spec.G2ADD_GAS,
    Spec.G2MUL: lambda _: Spec.G2MUL_GAS,
    Spec.G2MSM: msm_gas_func_gen(BLS12Group.G2, len(PointG2() + Scalar()), Spec.G2MUL_GAS),
    Spec.PAIRING: pairing_gas,
    Spec.MAP_FP_TO_G1: lambda _: Spec.MAP_FP_TO_G1_GAS,
    Spec.MAP_FP2_TO_G2: lambda _: Spec.MAP_FP2_TO_G2_GAS,
}
