"""Tests for the gentest CLI command."""

from click.testing import CliRunner

from cli.gentest.cli import generate
from cli.gentest.test_context_providers import StateTestProvider
from cli.pytest_commands.fill import fill
from ethereum_test_base_types import Account
from ethereum_test_tools import Environment, Storage, Transaction


def test_generate_success(tmp_path, monkeypatch):
    """Test the generate command with a successful scenario."""
    ## Arrange ##

    # This test is run in a CI environment, where connection to a node could be
    # unreliable. Therefore, we mock the RPC request to avoid any network issues.
    # This is done by patching the `get_context` method of the `StateTestProvider`.
    runner = CliRunner()
    transaction_hash = "0xa41f343be7a150b740e5c939fa4d89f3a2850dbe21715df96b612fc20d1906be"
    output_file = str(tmp_path / "gentest.py")

    def get_mock_context(self: StateTestProvider) -> dict:
        return {
            "environment": Environment(
                fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
                gas_limit=9916577,
                number=9974504,
                timestamp=1588257377,
                prev_randao=None,
                difficulty=2315196811272822,
                base_fee_per_gas=None,
                excess_blob_gas=None,
                target_blobs_per_block=None,
                parent_difficulty=None,
                parent_timestamp=None,
                parent_base_fee_per_gas=None,
                parent_gas_used=None,
                parent_gas_limit=None,
                blob_gas_used=None,
                parent_ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
                parent_blob_gas_used=None,
                parent_excess_blob_gas=None,
                parent_beacon_block_root=None,
                block_hashes={},
                ommers=[],
                withdrawals=None,
                extra_data=b"\x00",
                parent_hash=None,
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
                max_priority_fee_per_gas=None,
                max_fee_per_gas=None,
                gas_limit=21000,
                to="0xc6d96786477f82491bfead8f00b8294688f77abc",
                value=668250000000000000,
                data=b"",
                access_list=None,
                max_fee_per_blob_gas=None,
                blob_versioned_hashes=None,
                v=38,
                r=57233334052658009540326312124836763247359579695589124499839562829147086216092,
                s=49687643984819828983661675232336138386174947240467726918882054280625462464348,
                sender="0x8a4a4d396a06cba2a7a4a73245991de40cdec289",
                authorization_list=None,
                secret_key=None,
                error=None,
                protected=True,
                rlp_override=None,
                wrapped_blob_transaction=False,
                blobs=None,
                blob_kzg_commitments=None,
                blob_kzg_proofs=None,
            ),
            "tx_hash": transaction_hash,
        }

    monkeypatch.setattr(StateTestProvider, "get_context", get_mock_context)

    ## Genenrate ##
    gentest_result = runner.invoke(generate, [transaction_hash, output_file])
    assert gentest_result.exit_code == 0

    ## Fill ##
    fill_result = runner.invoke(fill, ["-c", "pytest.ini", "--skip-evm-dump", output_file])
    assert fill_result.exit_code == 0, f"Fill command failed:\n{fill_result.output}"
