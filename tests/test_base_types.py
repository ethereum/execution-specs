import pytest

from ethereum.base_types import U256, FixedBytes, Uint


def test_uint_new() -> None:
    value = Uint(5)
    assert isinstance(value, int)
    assert isinstance(value, Uint)
    assert value == 5


def test_uint_new_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(-5)


def test_uint_new_float() -> None:
    with pytest.raises(TypeError):
        Uint(0.1)  # type: ignore


def test_uint_radd() -> None:
    value = 4 + Uint(5)
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_radd_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) + Uint(5)


def test_uint_radd_float() -> None:
    value = (1.0) + Uint(5)
    assert not isinstance(value, int)
    assert value == 6.0


def test_uint_add() -> None:
    value = Uint(5) + 4
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_add_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(5) + (-4)


def test_uint_add_float() -> None:
    value = Uint(5) + (1.0)
    assert not isinstance(value, int)
    assert value == 6.0


def test_uint_iadd() -> None:
    value = Uint(5)
    value += 4
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_iadd_negative() -> None:
    value = Uint(5)
    with pytest.raises(OverflowError):
        value += -4


def test_uint_iadd_float() -> None:
    value = Uint(5)
    value += 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 6.0


def test_uint_rsub() -> None:
    value = 6 - Uint(5)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_rsub_too_big() -> None:
    with pytest.raises(OverflowError):
        6 - Uint(7)


def test_uint_rsub_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) - Uint(5)


def test_uint_rsub_float() -> None:
    value = (6.0) - Uint(5)
    assert not isinstance(value, int)
    assert value == 1.0


def test_uint_sub() -> None:
    value = Uint(5) - 4
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_sub_too_big() -> None:
    with pytest.raises(OverflowError):
        Uint(5) - 6


def test_uint_sub_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(5) - (-4)


def test_uint_sub_float() -> None:
    value = Uint(5) - (1.0)
    assert not isinstance(value, int)
    assert value == 4.0


def test_uint_isub() -> None:
    value = Uint(5)
    value -= 4
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_isub_too_big() -> None:
    value = Uint(5)
    with pytest.raises(OverflowError):
        value -= 6


def test_uint_isub_negative() -> None:
    value = Uint(5)
    with pytest.raises(OverflowError):
        value -= -4


def test_uint_isub_float() -> None:
    value = Uint(5)
    value -= 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 4.0


def test_uint_rmul() -> None:
    value = 4 * Uint(5)
    assert isinstance(value, Uint)
    assert value == 20


def test_uint_rmul_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) * Uint(5)


def test_uint_rmul_float() -> None:
    value = (1.0) * Uint(5)
    assert not isinstance(value, int)
    assert value == 5.0


def test_uint_mul() -> None:
    value = Uint(5) * 4
    assert isinstance(value, Uint)
    assert value == 20


def test_uint_mul_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(5) * (-4)


def test_uint_mul_float() -> None:
    value = Uint(5) * (1.0)
    assert not isinstance(value, int)
    assert value == 5.0


def test_uint_imul() -> None:
    value = Uint(5)
    value *= 4
    assert isinstance(value, Uint)
    assert value == 20


def test_uint_imul_negative() -> None:
    value = Uint(5)
    with pytest.raises(OverflowError):
        value *= -4


def test_uint_imul_float() -> None:
    value = Uint(5)
    value *= 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 5.0


def test_uint_floordiv() -> None:
    value = Uint(5) // 2
    assert isinstance(value, Uint)
    assert value == 2


def test_uint_floordiv_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(5) // -2


def test_uint_floordiv_float() -> None:
    value = Uint(5) // 2.0
    assert not isinstance(value, Uint)
    assert value == 2


def test_uint_rfloordiv() -> None:
    value = 5 // Uint(2)
    assert isinstance(value, Uint)
    assert value == 2


def test_uint_rfloordiv_negative() -> None:
    with pytest.raises(OverflowError):
        (-2) // Uint(5)


