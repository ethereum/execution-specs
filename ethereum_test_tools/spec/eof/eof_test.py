"""
Ethereum EOF test spec definition and filler.
"""

from typing import Callable, ClassVar, Generator, List, Optional, Type

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats

from ...common.base_types import Bytes
from ...exceptions import EOFException
from ..base.base_test import BaseFixture, BaseTest
from .types import Fixture


class EOFTest(BaseTest):
    """
    Filler type that tests EOF containers.
    """

    data: Bytes
    expect_exception: EOFException | None = None

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        # TODO: Potentially generate a state test and blockchain test too.
        FixtureFormats.EOF_TEST,
    ]

    def make_eof_test_fixture(
        self,
        *,
        fork: Fork,
        eips: Optional[List[int]],
    ) -> Fixture:
        """
        Generate the EOF test fixture.
        """
        return Fixture(
            vectors={
                "0": {
                    "code": self.data,
                    "results": {
                        fork.blockchain_test_network_name(): {
                            "exception": self.expect_exception,
                            "valid": self.expect_exception is None,
                        }
                    },
                }
            }
        )

    def generate(
        self,
        *,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormats,
        **_,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format == FixtureFormats.EOF_TEST:
            return self.make_eof_test_fixture(fork=fork, eips=eips)

        raise Exception(f"Unknown fixture format: {fixture_format}")


EOFTestSpec = Callable[[str], Generator[EOFTest, None, None]]
EOFTestFiller = Type[EOFTest]
