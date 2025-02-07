"""Hive instance information structures."""

from typing import List

from pydantic import BaseModel, Field

from ethereum_test_base_types import CamelModel


class ClientInfo(BaseModel):
    """Client information."""

    client: str
    nametag: str | None = None
    dockerfile: str | None = None
    build_args: dict[str, str] | None = None


class HiveInfo(CamelModel):
    """Hive instance information."""

    command: List[str]
    client_file: List[ClientInfo] = Field(default_factory=list)
    commit: str
    date: str
