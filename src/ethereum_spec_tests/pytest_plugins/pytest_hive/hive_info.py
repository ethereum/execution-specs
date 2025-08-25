"""Hive instance information structures."""

from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, RootModel

from ethereum_test_base_types import CamelModel


class YAMLModel(BaseModel):
    """A helper class for YAML serialization of pydantic models."""

    def yaml(self, **kwargs):
        """Return the YAML representation of the model."""
        return yaml.dump(self.model_dump(), **kwargs)

    @classmethod
    def parse_yaml(cls, yaml_string):
        """Parse a YAML string into a model instance."""
        data = yaml.safe_load(yaml_string)
        return cls(**data)


class ClientConfig(YAMLModel):
    """
    Client configuration for YAML serialization.

    Represents a single client entry in the clients.yaml file.
    """

    client: str
    nametag: Optional[str] = None
    dockerfile: Optional[str] = None
    build_args: Optional[Dict[str, str]] = Field(default_factory=lambda: {})


class ClientFile(RootModel, YAMLModel):
    """
    Represents the entire clients.yaml file structure.

    The clients.yaml file is a list of client configurations.
    """

    root: List[ClientConfig]


class HiveInfo(CamelModel):
    """Hive instance information."""

    command: List[str]
    client_file: ClientFile = Field(default_factory=lambda: ClientFile(root=[]))
    commit: str
    date: str
