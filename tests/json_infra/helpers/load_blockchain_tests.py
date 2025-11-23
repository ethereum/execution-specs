"""Helpers to load and run blockchain tests from JSON files."""

import importlib
from pathlib import Path
from typing import Any, Dict, Tuple
from unittest.mock import call, patch

import pytest
from _pytest.config import Config
from ethereum_rlp import rlp
from ethereum_rlp.exceptions import RLPException
from ethereum_types.numeric import U64

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import EthereumException, StateWithEmptyAccount
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.evm_tools.loaders.fixture_loader import Load

from .. import FORKS
from ..stash_keys import desired_forks_key
from .exceptional_test_patterns import exceptional_blockchain_test_patterns
from .fixtures import Fixture, FixturesFile, FixtureTestItem


class NoTestsFoundError(Exception):
    """
    An exception thrown when the test for a particular fork isn't
    available in the json fixture.
    """


def add_block_to_chain(
    chain: Any, json_block: Any, load: Load, mock_pow: bool
) -> None:
    """Add a block from JSON data to the blockchain chain."""
    (
        block,
        block_header_hash,
        block_rlp,
    ) = load.json_to_block(json_block)

    assert keccak256(rlp.encode(block.header)) == block_header_hash
    assert rlp.encode(block) == block_rlp

    if not mock_pow:
        load.fork.state_transition(chain, block)
    else:
        fork_module = importlib.import_module(
            f"ethereum.forks.{load.fork.fork_module}.fork"
        )
        with patch.object(
            fork_module,
            "validate_proof_of_work",
            autospec=True,
        ) as mocked_pow_validator:
            load.fork.state_transition(chain, block)
            mocked_pow_validator.assert_has_calls(
                [call(block.header)],
                any_order=False,
            )


class BlockchainTestFixture(Fixture, FixtureTestItem):
    """Single blockchain test fixture from a JSON file."""

    fork_name: str

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a single blockchain test fixture from a JSON file."""
        super().__init__(*args, **kwargs)
        self.fork_name = self.test_dict["network"]
        self.add_marker(pytest.mark.fork(self.fork_name))
        self.add_marker("json_blockchain_tests")
        self.eels_fork = FORKS[self.fork_name].short_name

        # Mark tests with exceptional markers
        test_patterns = exceptional_blockchain_test_patterns(
            self.fork_name, self.eels_fork
        )
        if any(x.search(self.nodeid) for x in test_patterns.expected_fail):
            self.add_marker(pytest.mark.skip("Expected to fail"))
        if any(x.search(self.nodeid) for x in test_patterns.slow):
            self.add_marker("slow")
        if any(x.search(self.nodeid) for x in test_patterns.big_memory):
            self.add_marker("bigmem")

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which the test fixture was collected."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, FixturesFile)
        return parent

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load test from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def runtest(self) -> None:
        """Run a blockchain state test from JSON test case data."""
        json_data = self.test_dict
        if "postState" not in json_data:
            pytest.xfail(
                f"{self.test_file}[{self.test_key}] doesn't have post state"
            )

        # Currently, there are 5 tests in the ethereum/tests fixtures
        # where we have non block specific exceptions.
        # For example: All the blocks process correctly but the final
        # block hash provided in the test is not correct. Or all the
        # blocks process correctly but the post state provided is not
        # right. Since these tests do not directly have anything to do
        # with the state teansition itself, we skip these
        # See src/BlockchainTestsFiller/InvalidBlocks/bcExpectSection
        # in ethereum/tests
        if "exceptions" in json_data:
            pytest.xfail(
                f"{self.test_file}[{self.test_key}] has unrelated exceptions"
            )

        load = Load(
            self.fork_name,
            self.eels_fork,
        )

        genesis_header = load.json_to_header(json_data["genesisBlockHeader"])
        parameters = [
            genesis_header,
            (),
            (),
        ]
        if hasattr(genesis_header, "withdrawals_root"):
            parameters.append(())

        if hasattr(genesis_header, "requests_root"):
            parameters.append(())

        genesis_block = load.fork.Block(*parameters)

        genesis_header_hash = hex_to_bytes(
            json_data["genesisBlockHeader"]["hash"]
        )
        assert keccak256(rlp.encode(genesis_header)) == genesis_header_hash
        genesis_rlp = hex_to_bytes(json_data["genesisRLP"])
        assert rlp.encode(genesis_block) == genesis_rlp

        try:
            state = load.json_to_state(json_data["pre"])
        except StateWithEmptyAccount as e:
            pytest.xfail(str(e))

        chain = load.fork.BlockChain(
            blocks=[genesis_block],
            state=state,
            chain_id=U64(json_data["genesisBlockHeader"].get("chainId", 1)),
        )

        mock_pow = (
            json_data["sealEngine"] == "NoProof"
            and not load.fork.proof_of_stake
        )

        for json_block in json_data["blocks"]:
            block_exception = None
            for key, value in json_block.items():
                if key.startswith("expectException"):
                    block_exception = value
                    break
                if key == "exceptions":
                    block_exception = value
                    break

            if block_exception:
                # TODO: Once all the specific exception types are thrown,
                #       only `pytest.raises` the correct exception type instead
                #       of all of them.
                with pytest.raises((EthereumException, RLPException)):
                    add_block_to_chain(chain, json_block, load, mock_pow)
                    load.fork.close_state(chain.state)
                return
            else:
                add_block_to_chain(chain, json_block, load, mock_pow)

        last_block_hash = hex_to_bytes(json_data["lastblockhash"])
        assert (
            keccak256(rlp.encode(chain.blocks[-1].header)) == last_block_hash
        )

        expected_post_state = load.json_to_state(json_data["postState"])
        assert chain.state == expected_post_state
        load.fork.close_state(chain.state)
        load.fork.close_state(expected_post_state)

    def reportinfo(self) -> Tuple[Path, int, str]:
        """Return information for test reporting."""
        return self.path, 1, self.name

    @classmethod
    def is_format(cls, test_dict: Dict[str, Any]) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        if "genesisBlockHeader" not in test_dict:
            return False
        if "blocks" not in test_dict:
            return False
        if "engineNewPayloads" in test_dict:
            return False
        if "preHash" in test_dict:
            return False
        if "network" not in test_dict:
            return False
        return True

    @classmethod
    def has_desired_fork(
        cls, test_dict: Dict[str, Any], config: Config
    ) -> bool:
        """
        Check if the item fork is in the desired forks list.
        """
        desired_forks = config.stash.get(desired_forks_key, None)
        if desired_forks is None or test_dict["network"] in desired_forks:
            return True
        return False
