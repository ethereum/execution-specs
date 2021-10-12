from functools import partial

import pytest

from ..vm.vm_test_helpers import run_test

run_sha3_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmSha3Test",
)
run_special_sha3_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "sha3_0.json",
        "sha3_1.json",
        "sha3_2.json",
        "sha3_bigOffset2.json",
        "sha3_memSizeNoQuadraticCost31.json",
        "sha3_memSizeQuadraticCost32.json",
        "sha3_memSizeQuadraticCost32_zeroSize.json",
        "sha3_memSizeQuadraticCost33.json",
        "sha3_memSizeQuadraticCost63.json",
        "sha3_memSizeQuadraticCost64.json",
        "sha3_memSizeQuadraticCost64_2.json",
        "sha3_memSizeQuadraticCost65.json",
        "sha3_3.json",
        "sha3_4.json",
        "sha3_5.json",
        "sha3_6.json",
        "sha3_bigOffset.json",
        "sha3_bigSize.json",
    ],
)
def test_sha3_succeeds(test_file: str) -> None:
    run_sha3_vm_test(test_file)


def test_sha3_fails_out_of_gas_memory_expansion() -> None:
    run_special_sha3_vm_test("sha3MemExp.json")
