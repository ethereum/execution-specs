"""
Base test class and helper functions for Ethereum state and blockchain tests.
"""

import hashlib
import json
from abc import abstractmethod
from functools import cached_property, reduce
from itertools import count
from os import path
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, Generator, Iterator, List, Optional

from pydantic import BaseModel, Field

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats, TransitionTool

from ...common import Environment, Transaction, Withdrawal
from ...common.conversions import to_hex
from ...common.types import CamelModel, Result
from ...reference_spec.reference_spec import ReferenceSpec


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


class BaseFixture(CamelModel):
    """Represents a base Ethereum test fixture of any type."""

    info: Dict[str, str] = Field(default_factory=dict, alias="_info")
    format: ClassVar[FixtureFormats] = FixtureFormats.UNSET_TEST_FORMAT

    @cached_property
    def json_dict(self) -> Dict[str, Any]:
        """
        Returns the JSON representation of the fixture.
        """
        return self.model_dump(mode="json", by_alias=True, exclude_none=True, exclude={"info"})

    @cached_property
    def hash(self) -> str:
        """
        Returns the hash of the fixture.
        """
        json_str = json.dumps(self.json_dict, sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
        return f"0x{h}"

    def json_dict_with_info(self, hash_only: bool = False) -> Dict[str, Any]:
        """
        Returns the JSON representation of the fixture with the info field.
        """
        dict_with_info = self.json_dict.copy()
        dict_with_info["_info"] = {"hash": self.hash}
        if not hash_only:
            dict_with_info["_info"].update(self.info)
        return dict_with_info

    def fill_info(
        self,
        t8n: TransitionTool,
        ref_spec: ReferenceSpec | None,
    ):
        """
        Fill the info field for this fixture
        """
        if "comment" not in self.info:
            self.info["comment"] = "`execution-spec-tests` generated test"
        self.info["filling-transition-tool"] = t8n.version()
        if ref_spec is not None:
            ref_spec.write_info(self.info)


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
        if cls.__name__ == "EOFTest":
            return "eof_test"
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