def test_uint_rfloordiv_float() -> None:
    value = 5.0 // Uint(2)
    assert not isinstance(value, Uint)
    assert value == 2


def test_uint_ifloordiv() -> None:
    value = Uint(5)
    value //= 2
    assert isinstance(value, Uint)
    assert value == 2


def test_uint_ifloordiv_negative() -> None:
    value = Uint(5)
    with pytest.raises(OverflowError):
        value //= -2


def test_uint_rmod() -> None:
    value = 6 % Uint(5)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_rmod_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) % Uint(5)


def test_uint_rmod_float() -> None:
    value = (6.0) % Uint(5)
    assert not isinstance(value, int)
    assert value == 1.0


def test_uint_mod() -> None:
    value = Uint(5) % 4
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_mod_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(5) % (-4)


def test_uint_mod_float() -> None:
    value = Uint(5) % (1.0)
    assert not isinstance(value, int)
    assert value == 0.0


def test_uint_imod() -> None:
    value = Uint(5)
    value %= 4
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_imod_negative() -> None:
    value = Uint(5)
    with pytest.raises(OverflowError):
        value %= -4


def test_uint_imod_float() -> None:
    value = Uint(5)
    value %= 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 0.0


def test_uint_divmod() -> None:
    quotient, remainder = divmod(Uint(5), 2)
    assert isinstance(quotient, Uint)
    assert isinstance(remainder, Uint)
    assert quotient == 2
    assert remainder == 1


def test_uint_divmod_negative() -> None:
    with pytest.raises(OverflowError):
        divmod(Uint(5), -2)


def test_uint_divmod_float() -> None:
    quotient, remainder = divmod(Uint(5), 2.0)
    assert not isinstance(quotient, Uint)
    assert not isinstance(remainder, Uint)
    assert quotient == 2
    assert remainder == 1


def test_uint_rdivmod() -> None:
    quotient, remainder = divmod(5, Uint(2))
    assert isinstance(quotient, Uint)
    assert isinstance(remainder, Uint)
    assert quotient == 2
    assert remainder == 1


def test_uint_rdivmod_negative() -> None:
    with pytest.raises(OverflowError):
        divmod(-5, Uint(2))


def test_uint_rdivmod_float() -> None:
    quotient, remainder = divmod(5.0, Uint(2))
    assert not isinstance(quotient, Uint)
    assert not isinstance(remainder, Uint)
    assert quotient == 2
    assert remainder == 1


def test_uint_pow() -> None:
    value = Uint(3) ** 2
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_pow_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(3) ** -2


def test_uint_pow_modulo() -> None:
    value = pow(Uint(4), 2, 3)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_pow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        pow(Uint(4), 2, -3)


def test_uint_rpow() -> None:
    value = 3 ** Uint(2)
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_rpow_negative() -> None:
    with pytest.raises(OverflowError):
        (-3) ** Uint(2)


def test_uint_rpow_modulo() -> None:
    value = Uint.__rpow__(Uint(2), 4, 3)
    assert isinstance(value, int)
    assert value == 1


def test_uint_rpow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        Uint.__rpow__(Uint(2), 4, -3)


def test_uint_ipow() -> None:
    value = Uint(3)
    value **= 2
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_ipow_negative() -> None:
    value = Uint(3)
    with pytest.raises(OverflowError):
        value **= -2


def test_uint_ipow_modulo() -> None:
    value = Uint(4).__ipow__(2, 3)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_ipow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        Uint(4).__ipow__(2, -3)


def test_uint_to_be_bytes_zero() -> None:
    encoded = Uint(0).to_be_bytes()
    assert encoded == bytes([])


def test_uint_to_be_bytes_one() -> None:
    encoded = Uint(1).to_be_bytes()
    assert encoded == bytes([1])


def test_uint_to_be_bytes_is_big_endian() -> None:
    encoded = Uint(0xABCD).to_be_bytes()
    assert encoded == bytes([0xAB, 0xCD])


def test_uint_to_be_bytes32_zero() -> None:
    encoded = Uint(0).to_be_bytes32()
    assert encoded == bytes([0] * 32)


