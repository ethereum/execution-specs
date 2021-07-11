from functools import partial

import pytest

from tests.frontier.vm.vm_test_helpers import run_test

run_push_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmPushDupSwapTest",
)
run_dup_vm_test = run_swap_vm_test = run_push_vm_test


def test_push_successfully() -> None:
    for i in range(1, 34):
        run_push_vm_test(f"push{i}.json")

    run_push_vm_test("push32Undefined2.json")
    # TODO: Run below test once suicide opcode has been implemented
    # "push32AndSuicide.json"


@pytest.mark.parametrize(
    "test_file",
    [
        "push1_missingStack.json",
        "push32Undefined.json",
        "push32Undefined3.json",
        "push32FillUpInputWithZerosAtTheEnd.json",
    ],
)
def test_push_failed(test_file: str) -> None:
    with pytest.raises(AssertionError):
        run_push_vm_test(test_file)


def test_dup() -> None:
    for i in range(1, 17):
        run_dup_vm_test(f"dup{i}.json")


def test_dup_error() -> None:
    with pytest.raises(AssertionError):
        run_dup_vm_test("dup2error.json")


def test_swap() -> None:
    for i in range(1, 17):
        run_swap_vm_test(f"swap{i}.json")

    # TODO: Run below test once JUMP opcode has been implemented
    # "swapjump1.json"


def test_swap_error() -> None:
    with pytest.raises(AssertionError):
        run_swap_vm_test("swap2error.json")
