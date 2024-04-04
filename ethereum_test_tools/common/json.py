"""
JSON encoding and decoding for Ethereum types.
"""

from typing import Any, Dict

from pydantic import BaseModel


def to_json(input: BaseModel) -> Dict[str, Any]:
    """
    Converts a value to its json representation.
    """
    return input.model_dump(mode="json", by_alias=True, exclude_none=True)