def test_uint_to_be_bytes32_one() -> None:
    encoded = Uint(1).to_be_bytes32()
    assert encoded == bytes([0] * 31 + [1])


def test_uint_to_be_bytes32_max_value() -> None:
    encoded = Uint(2**256 - 1).to_be_bytes32()
    assert encoded == bytes(
        [
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
        ]
    )


def test_uint_from_be_bytes_empty() -> None:
    value = Uint.from_be_bytes(b"")
    assert value == 0


def test_uint_from_be_bytes_one() -> None:
    value = Uint.from_be_bytes(bytes([1]))
    assert value == 1


def test_uint_from_be_bytes_is_big_endian() -> None:
    value = Uint.from_be_bytes(bytes([0xAB, 0xCD]))
    assert value == 0xABCD


def test_u256_new() -> None:
    value = U256(5)
    assert isinstance(value, int)
    assert isinstance(value, U256)
    assert value == 5


def test_u256_new_negative() -> None:
    with pytest.raises(OverflowError):
        U256(-5)


def test_u256_new_float() -> None:
    with pytest.raises(TypeError):
        U256(0.1)  # type: ignore


def test_u256_new_max_value() -> None:
    value = U256(2**256 - 1)
    assert isinstance(value, U256)
    assert value == 2**256 - 1


def test_u256_new_too_large() -> None:
    with pytest.raises(OverflowError):
        U256(2**256)


def test_u256_radd() -> None:
    value = 4 + U256(5)
    assert isinstance(value, U256)
    assert value == 9


def test_u256_radd_overflow() -> None:
    with pytest.raises(OverflowError):
        (2**256 - 1) + U256(5)


def test_u256_radd_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) + U256(5)


def test_u256_radd_float() -> None:
    value = (1.0) + U256(5)
    assert not isinstance(value, int)
    assert value == 6.0


def test_u256_add() -> None:
    value = U256(5) + 4
    assert isinstance(value, U256)
    assert value == 9


def test_u256_add_overflow() -> None:
    with pytest.raises(OverflowError):
        U256(5) + (2**256 - 1)


def test_u256_add_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5) + (-4)


def test_u256_add_float() -> None:
    value = U256(5) + (1.0)
    assert not isinstance(value, int)
    assert value == 6.0


def test_u256_wrapping_add() -> None:
    value = U256(5).wrapping_add(4)
    assert isinstance(value, U256)
    assert value == 9


def test_u256_wrapping_add_overflow() -> None:
    value = U256(5).wrapping_add(2**256 - 1)
    assert isinstance(value, U256)
    assert value == 4


def test_u256_wrapping_add_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5).wrapping_add(-4)


def test_u256_iadd() -> None:
    value = U256(5)
    value += 4
    assert isinstance(value, U256)
    assert value == 9


def test_u256_iadd_negative() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value += -4


def test_u256_iadd_float() -> None:
    value = U256(5)
    value += 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 6.0


def test_u256_iadd_overflow() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value += 2**256 - 1


def test_u256_rsub() -> None:
    value = 5 - U256(4)
    assert isinstance(value, U256)
    assert value == 1


def test_u256_rsub_underflow() -> None:
    with pytest.raises(OverflowError):
        (0) - U256(1)


def test_u256_rsub_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) - U256(5)


def test_u256_rsub_float() -> None:
    value = (5.0) - U256(1)
    assert not isinstance(value, int)
    assert value == 4.0


def test_u256_sub() -> None:
    value = U256(5) - 4
    assert isinstance(value, U256)
    assert value == 1


def test_u256_sub_underflow() -> None:
    with pytest.raises(OverflowError):
        U256(5) - 6


def test_u256_sub_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5) - (-4)


def test_u256_sub_float() -> None:
    value = U256(5) - (1.0)
    assert not isinstance(value, int)
    assert value == 4.0


def test_u256_wrapping_sub() -> None:
    value = U256(5).wrapping_sub(4)
    assert isinstance(value, U256)
    assert value == 1


