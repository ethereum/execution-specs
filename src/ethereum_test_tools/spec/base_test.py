"""
Generic Ethereum test base class
"""
import pprint
from abc import abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Mapping,
    Optional,
    Tuple,
)

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import Account, FixtureBlock, FixtureHeader, Transaction


def print_traces(traces: List[List[Dict]]):
    print("Printing traces for debugging purposes:")
    pp = pprint.PrettyPrinter(indent=4)
    for number, block in enumerate(traces):
        print(f"Block {number}:")
        pp.pprint(block)


def normalize_address(address: str) -> str:
    """
    Normalizes an address to be able to look it up in the alloc that is
    produced by the transition tool.
    """
    address = address.lower()
    if address.startswith("0x"):
        address = address[2:]
    address.rjust(40, "0")
    if len(address) > 40:
        raise Exception("invalid address")

    return "0x" + address


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
                raise Exception("tx expected to fail succeeded")
            elif not tx.error and error:
                raise Exception(f"tx unexpectedly failed: {error}")

            # TODO: Also we need a way to check we actually got the
            # correct error
    return list(rejected_txs.keys())


def verify_post_alloc(
    expected_post: Mapping[str, Account], got_alloc: Mapping[str, Any]
):
    """
    Verify that an allocation matches the expected post in the test.
    Raises exception on unexpected values.
    """
    for address, account in expected_post.items():
        address = normalize_address(address)
        if account is not None:
            if account == Account.NONEXISTENT:
                if address in got_alloc:
                    raise Exception(f"found unexpected account: {address}")
            else:
                if address in got_alloc:
                    account.check_alloc(address, got_alloc[address])
                else:
                    raise Exception(f"expected account not found: {address}")


class BaseTest:
    """
    Represents a base Ethereum test which must return a genesis and a
    blockchain.
    """

    pre: Mapping[str, Account]
    name: str = ""

    @abstractmethod
    def make_genesis(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: str,
    ) -> FixtureHeader:
        """
        Create a genesis block from the test definition.
        """
        pass

    @abstractmethod
    def make_blocks(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        genesis: FixtureHeader,
        fork: str,
        chain_id: int = 1,
        reward: int = 0,
        eips: Optional[List[int]] = None,
    ) -> Tuple[List[FixtureBlock], str, Dict[str, Any]]:
        """
        Generate the blockchain that must be executed sequentially during test.
        """
        pass


TestSpec = Callable[[str], Generator[BaseTest, None, None]]
