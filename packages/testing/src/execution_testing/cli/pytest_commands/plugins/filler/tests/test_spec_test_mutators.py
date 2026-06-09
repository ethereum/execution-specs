"""Test the spec-test mutator integration with the filler plugin."""

import json
import textwrap
from pathlib import Path
from typing import Any, Dict

import pytest

DELEGATION_PREFIX = "0xef0100"


test_module_contract = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Environment,
        Op,
        StateTestFiller,
        Transaction,
    )


    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Prague")
    def test_with_contract(state_test: StateTestFiller, pre: Alloc) -> None:
        sender = pre.fund_eoa()
        contract = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)
        tx = Transaction(to=contract, gas_limit=200_000, sender=sender)
        state_test(env=Environment(), pre=pre, post={}, tx=tx)
    """
)


def load_pre_alloc(fixture_path: Path) -> Dict[str, Dict[str, Any]]:
    """Merge the ``pre`` sections of every fixture in the file."""
    data = json.loads(fixture_path.read_text())
    merged: Dict[str, Dict[str, Any]] = {}
    for fixture in data.values():
        merged.update(fixture["pre"])
    return merged


@pytest.fixture()
def contract_test_dir(testdir: pytest.Testdir) -> Any:
    """Create tests/contract_test/test_module.py with a state test."""
    tests_dir = testdir.mkdir("tests")
    contract_dir = tests_dir.mkdir("contract_test")
    contract_dir.join("test_module.py").write(test_module_contract)
    return contract_dir


@pytest.fixture()
def fill_args(testdir: pytest.Testdir) -> list[str]:
    """Copy fill ini and return base pytest args."""
    testdir.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands"
            "/pytest_ini_files/pytest-fill.ini"
        )
    )
    return [
        "-c",
        "pytest-fill.ini",
        "--no-html",
        "--skip-index",
        "-m",
        "state_test",
        "--until=Prague",
        "--test-mutators=EIP_7702_ALL_CONTRACTS_AS_DELEGATIONS",
    ]


def test_eip_7702_mutator_applied_at_prague(
    testdir: pytest.Testdir,
    contract_test_dir: Any,
    fill_args: list[str],
) -> None:
    """
    Verify the EIP-7702 mutator turns every deployed contract into a
    delegated EOA when filling for Prague.

    The mutated fixture must contain at least one account whose code is a
    delegation designator (``0xef0100`` followed by an address), and the
    original contract bytecode must still appear in a separate account so
    the delegation can resolve to it.
    """
    del contract_test_dir
    result = testdir.runpytest(*fill_args)
    assert result.ret == 0, f"fill exited with non-zero status: {result.ret}"

    fixture_path = Path(
        "fixtures/state_tests/for_prague/contract_test/module/with_contract.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    pre = load_pre_alloc(fixture_path)
    delegations = {
        addr: account["code"]
        for addr, account in pre.items()
        if account.get("code", "0x").startswith(DELEGATION_PREFIX)
    }
    assert delegations, (
        "Expected at least one delegated EOA in the Prague pre-alloc, "
        f"got pre={pre}"
    )

    target_address = (
        "0x" + next(iter(delegations.values()))[len(DELEGATION_PREFIX) :]
    )
    target_account = pre.get(target_address.lower())
    assert target_account is not None, (
        f"Delegation target {target_address} not present in pre-alloc"
    )
    assert target_account.get("code", "0x") != "0x", (
        "Delegation target should hold the original contract bytecode"
    )


@pytest.mark.parametrize("fork", ["paris", "shanghai", "cancun"])
def test_eip_7702_mutator_not_applied_before_prague(
    testdir: pytest.Testdir,
    contract_test_dir: Any,
    fill_args: list[str],
    fork: str,
) -> None:
    """
    Verify the EIP-7702 mutator has no effect on forks that don't support
    it, even when the user enables it via ``--test-mutators``.

    The pre-alloc for Paris/Shanghai/Cancun must contain no delegation
    designators, so contracts remain plain contract accounts.
    """
    del contract_test_dir
    result = testdir.runpytest(*fill_args)
    assert result.ret == 0, f"fill exited with non-zero status: {result.ret}"

    fixture_path = Path(
        f"fixtures/state_tests/for_{fork}/contract_test/module/"
        "with_contract.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    pre = load_pre_alloc(fixture_path)
    delegations = [
        account["code"]
        for account in pre.values()
        if account.get("code", "0x").startswith(DELEGATION_PREFIX)
    ]
    assert not delegations, (
        f"Unexpected delegation designators in {fork} pre-alloc: {delegations}"
    )