def test_u256_wrapping_sub_underflow() -> None:
    value = U256(5).wrapping_sub(6)
    assert isinstance(value, U256)
    assert value == 2**256 - 1


def test_u256_wrapping_sub_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5).wrapping_sub(-4)


def test_u256_isub() -> None:
    value = U256(5)
    value -= 4
    assert isinstance(value, U256)
    assert value == 1


def test_u256_isub_negative() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value -= -4


def test_u256_isub_float() -> None:
    value = U256(5)
    value -= 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 4.0


def test_u256_isub_underflow() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value -= 6


def test_u256_rmul() -> None:
    value = 4 * U256(5)
    assert isinstance(value, U256)
    assert value == 20


def test_u256_rmul_overflow() -> None:
    with pytest.raises(OverflowError):
        (2**256 - 1) * U256(5)


def test_u256_rmul_negative() -> None:
    with pytest.raises(OverflowError):
        (-4) * U256(5)


def test_u256_rmul_float() -> None:
    value = (1.0) * U256(5)
    assert not isinstance(value, int)
    assert value == 5.0


def test_u256_mul() -> None:
    value = U256(5) * 4
    assert isinstance(value, U256)
    assert value == 20


def test_u256_mul_overflow() -> None:
    with pytest.raises(OverflowError):
        U256.MAX_VALUE * 4


def test_u256_mul_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5) * (-4)


def test_u256_mul_float() -> None:
    value = U256(5) * (1.0)
    assert not isinstance(value, int)
    assert value == 5.0


def test_u256_wrapping_mul() -> None:
    value = U256(5).wrapping_mul(4)
    assert isinstance(value, U256)
    assert value == 20


def test_u256_wrapping_mul_overflow() -> None:
    value = U256.MAX_VALUE.wrapping_mul(4)
    assert isinstance(value, U256)
    assert (
        value
        == 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
    )


def test_u256_wrapping_mul_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5).wrapping_mul(-4)


def test_u256_imul() -> None:
    value = U256(5)
    value *= 4
    assert isinstance(value, U256)
    assert value == 20


def test_u256_imul_negative() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value *= -4


def test_u256_imul_arg_overflow() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value *= 2**256


def test_u256_imul_float() -> None:
    value = U256(5)
    value *= 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 5.0


def test_u256_imul_overflow() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value *= 2**256 - 1


def test_u256_floordiv() -> None:
    value = U256(5) // 2
    assert isinstance(value, U256)
    assert value == 2


def test_u256_floordiv_overflow() -> None:
    with pytest.raises(OverflowError):
        U256(5) // (2**256)


def test_u256_floordiv_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5) // -2


def test_u256_floordiv_float() -> None:
    value = U256(5) // 2.0
    assert not isinstance(value, U256)
    assert value == 2


def test_u256_rfloordiv() -> None:
    value = 5 // U256(2)
    assert isinstance(value, U256)
    assert value == 2


def test_u256_rfloordiv_overflow() -> None:
    with pytest.raises(OverflowError):
        (2**256) // U256(2)


def test_u256_rfloordiv_negative() -> None:
    with pytest.raises(OverflowError):
        (-2) // U256(5)


def test_u256_rfloordiv_float() -> None:
    value = 5.0 // U256(2)
    assert not isinstance(value, U256)
    assert value == 2


def test_u256_ifloordiv() -> None:
    value = U256(5)
    value //= 2
    assert isinstance(value, U256)
    assert value == 2


def test_u256_ifloordiv_negative() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value //= -2


def test_u256_ifloordiv_overflow() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value //= 2**256


def test_u256_rmod() -> None:
    value = 6 % U256(5)
    assert isinstance(value, U256)
    assert value == 1


def test_u256_rmod_float() -> None:
    value = (6.0) % U256(5)
    assert not isinstance(value, int)
    assert value == 1.0


def test_u256_mod() -> None:
    value = U256(5) % 4
    assert isinstance(value, U256)
    assert value == 1


