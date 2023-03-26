import os
from functools import partial

import pytest

from .vm_test_helpers import run_test

run_bitwise_ops_vm_test = partial(
    run_test,
    os.path.join(
        os.environ["ETHEREUM_TESTS"],
        "LegacyTests/Constantinople/VMTests/vmBitwiseLogicOperation",
    ),
)


@pytest.mark.parametrize(
    "test_file",
    [
        "lt0.json",
        "lt1.json",
        "lt2.json",
        "lt3.json",
    ],
)
def test_lt(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "gt0.json",
        "gt1.json",
        "gt2.json",
        "gt3.json",
    ],
)
def test_gt(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "slt0.json",
        "slt1.json",
        "slt2.json",
        "slt3.json",
        "slt4.json",
    ],
)
def test_slt(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "sgt0.json",
        "sgt1.json",
        "sgt2.json",
        "sgt3.json",
        "sgt4.json",
    ],
)
def test_sgt(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "eq0.json",
        "eq1.json",
        "eq2.json",
    ],
)
def test_eq(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "iszero0.json",
        "iszero1.json",
        "iszeo2.json",
    ],
)
def test_iszero(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "and0.json",
        "and1.json",
        "and2.json",
        "and3.json",
        "and4.json",
        "and5.json",
    ],
)
def test_and(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "or0.json",
        "or1.json",
        "or2.json",
        "or3.json",
        "or4.json",
        "or5.json",
    ],
)
def test_or(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "xor0.json",
        "xor1.json",
        "xor2.json",
        "xor3.json",
        "xor4.json",
        "xor5.json",
    ],
)
def test_xor(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "not0.json",
        "not1.json",
        "not2.json",
        "not3.json",
        "not4.json",
        "not5.json",
    ],
)
def test_not(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "byte0.json",
        "byte1.json",
        "byte2.json",
        "byte3.json",
        "byte4.json",
        "byte5.json",
        "byte6.json",
        "byte7.json",
        "byte8.json",
        "byte9.json",
        "byte10.json",
        "byte11.json",
        "byteBN.json",
    ],
)
def test_byte(test_file: str) -> None:
    run_bitwise_ops_vm_test(test_file)
