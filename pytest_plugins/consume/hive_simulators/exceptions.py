"""
Custom exceptions utilized within consume simulators.
"""

import pprint

from ethereum_test_fixtures.blockchain import FixtureHeader


class GenesisBlockMismatchException(Exception):
    """
    Definers a mismatch exception between the client and fixture genesis blockhash.
    """

    def __init__(self, *, expected_header: FixtureHeader, got_header: FixtureHeader):
        message = (
            "Genesis block hash mismatch.\n\n"
            f"Expected: {expected_header.block_hash}\n"
            f"     Got: {got_header.block_hash}."
        )
        differences = self.compare_models(expected_header, got_header)
        if differences:
            message += (
                "\n\nGenesis block header field differences:\n"
                f"{pprint.pformat(differences, indent=4)}"
            )
        else:
            message += (
                "There were no differences in the expected and received genesis block headers."
            )
        super().__init__(message)

    @staticmethod
    def compare_models(expected: FixtureHeader, got: FixtureHeader) -> dict:
        """
        Compare two FixtureHeader model instances and return their differences.
        """
        differences = {}
        for (exp_name, exp_value), (_, got_value) in zip(expected, got):
            if "rlp" in exp_name or "fork" in exp_name:  # ignore rlp as not verbose enough
                continue
            if exp_value is None or got_value is None or exp_value != got_value:
                differences[exp_name] = {
                    "expected     ": str(exp_value),
                    "got (via rpc)": str(got_value),
                }
        return differences
