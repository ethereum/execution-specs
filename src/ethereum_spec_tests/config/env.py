"""
A module for exposing application-wide environment variables.

This module is responsible for loading, parsing, and validating the application's
environment configuration from the `env.yaml` file. It uses Pydantic to ensure that
the configuration adheres to expected formats and types.

Functions:
- create_default_config: Creates a default configuration file if it doesn't exist.

Classes:
- EnvConfig: Loads the configuration and exposes it as Python objects.
- RemoteNode: Represents a remote node configuration with validation.
- Config: Represents the overall configuration structure with validation.

Usage:
- Initialize an instance of EnvConfig to load the configuration.
- Access configuration values via properties (e.g., EnvConfig().remote_nodes).
"""

from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, HttpUrl, ValidationError

ENV_PATH = Path(__file__).resolve().parent.parent.parent / "env.yaml"


class RemoteNode(BaseModel):
    """
    Represents a configuration for a remote node.

    Attributes:
    - name (str): The name of the remote node.
    - node_url (HttpUrl): The URL for the remote node, validated as a proper URL.
    - rpc_headers (Dict[str, str]): A dictionary of optional RPC headers, defaults to empty dict.

    """

    name: str = "mainnet_archive"
    node_url: HttpUrl = HttpUrl("http://example.com")
    rpc_headers: Dict[str, str] = {"client-secret": "<secret>"}


class Config(BaseModel):
    """
    Represents the overall environment configuration.

    Attributes:
    - remote_nodes (List[RemoteNode]): A list of remote node configurations.

    """

    remote_nodes: List[RemoteNode] = [RemoteNode()]


class EnvConfig(Config):
    """
    Loads and validates environment configuration from `env.yaml`.

    This is a wrapper class for the Config model. It reads a config file
    from disk into a Config model and then exposes it.
    """

    def __init__(self):
        """Init for the EnvConfig class."""
        if not ENV_PATH.exists():
            raise FileNotFoundError(
                f"The configuration file '{ENV_PATH}' does not exist. "
                "Run `uv run eest make env` to create it."
            )

        with ENV_PATH.open("r") as file:
            config_data = yaml.safe_load(file)
            try:
                # Validate and parse with Pydantic
                super().__init__(**config_data)
            except ValidationError as e:
                raise ValueError(f"Invalid configuration: {e}") from e
