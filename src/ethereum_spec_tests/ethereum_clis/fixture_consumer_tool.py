"""Fixture consumer tool abstract class."""

from typing import List, Type

from ethereum_test_fixtures import FixtureConsumer, FixtureFormat

from .ethereum_cli import EthereumCLI


class FixtureConsumerTool(FixtureConsumer, EthereumCLI):
    """
    Fixture consumer tool abstract base class which should be inherited by all fixture consumer
    tool implementations.
    """

    registered_tools: List[Type["FixtureConsumerTool"]] = []
    default_tool: Type["FixtureConsumerTool"] | None = None

    def __init_subclass__(cls, *, fixture_formats: List[FixtureFormat]):
        """Register all subclasses of FixtureConsumerTool as possible tools."""
        FixtureConsumerTool.register_tool(cls)
        cls.fixture_formats = fixture_formats
