"""A module for managing configuration for the `check_eip_version` utility."""

from pydantic import BaseModel


class CheckEipVersionsConfig(BaseModel):
    """A class for accessing configurations for `check_eip_version`."""

    UNTIL_FORK: str = "Prague"
    """The target fork to check eip versions until."""