def test_u256_mod_overflow() -> None:
    with pytest.raises(OverflowError):
        U256(5) % (2**256)


def test_u256_mod_negative() -> None:
    with pytest.raises(OverflowError):
        U256(5) % (-4)


def test_u256_mod_float() -> None:
    value = U256(5) % (1.0)
    assert not isinstance(value, int)
    assert value == 0.0


def test_u256_imod() -> None:
    value = U256(5)
    value %= 4
    assert isinstance(value, U256)
    assert value == 1


def test_u256_imod_overflow() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value %= 2**256


def test_u256_imod_negative() -> None:
    value = U256(5)
    with pytest.raises(OverflowError):
        value %= -4


def test_u256_imod_float() -> None:
    value = U256(5)
    value %= 1.0  # type: ignore
    assert not isinstance(value, int)
    assert value == 0.0


def test_u256_divmod() -> None:
    quotient, remainder = divmod(U256(5), 2)
    assert isinstance(quotient, U256)
    assert isinstance(remainder, U256)
    assert quotient == 2
    assert remainder == 1


def test_u256_divmod_overflow() -> None:
    with pytest.raises(OverflowError):
        divmod(U256(5), 2**256)


def test_u256_divmod_negative() -> None:
    with pytest.raises(OverflowError):
        divmod(U256(5), -2)


def test_u256_divmod_float() -> None:
    quotient, remainder = divmod(U256(5), 2.0)
    assert not isinstance(quotient, U256)
    assert not isinstance(remainder, U256)
    assert quotient == 2
    assert remainder == 1


def test_u256_rdivmod() -> None:
    quotient, remainder = divmod(5, U256(2))
    assert isinstance(quotient, U256)
    assert isinstance(remainder, U256)
    assert quotient == 2
    assert remainder == 1


def test_u256_rdivmod_overflow() -> None:
    with pytest.raises(OverflowError):
        divmod(2**256, U256(2))


def test_u256_rdivmod_negative() -> None:
    with pytest.raises(OverflowError):
        divmod(-5, U256(2))


def test_u256_rdivmod_float() -> None:
    quotient, remainder = divmod(5.0, U256(2))
    assert not isinstance(quotient, U256)
    assert not isinstance(remainder, U256)
    assert quotient == 2
    assert remainder == 1


def test_u256_pow() -> None:
    value = U256(3) ** 2
    assert isinstance(value, U256)
    assert value == 9


def test_u256_pow_overflow() -> None:
    with pytest.raises(OverflowError):
        U256(340282366920938463463374607431768211456) ** 3


def test_u256_pow_negative() -> None:
    with pytest.raises(OverflowError):
        U256(3) ** -2


def test_u256_pow_modulo() -> None:
    value = pow(U256(4), 2, 3)
    assert isinstance(value, U256)
    assert value == 1


def test_u256_pow_modulo_overflow() -> None:
    with pytest.raises(OverflowError):
        pow(U256(4), 2, 2**257)


def test_u256_pow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        pow(U256(4), 2, -3)


def test_u256_rpow() -> None:
    value = 3 ** U256(2)
    assert isinstance(value, U256)
    assert value == 9


def test_u256_rpow_overflow() -> None:
    with pytest.raises(OverflowError):
        (2**256) ** U256(2)


def test_u256_rpow_negative() -> None:
    with pytest.raises(OverflowError):
        (-3) ** U256(2)


def test_u256_rpow_modulo() -> None:
    value = U256.__rpow__(U256(2), 4, 3)
    assert isinstance(value, int)
    assert value == 1


def test_u256_rpow_modulo_overflow() -> None:
    with pytest.raises(OverflowError):
        U256.__rpow__(U256(2), 4, 2**256 + 1)


def test_u256_rpow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        U256.__rpow__(U256(2), 4, -3)


def test_u256_ipow() -> None:
    value = U256(3)
    value **= 2
    assert isinstance(value, U256)
    assert value == 9


