import pytest

from eth1spec.number import Uint


def test_uint_new() -> None:
    value = Uint(5)
    assert isinstance(value, int)
    assert isinstance(value, Uint)
    assert value == 5


def test_uint_new_negative() -> None:
    with pytest.raises(ValueError):
        Uint(-5)


def test_uint_new_float() -> None:
    with pytest.raises(TypeError):
        Uint(0.1)  # type: ignore


def test_uint_radd() -> None:
    value = 4 + Uint(5)
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_radd_negative() -> None:
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        6 - Uint(7)


def test_uint_rsub_negative() -> None:
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        Uint(5) - 6


def test_uint_sub_negative() -> None:
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        value -= 6


def test_uint_isub_negative() -> None:
    value = Uint(5)
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        value //= -2


def test_uint_rmod() -> None:
    value = 6 % Uint(5)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_rmod_negative() -> None:
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        Uint(3) ** -2


def test_uint_pow_modulo() -> None:
    value = pow(Uint(4), 2, 3)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_pow_modulo_negative() -> None:
    with pytest.raises(ValueError):
        pow(Uint(4), 2, -3)


def test_uint_rpow() -> None:
    value = 3 ** Uint(2)
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_rpow_negative() -> None:
    with pytest.raises(ValueError):
        (-3) ** Uint(2)


def test_uint_rpow_modulo() -> None:
    value = Uint.__rpow__(Uint(2), 4, 3)
    assert isinstance(value, int)
    assert value == 1


def test_uint_rpow_modulo_negative() -> None:
    with pytest.raises(ValueError):
        Uint.__rpow__(Uint(2), 4, -3)


def test_uint_ipow() -> None:
    value = Uint(3)
    value **= 2
    assert isinstance(value, Uint)
    assert value == 9


def test_uint_ipow_negative() -> None:
    value = Uint(3)
    with pytest.raises(ValueError):
        value **= -2


def test_uint_ipow_modulo() -> None:
    value = Uint(4).__ipow__(2, 3)
    assert isinstance(value, Uint)
    assert value == 1


def test_uint_ipow_modulo_negative() -> None:
    with pytest.raises(ValueError):
        Uint(4).__ipow__(2, -3)
