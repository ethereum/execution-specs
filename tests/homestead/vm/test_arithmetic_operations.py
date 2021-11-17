from functools import partial

import pytest

from ..vm.vm_test_helpers import run_test

run_arithmetic_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmArithmeticTest",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "add0.json",
        "add1.json",
        "add2.json",
        "add3.json",
        "add4.json",
    ],
)
def test_add(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "sub0.json",
        "sub1.json",
        "sub2.json",
        "sub3.json",
        "sub4.json",
    ],
)
def test_sub(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mul0.json",
        "mul1.json",
        "mul2.json",
        "mul3.json",
        "mul4.json",
        "mul5.json",
        "mul6.json",
        "mul7.json",
    ],
)
def test_mul(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "div1.json",
        "divBoostBug.json",
        "divByNonZero0.json",
        "divByNonZero1.json",
        "divByNonZero2.json",
        "divByNonZero3.json",
        "divByZero.json",
        "divByZero_2.json",
    ],
)
def test_div(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "sdiv0.json",
        "sdiv1.json",
        "sdiv2.json",
        "sdiv3.json",
        "sdiv4.json",
        "sdiv5.json",
        "sdiv6.json",
        "sdiv7.json",
        "sdiv8.json",
        "sdiv9.json",
        "sdivByZero0.json",
        "sdivByZero1.json",
        "sdivByZero2.json",
        "sdiv_i256min.json",
        "sdiv_i256min2.json",
        "sdiv_i256min3.json",
        "sdiv_dejavu.json",
    ],
)
def test_sdiv(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mod0.json",
        "mod1.json",
        "mod2.json",
        "mod3.json",
        "mod4.json",
        "modByZero.json",
    ],
)
def test_mod(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "smod0.json",
        "smod1.json",
        "smod2.json",
        "smod3.json",
        "smod4.json",
        "smod5.json",
        "smod6.json",
        "smod7.json",
        "smod8_byZero.json",
        "smod_i256min1.json",
        "smod_i256min2.json",
    ],
)
def test_smod(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "addmod0.json",
        "addmod1.json",
        "addmod1_overflow2.json",
        "addmod1_overflow3.json",
        "addmod1_overflow4.json",
        "addmod1_overflowDiff.json",
        "addmod2.json",
        "addmod2_0.json",
        "addmod2_1.json",
        "addmod3.json",
        "addmod3_0.json",
    ],
)
def test_addmod(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mulmod0.json",
        "mulmod1.json",
        "mulmod1_overflow.json",
        "mulmod1_overflow2.json",
        "mulmod1_overflow3.json",
        "mulmod1_overflow4.json",
        "mulmod2.json",
        "mulmod2_0.json",
        "mulmod2_1.json",
        "mulmod3.json",
        "mulmod3_0.json",
        "mulmod4.json",
    ],
)
def test_mulmod(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "exp0.json",
        "exp1.json",
        "exp2.json",
        "exp3.json",
        "exp4.json",
        "exp5.json",
        "exp6.json",
        "exp7.json",
        "exp8.json",
        "expXY.json",
        "expXY_success.json",
    ],
)
def test_exp(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


@pytest.mark.parametrize("exponent", ([2, 4, 8, 16, 32, 64, 128, 256]))
def test_exp_power_2(exponent: int) -> None:
    run_arithmetic_vm_test(f"expPowerOf2_{exponent}.json")


def test_exp_power_256() -> None:
    for i in range(1, 34):
        run_arithmetic_vm_test(f"expPowerOf256_{i}.json")

    for i in range(34):
        run_arithmetic_vm_test(f"expPowerOf256Of256_{i}.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "signextend_0_BigByte.json",
        "signextend_00.json",
        "signextend_AlmostBiggestByte.json",
        "signextend_BigByte_0.json",
        "signextend_BigByteBigByte.json",
        "signextend_BigBytePlus1_2.json",
        "signextend_bigBytePlus1.json",
        "signextend_BitIsNotSet.json",
        "signextend_BitIsNotSetInHigherByte.json",
        "signextend_bitIsSet.json",
        "signextend_BitIsSetInHigherByte.json",
        "signextend_Overflow_dj42.json",
        "signextendInvalidByteNumber.json",
    ],
)
def test_signextend(test_file: str) -> None:
    run_arithmetic_vm_test(test_file)


def test_stop() -> None:
    run_arithmetic_vm_test("stop.json")
