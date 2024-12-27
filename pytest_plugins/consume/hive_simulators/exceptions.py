"""Custom exceptions utilized within consume simulators."""

import pprint
from typing import Dict, List, Tuple

from ethereum_test_fixtures.blockchain import FixtureHeader


class GenesisBlockMismatchExceptionError(Exception):
    """Definers a mismatch exception between the client and fixture genesis blockhash."""

    def __init__(self, *, expected_header: FixtureHeader, got_genesis_block: Dict[str, str]):
        """Initialize the exception with the expected and received genesis block headers."""
        message = (
            "Genesis block hash mismatch.\n\n"
            f"Expected: {expected_header.block_hash}\n"
            f"     Got: {got_genesis_block['hash']}."
        )
        differences, unexpected_fields = self.compare_models(
            expected_header, FixtureHeader(**got_genesis_block)
        )
        if differences:
            message += (
                "\n\nGenesis block header field differences:\n"
                f"{pprint.pformat(differences, indent=4)}"
            )
        elif unexpected_fields:
            message += (
                "\n\nUn-expected genesis block header fields from client:\n"
                f"{pprint.pformat(unexpected_fields, indent=4)}"
                "\nIs the fork configuration correct?"
            )
        else:
            message += (
                "There were no differences in the expected and received genesis block headers."
            )
        super().__init__(message)

    @staticmethod
    def compare_models(expected: FixtureHeader, got: FixtureHeader) -> Tuple[Dict, List]:
        """Compare two FixtureHeader model instances and return their differences."""
        differences = {}
        unexpected_fields = []
        for (exp_name, exp_value), (got_name, got_value) in zip(expected, got, strict=False):
            if "rlp" in exp_name or "fork" in exp_name:  # ignore rlp as not verbose enough
                continue
            if exp_value != got_value:
                differences[exp_name] = {
                    "expected     ": str(exp_value),
                    "got (via rpc)": str(got_value),
                }
            if got_value is None:
                unexpected_fields.append(got_name)
        return differences, unexpected_fields