def test_u256_ipow_overflow() -> None:
    value = U256(340282366920938463463374607431768211456)
    with pytest.raises(OverflowError):
        value **= 3


def test_u256_ipow_negative() -> None:
    value = U256(3)
    with pytest.raises(OverflowError):
        value **= -2


def test_u256_ipow_modulo() -> None:
    value = U256(4).__ipow__(2, 3)
    assert isinstance(value, U256)
    assert value == 1


def test_u256_ipow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        U256(4).__ipow__(2, -3)


def test_u256_ipow_modulo_overflow() -> None:
    with pytest.raises(OverflowError):
        U256(4).__ipow__(2, 2**256 + 1)


def test_u256_wrapping_pow() -> None:
    value = U256(3).wrapping_pow(2)
    assert isinstance(value, U256)
    assert value == 9


def test_u256_wrapping_pow_overflow() -> None:
    value = U256(340282366920938463463374607431768211455).wrapping_pow(3)
    assert isinstance(value, U256)
    assert value == 0x2FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF


def test_u256_wrapping_pow_negative() -> None:
    with pytest.raises(OverflowError):
        U256(3).wrapping_pow(-2)


def test_u256_wrapping_pow_modulo() -> None:
    value = U256(4).wrapping_pow(2, 3)
    assert isinstance(value, U256)
    assert value == 1


def test_u256_wrapping_pow_modulo_overflow() -> None:
    with pytest.raises(OverflowError):
        U256(4).wrapping_pow(2, 2**256 + 1)


def test_u256_wrapping_pow_modulo_negative() -> None:
    with pytest.raises(OverflowError):
        U256(4).wrapping_pow(2, -3)


def test_u256_to_be_bytes_zero() -> None:
    encoded = U256(0).to_be_bytes()
    assert encoded == bytes([])


def test_u256_to_be_bytes_one() -> None:
    encoded = U256(1).to_be_bytes()
    assert encoded == bytes([1])


def test_u256_to_be_bytes_is_big_endian() -> None:
    encoded = U256(0xABCD).to_be_bytes()
    assert encoded == bytes([0xAB, 0xCD])


def test_u256_to_be_bytes32_zero() -> None:
    encoded = U256(0).to_be_bytes32()
    assert encoded == bytes([0] * 32)


def test_u256_to_be_bytes32_one() -> None:
    encoded = U256(1).to_be_bytes32()
    assert encoded == bytes([0] * 31 + [1])


def test_u256_to_be_bytes32_max_value() -> None:
    encoded = U256(2**256 - 1).to_be_bytes32()
    assert encoded == bytes(
        [
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
        ]
    )


def test_u256_from_be_bytes_empty() -> None:
    value = U256.from_be_bytes(b"")
    assert value == 0


def test_u256_from_be_bytes_one() -> None:
    value = U256.from_be_bytes(bytes([1]))
    assert value == 1


def test_u256_from_be_bytes_is_big_endian() -> None:
    value = U256.from_be_bytes(bytes([0xAB, 0xCD]))
    assert value == 0xABCD


def test_u256_from_be_bytes_too_large() -> None:
    with pytest.raises(ValueError):
        U256.from_be_bytes(bytes([0xFF] * 33))


def test_u256_bitwise_and_successful() -> None:
    assert U256(0) & U256(0) == 0
    assert U256(2**256 - 1) & U256(2**256 - 1) == 2**256 - 1
    assert U256(2**256 - 1) & U256(0) == U256(0)


def test_u256_bitwise_and_fails() -> None:
    with pytest.raises(OverflowError):
        U256(0) & (2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1) & (2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1) & -10


def test_u256_bitwise_or_successful() -> None:
    assert U256(0) | U256(0) == 0
    assert U256(2**256 - 1) | U256(0) == 2**256 - 1
    assert U256(2**256 - 1) | U256(2**256 - 1) == U256(2**256 - 1)
    assert U256(2**256 - 1) | U256(17) == U256(2**256 - 1)
    assert U256(17) | U256(18) == U256(19)


