"""
JSON encoding and decoding for Ethereum types.
"""

from typing import Any, Dict

from pydantic import BaseModel, RootModel


def to_json(input: BaseModel | RootModel) -> Dict[str, Any]:
    """
    Converts a model to its json data representation.
    """
    return input.model_dump(mode="json", by_alias=True, exclude_none=True)
