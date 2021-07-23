from functools import partial

from tests.frontier.vm.vm_test_helpers import run_test

run_block_ops_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmBlockInfoTest",
)


def test_coinbase() -> None:
    run_block_ops_vm_test("coinbase.json")


def test_timestamp() -> None:
    run_block_ops_vm_test("timestamp.json")


def test_number() -> None:
    run_block_ops_vm_test("number.json")


def test_difficulty() -> None:
    run_block_ops_vm_test("difficulty.json")


def test_gas_limit() -> None:
    run_block_ops_vm_test("gaslimit.json")