def test_u256_bitwise_or_failed() -> None:
    with pytest.raises(OverflowError):
        U256(0) | (2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1) | (2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1) | -10


def test_u256_bitwise_xor_successful() -> None:
    assert U256(0) ^ U256(0) == 0
    assert U256(2**256 - 1) ^ U256(0) == 2**256 - 1
    assert U256(2**256 - 1) ^ U256(2**256 - 1) == U256(0)
    assert U256(2**256 - 1) ^ U256(17) == U256(2**256 - 1) - U256(17)
    assert U256(17) ^ U256(18) == U256(3)


def test_u256_bitwise_xor_failed() -> None:
    with pytest.raises(OverflowError):
        U256(0) | (2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1) ^ (2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1) ^ -10


def test_u256_bitwise_rxor_successful() -> None:
    assert U256(0).__rxor__(U256(0)) == 0
    assert U256(2**256 - 1).__rxor__(U256(0)) == 2**256 - 1
    assert U256(2**256 - 1).__rxor__(U256(2**256 - 1)) == U256(0)
    assert U256(2**256 - 1).__rxor__(U256(17)) == U256(2**256 - 1) - U256(
        17
    )
    assert U256(17).__rxor__(U256(18)) == U256(3)


def test_u256_bitwise_rxor_failed() -> None:
    with pytest.raises(OverflowError):
        U256(0).__rxor__(2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1).__rxor__(2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1).__rxor__(-10)


def test_u256_bitwise_ixor_successful() -> None:
    assert U256(0).__ixor__(U256(0)) == 0
    assert U256(2**256 - 1).__ixor__(U256(0)) == 2**256 - 1
    assert U256(2**256 - 1).__ixor__(U256(2**256 - 1)) == U256(0)
    assert U256(2**256 - 1).__ixor__(U256(17)) == U256(2**256 - 1) - U256(
        17
    )
    assert U256(17).__ixor__(U256(18)) == U256(3)


def test_u256_bitwise_ixor_failed() -> None:
    with pytest.raises(OverflowError):
        U256(0).__ixor__(2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1).__ixor__(2**256)
    with pytest.raises(OverflowError):
        U256(2**256 - 1).__ixor__(-10)


def test_u256_invert() -> None:
    assert ~U256(0) == int(U256.MAX_VALUE)
    assert ~U256(10) == int(U256.MAX_VALUE) - 10
    assert ~U256(2**256 - 1) == 0


def test_u256_rshift() -> None:
    assert U256.MAX_VALUE >> 255 == 1
    assert U256.MAX_VALUE >> 256 == 0
    assert U256.MAX_VALUE >> 257 == 0
    assert U256(0) >> 20 == 0


def test_fixed_bytes_init_too_short() -> None:
    class TestBytes(FixedBytes):
        LENGTH = 5

    with pytest.raises(ValueError):
        TestBytes(b"\0")


def test_fixed_bytes_init_too_long() -> None:
    class TestBytes(FixedBytes):
        LENGTH = 5

    with pytest.raises(ValueError):
        TestBytes(b"\0" * 6)


def test_fixed_bytes_init() -> None:
    class TestBytes(FixedBytes):
        LENGTH = 5

    tb = TestBytes(b"\0" * 5)
    assert tb == b"\0\0\0\0\0"


def test_fixed_bytes_init_bytearray() -> None:
    class TestBytes(FixedBytes):
        LENGTH = 5

    tb = TestBytes(bytearray([0, 0, 0, 0, 0]))
    assert tb == b"\0\0\0\0\0"
    assert isinstance(tb, bytes)
    assert not isinstance(tb, bytearray)


def test_fixed_bytes_concat() -> None:
    class TestBytes(FixedBytes):
        LENGTH = 5

    tb0 = TestBytes(b"\0" * 5)
    tb1 = TestBytes(b"1" * 5)

    tb = tb0 + tb1

    assert tb == b"\x00\x00\x00\x00\x0011111"
    assert isinstance(tb, bytes)
    assert not isinstance(tb, TestBytes)
