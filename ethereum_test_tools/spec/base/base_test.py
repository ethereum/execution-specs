"""
Base test class and helper functions for Ethereum state and blockchain tests.
"""
from abc import abstractmethod
from dataclasses import dataclass, field
from itertools import count
from os import path
from typing import Any, Callable, Dict, Generator, Iterator, List, Mapping, Optional

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ...common import Account, Address, Environment, Transaction, withdrawals_root
from ...common.conversions import to_hex
from ...common.json import JSONEncoder
from ...common.json import field as json_field
from ...reference_spec.reference_spec import ReferenceSpec


def verify_transactions(txs: List[Transaction] | None, result) -> List[int]:
    """
    Verify rejected transactions (if any) against the expected outcome.
    Raises exception on unexpected rejections or unexpected successful txs.
    """
    rejected_txs: Dict[int, Any] = {}
    if "rejected" in result:
        for rejected_tx in result["rejected"]:
            if "index" not in rejected_tx or "error" not in rejected_tx:
                raise Exception("badly formatted result")
            rejected_txs[rejected_tx["index"]] = rejected_tx["error"]

    if txs is not None:
        for i, tx in enumerate(txs):
            error = rejected_txs[i] if i in rejected_txs else None
            if tx.error and not error:
                raise Exception(f"tx expected to fail succeeded: pos={i}, nonce={tx.nonce}")
            elif not tx.error and error:
                raise Exception(f"tx unexpectedly failed: {error}")

            # TODO: Also we need a way to check we actually got the
            # correct error
    return list(rejected_txs.keys())


def verify_post_alloc(expected_post: Mapping, got_alloc: Mapping):
    """
    Verify that an allocation matches the expected post in the test.
    Raises exception on unexpected values.
    """
    got_alloc_normalized: Dict[str, Any] = {
        Address(address).hex(): got_alloc[address] for address in got_alloc
    }
    for address, account in expected_post.items():
        address = Address(address).hex()
        if account is not None:
            if account == Account.NONEXISTENT:
                if address in got_alloc_normalized:
                    raise Exception(f"found unexpected account: {address}")
            else:
                if address in got_alloc_normalized:
                    account.check_alloc(address, got_alloc_normalized[address])
                else:
                    raise Exception(f"expected account not found: {address}")


def verify_result(result: Mapping, env: Environment):
    """
    Verify that values in the t8n result match the expected values.
    Raises exception on unexpected values.
    """
    if env.withdrawals is not None:
        assert result["withdrawalsRoot"] == to_hex(withdrawals_root(env.withdrawals))


@dataclass(kw_only=True)
class BaseTestConfig:
    """
    General configuration that all tests must support.
    """

    enable_hive: bool = False
    """
    Enable any hive-related properties that the output could contain.
    """
    blockchain_test: bool = False
    """
    Enable BlockchainTest type tests production.
    """
    state_test: bool = False
    """
    Enable StateTest type tests production.
    """


@dataclass(kw_only=True)
class BaseFixture:
    """
    Represents a base Ethereum test fixture of any type.
    """

    info: Dict[str, str] = json_field(
        default_factory=dict,
        json_encoder=JSONEncoder.Field(
            name="_info",
            to_json=True,
        ),
    )

    def fill_info(
        self,
        t8n: TransitionTool,
        ref_spec: ReferenceSpec | None,
    ):
        """
        Fill the info field for this fixture
        """
        self.info["filling-transition-tool"] = t8n.version()
        if ref_spec is not None:
            ref_spec.write_info(self.info)

    def to_json(self) -> Dict[str, Any]:
        """
        Convert to JSON.

        TODO: This has to be replaced in the future to allow for different fixtures to do whatever
        they want in the output file, and somehow be able to merge themselves automatically with
        other fixtures of the same type.
        """
        pass


@dataclass(kw_only=True)
class BaseTest:
    """
    Represents a base Ethereum test which must return a genesis and a
    blockchain.
    """

    pre: Mapping
    tag: str = ""
    base_test_config: BaseTestConfig = field(default_factory=BaseTestConfig)

    # Transition tool specific fields
    t8n_dump_dir: Optional[str] = ""
    t8n_call_counter: Iterator[int] = field(init=False, default_factory=count)

    @abstractmethod
    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> Optional[BaseFixture]:
        """
        Generate the test fixture.
        """
        pass

    @classmethod
    @abstractmethod
    def pytest_parameter_name(cls) -> str:
        """
        Must return the name of the parameter used in pytest to select this
        spec type as filler for the test.
        """
        pass

    def get_next_transition_tool_output_path(self) -> str:
        """
        Returns the path to the next transition tool output file.
        """
        if not self.t8n_dump_dir:
            return ""
        return path.join(
            self.t8n_dump_dir,
            str(next(self.t8n_call_counter)),
        )


TestSpec = Callable[[Fork], Generator[BaseTest, None, None]]
