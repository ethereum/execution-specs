"""Tests for the gentest CLI command."""

import pytest
from click.testing import CliRunner

from cli.gentest.cli import generate
from cli.gentest.test_context_providers import StateTestProvider
from cli.pytest_commands.fill import fill
from ethereum_test_base_types import Account
from ethereum_test_tools import Environment, Storage, Transaction

transactions_by_type = {
    0: {
        "environment": Environment(
            fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
            gas_limit=9916577,
            number=9974504,
            timestamp=1588257377,
            difficulty=2315196811272822,
            parent_ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
            extra_data=b"\x00",
        ),
        "pre_state": {
            "0x5a0b54d5dc17e0aadc383d2db43b0a0d3e029c4c": Account(
                nonce=6038603, balance=23760714652307793035, code=b"", storage=Storage(root={})
            ),
            "0x8a4a4d396a06cba2a7a4a73245991de40cdec289": Account(
                nonce=2, balance=816540000000000000, code=b"", storage=Storage(root={})
            ),
            "0xc6d96786477f82491bfead8f00b8294688f77abc": Account(
                nonce=25, balance=29020266497911578313, code=b"", storage=Storage(root={})
            ),
        },
        "transaction": Transaction(
            ty=0,
            chain_id=1,
            nonce=2,
            gas_price=10000000000,
            gas_limit=21000,
            to="0xc6d96786477f82491bfead8f00b8294688f77abc",
            value=668250000000000000,
            data=b"",
            v=38,
            r=57233334052658009540326312124836763247359579695589124499839562829147086216092,
            s=49687643984819828983661675232336138386174947240467726918882054280625462464348,
            sender="0x8a4a4d396a06cba2a7a4a73245991de40cdec289",
        ),
    },
    2: {
        "environment": Environment(
            fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
            gas_limit=30172625,
            number=21758000,
            timestamp=1738489319,
            parent_ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
            extra_data=b"\x00",
        ),
        "pre_state": {
            "0x24d6c74d811cfde65995ed26fd08af445f8aab06": Account(
                nonce=1011, balance=139840767390685635650, code=b"", storage=Storage(root={})
            ),
            "0xd5fbda4c79f38920159fe5f22df9655fde292d47": Account(
                nonce=553563, balance=162510989019530720334, code=b"", storage=Storage(root={})
            ),
            "0xe2e29f9a85cfecb9cdaa83a81c7aa2792f24d93f": Account(
                nonce=104, balance=553317651330968100, code=b"", storage=Storage(root={})
            ),
        },
        "transaction": Transaction(
            ty=2,
            chain_id=1,
            nonce=553563,
            max_priority_fee_per_gas=1900000,
            max_fee_per_gas=3992652948,
            gas_limit=63000,
            to="0xe2e29f9a85cfecb9cdaa83a81c7aa2792f24d93f",
            value=221305417266040400,
            v=1,
            r=23565967349511399087318407428036702220029523660288023156323795583373026415631,
            s=9175853102116430015855393834807954374677057556696757715994220939907579927771,
            sender="0xd5fbda4c79f38920159fe5f22df9655fde292d47",
        ),
    },
}


@pytest.fixture
def transaction_hash(tx_type: int) -> str:  # noqa: D103
    return str(transactions_by_type[tx_type]["transaction"].hash)  # type: ignore


@pytest.mark.parametrize("tx_type", list(transactions_by_type.keys()))
def test_tx_type(tmp_path, monkeypatch, tx_type, transaction_hash):
    """Generates a test case for any transaction type."""
    ## Arrange ##
    # This test is run in a CI environment, where connection to a node could be
    # unreliable. Therefore, we mock the RPC request to avoid any network issues.
    # This is done by patching the `get_context` method of the `StateTestProvider`.
    runner = CliRunner()
    output_file = str(tmp_path / f"gentest_type_{tx_type}.py")

    tx = transactions_by_type[tx_type]

    def get_mock_context(self: StateTestProvider) -> dict:
        return tx

    monkeypatch.setattr(StateTestProvider, "get_context", get_mock_context)

    ## Generate ##
    gentest_result = runner.invoke(generate, [transaction_hash, output_file])
    assert gentest_result.exit_code == 0

    ## Fill ##
    fill_result = runner.invoke(fill, ["-c", "pytest.ini", "--skip-evm-dump", output_file])
    assert fill_result.exit_code == 0, f"Fill command failed:\n{fill_result.output}"
