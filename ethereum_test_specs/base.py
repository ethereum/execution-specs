"""
Base test class and helper functions for Ethereum state and blockchain tests.
"""

from abc import abstractmethod
from functools import reduce
from itertools import count
from os import path
from pathlib import Path
from typing import Callable, ClassVar, Dict, Generator, Iterator, List, Optional

import pytest
from pydantic import BaseModel, Field

from ethereum_test_base_types import to_hex
from ethereum_test_fixtures import BaseFixture, FixtureFormats
from ethereum_test_forks import Fork
from ethereum_test_types import Environment, Transaction, Withdrawal
from evm_transition_tool import Result, TransitionTool


class HashMismatchException(Exception):
    """Exception raised when the expected and actual hashes don't match."""

    def __init__(self, expected_hash, actual_hash, message="Hashes do not match"):
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        self.message = message
        super().__init__(self.message)

    def __str__(self):  # noqa: D105
        return f"{self.message}: Expected {self.expected_hash}, got {self.actual_hash}"


def verify_transactions(txs: List[Transaction], result: Result) -> List[int]:
    """
    Verify rejected transactions (if any) against the expected outcome.
    Raises exception on unexpected rejections or unexpected successful txs.
    """
    rejected_txs: Dict[int, str] = {
        rejected_tx.index: rejected_tx.error for rejected_tx in result.rejected_transactions
    }

    for i, tx in enumerate(txs):
        error = rejected_txs[i] if i in rejected_txs else None
        if tx.error and not error:
            raise Exception(f"tx expected to fail succeeded: pos={i}, nonce={tx.nonce}")
        elif not tx.error and error:
            raise Exception(f"tx unexpectedly failed: {error}")

        # TODO: Also we need a way to check we actually got the
        # correct error
    return list(rejected_txs.keys())


def verify_result(result: Result, env: Environment):
    """
    Verify that values in the t8n result match the expected values.
    Raises exception on unexpected values.
    """
    if env.withdrawals is not None:
        assert result.withdrawals_root == to_hex(Withdrawal.list_root(env.withdrawals))


class BaseTest(BaseModel):
    """
    Represents a base Ethereum test which must return a single test fixture.
    """

    tag: str = ""

    # Transition tool specific fields
    t8n_dump_dir: Path | None = Field(None, exclude=True)
    _t8n_call_counter: Iterator[int] = count(0)

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = []

    @abstractmethod
    def generate(
        self,
        *,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormats,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """
        Generate the list of test fixtures.
        """
        pass

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Must return the name of the parameter used in pytest to select this
        spec type as filler for the test.

        By default, it returns the underscore separated name of the class.
        """
        return reduce(lambda x, y: x + ("_" if y.isupper() else "") + y, cls.__name__).lower()

    def get_next_transition_tool_output_path(self) -> str:
        """
        Returns the path to the next transition tool output file.
        """
        if not self.t8n_dump_dir:
            return ""
        return path.join(
            self.t8n_dump_dir,
            str(next(self._t8n_call_counter)),
        )


TestSpec = Callable[[Fork], Generator[BaseTest, None, None]]
