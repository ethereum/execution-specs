"""Chain Configuration related types for Ethereum tests."""

from pydantic import Field

from execution_testing.base_types import CamelModel

DEFAULT_CHAIN_ID = 1


class ChainConfigDefaults:
    """
    Default values for the chain configuration.

    Can be modified by modules that import this module and want to override the
    default values.
    """

    chain_id: int = DEFAULT_CHAIN_ID


class ChainConfig(CamelModel):
    """Chain configuration."""

    chain_id: int = Field(
        default_factory=lambda: ChainConfigDefaults.chain_id,
        validate_default=True,
    )
